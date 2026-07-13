#!/usr/bin/env python3
"""
Collection Transfer - index folders locally, upload the result to the server.

Lets a workstation do the heavy indexing work (document download, OCR,
embedding) and ship the finished vectors to the production server, so the
server never spends CPU/API time indexing.

Workflow:
    # 1. On your local machine: index the folder as usual
    python incremental_indexer.py --folder <FOLDER_ID>
    #    (or use the admin dashboard / folder_indexer.py)

    # 2. Export the finished collection to a package file
    python collection_transfer.py export --folder <FOLDER_ID>
    #    -> writes folder_<FOLDER_ID>.ragpack.gz

    # 3. Copy the package to the server (scp, Plesk file manager, etc.)
    scp folder_<FOLDER_ID>.ragpack.gz user@server:/path/to/rag-system/

    # 4. On the server: import it (no re-embedding happens)
    python collection_transfer.py import folder_<FOLDER_ID>.ragpack.gz

    # Optional: inspect a package without importing
    python collection_transfer.py inspect folder_<FOLDER_ID>.ragpack.gz

The package contains the chunk texts, embeddings, metadata, the file-tracker
rows (so incremental sync on the server knows these files are up to date),
and the indexed_folders.json entry (so the chat app lists the collection).

IMPORTANT: local and server must use the same embedding model
(USE_VERTEX_EMBEDDINGS in config.py) — the import checks dimensions and
refuses mismatches.
"""

import argparse
import gzip
import json
import os
import sys
from datetime import datetime

PACKAGE_VERSION = 1
BATCH_SIZE = 500


def _collection_name(folder_id: str) -> str:
    return f"folder_{folder_id}"


def _load_indexed_folders() -> dict:
    if os.path.exists('indexed_folders.json'):
        with open('indexed_folders.json', 'r') as f:
            return json.load(f)
    return {}


def export_folder(folder_id: str, output: str = None) -> int:
    """Export one folder's collection + tracker state to a package file."""
    from vector_store import VectorStore
    from file_tracker import FileTracker

    name = _collection_name(folder_id)
    output = output or f"{name}.ragpack.gz"

    vs = VectorStore(collection_name=name)
    total = vs.collection.count()
    if total == 0:
        print(f"ERROR: collection '{name}' is empty — index the folder first")
        return 1

    tracker = FileTracker()
    tracker_rows = tracker.get_files_in_folder(folder_id)

    folder_entry = _load_indexed_folders().get(folder_id, {})

    # Peek one embedding for the dimension
    sample = vs.collection.get(limit=1, include=['embeddings'])
    sample_emb = sample.get('embeddings')
    dim = len(sample_emb[0]) if sample_emb is not None and len(sample_emb) else 0

    manifest = {
        'version': PACKAGE_VERSION,
        'folder_id': folder_id,
        'collection_name': name,
        'folder_name': folder_entry.get('name', ''),
        'chunk_count': total,
        'embedding_dim': dim,
        'tracked_files': len(tracker_rows),
        'exported_at': datetime.utcnow().isoformat(),
        'tracker_rows': tracker_rows,
        'indexed_folders_entry': folder_entry,
    }

    print(f"Exporting '{name}': {total} chunks, {len(tracker_rows)} tracked files, dim={dim}")

    written = 0
    with gzip.open(output, 'wt', encoding='utf-8') as out:
        out.write(json.dumps({'manifest': manifest}) + '\n')

        offset = 0
        while offset < total:
            batch = vs.collection.get(
                limit=BATCH_SIZE,
                offset=offset,
                include=['documents', 'metadatas', 'embeddings']
            )
            ids = batch.get('ids', [])
            if not ids:
                break
            docs = batch.get('documents') or []
            metas = batch.get('metadatas') or []
            embs = batch.get('embeddings')
            embs = embs if embs is not None else []

            for i, chunk_id in enumerate(ids):
                emb = embs[i]
                if hasattr(emb, 'tolist'):
                    emb = emb.tolist()
                out.write(json.dumps({
                    'id': chunk_id,
                    'document': docs[i],
                    'metadata': metas[i],
                    'embedding': emb,
                }) + '\n')
                written += 1

            offset += len(ids)
            print(f"  exported {min(offset, total)}/{total} chunks...")

    size_mb = os.path.getsize(output) / (1024 * 1024)
    print(f"\nDone: {output} ({written} chunks, {size_mb:.1f} MB)")
    print("Copy this file to the server and run:")
    print(f"  python collection_transfer.py import {os.path.basename(output)}")
    return 0


def export_all(output_dir: str = '.') -> int:
    """Export every folder in indexed_folders.json to package files."""
    folders = _load_indexed_folders()
    if not folders:
        print("ERROR: indexed_folders.json is empty — nothing to export")
        return 1

    exported, failed = [], []
    for folder_id, info in folders.items():
        name = info.get('name', folder_id)
        print(f"\n=== {name} ===")
        out = os.path.join(output_dir, f"folder_{folder_id}.ragpack.gz")
        try:
            if export_folder(folder_id, out) == 0:
                exported.append(out)
            else:
                failed.append(name)
        except Exception as e:
            print(f"ERROR exporting {name}: {e}")
            failed.append(name)

    print(f"\n{'=' * 50}")
    print(f"Exported {len(exported)} package(s)" +
          (f"; failed/empty: {', '.join(failed)}" if failed else ""))
    if exported:
        print("\nCopy the .ragpack.gz files to the server, then run there:")
        print("  python collection_transfer.py import " +
              " ".join(os.path.basename(p) for p in exported))
    return 0 if exported else 1


def _read_package(path: str):
    """Yield (manifest, chunk_iterator) from a package file."""
    f = gzip.open(path, 'rt', encoding='utf-8')
    header = json.loads(f.readline())
    manifest = header['manifest']

    def chunks():
        with f:
            for line in f:
                line = line.strip()
                if line:
                    yield json.loads(line)

    return manifest, chunks()


def inspect_package(path: str) -> int:
    """Print a package's manifest without importing it."""
    manifest, _ = _read_package(path)
    print(json.dumps({k: v for k, v in manifest.items()
                      if k not in ('tracker_rows',)}, indent=2))
    print(f"tracker_rows: {len(manifest.get('tracker_rows', []))} entries")
    return 0


def import_package(path: str, replace: bool = False) -> int:
    """Import a package into this machine's ChromaDB + tracker."""
    from vector_store import VectorStore
    from file_tracker import FileTracker

    manifest, chunk_iter = _read_package(path)

    if manifest.get('version') != PACKAGE_VERSION:
        print(f"ERROR: unsupported package version {manifest.get('version')}")
        return 1

    folder_id = manifest['folder_id']
    name = manifest['collection_name']
    dim = manifest.get('embedding_dim', 0)

    print(f"Importing '{name}' ({manifest.get('folder_name') or folder_id})")
    print(f"  chunks: {manifest['chunk_count']}, embedding dim: {dim}")

    vs = VectorStore(collection_name=name)

    # Refuse dimension mismatches against existing data
    if vs.collection.count() > 0:
        sample = vs.collection.get(limit=1, include=['embeddings'])
        sample_emb = sample.get('embeddings')
        existing_dim = len(sample_emb[0]) if sample_emb is not None and len(sample_emb) else 0
        if existing_dim and dim and existing_dim != dim:
            print(f"ERROR: existing collection uses {existing_dim}-dim embeddings, "
                  f"package has {dim}-dim. Re-export with the matching embedder "
                  f"or run with --replace to overwrite.")
            if not replace:
                return 1
        if replace:
            print(f"  --replace: clearing existing collection ({vs.collection.count()} chunks)")
            vs.clear_collection()

    # Upsert chunks in batches
    batch_ids, batch_docs, batch_metas, batch_embs = [], [], [], []
    imported = 0

    def flush():
        nonlocal imported
        if not batch_ids:
            return
        vs.collection.upsert(
            ids=list(batch_ids),
            documents=list(batch_docs),
            metadatas=list(batch_metas),
            embeddings=list(batch_embs),
        )
        imported += len(batch_ids)
        print(f"  imported {imported}/{manifest['chunk_count']} chunks...")
        batch_ids.clear(); batch_docs.clear(); batch_metas.clear(); batch_embs.clear()

    for chunk in chunk_iter:
        batch_ids.append(chunk['id'])
        batch_docs.append(chunk['document'])
        batch_metas.append(chunk['metadata'])
        batch_embs.append(chunk['embedding'])
        if len(batch_ids) >= BATCH_SIZE:
            flush()
    flush()

    # Import tracker rows so incremental sync skips these files
    tracker = FileTracker()
    rows = manifest.get('tracker_rows', [])
    for row in rows:
        tracker.update_file_state(
            file_id=row['file_id'],
            file_name=row.get('file_name', ''),
            mime_type=row.get('mime_type', ''),
            folder_id=row.get('folder_id', folder_id),
            folder_name=row.get('folder_name', ''),
            modified_time=row.get('modified_time', ''),
            chunk_count=row.get('chunk_count', 0),
            content_hash=row.get('content_hash'),
            file_size=row.get('file_size'),
        )
    print(f"  tracker: recorded {len(rows)} files")

    # Merge indexed_folders.json entry so the chat app lists the collection
    entry = manifest.get('indexed_folders_entry') or {}
    entry.setdefault('collection_name', name)
    entry.setdefault('name', manifest.get('folder_name') or folder_id)
    # File/chunk counts shown in the collection picker
    entry['files_processed'] = len(rows)
    entry['file_count'] = len(rows)
    entry['chunks_created'] = imported
    entry['indexed_at'] = entry.get('indexed_at') or datetime.utcnow().isoformat()
    entry['imported_at'] = datetime.utcnow().isoformat()
    indexed = _load_indexed_folders()
    indexed[folder_id] = {**indexed.get(folder_id, {}), **entry}
    with open('indexed_folders.json', 'w') as f:
        json.dump(indexed, f, indent=2)
    print("  indexed_folders.json updated")

    print(f"\nDone: {imported} chunks in collection '{name}'.")
    print("Restart the app (or use admin > Update Collections) to pick up the new collection.")
    return 0


def main():
    parser = argparse.ArgumentParser(
        description='Transfer indexed collections between machines (index locally, upload to server)',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__.split('Workflow:')[1] if 'Workflow:' in (__doc__ or '') else ''
    )
    sub = parser.add_subparsers(dest='command', required=True)

    p_export = sub.add_parser('export', help='Export folder collection(s) to package file(s)')
    group = p_export.add_mutually_exclusive_group(required=True)
    group.add_argument('--folder', help='Google Drive folder ID')
    group.add_argument('--all', action='store_true',
                       help='Export every folder in indexed_folders.json')
    p_export.add_argument('--output', '-o',
                          help='Output file (--folder) or directory (--all)')

    p_import = sub.add_parser('import', help='Import package file(s) into this machine')
    p_import.add_argument('packages', nargs='+', help='Package file(s) (.ragpack.gz)')
    p_import.add_argument('--replace', action='store_true',
                          help='Clear each existing collection before importing')

    p_inspect = sub.add_parser('inspect', help='Show a package manifest without importing')
    p_inspect.add_argument('package', help='Package file (.ragpack.gz)')

    args = parser.parse_args()

    if args.command == 'export':
        if args.all:
            return export_all(args.output or '.')
        return export_folder(args.folder, args.output)
    if args.command == 'import':
        rc = 0
        for pkg in args.packages:
            print(f"\n=== Importing {os.path.basename(pkg)} ===")
            rc = max(rc, import_package(pkg, replace=args.replace))
        return rc
    if args.command == 'inspect':
        return inspect_package(args.package)
    return 1


if __name__ == '__main__':
    sys.exit(main())

#!/usr/bin/env python3
"""
Incremental Document Indexer

Intelligent document digestion system that:
1. Detects new and modified files in Google Drive
2. Only processes changed documents (cost-effective)
3. Removes orphaned documents from vector store
4. Can be scheduled for automatic midnight runs

Usage:
    python incremental_indexer.py                    # Interactive mode
    python incremental_indexer.py --sync             # Full incremental sync
    python incremental_indexer.py --folder <id>      # Sync specific folder
    python incremental_indexer.py --status           # Show sync status
    python incremental_indexer.py --dry-run          # Preview without changes
"""

import os
import sys
import time
import json
import argparse
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple

# Windows console: emoji prints in downstream modules crash under cp1252
if os.name == 'nt':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except (AttributeError, OSError):
        pass

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Load environment (GOOGLE_APPLICATION_CREDENTIALS for Vertex embeddings)
try:
    from dotenv import load_dotenv
    _env_prod = os.path.join(os.path.dirname(os.path.abspath(__file__)), '.env.production')
    load_dotenv(_env_prod if os.path.exists(_env_prod) else None)
except ImportError:
    pass

# Note: Heavy imports are deferred to _initialize_services() for faster startup
from file_tracker import FileTracker, compute_content_hash

# Configure logging - ensure logs directory exists
log_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'logs')
os.makedirs(log_dir, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler(os.path.join(log_dir, 'incremental_indexer.log')),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class IncrementalIndexer:
    """
    Incremental document indexer that only processes new/changed files.
    
    Key features:
    - Tracks file states in SQLite database
    - Uses modification time + content hash for change detection
    - Batch processes embeddings for efficiency
    - Removes orphaned documents from vector store
    - Provides detailed sync statistics
    """
    
    # Supported MIME types for indexing
    SUPPORTED_MIME_TYPES = {
        'application/pdf',
        'application/vnd.google-apps.document',
        'application/vnd.google-apps.presentation',
        'application/vnd.google-apps.spreadsheet',
        'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
        'application/vnd.openxmlformats-officedocument.presentationml.presentation',
        'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        'text/csv',
        'text/plain',
        'image/jpeg',
        'image/png',
        'image/tiff'
    }
    
    def __init__(
        self,
        tracker_db: str = "./file_tracker.db",
        dry_run: bool = False,
        batch_size: int = 50
    ):
        """
        Initialize the incremental indexer.
        
        Args:
            tracker_db: Path to file tracker SQLite database
            dry_run: If True, only preview changes without making them
            batch_size: Number of documents to process in each batch
        """
        self.dry_run = dry_run
        self.batch_size = batch_size
        
        # Initialize components
        self.tracker = FileTracker(tracker_db)
        self._VectorStore = None
        self.drive_service = None
        self.loader = None
        self.embedder = None
        
        # Statistics
        self.stats = {
            'files_checked': 0,
            'files_added': 0,
            'files_updated': 0,
            'files_deleted': 0,
            'files_skipped': 0,
            'files_failed': 0,
            'chunks_added': 0,
            'errors': []
        }
        
        logger.info(f"Incremental indexer initialized (dry_run={dry_run})")
    
    def _initialize_services(self):
        """Initialize Google Drive and embedding services (lazy imports)."""
        # Lazy imports for heavy dependencies
        from config import (
            CHUNK_SIZE, CHUNK_OVERLAP, INDEXED_FOLDERS_FILE,
            USE_VERTEX_EMBEDDINGS, PROJECT_ID, LOCATION
        )
        self.CHUNK_SIZE = CHUNK_SIZE
        self.CHUNK_OVERLAP = CHUNK_OVERLAP
        self.INDEXED_FOLDERS_FILE = INDEXED_FOLDERS_FILE
        
        if self.drive_service is None:
            try:
                from google_drive_oauth import get_drive_service
                self.drive_service = get_drive_service()
                if not self.drive_service:
                    raise Exception("Could not get Drive service - authentication required")
                logger.info("Google Drive service initialized")
            except Exception as e:
                logger.error(f"Failed to initialize Drive service: {e}")
                raise
        
        if self.loader is None:
            from document_loader import GoogleDriveLoader
            self.loader = GoogleDriveLoader(self.drive_service)
            logger.info("Document loader initialized")
        
        # Vector store is created per-folder in sync_folder() to target the
        # correct collection (folder_{id}), so we only import here.
        from vector_store import VectorStore
        self._VectorStore = VectorStore
        
        if self.embedder is None:
            if USE_VERTEX_EMBEDDINGS:
                from vertex_embeddings import VertexEmbedder
                self.embedder = VertexEmbedder()
            else:
                from embeddings import LocalEmbedder
                self.embedder = LocalEmbedder()
            logger.info("Embedder initialized")
    
    def _get_indexed_folders(self) -> Dict:
        """Load the configured folders to index."""
        indexed_file = getattr(self, 'INDEXED_FOLDERS_FILE', 'indexed_folders.json')
        if os.path.exists(indexed_file):
            with open(indexed_file, 'r') as f:
                return json.load(f)
        return {}
    
    def _get_files_recursive(
        self, 
        folder_id: str, 
        shared_drive_id: Optional[str] = None,
        depth: int = 0
    ) -> List[Dict]:
        """Recursively get all files from a folder."""
        all_files = []
        
        query = f"'{folder_id}' in parents and trashed=false"
        params = {
            'q': query,
            'spaces': 'drive',
            'fields': 'files(id, name, mimeType, size, modifiedTime), nextPageToken',
            'pageSize': 1000,
            'supportsAllDrives': True,
            'includeItemsFromAllDrives': True
        }
        
        if shared_drive_id:
            params['driveId'] = shared_drive_id
            params['corpora'] = 'drive'
        
        page_token = None
        
        while True:
            try:
                params['pageToken'] = page_token
                response = self.drive_service.files().list(**params).execute()
                
                items = response.get('files', [])
                
                for item in items:
                    mime_type = item.get('mimeType', '')
                    
                    if mime_type == 'application/vnd.google-apps.folder':
                        # Recurse into subfolder
                        subfolder_files = self._get_files_recursive(
                            item['id'],
                            shared_drive_id,
                            depth + 1
                        )
                        all_files.extend(subfolder_files)
                    elif mime_type in self.SUPPORTED_MIME_TYPES:
                        item['folder_id'] = folder_id
                        all_files.append(item)
                
                page_token = response.get('nextPageToken')
                if not page_token:
                    break
                    
            except Exception as e:
                logger.error(f"Error listing files in folder {folder_id}: {e}")
                self.stats['errors'].append(f"Folder {folder_id}: {str(e)}")
                break
        
        return all_files
    
    def _extract_and_chunk_file(
        self,
        file: Dict,
        folder_name: str
    ) -> Tuple[Optional[List[str]], Optional[str]]:
        """
        Extract text from file and chunk it.
        
        Returns:
            (chunks, content_hash) or (None, None) on failure
        """
        # Lazy imports
        from document_loader import extract_text, chunk_text
        
        file_id = file['id']
        file_name = file['name']
        mime_type = file['mimeType']
        
        try:
            # Extract text based on file type
            if mime_type == 'application/vnd.google-apps.document':
                text = self.loader.export_google_doc(file_id)
            elif mime_type == 'application/vnd.google-apps.presentation':
                text = self.loader.export_google_slides(file_id)
            elif mime_type == 'application/vnd.google-apps.spreadsheet':
                text = self.loader.export_google_sheets(file_id)
            else:
                content = self.loader.download_file(file_id)
                if content is None:
                    return None, None
                text = extract_text(content, mime_type, file_name, self.loader.ocr_service)
            
            if not text or len(text.strip()) < 50:
                logger.debug(f"File {file_name} has no meaningful content")
                return None, None
            
            # Compute content hash for change detection
            content_hash = compute_content_hash(text)
            
            # Chunk the text
            chunk_size = getattr(self, 'CHUNK_SIZE', 400)
            chunk_overlap = getattr(self, 'CHUNK_OVERLAP', 100)
            chunks = chunk_text(text, chunk_size, chunk_overlap)
            
            if not chunks:
                return None, None
            
            return chunks, content_hash
            
        except Exception as e:
            logger.error(f"Error processing {file_name}: {e}")
            self.stats['errors'].append(f"File {file_name}: {str(e)}")
            return None, None
    
    def _update_chunk_file_name(self, vector_store, file_id: str, new_name: str):
        """Update file_name metadata on existing chunks (rename with unchanged content)."""
        try:
            existing = vector_store.collection.get(where={"file_id": file_id})
            ids = existing.get('ids', [])
            metas = existing.get('metadatas', [])
            if ids:
                for m in metas:
                    m['file_name'] = new_name
                    if 'filename' in m:
                        m['filename'] = new_name
                vector_store.collection.update(ids=ids, metadatas=metas)
                logger.info(f"  Renamed {len(ids)} chunks to '{new_name}' without re-embedding")
        except Exception as e:
            logger.warning(f"Could not update chunk metadata for {file_id}: {e}")

    def _remove_file_from_index(self, file_id: str, vector_store=None):
        """Remove all chunks for a file from the vector store."""
        if self.dry_run:
            logger.info(f"[DRY RUN] Would remove file {file_id} from index")
            return

        if vector_store is None:
            raise ValueError("vector_store is required")
        try:
            vector_store.collection.delete(where={"file_id": file_id})
            logger.debug(f"Removed file {file_id} from vector store")
        except Exception as e:
            logger.error(f"Error removing file {file_id}: {e}")
    
    def _process_batch(
        self,
        batch_chunks: List[str],
        batch_metadatas: List[Dict],
        batch_ids: List[str],
        vector_store=None
    ) -> bool:
        """Process a batch of chunks - generate embeddings and store. Returns True on success."""
        if self.dry_run:
            logger.info(f"[DRY RUN] Would add {len(batch_chunks)} chunks")
            return True

        if vector_store is None:
            raise ValueError("vector_store is required")
        try:
            embeddings = self.embedder.embed_documents(batch_chunks)

            vector_store.add_documents(
                batch_chunks,
                embeddings,
                batch_metadatas,
                batch_ids
            )

            self.stats['chunks_added'] += len(batch_chunks)
            logger.info(f"Added {len(batch_chunks)} chunks to {vector_store.collection_name}")
            return True

        except Exception as e:
            logger.error(f"Error processing batch: {e}")
            self.stats['errors'].append(f"Batch processing: {str(e)}")
            return False

    def _commit_file_states(self, pending_states: List[Dict]):
        """Commit deferred file tracker updates after successful embedding storage."""
        if self.dry_run:
            return
        for state in pending_states:
            self.tracker.update_file_state(**state)
    
    def sync_folder(
        self,
        folder_id: str,
        folder_name: str,
        folder_location: str,
        shared_drive_id: Optional[str] = None
    ) -> Dict:
        """
        Sync a single folder - detect and process changes.
        
        Args:
            folder_id: Google Drive folder ID
            folder_name: Human-readable folder name
            folder_location: Location (e.g., shared drive name)
            shared_drive_id: Optional shared drive ID
            
        Returns:
            Statistics for this folder sync
        """
        logger.info(f"Syncing folder: {folder_name} ({folder_id})")

        collection_name = f"folder_{folder_id}"
        folder_vs = self._VectorStore(collection_name=collection_name)
        logger.info(f"Using collection '{collection_name}' for folder {folder_name}")

        folder_stats = {
            'files_checked': 0,
            'files_added': 0,
            'files_updated': 0,
            'files_skipped': 0,
            'files_failed': 0
        }
        
        # Get all files in folder
        files = self._get_files_recursive(folder_id, shared_drive_id)
        folder_stats['files_checked'] = len(files)
        self.stats['files_checked'] += len(files)
        
        logger.info(f"Found {len(files)} files in {folder_name}")
        
        # Track which files we see (for deletion detection)
        seen_file_ids = set()
        
        # Batch processing lists
        batch_chunks = []
        batch_metadatas = []
        batch_ids = []
        pending_file_states = []

        for idx, file in enumerate(files, 1):
            file_id = file['id']
            file_name = file['name']
            modified_time = file.get('modifiedTime', '')

            seen_file_ids.add(file_id)

            needs_update, reason = self.tracker.check_file_needs_update(
                file_id,
                modified_time
            )

            if not needs_update:
                if not self.dry_run:
                    self.tracker.mark_file_checked(file_id)
                folder_stats['files_skipped'] += 1
                self.stats['files_skipped'] += 1
                continue

            logger.info(f"[{idx}/{len(files)}] Processing {file_name} ({reason})")

            chunks, content_hash = self._extract_and_chunk_file(file, folder_name)

            if not chunks:
                folder_stats['files_failed'] += 1
                self.stats['files_failed'] += 1
                continue

            if reason in ['modified', 'content_changed']:
                prev = self.tracker.get_file_state(file_id)
                if prev and content_hash and prev.get('content_hash') == content_hash:
                    # Touched in Drive (re-save, comment, rename) but the text is
                    # identical — refresh the tracker, keep existing embeddings.
                    logger.info(f"  Content unchanged for {file_name}; skipping re-embed")
                    if not self.dry_run:
                        if file_name != prev.get('file_name'):
                            self._update_chunk_file_name(folder_vs, file_id, file_name)
                        self.tracker.update_file_state(
                            file_id=file_id,
                            file_name=file_name,
                            mime_type=file['mimeType'],
                            folder_id=folder_id,
                            folder_name=folder_name,
                            modified_time=modified_time,
                            chunk_count=prev.get('chunk_count') or len(chunks),
                            content_hash=content_hash,
                            file_size=int(file.get('size', 0) or 0)
                        )
                    folder_stats['files_skipped'] += 1
                    self.stats['files_skipped'] += 1
                    continue

                # Real content change: replace the old chunks
                self._remove_file_from_index(file_id, vector_store=folder_vs)

            for i, chunk in enumerate(chunks):
                batch_chunks.append(chunk)
                batch_metadatas.append({
                    'file_id': file_id,
                    'file_name': file_name,
                    'folder_id': folder_id,
                    'folder_name': folder_name,
                    'mime_type': file['mimeType'],
                    'chunk_index': i,
                    'total_chunks': len(chunks),
                    'modified_time': modified_time
                })
                batch_ids.append(f"{file_id}_chunk_{i}")

            # Defer tracker update until embeddings are stored successfully
            pending_file_states.append({
                'file_id': file_id,
                'file_name': file_name,
                'mime_type': file['mimeType'],
                'folder_id': folder_id,
                'folder_name': folder_name,
                'modified_time': modified_time,
                'chunk_count': len(chunks),
                'content_hash': content_hash,
                'file_size': int(file.get('size', 0))
            })

            if reason == 'new':
                folder_stats['files_added'] += 1
                self.stats['files_added'] += 1
            else:
                folder_stats['files_updated'] += 1
                self.stats['files_updated'] += 1

            if len(batch_chunks) >= self.batch_size:
                if self._process_batch(batch_chunks, batch_metadatas, batch_ids, vector_store=folder_vs):
                    self._commit_file_states(pending_file_states)
                pending_file_states = []
                batch_chunks = []
                batch_metadatas = []
                batch_ids = []

        if batch_chunks:
            if self._process_batch(batch_chunks, batch_metadatas, batch_ids, vector_store=folder_vs):
                self._commit_file_states(pending_file_states)
        
        # Detect deleted files
        tracked_files = self.tracker.get_files_in_folder(folder_id)
        deleted_count = 0
        
        for tracked_file in tracked_files:
            if tracked_file['file_id'] not in seen_file_ids:
                logger.info(f"File deleted from source: {tracked_file['file_name']}")
                self._remove_file_from_index(tracked_file['file_id'], vector_store=folder_vs)
                
                if not self.dry_run:
                    self.tracker.mark_file_deleted(tracked_file['file_id'])
                
                deleted_count += 1
        
        self.stats['files_deleted'] += deleted_count
        
        logger.info(f"Folder {folder_name} sync complete: "
                   f"added={folder_stats['files_added']}, "
                   f"updated={folder_stats['files_updated']}, "
                   f"skipped={folder_stats['files_skipped']}, "
                   f"deleted={deleted_count}")
        
        return folder_stats
    
    def run_full_sync(self) -> Dict:
        """
        Run full incremental sync on all configured folders.
        
        Returns:
            Complete sync statistics
        """
        logger.info("=" * 60)
        logger.info("Starting full incremental sync")
        logger.info("=" * 60)
        
        start_time = time.time()
        
        # Initialize services
        self._initialize_services()
        
        # Start sync session (skip tracker writes in dry-run)
        session_id = None
        if not self.dry_run:
            session_id = self.tracker.start_sync_session()

        # Load configured folders
        indexed_folders = self._get_indexed_folders()

        if not indexed_folders:
            logger.warning("No folders configured for indexing!")
            logger.info("Configure folders in indexed_folders.json or through admin panel")
            if session_id is not None:
                self.tracker.complete_sync_session(
                    session_id=session_id, status='completed',
                    files_checked=0, files_added=0, files_updated=0,
                    files_deleted=0, files_skipped=0, folders_scanned=0,
                    errors=None
                )
            return self.stats
        
        logger.info(f"Found {len(indexed_folders)} configured folders")
        
        # Sync each folder
        for folder_id, folder_info in indexed_folders.items():
            try:
                self.sync_folder(
                    folder_id=folder_id,
                    folder_name=folder_info.get('name', 'Unknown'),
                    folder_location=folder_info.get('location', 'Unknown'),
                    shared_drive_id=None  # Will be auto-detected
                )
            except Exception as e:
                logger.error(f"Error syncing folder {folder_info.get('name')}: {e}")
                self.stats['errors'].append(f"Folder sync error: {str(e)}")
        
        # Complete sync session
        duration = time.time() - start_time
        
        if session_id is not None:
            self.tracker.complete_sync_session(
                session_id=session_id,
                status='completed' if not self.stats['errors'] else 'completed_with_errors',
                files_checked=self.stats['files_checked'],
                files_added=self.stats['files_added'],
                files_updated=self.stats['files_updated'],
                files_deleted=self.stats['files_deleted'],
                files_skipped=self.stats['files_skipped'],
                folders_scanned=len(indexed_folders),
                errors=json.dumps(self.stats['errors']) if self.stats['errors'] else None
            )
        
        # Log summary
        logger.info("=" * 60)
        logger.info("Sync Complete!")
        logger.info("=" * 60)
        logger.info(f"Duration: {duration:.1f} seconds")
        logger.info(f"Files checked: {self.stats['files_checked']}")
        logger.info(f"Files added: {self.stats['files_added']}")
        logger.info(f"Files updated: {self.stats['files_updated']}")
        logger.info(f"Files skipped (up-to-date): {self.stats['files_skipped']}")
        logger.info(f"Files deleted: {self.stats['files_deleted']}")
        logger.info(f"Files failed: {self.stats['files_failed']}")
        logger.info(f"Chunks added: {self.stats['chunks_added']}")
        if self.stats['errors']:
            logger.warning(f"Errors: {len(self.stats['errors'])}")
        logger.info("=" * 60)
        
        return self.stats
    
    def show_status(self):
        """Display current tracking status and sync history."""
        stats = self.tracker.get_stats()
        history = self.tracker.get_sync_history(5)
        
        print("\n" + "=" * 60)
        print("INCREMENTAL INDEXER STATUS")
        print("=" * 60)
        
        print(f"\nTracked Files: {stats['total_files']}")
        print(f"Total Chunks: {stats['total_chunks']}")
        
        if stats['files_by_folder']:
            print("\nFiles by Folder:")
            for folder, count in stats['files_by_folder'].items():
                print(f"  - {folder}: {count} files")
        
        if history:
            print("\nRecent Sync History:")
            print("-" * 60)
            for sync in history:
                started = sync['started_at'][:19] if sync['started_at'] else 'N/A'
                status = sync['status']
                duration = f"{sync['duration_seconds']:.1f}s" if sync['duration_seconds'] else 'N/A'
                added = sync['files_added']
                updated = sync['files_updated']
                skipped = sync['files_skipped']
                
                print(f"  {started} | {status:20} | {duration:8} | "
                      f"+{added} ~{updated} ={skipped}")
        
        print("=" * 60)


def main():
    """Main entry point for command-line usage."""
    parser = argparse.ArgumentParser(
        description='Incremental Document Indexer',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python incremental_indexer.py --sync          # Run full incremental sync
  python incremental_indexer.py --dry-run       # Preview changes without making them
  python incremental_indexer.py --status        # Show current status
  python incremental_indexer.py --folder <id>   # Sync specific folder
        """
    )
    
    parser.add_argument(
        '--sync',
        action='store_true',
        help='Run full incremental sync on all configured folders'
    )
    parser.add_argument(
        '--folder',
        type=str,
        help='Sync a specific folder by ID'
    )
    parser.add_argument(
        '--status',
        action='store_true',
        help='Show current tracking status and sync history'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Preview changes without actually making them'
    )
    parser.add_argument(
        '--batch-size',
        type=int,
        default=50,
        help='Number of documents to process in each batch (default: 50)'
    )
    
    args = parser.parse_args()
    
    # Ensure logs directory exists
    os.makedirs('logs', exist_ok=True)
    
    if args.status:
        indexer = IncrementalIndexer(dry_run=True)
        indexer.show_status()
        return 0
    
    if args.sync or args.folder:
        indexer = IncrementalIndexer(
            dry_run=args.dry_run,
            batch_size=args.batch_size
        )
        
        if args.folder:
            # Sync specific folder — use its configured name if we know it
            indexer._initialize_services()
            folder_info = indexer._get_indexed_folders().get(args.folder, {})
            indexer.sync_folder(
                folder_id=args.folder,
                folder_name=folder_info.get('name', args.folder),
                folder_location=folder_info.get('location', 'Manual')
            )
        else:
            # Full sync
            indexer.run_full_sync()
        
        return 0
    
    # No arguments - show help
    parser.print_help()
    return 1


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n\nInterrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

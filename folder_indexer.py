# folder_indexer.py - Root-level folders only

from auth import authenticate_google_drive
from document_loader import GoogleDriveLoader, extract_text, chunk_text
from vector_store import VectorStore
from config import CHUNK_SIZE, CHUNK_OVERLAP, USE_VERTEX_EMBEDDINGS
import json
import os
import time


class FolderIndexer:
    """Index specific ROOT-LEVEL folders only"""
    
    def __init__(self):
        self.indexed_folders_file = 'indexed_folders.json'
        self.load_indexed_folders()
    
    def load_indexed_folders(self):
        if os.path.exists(self.indexed_folders_file):
            with open(self.indexed_folders_file, 'r') as f:
                self.indexed_folders = json.load(f)
        else:
            self.indexed_folders = {}
    
    def save_indexed_folders(self):
        with open(self.indexed_folders_file, 'w') as f:
            json.dump(self.indexed_folders, f, indent=2)
    
    def list_shared_drives(self, drive_service):
        """Get all Shared Drives user has access to"""
        print("\n📁 Fetching Shared Drives...")
        
        try:
            response = drive_service.drives().list(
                pageSize=100,
                fields='drives(id, name)'
            ).execute()
            
            shared_drives = response.get('drives', [])
            print(f"✓ Found {len(shared_drives)} Shared Drives\n")
            return shared_drives
        except Exception as e:
            print(f"Error fetching Shared Drives: {e}")
            return []
    
    def select_shared_drives(self, drive_service):
        """Let user select which Shared Drives to browse"""
        shared_drives = self.list_shared_drives(drive_service)
        
        if not shared_drives:
            print("No Shared Drives found.")
            # Still allow selecting My Drive
        
        # Display Shared Drives
        print("=" * 80)
        print("SELECT SHARED DRIVES TO BROWSE")
        print("=" * 80)
        print("\nWhich Shared Drives do you want to browse folders from?")
        print()
        
        for i, drive in enumerate(shared_drives, 1):
            print(f"{i}. {drive['name']}")
        
        print(f"\n{len(shared_drives) + 1}. My Drive")
        print(f"{len(shared_drives) + 2}. All of the above")
        
        print("\n" + "=" * 80)
        print("Enter numbers (comma-separated)")
        print(f"Examples: '1' for just one, '1,3' for multiple, '{len(shared_drives) + 2}' for all")
        print("=" * 80)
        
        selection = input("\nSelect drives: ").strip()
        
        if not selection:
            return []
        
        # Parse selection
        selected_indices = set()
        for part in selection.split(','):
            part = part.strip()
            if part.isdigit():
                selected_indices.add(int(part))
        
        # Build list of selected drives
        selected_drives = []
        include_my_drive = False
        
        # Check if "All" was selected
        if len(shared_drives) + 2 in selected_indices:
            selected_drives = shared_drives
            include_my_drive = True
        else:
            # Add specific shared drives
            for idx in selected_indices:
                if 1 <= idx <= len(shared_drives):
                    selected_drives.append(shared_drives[idx - 1])
                elif idx == len(shared_drives) + 1:
                    include_my_drive = True
        
        result = {
            'shared_drives': selected_drives,
            'include_my_drive': include_my_drive
        }
        
        # Show selection
        print(f"\n✓ Selected:")
        if include_my_drive:
            print("  - My Drive")
        for drive in selected_drives:
            print(f"  - {drive['name']}")
        
        return result
    
    def get_root_folders_only(self, drive_service, drive_selection):
        """Get ONLY root-level folders from selected drives"""
        folders = []
        
        # Get My Drive ROOT folders if requested
        if drive_selection['include_my_drive']:
            print("\n📁 Fetching ROOT folders from My Drive...")
            page_token = None
            my_drive_folders = []
            
            while True:
                try:
                    # Get all folders first
                    response = drive_service.files().list(
                        q="mimeType='application/vnd.google-apps.folder' and trashed=false",
                        spaces='drive',
                        fields='nextPageToken, files(id, name, parents)',
                        pageToken=page_token,
                        pageSize=1000
                    ).execute()
                    
                    batch = response.get('files', [])
                    my_drive_folders.extend(batch)
                    
                    page_token = response.get('nextPageToken', None)
                    if page_token is None:
                        break
                except Exception as e:
                    print(f"  Error: {e}")
                    break
            
            # Filter to only root folders (those without parents or with root as parent)
            root_folders = []
            for folder in my_drive_folders:
                parents = folder.get('parents', [])
                # Root folders either have no parents or their parent is the root
                if not parents or len(parents) == 0:
                    folder['location'] = 'My Drive'
                    folder['shared_drive_id'] = None
                    root_folders.append(folder)
            
            print(f"  ✓ Found {len(root_folders)} root folders")
            folders.extend(root_folders)
        
        # Get ROOT folders from selected Shared Drives
        for shared_drive in drive_selection['shared_drives']:
            print(f"\n📁 Fetching ROOT folders from: {shared_drive['name']}...")
            
            try:
                # For Shared Drives, we need to find folders with no parents or whose parent is the drive root
                # The trick: get all folders, then filter for those without parents in the results
                page_token = None
                all_folders = []
                
                while True:
                    response = drive_service.files().list(
                        q="mimeType='application/vnd.google-apps.folder' and trashed=false",
                        driveId=shared_drive['id'],
                        corpora='drive',
                        fields='nextPageToken, files(id, name, parents)',
                        pageToken=page_token,
                        pageSize=1000,
                        supportsAllDrives=True,
                        includeItemsFromAllDrives=True
                    ).execute()
                    
                    batch = response.get('files', [])
                    all_folders.extend(batch)
                    
                    page_token = response.get('nextPageToken', None)
                    if page_token is None:
                        break
                
                # Build a set of all folder IDs
                all_folder_ids = {f['id'] for f in all_folders}
                
                # Root folders are those whose parents are NOT in the folder list
                # (meaning their parent is the drive root itself)
                root_folders = []
                for folder in all_folders:
                    parents = folder.get('parents', [])
                    
                    # If no parents listed, it's a root folder
                    if not parents:
                        is_root = True
                    else:
                        # If all parents are NOT in our folder list, this is a root folder
                        is_root = all(parent_id not in all_folder_ids for parent_id in parents)
                    
                    if is_root:
                        folder['location'] = shared_drive['name']
                        folder['shared_drive_id'] = shared_drive['id']
                        root_folders.append(folder)
                
                print(f"  ✓ Found {len(root_folders)} root folders (filtered from {len(all_folders)} total)")
                folders.extend(root_folders)
                
            except Exception as e:
                print(f"  Error: {e}")
        
        return folders
    
    def select_folders_interactive(self, drive_service):
        """Two-step selection: drives first, then ROOT folders only"""
        
        # Step 1: Select which drives to browse
        drive_selection = self.select_shared_drives(drive_service)
        
        if not drive_selection['shared_drives'] and not drive_selection['include_my_drive']:
            print("\nNo drives selected.")
            return []
        
        # Step 2: Get ROOT folders only from selected drives
        print("\n" + "=" * 80)
        folders = self.get_root_folders_only(drive_service, drive_selection)
        
        if not folders:
            print("No root folders found in selected drives!")
            return []
        
        # Sort folders by location, then name
        folders.sort(key=lambda x: (x['location'], x['name'].lower()))
        
        # Display folders grouped by location
        print("\n" + "=" * 80)
        print("SELECT ROOT-LEVEL FOLDERS TO INDEX")
        print("=" * 80)
        print("(Showing only top-level folders, not subfolders)")
        print()
        
        current_location = None
        for i, folder in enumerate(folders, 1):
            # Print location header when it changes
            if folder['location'] != current_location:
                current_location = folder['location']
                print(f"\n📂 {current_location}")
                print("-" * 80)
            
            status = "✓" if folder['id'] in self.indexed_folders else " "
            print(f"[{status}] {i:3d}. {folder['name']}")
        
        print("\n" + "=" * 80)
        print("Enter folder numbers (comma-separated)")
        print("Examples: '1' or '1,5,8' or '1-5' for range")
        print("=" * 80)
        
        selection = input("\nFolders to index: ").strip()
        
        if not selection:
            return []
        
        # Parse selection
        selected_indices = set()
        
        for part in selection.split(','):
            part = part.strip()
            if '-' in part:
                start, end = part.split('-')
                selected_indices.update(range(int(start), int(end) + 1))
            else:
                if part.isdigit():
                    selected_indices.add(int(part))
        
        # Get selected folders
        selected_folders = []
        for idx in selected_indices:
            if 1 <= idx <= len(folders):
                folder = folders[idx - 1]
                selected_folders.append({
                    'id': folder['id'],
                    'name': folder['name'],
                    'location': folder['location'],
                    'shared_drive_id': folder.get('shared_drive_id')
                })
        
        return selected_folders
    
    def get_files_recursively(self, drive_service, folder_id, shared_drive_id=None):
        """Get all files in folder AND all subfolders recursively"""
        all_files = []
        
        # Build query parameters
        query = f"'{folder_id}' in parents and trashed=false"
        
        params = {
            'q': query,
            'spaces': 'drive',
            # OPTIMIZATION: Get modifiedTime for delta indexing
            'fields': 'files(id, name, mimeType, size, modifiedTime)',
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
                response = drive_service.files().list(**params).execute()
                
                items = response.get('files', [])
                
                for item in items:
                    mime_type = item.get('mimeType', '')
                    
                    # If it's a folder, recursively get its contents
                    if mime_type == 'application/vnd.google-apps.folder':
                        subfolder_files = self.get_files_recursively(
                            drive_service, 
                            item['id'], 
                            shared_drive_id
                        )
                        all_files.extend(subfolder_files)
                    else:
                        # It's a file, add it
                        all_files.append(item)
                
                page_token = response.get('nextPageToken', None)
                if page_token is None:
                    break
                    
            except Exception as e:
                print(f"    Error scanning subfolder: {e}")
                break
        
        return all_files
    
    def get_files_in_folders(self, drive_service, folder_selections):
        """Get all files in selected folders (including subfolders)"""
        print(f"\n📄 Fetching files from {len(folder_selections)} folders...")
        print("(This will include all subfolders recursively)")
        
        all_files = []
        
        for folder_selection in folder_selections:
            folder_id = folder_selection['id']
            folder_name = folder_selection['name']
            location = folder_selection['location']
            shared_drive_id = folder_selection.get('shared_drive_id')
            
            print(f"\n  📁 {location} / {folder_name}")
            print(f"     Scanning folder and all subfolders...")
            
            # Get files recursively
            folder_files = self.get_files_recursively(drive_service, folder_id, shared_drive_id)
            
            print(f"    ✓ Found {len(folder_files)} files (including subfolders)")
            all_files.extend(folder_files)
        
        # Filter supported types
        supported = [
            'application/pdf',
            'application/vnd.google-apps.document',
            'application/vnd.google-apps.presentation',
            'application/vnd.google-apps.spreadsheet',
            'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            'application/vnd.openxmlformats-officedocument.presentationml.presentation',
            'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            'text/csv',
            'text/plain'
        ]
        
        filtered = [f for f in all_files if f.get('mimeType') in supported]
        
        print(f"\n✓ Total files found: {len(all_files)}")
        print(f"✓ Indexable files: {len(filtered)}")
        
        return filtered
    
    def index_folders(self, folder_selections, drive_service):
        """Index selected folders"""
        
        files = self.get_files_in_folders(drive_service, folder_selections)
        
        if not files:
            print("\n⚠️  No files to index!")
            return
        
        # Show breakdown
        print("\n" + "=" * 80)
        print("FILES TO INDEX")
        print("=" * 80)
        print(f"Total: {len(files)} files")
        
        total_size = sum(int(f.get('size', 0)) for f in files)
        print(f"Size: {total_size / (1024**3):.2f} GB")
        
        # Estimate is faster now with batching
        avg_time = 2 # (download + embed)
        est_minutes = (len(files) * avg_time) / 60
        print(f"⏱️  Estimated: {est_minutes:.0f} minutes")
        
        print("\n" + "=" * 80)
        response = input("Proceed? (yes/no): ")
        
        if response.lower() != 'yes':
            print("Cancelled")
            return
        
        # Initialize
        print("\n📦 Initializing...")
        loader = GoogleDriveLoader(drive_service)
        if USE_VERTEX_EMBEDDINGS:
            from vertex_embeddings import VertexEmbedder
            embedder = VertexEmbedder()
        else:
            from embeddings import LocalEmbedder
            embedder = LocalEmbedder()
        vector_store = VectorStore()
        
        # Index
        print("\n🚀 Indexing...\n")
        print("=" * 80)
        
        successful = 0
        failed = 0
        empty = 0
        skipped = 0
        start_time = time.time()
        
        # OPTIMIZATION: Batch Processing
        all_chunks = []
        all_metadatas = []
        all_ids = []
        
        for idx, file in enumerate(files, 1):
            if idx % 25 == 0:
                elapsed = time.time() - start_time
                rate = idx / elapsed
                remaining = (len(files) - idx) / rate
                print(f"\n⏱️  Progress: {idx}/{len(files)} ({idx/len(files)*100:.1f}%) - ETA: {remaining/60:.0f} mins")
            
            print(f"\n[{idx}/{len(files)}] {file['name'][:60]}")
            
            try:
                # --- OPTIMIZATION: Delta Indexing ---
                # Check if this file is already indexed and up-to-date
                try:
                    existing_doc = vector_store.collection.get(
                        where={"file_id": file['id']},
                        limit=1,
                        include=["metadatas"]
                    )
                    
                    if existing_doc['metadatas']:
                        indexed_time = existing_doc['metadatas'][0].get('modified_time')
                        if indexed_time and indexed_time == file.get('modifiedTime'):
                            print(f"  ✓ Skipping (up-to-date)")
                            skipped += 1
                            continue # Skip to the next file
                    
                    # File is new or modified, clear old chunks before adding new
                    if existing_doc['ids']:
                        print("  File modified. Clearing old chunks...")
                        vector_store.collection.delete(where={"file_id": file['id']})

                except Exception as e:
                    print(f"  Warning: Could not check existing doc: {e}")
                # --- End Delta Indexing Check ---

                mime_type = file['mimeType']
                
                if mime_type == 'application/vnd.google-apps.document':
                    text = loader.export_google_doc(file['id'])
                elif mime_type == 'application/vnd.google-apps.presentation':
                    text = loader.export_google_slides(file['id'])
                elif mime_type == 'application/vnd.google-apps.spreadsheet':
                    text = loader.export_google_sheets(file['id'])
                else:
                    content = loader.download_file(file['id'])
                    if content is None:
                        failed += 1
                        continue
                    text = extract_text(content, mime_type)
                
                if not text or len(text.strip()) < 50:
                    print("  ⚠️  Empty")
                    empty += 1
                    continue
                
                print(f"  ✓ {len(text):,} chars")
                
                chunks = chunk_text(text, CHUNK_SIZE, CHUNK_OVERLAP)
                
                if not chunks:
                    empty += 1
                    continue
                
                # Embeddings are done in one batch later
                
                metadatas = [
                    {
                        'file_id': file['id'],
                        'file_name': file['name'],
                        'mime_type': mime_type,
                        'chunk_index': i,
                        'total_chunks': len(chunks),
                        'modified_time': file.get('modifiedTime') # For delta indexing
                    }
                    for i in range(len(chunks))
                ]
                
                ids = [f"{file['id']}_chunk_{i}" for i in range(len(chunks))]
                
                # Add to batch lists
                all_chunks.extend(chunks)
                all_metadatas.extend(metadatas)
                all_ids.extend(ids)
                
                successful += 1
                print(f"  ✅ {len(chunks)} chunks (queued)")
                
                # OPTIMIZATION: Removed time.sleep(0.3)
                
            except KeyboardInterrupt:
                print(f"\n\n⚠️  Interrupted!")
                break
            except Exception as e:
                print(f"  ✗ Error: {e}")
                failed += 1
        
        # --- OPTIMIZATION: Process Batches ---
        if all_chunks:
            print("\n" + "=" * 80)
            print(f"🚀 Processing {successful} files...")
            print(f"  Generating embeddings for {len(all_chunks)} total chunks...")
            
            try:
                all_embeddings = embedder.embed_documents(all_chunks)
                
                print(f"  Adding {len(all_chunks)} chunks to vector store...")
                vector_store.add_documents(all_chunks, all_embeddings, all_metadatas, all_ids)
                
                print("✓ Batch add complete!")
                
            except Exception as e:
                print(f"\n✗ Error during batch processing: {e}")
                print("  Some documents may not have been indexed.")

        
        # Mark as indexed
        for folder_selection in folder_selections:
            self.indexed_folders[folder_selection['id']] = {
                'name': folder_selection['name'],
                'location': folder_selection['location'],
                'indexed_at': time.strftime('%Y-%m-%d %H:%M:%S'),
                'files_processed': successful # Renamed for clarity
            }
        
        self.save_indexed_folders()
        
        # Summary
        total_time = time.time() - start_time
        
        print("\n" + "=" * 80)
        print("🎉 COMPLETE!")
        print("=" * 80)
        print(f"✅ Success (new/updated): {successful}")
        print(f"✓ Skipped (up-to-date): {skipped}")
        print(f"⚠️  Empty: {empty}")
        print(f"❌ Failed: {failed}")
        print(f"⏱️  Time: {total_time/60:.1f} minutes")
        print(f"📊 Total indexed: {vector_store.get_stats()['total_documents']}")
        print("=" * 80)


def main():
    """Main function"""
    print("\n" + "=" * 80)
    print("ROOT-LEVEL FOLDER INDEXING")
    print("=" * 80)
    
    indexer = FolderIndexer()
    
    print("\n1️⃣  Authenticating...")
    drive_service = authenticate_google_drive()
    
    print("\n2️⃣  Select drives and folders...")
    selected = indexer.select_folders_interactive(drive_service)
    
    if not selected:
        print("\nNo folders selected.")
        return
    
    print(f"\n✓ Selected {len(selected)} folders:")
    for f in selected:
        print(f"  - [{f['location']}] {f['name']}")
    
    print("\n3️⃣  Indexing...")
    indexer.index_folders(selected, drive_service)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nExiting...")
# folder_indexer.py - Root-level folders only (MODIFIED with accurate root finding)
# --- NO CHANGES TO LOGIC, just imports ---

from auth import authenticate_google_drive
from document_loader import GoogleDriveLoader, extract_text, chunk_text
from embeddings import LocalEmbedder
from vector_store import VectorStore
from config import CHUNK_SIZE, CHUNK_OVERLAP, INDEXED_FOLDERS_FILE
from incremental_indexing import IncrementalIndexingManager
import json
import os
import sys

# Fix Windows console encoding for Unicode characters
if os.name == 'nt':  # Windows
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except (AttributeError, OSError):
        pass

def safe_print(*args, **kwargs):
    """Safe print function that handles Unicode encoding errors on Windows"""
    try:
        print(*args, **kwargs)
    except UnicodeEncodeError:
        safe_args = []
        for arg in args:
            if isinstance(arg, str):
                safe_arg = (arg.replace('🔍', '[SEARCH]')
                             .replace('📊', '[STATS]')
                             .replace('⚡', '[FAST]'))
                safe_args.append(safe_arg)
            else:
                safe_args.append(str(arg))
        print(*safe_args, **kwargs)
import time


class FolderIndexer:
    """Index specific ROOT-LEVEL folders only into separate collections with incremental indexing"""
    
    def __init__(self):
        self.indexed_folders_file = INDEXED_FOLDERS_FILE
        self.incremental_manager = IncrementalIndexingManager()
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
        print("\nWhich Shared Drives do you want to browse folders from?\n")
        
        for i, drive in enumerate(shared_drives, 1):
            print(f"{i}. {drive['name']}")
        
        print(f"\n{len(shared_drives) + 1}. My Drive")
        print(f"{len(shared_drives) + 2}. All of the above")
        
        print("\n" + "=" * 80)
        print("Enter numbers (comma-separated)")
        print(f"Examples: '1' for just one, '1,3' for multiple, '{len(shared_drives) + 2}' for all")
        print(f"           Or '1, {len(shared_drives) + 1}' for a shared drive and My Drive")
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
            my_drive_root_id = None
            
            # 1. Get the ID of the 'My Drive' root folder itself
            try:
                root_info = drive_service.files().get(
                    fileId='root', 
                    fields='id'
                ).execute()
                my_drive_root_id = root_info['id']
                print(f"  ✓ 'My Drive' root ID: {my_drive_root_id}")
            except Exception as e:
                print(f"  ✗ Error fetching 'My Drive' root ID: {e}")
                print("  Skipping My Drive.")
            
            # 2. If we have the root ID, query for folders *inside* it
            if my_drive_root_id:
                page_token = None
                # This query specifically asks for folders whose parent is the root
                my_drive_query = f"'{my_drive_root_id}' in parents and mimeType='application/vnd.google-apps.folder' and trashed=false"
                
                my_drive_folders_found = 0
                while True:
                    try:
                        response = drive_service.files().list(
                            q=my_drive_query,
                            spaces='drive',
                            fields='nextPageToken, files(id, name, parents)',
                            pageToken=page_token,
                            pageSize=1000
                        ).execute()
                        
                        batch = response.get('files', [])
                        for folder in batch:
                            folder['location'] = 'My Drive'
                            folder['shared_drive_id'] = None
                            folders.append(folder) # Add directly to the main 'folders' list
                            my_drive_folders_found += 1
                        
                        page_token = response.get('nextPageToken', None)
                        if page_token is None:
                            break
                    except Exception as e:
                        print(f"  Error listing My Drive folders: {e}")
                        break
                print(f"  ✓ Found {my_drive_folders_found} root folders in My Drive.")
        
        # Get ROOT folders from selected Shared Drives (This logic was correct)
        for shared_drive in drive_selection['shared_drives']:
            print(f"\n📁 Fetching ROOT folders from: {shared_drive['name']}...")
            
            try:
                page_token = None
                all_folders_in_drive = []
                
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
                    all_folders_in_drive.extend(batch)
                    
                    page_token = response.get('nextPageToken', None)
                    if page_token is None:
                        break
                
                # A folder in a Shared Drive is a "root folder" if its parent
                # is the Shared Drive ID itself, not another folder.
                all_folder_ids_in_drive = {f['id'] for f in all_folders_in_drive}
                root_folders_in_drive = []
                
                for folder in all_folders_in_drive:
                    parents = folder.get('parents', [])
                    if not parents:
                        is_root = True # Should not happen, but safety check
                    else:
                        # Check if *any* parent is *not* another folder in this drive
                        # This implies its parent is the drive root
                        is_root = any(parent_id not in all_folder_ids_in_drive for parent_id in parents)
                    
                    if is_root:
                        folder['location'] = shared_drive['name']
                        folder['shared_drive_id'] = shared_drive['id']
                        root_folders_in_drive.append(folder)
                
                print(f"  ✓ Found {len(root_folders_in_drive)} root folders (filtered from {len(all_folders_in_drive)} total)")
                folders.extend(root_folders_in_drive)
                
            except Exception as e:
                print(f"  Error: {e}")
        
        return folders

    def select_folders_interactive(self, drive_service):
        """
        Two-step selection: drives first, then ROOT folders.
        Includes a search filter for large numbers of folders.
        Returns: (selected_folders_list, universal_folder_object)
        """
        
        # Step 1: Select which drives to browse
        drive_selection = self.select_shared_drives(drive_service)
        
        if not drive_selection['shared_drives'] and not drive_selection['include_my_drive']:
            print("\nNo drives selected.")
            return [], None
        
        # Step 2: Get ALL ROOT folders from selected drives
        print("\n" + "=" * 80)
        all_folders = self.get_root_folders_only(drive_service, drive_selection)
        
        if not all_folders:
            print("No root folders found in selected drives!")
            return [], None
        
        # --- NEW: Filter Step ---
        safe_print(f"\n🔍 Found {len(all_folders)} total root folders.")
        print("To narrow down the list, enter a search term (e.g., 'sales', 'universal').")
        filter_term = input("Filter by name (or press Enter to show all): ").strip().lower()

        if filter_term:
            folders = [f for f in all_folders if filter_term in f['name'].lower()]
            if not folders:
                print(f"No folders found matching '{filter_term}'. Showing all {len(all_folders)}.")
                folders = all_folders
            else:
                print(f"✓ Showing {len(folders)} matching folders:")
        else:
            folders = all_folders
        # --- End Filter Step ---
        
        # Sort folders by location, then name
        folders.sort(key=lambda x: (x['location'], x['name'].lower()))
        
        # --- Step 3: Select Folders to Index ---
        print("\n" + "=" * 80)
        print("SELECT ROOT-LEVEL FOLDERS TO INDEX")
        print("=" * 80)
        print("(These will become your separate 'Chat Modes')")
        print()
        
        current_location = None
        for i, folder in enumerate(folders, 1):
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
            return [], None
        
        # Parse selection
        selected_indices = set()
        for part in selection.split(','):
            part = part.strip()
            if '-' in part:
                try:
                    start, end = part.split('-')
                    selected_indices.update(range(int(start), int(end) + 1))
                except ValueError:
                    print(f"Invalid range: {part}")
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
        
        # --- NEW: Step 4: Select Universal Folder ---
        print("\n" + "=" * 80)
        print("SELECT 'UNIVERSAL TRUTHS' FOLDER (OPTIONAL)")
        print("=" * 80)
        print("Select a folder from the *same list* whose contents")
        print("should be ADDED to ALL of the folders you selected above.")
        print("\n(Enter a single number, or press Enter to skip)")
        
        universal_selection = input("\nUniversal folder to add: ").strip()
        universal_folder_object = None
        
        if universal_selection.isdigit():
            idx = int(universal_selection)
            if 1 <= idx <= len(folders):
                # We use the original 'folders' list to get the object
                universal_folder_object = folders[idx - 1]
                print(f"✓ Will add '{universal_folder_object['name']}' to all other indexes.")
            else:
                print("Invalid selection. No universal folder will be added.")
        else:
            print("No universal folder selected.")

        return selected_folders, universal_folder_object
    
    def get_files_recursively(self, drive_service, folder_id, shared_drive_id=None, current_path="", path_prefix="", parent_folder_name=""):
        """
        Get all files in folder AND all subfolders recursively.
        Tracks the relative path (e.g., "January/Reports/")
        Adds a 'path_prefix' (e.g., "[UNIVERSAL]/")
        Tracks parent folder information for folder-aware search
        """
        all_files = []
        
        query = f"'{folder_id}' in parents and trashed=false"
        
        params = {
            'q': query,
            'spaces': 'drive',
            'fields': 'files(id, name, mimeType, size, modifiedTime, parents)',  # Added 'parents'
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
                    
                    if mime_type == 'application/vnd.google-apps.folder':
                        new_path = f"{current_path}{item['name']}/"
                        
                        subfolder_files = self.get_files_recursively(
                            drive_service, 
                            item['id'], 
                            shared_drive_id,
                            current_path=new_path,
                            path_prefix=path_prefix,
                            parent_folder_name=item['name']  # Pass folder name down
                        )
                        all_files.extend(subfolder_files)
                    else:
                        # Store the full relative path with prefix and folder metadata
                        item['relative_path'] = f"{path_prefix}{current_path}"
                        # Extract folder name from path (last folder in path)
                        folder_parts = current_path.strip('/').split('/')
                        item['folder_name'] = folder_parts[-1] if folder_parts and folder_parts[0] else parent_folder_name
                        # Get parent folder ID from parents array
                        item['parent_folder_id'] = item.get('parents', [folder_id])[0] if item.get('parents') else folder_id
                        all_files.append(item)
                
                page_token = response.get('nextPageToken', None)
                if page_token is None:
                    break
                    
            except Exception as e:
                print(f"    Error scanning subfolder: {e}")
                break
        
        return all_files
    
    def get_files_in_folders(self, drive_service, folder_selections, path_prefix=""):
        """
        Get all files in selected folders (including subfolders)
        Accepts a 'path_prefix' to prepend to all file paths.
        """
        print(f"\n📄 Fetching files from {len(folder_selections)} folders (Prefix: '{path_prefix}')...")
        
        all_files = []
        
        for folder_selection in folder_selections:
            folder_id = folder_selection['id']
            folder_name = folder_selection['name']
            location = folder_selection['location']
            shared_drive_id = folder_selection.get('shared_drive_id')
            
            print(f"\n  📁 {location} / {folder_name}")
            print(f"     Scanning folder and all subfolders...")
            
            folder_files = self.get_files_recursively(
                drive_service, 
                folder_id, 
                shared_drive_id,
                current_path="", # Start with empty path from the root
                path_prefix=path_prefix
            )
            
            print(f"    ✓ Found {len(folder_files)} files (including subfolders)")
            all_files.extend(folder_files)
        
        supported = [
            'application/pdf',
            'application/vnd.google-apps.document',
            'application/vnd.google-apps.presentation',
            'application/vnd.google-apps.spreadsheet',
            'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            'application/vnd.openxmlformats-officedocument.presentationml.presentation',
            'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            'text/csv',
            'text/plain',
            # Image formats for OCR processing
            'image/jpeg',
            'image/jpg', 
            'image/png',
            'image/gif',
            'image/bmp',
            'image/tiff',
            'image/webp'
        ]
        
        filtered = [f for f in all_files if f.get('mimeType') in supported]
        
        print(f"\n✓ Total files found: {len(all_files)}")
        print(f"✓ Indexable files: {len(filtered)}")
        
        return filtered

    def index_folders_incremental(self, folder_selections, universal_folder, drive_service):
        """
        Enhanced indexing with incremental processing - only new/modified files
        """
        if not folder_selections:
            print("\nNo folders selected to index.")
            return

        print("\n" + "=" * 80)
        print(f"🚀 INCREMENTAL INDEXING FOR {len(folder_selections)} FOLDER(S)")
        print("Only new and modified files will be processed!")
        print("=" * 80)

        loader = GoogleDriveLoader(drive_service)
        embedder = LocalEmbedder()
        
        overall_start_time = time.time()
        total_stats = {
            'new': 0, 'modified': 0, 'unchanged': 0, 'deleted': 0, 'failed': 0
        }
        
        # Get Universal Files First
        universal_files = []
        if universal_folder:
            print("=" * 80)
            print("1. Fetching 'Universal Truths' files...")
            universal_files = self.get_files_in_folders(
                drive_service, 
                [universal_folder], 
                path_prefix="[UNIVERSAL]/"
            )
            print(f"✓ Found {len(universal_files)} universal files to inject.")
            print("=" * 80)
        
        # Process each folder with incremental indexing
        for folder_selection in folder_selections:
            folder_id = folder_selection['id']
            folder_name = folder_selection['name']
            location = folder_selection['location']
            collection_name = f"folder_{folder_id}"
            
            print("\n\n" + "=" * 80)
            print(f"Processing: [{location}] {folder_name}")
            print(f"Collection: {collection_name}")
            print("=" * 80)

            try:
                vector_store = VectorStore(collection_name=collection_name)
            except Exception as e:
                print(f"✗ FATAL: Could not initialize vector store: {e}")
                continue

            # Get all files in folder
            print(f"  ...Fetching files for '{folder_name}'...")
            specific_files = self.get_files_in_folders(drive_service, [folder_selection], path_prefix="")
            all_files = universal_files + specific_files
            
            if not all_files:
                print("\n⚠️  No files found!")
                continue
            
            # Analyze files for incremental processing
            categorized = self.incremental_manager.filter_files_for_processing(
                all_files, collection_name
            )
            
            # Show incremental analysis
            print(self.incremental_manager.get_incremental_summary(categorized))
            
            # Clean up deleted files
            current_file_ids = {f['id'] for f in all_files}
            deleted_count = self.incremental_manager.cleanup_deleted_files(
                vector_store, collection_name, current_file_ids
            )
            total_stats['deleted'] += deleted_count
            
            # Process only new and modified files
            files_to_process = categorized['new'] + categorized['modified']
            total_stats['unchanged'] += len(categorized['unchanged'])
            
            if not files_to_process:
                print("\n🎉 Collection is up to date! No files need processing.")
                # Still update the indexed timestamp
                self.indexed_folders[folder_id] = {
                    'name': folder_name,
                    'location': location,
                    'collection_name': collection_name,
                    'indexed_at': time.strftime('%Y-%m-%d %H:%M:%S'),
                    'files_processed': len(categorized['unchanged']),
                    'incremental_indexing': True
                }
                self.save_indexed_folders()
                continue
            
            # Ask for confirmation
            safe_print(f"\n📊 Will process {len(files_to_process)} files:")
            print(f"  🆕 New: {len(categorized['new'])}")
            print(f"  🔄 Modified: {len(categorized['modified'])}")
            print(f"  ✅ Skipped: {len(categorized['unchanged'])}")
            
            response = input("\nProceed with incremental indexing? (yes/no): ")
            if response.lower() != 'yes':
                print("Cancelled.")
                continue
            
            # Process files
            print("\n🚀 Starting incremental indexing...\n")
            
            successful = 0
            failed = 0
            start_time = time.time()
            
            all_chunks = []
            all_metadatas = []
            all_ids = []
            
            for idx, file in enumerate(files_to_process, 1):
                file_id = file['id']
                
                # Determine if this is new or modified
                status_indicator = "🆕" if file_id not in self.incremental_manager.file_registry else "🔄"
                
                print(f"\n[{idx}/{len(files_to_process)}] {status_indicator} {file.get('relative_path', '')}{file['name'][:50]}")
                
                # Remove old chunks if file was modified
                if file_id in self.incremental_manager.file_registry:
                    try:
                        vector_store.collection.delete(where={"file_id": file_id})
                        print("    (Removed old chunks)")
                    except Exception as e:
                        print(f"    Warning: Could not remove old chunks: {e}")
                
                try:
                    # Process file (same logic as before)
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
                        text = extract_text(content, mime_type, file.get('name', ''), loader.ocr_service)
                    
                    # Check if text was filtered out due to poor quality
                    if text is None:
                        print("    ❌ Text filtered out (poor quality)")
                        failed += 1
                        continue
                    
                    if not text or len(text.strip()) < 50:
                        print("    ⚠️  Empty content")
                        continue
                    
                    # Check if this is a CSV file
                    is_csv = mime_type == 'text/csv' or file['name'].lower().endswith('.csv')
                    
                    # NEW: Don't chunk CSVs - treat as single unit
                    if is_csv:
                        print(f"    📊 CSV DETECTED: {file['name']} - storing as SINGLE COMPLETE unit")
                        # Add folder context to CSV for better search matching
                        folder_path = file.get('relative_path', '')
                        folder_context = f"\n[FILE LOCATION: {folder_path}]\n[FILE NAME: {file['name']}]\n\n"
                        text_with_context = folder_context + text
                        chunks = [text_with_context]  # Single chunk = entire CSV with context
                    else:
                        chunks = chunk_text(text, CHUNK_SIZE, CHUNK_OVERLAP)
                    
                    if not chunks:
                        continue
                    
                    print(f"    ✓ {len(text):,} chars → {len(chunks)} chunk(s)")
                    
                    # Create metadata with enhanced tracking
                    metadatas = [
                        {
                            'file_id': file['id'],
                            'file_name': file['name'],
                            'file_path': file.get('relative_path', ''),
                            'folder_name': file.get('folder_name', ''),
                            'parent_folder_id': file.get('parent_folder_id', ''),
                            'mime_type': mime_type,
                            'chunk_index': i,
                            'total_chunks': len(chunks),
                            'is_csv': is_csv,  # Flag CSV chunks for auto-fetching
                            'modified_time': file.get('modifiedTime'),
                            'indexed_time': time.strftime('%Y-%m-%d %H:%M:%S'),
                            'processing_status': 'new' if file_id not in self.incremental_manager.file_registry else 'modified'
                        }
                        for i in range(len(chunks))
                    ]
                    
                    ids = [f"{file['id']}_chunk_{i}" for i in range(len(chunks))]
                    
                    all_chunks.extend(chunks)
                    all_metadatas.extend(metadatas)
                    all_ids.extend(ids)
                    
                    # Mark as processed in tracking system
                    file_info = dict(file)
                    file_info['chunks_created'] = len(chunks)
                    file_info['collection_name'] = collection_name
                    self.incremental_manager.mark_file_processed(file_id, file_info)
                    
                    successful += 1
                    if file_id in self.incremental_manager.file_registry:
                        total_stats['modified'] += 1
                    else:
                        total_stats['new'] += 1
                    
                except Exception as e:
                    print(f"    ✗ Error: {e}")
                    self.incremental_manager.mark_file_failed(file_id, str(e))
                    failed += 1
                    total_stats['failed'] += 1
            
            # Batch process all chunks
            if all_chunks:
                print(f"\n🚀 Processing {len(all_chunks)} chunks for vector storage...")
                try:
                    all_embeddings = embedder.embed_documents(all_chunks)
                    vector_store.add_documents(all_chunks, all_embeddings, all_metadatas, all_ids)
                    print("✓ Batch processing complete!")
                except Exception as e:
                    print(f"✗ Error during batch processing: {e}")
            
            # Update folder tracking
            self.indexed_folders[folder_id] = {
                'name': folder_name,
                'location': location,
                'collection_name': collection_name,
                'indexed_at': time.strftime('%Y-%m-%d %H:%M:%S'),
                'files_processed': successful + len(categorized['unchanged']),  # Total files in collection
                'new_files_processed': len(categorized['new']),
                'modified_files_processed': len(categorized['modified']),
                'incremental_indexing': True
            }
            self.save_indexed_folders()
            self.incremental_manager.save_file_registry()
            
            # Summary for this folder
            total_time = time.time() - start_time
            print("\n" + "=" * 80)
            print(f"🎉 INCREMENTAL INDEXING COMPLETE: {folder_name}")
            print("=" * 80)
            print(f"✅ Processed: {successful}")
            print(f"✓ Skipped (unchanged): {len(categorized['unchanged'])}")
            print(f"🗑️  Cleaned up: {deleted_count} deleted files")
            print(f"❌ Failed: {failed}")
            print(f"⏱️  Time: {total_time/60:.1f} minutes")
            safe_print(f"📊 Collection size: {vector_store.get_stats()['total_documents']} chunks")
            print("=" * 80)

        # Final Summary
        overall_time = time.time() - overall_start_time
        print("\n\n" + "=" * 80)
        print("🎉 INCREMENTAL INDEXING COMPLETE!")
        print("=" * 80)
        print(f"🆕 New files: {total_stats['new']}")
        print(f"🔄 Modified files: {total_stats['modified']}")  
        print(f"✅ Unchanged files: {total_stats['unchanged']} (skipped)")
        print(f"🗑️  Deleted files: {total_stats['deleted']} (cleaned)")
        print(f"❌ Failed files: {total_stats['failed']}")
        print(f"⏱️  Total time: {overall_time/60:.1f} minutes")
        print("=" * 80)
        
        total_files = sum(total_stats.values())
        if total_files > 0:
            efficiency = total_stats['unchanged'] / total_files * 100
            safe_print(f"⚡ Efficiency: {efficiency:.1f}% of files skipped (incremental indexing)")

    def index_folders_unattended(self, folder_selections, universal_folder, drive_service):
        """
        Index selected folders WITHOUT any confirmation prompts.
        Same as index_folders but runs fully automated for unattended execution.
        """
        
        if not folder_selections:
            print("\nNo folders selected to index.")
            return

        print("\n" + "=" * 80)
        print(f"🤖 UNATTENDED INDEXING FOR {len(folder_selections)} FOLDER(S)")
        print("Running fully automated - no confirmations required")
        print("Each folder will be indexed into a separate database collection.")
        print("=" * 80)

        loader = GoogleDriveLoader(drive_service)
        embedder = LocalEmbedder()
        
        overall_start_time = time.time()
        
        # --- Get Universal Files FIRST ---
        universal_files = []
        if universal_folder:
            print("=" * 80)
            print("1. Fetching 'Universal Truths' files...")
            universal_files = self.get_files_in_folders(
                drive_service, 
                [universal_folder], 
                path_prefix="[UNIVERSAL]/"
            )
            print(f"✓ Found {len(universal_files)} universal files to inject.")
            print("=" * 80)
        
        # --- Process each folder automatically ---
        for folder_selection in folder_selections:
            folder_id = folder_selection['id']
            folder_name = folder_selection['name']
            location = folder_selection['location']
            
            collection_name = f"folder_{folder_id}"
            
            print("\n\n" + "=" * 80)
            print(f"Processing: [{location}] {folder_name}")
            print(f"Collection: {collection_name}")
            print("=" * 80)

            try:
                vector_store = VectorStore(collection_name=collection_name)
            except Exception as e:
                print(f"✗ FATAL: Could not initialize vector store for {collection_name}: {e}")
                print("Skipping this folder.")
                continue

            # --- Clear old universal files before re-injecting ---
            try:
                print("  ...Clearing old [UNIVERSAL] files from this collection...")
                all_docs = vector_store.collection.get()
                if all_docs and all_docs.get('metadatas'):
                    universal_ids = [
                        doc_id for doc_id, metadata in zip(all_docs['ids'], all_docs['metadatas'])
                        if metadata.get('file_path', '').startswith('[UNIVERSAL]')
                    ]
                    if universal_ids:
                        vector_store.collection.delete(ids=universal_ids)
                        print(f"  ✓ Cleared {len(universal_ids)} old universal file chunks.")
                    else:
                        print("  ✓ No old universal files to clear.")
                else:
                    print("  ✓ Collection is empty, nothing to clear.")
            except Exception as e:
                print(f"  Warning: Could not clear old universal files: {e}")

            # --- Get specific files and combine with universal files ---
            print(f"  ...Fetching specific files for '{folder_name}'...")
            specific_files = self.get_files_in_folders(drive_service, [folder_selection], path_prefix="")
            
            files = universal_files + specific_files
            
            if not files:
                print("\n⚠️  No indexable files found for this folder (or universal)!")
                self.indexed_folders[folder_id] = {
                    'name': folder_name, 'location': location,
                    'collection_name': collection_name,
                    'indexed_at': time.strftime('%Y-%m-%d %H:%M:%S'),
                    'files_processed': 0
                }
                self.save_indexed_folders()
                continue
            
            # Show breakdown (no confirmation prompt)
            print("\n" + "=" * 80)
            print("FILES TO INDEX IN THIS COLLECTION")
            print("=" * 80)
            print(f"Total: {len(files)} files ({len(specific_files)} specific + {len(universal_files)} universal)")
            
            total_size = sum(int(f.get('size', 0)) for f in files)
            print(f"Size: {total_size / (1024**3):.2f} GB")
            
            print("\n🚀 Starting unattended indexing...")
            print("=" * 80)
            
            successful = 0
            failed = 0
            empty = 0
            skipped = 0
            start_time = time.time()
            
            all_chunks = []
            all_metadatas = []
            all_ids = []
            
            for idx, file in enumerate(files, 1):
                if idx % 25 == 0:
                    elapsed = time.time() - start_time
                    if elapsed > 0:
                        rate = idx / elapsed
                        remaining = (len(files) - idx) / rate
                        print(f"\n⏱️  Progress: {idx}/{len(files)} ({idx/len(files)*100:.1f}%) - ETA: {remaining/60:.0f} mins")
                
                print(f"\n[{idx}/{len(files)}] {file.get('relative_path', '')}{file['name'][:60]}")
                
                try:
                    # Delta Indexing Check
                    try:
                        existing_doc = vector_store.collection.get(
                            where={"file_id": file['id']},
                            limit=1,
                            include=["metadatas"]
                        )
                        if existing_doc['metadatas']:
                            indexed_time = existing_doc['metadatas'][0].get('modified_time')
                            if indexed_time and indexed_time == file.get('modifiedTime'):
                                print(f"  ✓ Skipping (up-to-date in this collection)")
                                skipped += 1
                                continue 
                        if existing_doc['ids']:
                            print("  File modified. Clearing old chunks from this collection...")
                            vector_store.collection.delete(where={"file_id": file['id']})
                    except Exception as e:
                        print(f"  Warning: Could not check existing doc: {e}")

                    # File Loading
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
                        text = extract_text(content, mime_type, file.get('name', ''), loader.ocr_service)
                    
                    if text is None:
                        print("  ❌ Filtered out (poor quality)")
                        failed += 1
                        continue
                    
                    if not text or len(text.strip()) < 50:
                        print("  ⚠️  Empty")
                        empty += 1
                        continue
                    
                    print(f"  ✓ {len(text):,} chars")
                    
                    # Check if CSV
                    is_csv = mime_type == 'text/csv' or file['name'].lower().endswith('.csv')
                    
                    if is_csv:
                        print(f"    📊 CSV DETECTED: {file['name']} - storing as SINGLE COMPLETE unit")
                        folder_path = file.get('relative_path', '')
                        folder_context = f"\n[FILE LOCATION: {folder_path}]\n[FILE NAME: {file['name']}]\n\n"
                        text_with_context = folder_context + text
                        chunks = [text_with_context]
                    else:
                        chunks = chunk_text(text, CHUNK_SIZE, CHUNK_OVERLAP)
                    
                    if not chunks:
                        empty += 1
                        continue
                    
                    # Metadatas
                    metadatas = [
                        {
                            'file_id': file['id'],
                            'file_name': file['name'],
                            'file_path': file.get('relative_path', ''),
                            'folder_name': file.get('folder_name', ''),
                            'parent_folder_id': file.get('parent_folder_id', ''),
                            'mime_type': mime_type,
                            'chunk_index': i,
                            'total_chunks': len(chunks),
                            'is_csv': is_csv,
                            'modified_time': file.get('modifiedTime') 
                        }
                        for i in range(len(chunks))
                    ]
                    
                    ids = [f"{file['id']}_chunk_{i}" for i in range(len(chunks))]
                    
                    all_chunks.extend(chunks)
                    all_metadatas.extend(metadatas)
                    all_ids.extend(ids)
                    
                    successful += 1
                    print(f"  ✅ {len(chunks)} chunks (queued)")
                    
                except KeyboardInterrupt:
                    print(f"\n\n⚠️  Interrupted!")
                    break
                except Exception as e:
                    print(f"  ✗ Error: {e}")
                    failed += 1
            
            # --- Process Batches ---
            if all_chunks:
                print("\n" + "=" * 80)
                print(f"🚀 Processing {successful} files for collection '{collection_name}'...")
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
            self.indexed_folders[folder_id] = {
                'name': folder_name,
                'location': location,
                'collection_name': collection_name,
                'indexed_at': time.strftime('%Y-%m-%d %H:%M:%S'),
                'files_processed': successful
            }
            self.save_indexed_folders()
            
            # Summary for this folder
            total_time = time.time() - start_time
            print("\n" + "=" * 80)
            print(f"🎉 FOLDER COMPLETE: {folder_name}")
            print("=" * 80)
            print(f"✅ Success (new/updated): {successful}")
            print(f"✓ Skipped (up-to-date): {skipped}")
            print(f"⚠️  Empty: {empty}")
            print(f"❌ Failed: {failed}")
            print(f"⏱️  Time: {total_time/60:.1f} minutes")
            safe_print(f"📊 Total in collection: {vector_store.get_stats()['total_documents']}")
            print("=" * 80)

        # Final Summary
        overall_time = time.time() - overall_start_time
        print("\n\n" + "=" * 80)
        print("🎉 UNATTENDED INDEXING COMPLETE!")
        print(f"⏱️  Total time: {overall_time/60:.1f} minutes")
        print("=" * 80)

    def index_folders(self, folder_selections, universal_folder, drive_service):
        """
        Index selected folders.
        Injects files from 'universal_folder' into each collection.
        """
        
        if not folder_selections:
            print("\nNo folders selected to index.")
            return

        print("\n" + "=" * 80)
        print(f"STARTING INDEXING FOR {len(folder_selections)} FOLDER(S)")
        print("Each folder will be indexed into a separate database collection.")
        print("=" * 80)

        loader = GoogleDriveLoader(drive_service)
        embedder = LocalEmbedder()
        
        overall_start_time = time.time()
        
        # --- Get Universal Files FIRST ---
        universal_files = []
        if universal_folder:
            print("=" * 80)
            print("1. Fetching 'Universal Truths' files...")
            universal_files = self.get_files_in_folders(
                drive_service, 
                [universal_folder], 
                path_prefix="[UNIVERSAL]/" # Add prefix
            )
            print(f"✓ Found {len(universal_files)} universal files to inject.")
            print("=" * 80)
        
        # --- Now, loop through each folder and index IT + universal files ---
        for folder_selection in folder_selections:
            folder_id = folder_selection['id']
            folder_name = folder_selection['name']
            location = folder_selection['location']
            
            collection_name = f"folder_{folder_id}"
            
            print("\n\n" + "=" * 80)
            print(f"Processing: [{location}] {folder_name}")
            print(f"Collection: {collection_name}")
            print("=" * 80)

            try:
                vector_store = VectorStore(collection_name=collection_name)
            except Exception as e:
                print(f"✗ FATAL: Could not initialize vector store for {collection_name}: {e}")
                print("Skipping this folder.")
                continue

            # --- Clear old universal files before re-injecting ---
            try:
                print("  ...Clearing old [UNIVERSAL] files from this collection...")
                # Get all documents with [UNIVERSAL] in their file_path
                # ChromaDB doesn't support $like, so we query and filter
                all_docs = vector_store.collection.get()
                if all_docs and all_docs.get('metadatas'):
                    universal_ids = [
                        doc_id for doc_id, metadata in zip(all_docs['ids'], all_docs['metadatas'])
                        if metadata.get('file_path', '').startswith('[UNIVERSAL]')
                    ]
                    if universal_ids:
                        vector_store.collection.delete(ids=universal_ids)
                        print(f"  ✓ Cleared {len(universal_ids)} old universal file chunks.")
                    else:
                        print("  ✓ No old universal files to clear.")
                else:
                    print("  ✓ Collection is empty, nothing to clear.")
            except Exception as e:
                print(f"  Warning: Could not clear old universal files: {e}")

            # --- Get specific files and combine with universal files ---
            print(f"  ...Fetching specific files for '{folder_name}'...")
            specific_files = self.get_files_in_folders(drive_service, [folder_selection], path_prefix="")
            
            files = universal_files + specific_files # Combine lists
            
            if not files:
                print("\n⚠️  No indexable files found for this folder (or universal)!")
                self.indexed_folders[folder_id] = {
                    'name': folder_name, 'location': location,
                    'collection_name': collection_name,
                    'indexed_at': time.strftime('%Y-%m-%d %H:%M:%S'),
                    'files_processed': 0
                }
                self.save_indexed_folders()
                continue
            
            # Show breakdown
            print("\n" + "=" * 80)
            print("FILES TO INDEX IN THIS COLLECTION")
            print("=" * 80)
            print(f"Total: {len(files)} files ({len(specific_files)} specific + {len(universal_files)} universal)")
            
            total_size = sum(int(f.get('size', 0)) for f in files)
            print(f"Size: {total_size / (1024**3):.2f} GB")
            avg_time = 2 
            est_minutes = (len(files) * avg_time) / 60
            print(f"⏱️  Estimated: {est_minutes:.0f} minutes")
            
            print("\n" + "=" * 80)
            response = input("Proceed with this folder? (yes/no): ")
            
            if response.lower() != 'yes':
                print("Cancelled for this folder.")
                continue
            
            # Index
            print("\n🚀 Indexing collection...\n")
            print("=" * 80)
            
            successful = 0
            failed = 0
            empty = 0
            skipped = 0
            start_time = time.time()
            
            all_chunks = []
            all_metadatas = []
            all_ids = []
            
            for idx, file in enumerate(files, 1):
                if idx % 25 == 0:
                    elapsed = time.time() - start_time
                    if elapsed > 0:
                        rate = idx / elapsed
                        remaining = (len(files) - idx) / rate
                        print(f"\n⏱️  Progress: {idx}/{len(files)} ({idx/len(files)*100:.1f}%) - ETA: {remaining/60:.0f} mins")
                
                print(f"\n[{idx}/{len(files)}] {file.get('relative_path', '')}{file['name'][:60]}")
                
                try:
                    # Delta Indexing Check (works for both universal and specific)
                    try:
                        existing_doc = vector_store.collection.get(
                            where={"file_id": file['id']},
                            limit=1,
                            include=["metadatas"]
                        )
                        if existing_doc['metadatas']:
                            indexed_time = existing_doc['metadatas'][0].get('modified_time')
                            if indexed_time and indexed_time == file.get('modifiedTime'):
                                print(f"  ✓ Skipping (up-to-date in this collection)")
                                skipped += 1
                                continue 
                        if existing_doc['ids']:
                            print("  File modified. Clearing old chunks from this collection...")
                            vector_store.collection.delete(where={"file_id": file['id']})
                    except Exception as e:
                        print(f"  Warning: Could not check existing doc: {e}")

                    # File Loading
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
                        text = extract_text(content, mime_type, file.get('name', ''), loader.ocr_service)
                    
                    # Check if text was filtered out due to poor quality
                    if text is None:
                        print("  ❌ Filtered out (poor quality)")
                        failed += 1
                        continue
                    
                    if not text or len(text.strip()) < 50:
                        print("  ⚠️  Empty")
                        empty += 1
                        continue
                    
                    print(f"  ✓ {len(text):,} chars")
                    
                    # Check if this is a CSV file
                    is_csv = mime_type == 'text/csv' or file['name'].lower().endswith('.csv')
                    
                    # NEW: Don't chunk CSVs - treat as single unit
                    if is_csv:
                        print(f"    📊 CSV DETECTED: {file['name']} - storing as SINGLE COMPLETE unit")
                        # Add folder context to CSV for better search matching
                        folder_path = file.get('relative_path', '')
                        folder_context = f"\n[FILE LOCATION: {folder_path}]\n[FILE NAME: {file['name']}]\n\n"
                        text_with_context = folder_context + text
                        chunks = [text_with_context]  # Single chunk = entire CSV with context
                    else:
                        chunks = chunk_text(text, CHUNK_SIZE, CHUNK_OVERLAP)
                    
                    if not chunks:
                        empty += 1
                        continue
                    
                    # Metadatas - Enhanced with folder information
                    metadatas = [
                        {
                            'file_id': file['id'],
                            'file_name': file['name'],
                            'file_path': file.get('relative_path', ''),
                            'folder_name': file.get('folder_name', ''),  # NEW: Folder name
                            'parent_folder_id': file.get('parent_folder_id', ''),  # NEW: Parent folder ID
                            'mime_type': mime_type,
                            'chunk_index': i,
                            'total_chunks': len(chunks),
                            'is_csv': is_csv,  # Flag CSV chunks for auto-fetching
                            'modified_time': file.get('modifiedTime') 
                        }
                        for i in range(len(chunks))
                    ]
                    
                    ids = [f"{file['id']}_chunk_{i}" for i in range(len(chunks))]
                    
                    all_chunks.extend(chunks)
                    all_metadatas.extend(metadatas)
                    all_ids.extend(ids)
                    
                    successful += 1
                    print(f"  ✅ {len(chunks)} chunks (queued)")
                    
                except KeyboardInterrupt:
                    print(f"\n\n⚠️  Interrupted!")
                    break
                except Exception as e:
                    print(f"  ✗ Error: {e}")
                    failed += 1
            
            # --- Process Batches ---
            if all_chunks:
                print("\n" + "=" * 80)
                print(f"🚀 Processing {successful} files for collection '{collection_name}'...")
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
            self.indexed_folders[folder_id] = {
                'name': folder_name,
                'location': location,
                'collection_name': collection_name,
                'indexed_at': time.strftime('%Y-%m-%d %H:%M:%S'),
                'files_processed': successful # This counts specific + universal
            }
            self.save_indexed_folders()
            
            # Summary for this folder
            total_time = time.time() - start_time
            print("\n" + "=" * 80)
            print(f"🎉 FOLDER COMPLETE: {folder_name}")
            print("=" * 80)
            print(f"✅ Success (new/updated): {successful}")
            print(f"✓ Skipped (up-to-date): {skipped}")
            print(f"⚠️  Empty: {empty}")
            print(f"❌ Failed: {failed}")
            print(f"⏱️  Time: {total_time/60:.1f} minutes")
            safe_print(f"📊 Total in collection: {vector_store.get_stats()['total_documents']}")
            print("=" * 80)

        # Final Summary
        overall_time = time.time() - overall_start_time
        print("\n\n" + "=" * 80)
        print("🎉 ALL FOLDERS PROCESSED!")
        print(f"⏱️  Total time: {overall_time/60:.1f} minutes")
        print("=" * 80)


def main():
    """Main function with incremental indexing option"""
    print("\n" + "=" * 80)
    print("ROOT-LEVEL FOLDER INDEXING")
    print("=" * 80)
    
    indexer = FolderIndexer()
    
    print("\n1️⃣  Authenticating...")
    drive_service = authenticate_google_drive()
    
    print("\n2️⃣  Select drives and folders...")
    selected, universal = indexer.select_folders_interactive(drive_service)
    
    if not selected:
        print("\nNo folders selected.")
        return
    
    print(f"\n✓ Selected {len(selected)} folders to index:")
    for f in selected:
        print(f"  - [{f['location']}] {f['name']}")
    
    if universal:
        print(f"\n✓ Will inject '{universal['name']}' into all of them.")
    
    # Check if any folders have been indexed before
    previously_indexed = [f for f in selected if f['id'] in indexer.indexed_folders]
    
    if previously_indexed:
        safe_print(f"\n📊 {len(previously_indexed)} folder(s) have been indexed before:")
        for f in previously_indexed:
            folder_info = indexer.indexed_folders[f['id']]
            print(f"  - {f['name']} (last indexed: {folder_info['indexed_at']})")
        
        print("\n" + "=" * 80)
        print("INDEXING MODE SELECTION")
        print("=" * 80)
        print("1. 🚀 Incremental Indexing (RECOMMENDED)")
        print("   - Only processes new and modified files")
        print("   - Much faster for re-indexing")
        print("   - Automatically cleans up deleted files")
        print("")
        print("2. 🔄 Full Re-indexing")
        print("   - Processes all files regardless of changes")
        print("   - Slower but ensures complete rebuild")
        print("   - Use if you suspect indexing issues")
        print("")
        print("3. 🤖 Unattended Full Re-indexing")
        print("   - Same as Full Re-indexing but no confirmations")
        print("   - Processes all folders automatically")
        print("   - For automated/scheduled runs")
        
        mode_choice = input("\nSelect indexing mode (1, 2, or 3): ").strip()
        
        if mode_choice == "1" or mode_choice == "":
            print("\n✅ Using Incremental Indexing")
            indexer.index_folders_incremental(selected, universal, drive_service)
        elif mode_choice == "3":
            print("\n✅ Using Unattended Full Re-indexing")
            indexer.index_folders_unattended(selected, universal, drive_service)
        else:
            print("\n✅ Using Full Re-indexing")
            indexer.index_folders(selected, universal, drive_service)
    else:
        print("\n3️⃣  First-time indexing (will use full indexing)...")
        indexer.index_folders(selected, universal, drive_service)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nExiting...")

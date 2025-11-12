#!/usr/bin/env python3
"""
Incremental Indexing System
Tracks individual files and only processes new/modified content
"""

import json
import os
import time
import logging
from typing import Dict, List, Set, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

class IncrementalIndexingManager:
    """
    Manages incremental indexing by tracking individual files and their states
    """
    
    def __init__(self, tracking_file: str = "file_tracking.json"):
        self.tracking_file = tracking_file
        self.file_registry: Dict[str, Dict] = {}
        self.load_file_registry()
    
    def load_file_registry(self):
        """Load the file tracking registry from disk"""
        if os.path.exists(self.tracking_file):
            try:
                with open(self.tracking_file, 'r', encoding='utf-8') as f:
                    self.file_registry = json.load(f)
                logger.info(f"Loaded file registry with {len(self.file_registry)} tracked files")
            except Exception as e:
                logger.error(f"Failed to load file registry: {e}")
                self.file_registry = {}
        else:
            self.file_registry = {}
            logger.info("Starting with empty file registry")
    
    def save_file_registry(self):
        """Save the file tracking registry to disk"""
        try:
            with open(self.tracking_file, 'w', encoding='utf-8') as f:
                json.dump(self.file_registry, f, indent=2, ensure_ascii=False)
            logger.info(f"Saved file registry with {len(self.file_registry)} tracked files")
        except Exception as e:
            logger.error(f"Failed to save file registry: {e}")
    
    def get_file_status(self, file_id: str, modified_time: str, file_size: Optional[str] = None) -> str:
        """
        Determine the status of a file: 'new', 'modified', or 'unchanged'
        
        Args:
            file_id: Google Drive file ID
            modified_time: File's last modified timestamp
            file_size: File size (optional additional check)
        
        Returns:
            'new' | 'modified' | 'unchanged'
        """
        if file_id not in self.file_registry:
            return 'new'
        
        tracked_file = self.file_registry[file_id]
        
        # Check modification time
        if tracked_file.get('modified_time') != modified_time:
            return 'modified'
        
        # Optional: Check file size as additional verification
        if file_size and tracked_file.get('file_size') != file_size:
            return 'modified'
        
        return 'unchanged'
    
    def mark_file_processed(self, file_id: str, file_info: Dict):
        """
        Mark a file as successfully processed and update tracking info
        
        Args:
            file_id: Google Drive file ID
            file_info: Dictionary with file metadata
        """
        self.file_registry[file_id] = {
            'file_name': file_info.get('name', ''),
            'modified_time': file_info.get('modifiedTime', ''),
            'file_size': file_info.get('size', ''),
            'mime_type': file_info.get('mimeType', ''),
            'last_indexed': datetime.now().isoformat(),
            'collection_name': file_info.get('collection_name', ''),
            'folder_name': file_info.get('folder_name', ''),
            'relative_path': file_info.get('relative_path', ''),
            'chunks_created': file_info.get('chunks_created', 0)
        }
    
    def mark_file_failed(self, file_id: str, error: str):
        """Mark a file as failed to process"""
        if file_id in self.file_registry:
            self.file_registry[file_id]['last_error'] = error
            self.file_registry[file_id]['last_error_time'] = datetime.now().isoformat()
    
    def remove_file_tracking(self, file_id: str):
        """Remove a file from tracking (e.g., when deleted)"""
        if file_id in self.file_registry:
            del self.file_registry[file_id]
    
    def get_collection_files(self, collection_name: str) -> List[str]:
        """Get all file IDs that belong to a specific collection"""
        return [
            file_id for file_id, info in self.file_registry.items()
            if info.get('collection_name') == collection_name
        ]
    
    def filter_files_for_processing(self, files: List[Dict], collection_name: str) -> Dict[str, List[Dict]]:
        """
        Filter files into categories: new, modified, unchanged
        
        Args:
            files: List of file dictionaries from Google Drive API
            collection_name: Target collection name
        
        Returns:
            Dictionary with 'new', 'modified', 'unchanged' lists
        """
        categorized = {
            'new': [],
            'modified': [],
            'unchanged': []
        }
        
        for file in files:
            file_id = file['id']
            modified_time = file.get('modifiedTime', '')
            file_size = file.get('size', '')
            
            status = self.get_file_status(file_id, modified_time, file_size)
            
            # Add collection name to file info for tracking
            file['collection_name'] = collection_name
            
            categorized[status].append(file)
        
        return categorized
    
    def get_incremental_summary(self, categorized_files: Dict[str, List[Dict]]) -> str:
        """Generate a summary of what will be processed"""
        new_count = len(categorized_files['new'])
        modified_count = len(categorized_files['modified'])
        unchanged_count = len(categorized_files['unchanged'])
        total_to_process = new_count + modified_count
        
        summary = f"""
📊 INCREMENTAL INDEXING ANALYSIS
================================
📄 Total files found: {new_count + modified_count + unchanged_count}
🆕 New files: {new_count}
🔄 Modified files: {modified_count}
✅ Unchanged files: {unchanged_count} (will be skipped)

🚀 Files to process: {total_to_process}
⚡ Time savings: {unchanged_count} files skipped
"""
        
        if total_to_process == 0:
            summary += "\n🎉 No new or modified files - collection is up to date!"
        
        return summary
    
    def cleanup_deleted_files(self, vector_store, collection_name: str, current_file_ids: Set[str]):
        """
        Remove files from vector store and tracking that no longer exist in the folder
        
        Args:
            vector_store: Vector store instance
            collection_name: Collection name
            current_file_ids: Set of file IDs currently in the folder
        """
        tracked_files = self.get_collection_files(collection_name)
        deleted_files = set(tracked_files) - current_file_ids
        
        if not deleted_files:
            return 0
        
        deleted_count = 0
        for file_id in deleted_files:
            try:
                # Remove from vector store
                vector_store.collection.delete(where={"file_id": file_id})
                
                # Remove from tracking
                self.remove_file_tracking(file_id)
                deleted_count += 1
                
                logger.info(f"Removed deleted file from index: {file_id}")
            except Exception as e:
                logger.error(f"Failed to remove deleted file {file_id}: {e}")
        
        if deleted_count > 0:
            logger.info(f"Cleaned up {deleted_count} deleted files from collection {collection_name}")
        
        return deleted_count


def create_enhanced_folder_indexer():
    """
    Create an enhanced version of folder_indexer.py with incremental indexing
    """
    enhanced_code = '''
# Enhanced folder_indexer.py with Incremental Indexing

from auth import authenticate_google_drive
from document_loader import GoogleDriveLoader, extract_text, chunk_text
from embeddings import LocalEmbedder
from vector_store import VectorStore
from config import CHUNK_SIZE, CHUNK_OVERLAP, INDEXED_FOLDERS_FILE
from incremental_indexing import IncrementalIndexingManager
import json
import os
import time


class EnhancedFolderIndexer:
    """Enhanced folder indexer with incremental indexing capabilities"""
    
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
    
    def index_folders_incremental(self, folder_selections, universal_folder, drive_service):
        """
        Enhanced indexing with incremental processing
        """
        if not folder_selections:
            print("\\nNo folders selected to index.")
            return

        print("\\n" + "=" * 80)
        print(f"ENHANCED INCREMENTAL INDEXING FOR {len(folder_selections)} FOLDER(S)")
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
            
            print("\\n\\n" + "=" * 80)
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
                print("\\n⚠️  No files found!")
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
                print("\\n🎉 Collection is up to date! No files need processing.")
                continue
            
            # Ask for confirmation
            print(f"\\n📊 Will process {len(files_to_process)} files:")
            print(f"  🆕 New: {len(categorized['new'])}")
            print(f"  🔄 Modified: {len(categorized['modified'])}")
            print(f"  ✅ Skipped: {len(categorized['unchanged'])}")
            
            response = input("\\nProceed with incremental indexing? (yes/no): ")
            if response.lower() != 'yes':
                print("Cancelled.")
                continue
            
            # Process files
            print("\\n🚀 Starting incremental indexing...\\n")
            
            successful = 0
            failed = 0
            start_time = time.time()
            
            all_chunks = []
            all_metadatas = []
            all_ids = []
            
            for idx, file in enumerate(files_to_process, 1):
                file_id = file['id']
                print(f"\\n[{idx}/{len(files_to_process)}] {file.get('relative_path', '')}{file['name'][:60]}")
                
                # Check if file was modified and remove old chunks
                if file_id in self.incremental_manager.file_registry:
                    print("  🔄 File modified - removing old chunks...")
                    try:
                        vector_store.collection.delete(where={"file_id": file_id})
                    except Exception as e:
                        print(f"  Warning: Could not remove old chunks: {e}")
                
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
                    
                    if not text or len(text.strip()) < 50:
                        print("  ⚠️  Empty content")
                        continue
                    
                    chunks = chunk_text(text, CHUNK_SIZE, CHUNK_OVERLAP)
                    if not chunks:
                        continue
                    
                    print(f"  ✓ {len(text):,} chars → {len(chunks)} chunks")
                    
                    # Create metadata
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
                            'modified_time': file.get('modifiedTime'),
                            'indexed_time': time.strftime('%Y-%m-%d %H:%M:%S')
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
                    print(f"  ✗ Error: {e}")
                    self.incremental_manager.mark_file_failed(file_id, str(e))
                    failed += 1
                    total_stats['failed'] += 1
            
            # Batch process all chunks
            if all_chunks:
                print(f"\\n🚀 Processing {len(all_chunks)} chunks for vector storage...")
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
                'files_processed': successful,
                'incremental_indexing': True
            }
            self.save_indexed_folders()
            self.incremental_manager.save_file_registry()
            
            # Summary for this folder
            total_time = time.time() - start_time
            print("\\n" + "=" * 80)
            print(f"🎉 INCREMENTAL INDEXING COMPLETE: {folder_name}")
            print("=" * 80)
            print(f"✅ Processed: {successful}")
            print(f"✓ Skipped (unchanged): {len(categorized['unchanged'])}")
            print(f"🗑️  Cleaned up: {deleted_count} deleted files")
            print(f"❌ Failed: {failed}")
            print(f"⏱️  Time: {total_time/60:.1f} minutes")
            print(f"📊 Collection size: {vector_store.get_stats()['total_documents']} chunks")
            print("=" * 80)

        # Final Summary
        overall_time = time.time() - overall_start_time
        print("\\n\\n" + "=" * 80)
        print("🎉 INCREMENTAL INDEXING COMPLETE!")
        print("=" * 80)
        print(f"🆕 New files: {total_stats['new']}")
        print(f"🔄 Modified files: {total_stats['modified']}")  
        print(f"✅ Unchanged files: {total_stats['unchanged']} (skipped)")
        print(f"🗑️  Deleted files: {total_stats['deleted']} (cleaned)")
        print(f"❌ Failed files: {total_stats['failed']}")
        print(f"⏱️  Total time: {overall_time/60:.1f} minutes")
        print("=" * 80)
        
        efficiency = total_stats['unchanged'] / (sum(total_stats.values()) or 1) * 100
        print(f"⚡ Efficiency: {efficiency:.1f}% of files skipped (incremental indexing)")
'''

    return enhanced_code


if __name__ == "__main__":
    # Test the incremental indexing manager
    manager = IncrementalIndexingManager()
    
    # Example usage
    test_files = [
        {
            'id': 'file1',
            'name': 'document.pdf',
            'modifiedTime': '2025-11-07T10:00:00Z',
            'size': '1024'
        },
        {
            'id': 'file2', 
            'name': 'image.jpg',
            'modifiedTime': '2025-11-07T11:00:00Z',
            'size': '2048'
        }
    ]
    
    categorized = manager.filter_files_for_processing(test_files, "test_collection")
    print(manager.get_incremental_summary(categorized))
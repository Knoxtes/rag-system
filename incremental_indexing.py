"""
Incremental Indexing Manager
Tracks file modifications and manages incremental updates
"""

import json
import os
import time
from datetime import datetime
from typing import Dict, List, Any

class IncrementalIndexingManager:
    """Manages incremental indexing state and file tracking"""
    
    def __init__(self, registry_file='incremental_registry.json'):
        self.registry_file = registry_file
        self.file_registry = {}
        self.load_file_registry()
    
    def load_file_registry(self):
        """Load file registry from disk"""
        if os.path.exists(self.registry_file):
            try:
                with open(self.registry_file, 'r') as f:
                    self.file_registry = json.load(f)
            except Exception as e:
                print(f"Warning: Could not load file registry: {e}")
                self.file_registry = {}
        else:
            self.file_registry = {}
    
    def save_file_registry(self):
        """Save file registry to disk"""
        try:
            with open(self.registry_file, 'w') as f:
                json.dump(self.file_registry, f, indent=2)
        except Exception as e:
            print(f"Warning: Could not save file registry: {e}")
    
    def filter_files_for_processing(self, files: List[Dict], collection_name: str) -> Dict[str, List]:
        """
        Categorize files into new, modified, and unchanged
        
        Args:
            files: List of file dictionaries from Google Drive
            collection_name: Name of the collection being processed
        
        Returns:
            Dictionary with 'new', 'modified', and 'unchanged' file lists
        """
        categorized = {
            'new': [],
            'modified': [],
            'unchanged': []
        }
        
        for file in files:
            file_id = file['id']
            file_modified_time = file.get('modifiedTime')
            
            if file_id not in self.file_registry:
                # New file
                categorized['new'].append(file)
            else:
                # Check if file was modified
                registry_entry = self.file_registry[file_id]
                registry_modified_time = registry_entry.get('modified_time')
                registry_collection = registry_entry.get('collection_name')
                
                # File is modified if:
                # 1. Modified time changed, OR
                # 2. File is now being indexed in a different collection
                if (file_modified_time != registry_modified_time or 
                    collection_name != registry_collection):
                    categorized['modified'].append(file)
                else:
                    categorized['unchanged'].append(file)
        
        return categorized
    
    def mark_file_processed(self, file_id: str, file_info: Dict):
        """Mark a file as successfully processed"""
        self.file_registry[file_id] = {
            'file_name': file_info.get('name', ''),
            'modified_time': file_info.get('modifiedTime'),
            'processed_at': datetime.now().isoformat(),
            'collection_name': file_info.get('collection_name', ''),
            'chunks_created': file_info.get('chunks_created', 0),
            'file_path': file_info.get('relative_path', ''),
            'status': 'success'
        }
    
    def mark_file_failed(self, file_id: str, error_message: str):
        """Mark a file as failed to process"""
        if file_id in self.file_registry:
            self.file_registry[file_id]['status'] = 'failed'
            self.file_registry[file_id]['error'] = error_message
            self.file_registry[file_id]['failed_at'] = datetime.now().isoformat()
        else:
            self.file_registry[file_id] = {
                'status': 'failed',
                'error': error_message,
                'failed_at': datetime.now().isoformat()
            }
    
    def cleanup_deleted_files(self, vector_store, collection_name: str, current_file_ids: set) -> int:
        """
        Remove files from vector store that no longer exist in Google Drive
        
        Args:
            vector_store: VectorStore instance
            collection_name: Name of the collection
            current_file_ids: Set of file IDs currently in Google Drive
        
        Returns:
            Number of deleted files cleaned up
        """
        deleted_count = 0
        
        try:
            # Get all documents in the collection
            all_docs = vector_store.collection.get(include=["metadatas"])
            
            if all_docs and all_docs.get('metadatas'):
                # Find files in vector store that are no longer in Google Drive
                deleted_file_ids = set()
                
                for metadata in all_docs['metadatas']:
                    file_id = metadata.get('file_id')
                    if file_id and file_id not in current_file_ids:
                        deleted_file_ids.add(file_id)
                
                # Delete chunks for each deleted file
                for file_id in deleted_file_ids:
                    try:
                        vector_store.collection.delete(where={"file_id": file_id})
                        deleted_count += 1
                        print(f"  🗑️ Cleaned up deleted file: {file_id}")
                        
                        # Remove from registry
                        if file_id in self.file_registry:
                            del self.file_registry[file_id]
                            
                    except Exception as e:
                        print(f"  Warning: Could not delete chunks for file {file_id}: {e}")
        
        except Exception as e:
            print(f"Warning: Could not cleanup deleted files: {e}")
        
        return deleted_count
    
    def get_incremental_summary(self, categorized: Dict[str, List]) -> str:
        """Get a formatted summary of incremental analysis"""
        summary = "\n" + "=" * 80 + "\n"
        summary += "📊 INCREMENTAL ANALYSIS\n"
        summary += "=" * 80 + "\n"
        summary += f"🆕 New files: {len(categorized['new'])}\n"
        summary += f"🔄 Modified files: {len(categorized['modified'])}\n"
        summary += f"✅ Unchanged files: {len(categorized['unchanged'])} (will skip)\n"
        summary += "=" * 80
        
        if categorized['unchanged']:
            efficiency = len(categorized['unchanged']) / (len(categorized['new']) + len(categorized['modified']) + len(categorized['unchanged'])) * 100
            summary += f"\n⚡ Efficiency: {efficiency:.1f}% of files will be skipped"
        
        return summary
    
    def get_registry_stats(self) -> Dict:
        """Get statistics about the file registry"""
        total_files = len(self.file_registry)
        successful_files = len([f for f in self.file_registry.values() if f.get('status') == 'success'])
        failed_files = len([f for f in self.file_registry.values() if f.get('status') == 'failed'])
        
        return {
            'total_files': total_files,
            'successful_files': successful_files,
            'failed_files': failed_files,
            'success_rate': (successful_files / total_files * 100) if total_files > 0 else 0
        }
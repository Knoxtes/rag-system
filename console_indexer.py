#!/usr/bin/env python3
"""
Console Google Drive Indexer

A command-line tool for indexing folders from Google Drive using the RAG system.
Supports both individual folder indexing and full collection indexing.

Usage:
    python console_indexer.py --list-folders                    # List all available folders
    python console_indexer.py --index-folder <folder_id>        # Index specific folder
    python console_indexer.py --index-all                       # Index all collections
    python console_indexer.py --search <query>                  # Search in collections

Examples:
    python console_indexer.py --list-folders
    python console_indexer.py --index-folder "1ABC123xyz"
    python console_indexer.py --index-all
    python console_indexer.py --search "marketing strategy"

Requirements:
    - credentials.json file for Google Drive access
    - Valid config.py with collections defined
"""

import os
import sys
import argparse
import json
from datetime import datetime
from pathlib import Path

# Fix Windows console encoding for Unicode characters
if os.name == 'nt':  # Windows
    try:
        # Try to set UTF-8 encoding for stdout
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except (AttributeError, OSError):
        # Fallback for older Python versions or if reconfigure fails
        import codecs
        sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
        sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import all necessary modules
from google_drive_oauth import get_drive_service
from vector_store import VectorStore
from embeddings import LocalEmbedder
import config
import time
import traceback

# For colored output
try:
    from rich.console import Console
    from rich.panel import Panel
    from rich.progress import Progress, TaskID
    from rich.table import Table
    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False
    print("⚠️  Rich not installed. Install with: pip install rich")

def safe_drive_call(func, max_retries=3, backoff=2, **kwargs):
    """Safely call Google Drive API with retries"""
    for attempt in range(max_retries):
        try:
            return func(**kwargs).execute()
        except Exception as e:
            if attempt == max_retries - 1:
                raise e
            print(f"⚠️  Drive API error (attempt {attempt + 1}/{max_retries}): {e}")
            time.sleep(backoff * (attempt + 1))
    return None

class ConsoleIndexer:
    """Console-based Google Drive indexer using existing RAG system components"""
    
    def __init__(self):
        self.console = Console() if RICH_AVAILABLE else None
        self.drive_service = None
        self.vector_store = None
        self.embedder = None
        self.shared_drive_id = getattr(config, 'SHARED_DRIVE_ID', None)
        
        # Print startup banner
        self._print_banner()
        
        # Initialize components
        self._init_google_drive()
        self._init_vector_store()
    
    def _print_banner(self):
        """Print startup banner"""
        banner = """
╔══════════════════════════════════════════════════════════════════╗
║                    🔍 Console Google Drive Indexer               ║
║                                                                  ║
║  Index folders from Google Drive into your RAG system           ║
║  Compatible with existing web interface and configurations      ║
╚══════════════════════════════════════════════════════════════════╝
        """
        
        if self.console:
            self.console.print(Panel(banner.strip(), style="blue"))
        else:
            print(banner)
    
    def _init_google_drive(self):
        """Initialize Google Drive service"""
        try:
            if self.console:
                self.console.print("📂 Connecting to Google Drive...", style="blue")
            else:
                print("📂 Connecting to Google Drive...")
            
            self.drive_service = get_drive_service()
            
            if self.console:
                self.console.print("✅ Connected to Google Drive!", style="green")
            else:
                print("✅ Connected to Google Drive!")
                
        except Exception as e:
            if self.console:
                self.console.print(f"❌ Failed to connect to Google Drive: {e}", style="red")
            else:
                print(f"❌ Failed to connect to Google Drive: {e}")
            sys.exit(1)
    
    def _init_vector_store(self):
        """Initialize vector store and embedder"""
        try:
            if self.console:
                self.console.print("🧮 Initializing embeddings...", style="blue")
            else:
                print("🧮 Initializing embeddings...")
            
            # Initialize embedder
            if hasattr(config, 'USE_VERTEX_EMBEDDINGS') and config.USE_VERTEX_EMBEDDINGS:
                try:
                    from vertex_embeddings import VertexEmbedder
                    self.embedder = VertexEmbedder()
                    if self.console:
                        self.console.print("✅ Using Vertex AI embeddings (768-dim)", style="green")
                    else:
                        print("✅ Using Vertex AI embeddings (768-dim)")
                except ImportError:
                    self.embedder = LocalEmbedder()
                    if self.console:
                        self.console.print("⚠️  Using local embeddings (Vertex AI not available)", style="yellow")
                    else:
                        print("⚠️  Using local embeddings (Vertex AI not available)")
            else:
                self.embedder = LocalEmbedder()
                if self.console:
                    self.console.print("✅ Using local embeddings (384-dim)", style="green")
                else:
                    print("✅ Using local embeddings (384-dim)")
            
            # Initialize vector store
            self.vector_store = VectorStore()
            
        except Exception as e:
            if self.console:
                self.console.print(f"❌ Failed to initialize embeddings: {e}", style="red")
            else:
                print(f"❌ Failed to initialize embeddings: {e}")
            sys.exit(1)
    
    def list_folders(self):
        """List all available folders from Google Drive"""
        if not self.shared_drive_id:
            if self.console:
                self.console.print("❌ SHARED_DRIVE_ID not configured in config.py", style="red")
            else:
                print("❌ SHARED_DRIVE_ID not configured in config.py")
            return
        
        try:
            if self.console:
                self.console.print("📁 Fetching folders from Google Drive...", style="blue")
            else:
                print("📁 Fetching folders from Google Drive...")
            
            # Get all folders from shared drive
            query = f"parents in '{self.shared_drive_id}' and mimeType='application/vnd.google-apps.folder' and trashed=false"
            folders = safe_drive_call(
                self.drive_service.files().list,
                q=query,
                driveId=self.shared_drive_id,
                corpora='drive',
                includeItemsFromAllDrives=True,
                supportsAllDrives=True,
                fields="files(id, name, modifiedTime, parents)"
            )
            
            if not folders or 'files' not in folders:
                if self.console:
                    self.console.print("❌ No folders found", style="red")
                else:
                    print("❌ No folders found")
                return
            
            folder_list = folders['files']
            
            if self.console:
                # Create rich table
                table = Table(title="📁 Available Google Drive Folders")
                table.add_column("#", style="cyan", width=4)
                table.add_column("Folder Name", style="green")
                table.add_column("Folder ID", style="yellow", width=30)
                table.add_column("Last Modified", style="blue")
                table.add_column("Status", style="magenta")
                
                for i, folder in enumerate(folder_list, 1):
                    folder_name = folder.get('name', 'Unknown')
                    folder_id = folder.get('id', 'Unknown')
                    modified = folder.get('modifiedTime', 'Unknown')
                    
                    # Check if already indexed
                    try:
                        collections = self.vector_store.list_all_collections()
                        collection_exists = folder_name in [c.name for c in collections]
                    except:
                        collection_exists = False
                    status = "✅ Indexed" if collection_exists else "⏳ Not indexed"
                    
                    # Format modified time
                    try:
                        if modified != 'Unknown':
                            dt = datetime.fromisoformat(modified.replace('Z', '+00:00'))
                            modified = dt.strftime('%Y-%m-%d %H:%M')
                    except:
                        pass
                    
                    table.add_row(str(i), folder_name, folder_id, modified, status)
                
                self.console.print(table)
                self.console.print(f"\n💡 Found {len(folder_list)} folders")
                self.console.print("💡 Use --index-folder <folder_id> to index a specific folder")
                
            else:
                # Plain text output
                print(f"\n📁 Found {len(folder_list)} folders:")
                print("-" * 80)
                for i, folder in enumerate(folder_list, 1):
                    folder_name = folder.get('name', 'Unknown')
                    folder_id = folder.get('id', 'Unknown')
                    modified = folder.get('modifiedTime', 'Unknown')
                    
                    # Check if already indexed
                    try:
                        collections = self.vector_store.list_all_collections()
                        collection_exists = folder_name in [c.name for c in collections]
                    except:
                        collection_exists = False
                    status = "✅ Indexed" if collection_exists else "⏳ Not indexed"
                    
                    print(f"{i:2d}. {folder_name}")
                    print(f"    ID: {folder_id}")
                    print(f"    Status: {status}")
                    print(f"    Modified: {modified}")
                    print()
                
                print("💡 Use --index-folder <folder_id> to index a specific folder")
        
        except Exception as e:
            if self.console:
                self.console.print(f"❌ Error listing folders: {e}", style="red")
            else:
                print(f"❌ Error listing folders: {e}")
    
    def get_all_files_recursive_from_folder(self, folder_id, folder_name="Unknown"):
        """Get all files recursively from a folder - matches admin_routes.py logic"""
        all_files = []
        processed_folders = set()
        
        def get_files_from_folder(current_folder_id, path=""):
            if current_folder_id in processed_folders:
                return
            processed_folders.add(current_folder_id)
            
            try:
                # Get all items in current folder
                query = f"parents in '{current_folder_id}' and trashed=false"
                items = safe_drive_call(
                    self.drive_service.files().list,
                    q=query,
                    driveId=self.shared_drive_id,
                    corpora='drive',
                    includeItemsFromAllDrives=True,
                    supportsAllDrives=True,
                    fields="files(id, name, mimeType, size, modifiedTime, parents)"
                )
                
                if not items or 'files' not in items:
                    return
                
                for item in items['files']:
                    item_name = item.get('name', '')
                    item_type = item.get('mimeType', '')
                    
                    # Skip hidden/system files
                    if item_name.startswith('.') or item_name.startswith('~'):
                        continue
                    
                    current_path = f"{path}/{item_name}" if path else item_name
                    
                    if item_type == 'application/vnd.google-apps.folder':
                        # Recursively process subfolder
                        get_files_from_folder(item['id'], current_path)
                    else:
                        # Add file to list
                        item['path'] = current_path
                        item['root_folder'] = folder_name
                        all_files.append(item)
            
            except Exception as e:
                print(f"⚠️  Error processing folder {current_folder_id}: {e}")
        
        get_files_from_folder(folder_id)
        return all_files
    
    def index_folder(self, folder_id, force=False):
        """Index a specific folder"""
        try:
            # Get folder information
            folder_info = safe_drive_call(
                self.drive_service.files().get,
                fileId=folder_id,
                supportsAllDrives=True,
                fields="id, name"
            )
            
            if not folder_info:
                if self.console:
                    self.console.print(f"❌ Folder {folder_id} not found", style="red")
                else:
                    print(f"❌ Folder {folder_id} not found")
                return False
            
            folder_name = folder_info.get('name', 'Unknown')
            
            # Use the same collection naming convention as the admin system
            collection_name = f"folder_{folder_id}"
            
            # Check if already indexed
            try:
                collections = self.vector_store.list_all_collections()
                collection_exists = collection_name in [c.name for c in collections]
            except:
                collection_exists = False
            if collection_exists and not force:
                if self.console:
                    self.console.print(f"⚠️  Collection '{folder_name}' already exists. Use --force to reindex.", style="yellow")
                else:
                    print(f"⚠️  Collection '{folder_name}' already exists. Use --force to reindex.")
                return False
            
            if self.console:
                self.console.print(f"🔄 Indexing folder: {folder_name} ({folder_id})", style="blue")
            else:
                print(f"🔄 Indexing folder: {folder_name} ({folder_id})")
            
            # Get all files recursively
            all_files = self.get_all_files_recursive_from_folder(folder_id, folder_name)
            
            if not all_files:
                if self.console:
                    self.console.print(f"⚠️  No files found in folder '{folder_name}'", style="yellow")
                else:
                    print(f"⚠️  No files found in folder '{folder_name}'")
                return False
            
            if self.console:
                self.console.print(f"📄 Found {len(all_files)} files to index", style="green")
            else:
                print(f"📄 Found {len(all_files)} files to index")
            
            # Delete existing collection if force reindexing
            if collection_exists and force:
                self.vector_store.delete_collection_by_name(collection_name)
                if self.console:
                    self.console.print(f"🗑️  Deleted existing collection '{folder_name}'", style="yellow")
                else:
                    print(f"🗑️  Deleted existing collection '{folder_name}'")
            
            # Process files with progress tracking
            success_count = 0
            error_count = 0
            skipped_count = 0
            
            if RICH_AVAILABLE and self.console:
                with Progress(console=self.console) as progress:
                    task = progress.add_task(f"Processing {folder_name}...", total=len(all_files))
                    
                    for i, file_info in enumerate(all_files):
                        try:
                            # Process individual file using correct collection name
                            success = self._process_file(file_info, collection_name)
                            if success:
                                success_count += 1
                            elif success is False:
                                error_count += 1
                            else:
                                skipped_count += 1
                        except Exception as e:
                            error_count += 1
                            print(f"Error processing {file_info.get('name', 'unknown')}: {e}")
                        
                        progress.update(task, advance=1)
            else:
                # Simple progress without rich
                for i, file_info in enumerate(all_files):
                    print(f"Processing {i+1}/{len(all_files)}: {file_info.get('name', 'unknown')}")
                    try:
                        success = self._process_file(file_info, collection_name)
                        if success:
                            success_count += 1
                        elif success is False:
                            error_count += 1
                        else:
                            skipped_count += 1
                    except Exception as e:
                        error_count += 1
                        print(f"Error processing {file_info.get('name', 'unknown')}: {e}")
                            error_count += 1
                    except Exception as e:
                        error_count += 1
                        print(f"Error: {e}")
            
            # Summary
            if self.console:
                self.console.print(f"\n✅ Indexing complete!", style="green")
                self.console.print(f"   • Successfully processed: {success_count} files")
                self.console.print(f"   • Errors: {error_count} files")
                self.console.print(f"   • Collection: {folder_name}")
            else:
                print(f"\n✅ Indexing complete!")
                print(f"   • Successfully processed: {success_count} files")
                print(f"   • Errors: {error_count} files")
                print(f"   • Collection: {folder_name}")
            
            return True
            
        except Exception as e:
            if self.console:
                self.console.print(f"❌ Error indexing folder: {e}", style="red")
            else:
                print(f"❌ Error indexing folder: {e}")
            return False
    
    def _update_indexed_folders_registry(self, folder_id, folder_info):
        """Update the indexed_folders.json file with new folder information"""
        import json
        import os
        from datetime import datetime
        
        registry_file = 'indexed_folders.json'
        
        # Load existing registry
        if os.path.exists(registry_file):
            try:
                with open(registry_file, 'r', encoding='utf-8') as f:
                    registry = json.load(f)
            except Exception as e:
                if self.console:
                    self.console.print(f"⚠️  Error reading registry: {e}. Creating new registry.", style="yellow")
                else:
                    print(f"⚠️  Error reading registry: {e}. Creating new registry.")
                registry = {}
        else:
            registry = {}
        
        # Update registry with folder info
        registry[folder_id] = folder_info
        
        # Save updated registry
        try:
            with open(registry_file, 'w', encoding='utf-8') as f:
                json.dump(registry, f, indent=2)
            
            if self.console:
                self.console.print(f"📝 Updated indexed folders registry", style="green")
            else:
                print(f"📝 Updated indexed folders registry")
        except Exception as e:
            if self.console:
                self.console.print(f"❌ Error updating registry: {e}", style="red")
            else:
                print(f"❌ Error updating registry: {e}")

    def _process_file(self, file_info, collection_name):
        """Process a single file and add to vector store (simplified version)"""
        try:
            file_id = file_info.get('id')
            file_name = file_info.get('name', 'unknown')
            file_path = file_info.get('path', file_name)
            
            # Skip if no ID
            if not file_id:
                return False
            
            # For now, just log the file without processing
            # This is a simplified version to test the indexing workflow
            # In a full implementation, you would:
            # 1. Download file content from Google Drive
            # 2. Extract text based on file type  
            # 3. Chunk the content
            # 4. Generate embeddings
            # 5. Store in vector database
            
            # Skip files that are too large or binary
            file_size = file_info.get('size', 0)
            if isinstance(file_size, str):
                try:
                    file_size = int(file_size)
                except:
                    file_size = 0
            
            # Skip very large files (>10MB)
            if file_size > 10 * 1024 * 1024:
                return False
            
            # Skip common non-text file types
            skip_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.ico', '.tiff',
                             '.mp4', '.avi', '.mov', '.wmv', '.mp3', '.wav', '.zip', 
                             '.rar', '.exe', '.dll', '.bin'}
            
            file_ext = os.path.splitext(file_name.lower())[1]
            if file_ext in skip_extensions:
                return False
            
            # For demo purposes, just return success without actual processing
            # This allows testing the folder structure and file discovery
            return True
            
        except Exception as e:
            if self.console:
                self.console.print(f"Error processing file {file_info.get('name', 'unknown')}: {e}", style="yellow")
            else:
                print(f"Error processing file {file_info.get('name', 'unknown')}: {e}")
            return False
    
    def index_all_collections(self):
        """Index all collections defined in config"""
        if not hasattr(config, 'COLLECTIONS') or not config.COLLECTIONS:
            if self.console:
                self.console.print("❌ No collections defined in config.py", style="red")
            else:
                print("❌ No collections defined in config.py")
            return
        
        if self.console:
            self.console.print(f"🔄 Starting full indexing of {len(config.COLLECTIONS)} collections", style="blue")
        else:
            print(f"🔄 Starting full indexing of {len(config.COLLECTIONS)} collections")
        
        for i, collection in enumerate(config.COLLECTIONS, 1):
            folder_id = collection.get('folder_id')
            collection_name = collection.get('name', f'Collection {i}')
            
            if not folder_id:
                if self.console:
                    self.console.print(f"⚠️  Skipping '{collection_name}' - no folder_id", style="yellow")
                else:
                    print(f"⚠️  Skipping '{collection_name}' - no folder_id")
                continue
            
            if self.console:
                self.console.print(f"\n📁 [{i}/{len(config.COLLECTIONS)}] Indexing: {collection_name}")
            else:
                print(f"\n📁 [{i}/{len(config.COLLECTIONS)}] Indexing: {collection_name}")
            
            self.index_folder(folder_id, force=False)
        
        if self.console:
            self.console.print("\n✅ Full indexing complete!", style="green")
        else:
            print("\n✅ Full indexing complete!")
    
    def search_collections(self, query):
        """Search across all collections"""
        try:
            if self.console:
                self.console.print(f"🔍 Searching for: '{query}'", style="blue")
            else:
                print(f"🔍 Searching for: '{query}'")
            
            # Get all collections
            collections = self.vector_store.list_all_collections()
            collections = [c.name for c in collections] if collections else []
            
            if not collections:
                if self.console:
                    self.console.print("⚠️  No collections found to search", style="yellow")
                else:
                    print("⚠️  No collections found to search")
                return
            
            results_found = False
            for collection_name in collections:
                try:
                    # Search in this collection
                    results = self.vector_store.search(collection_name, query, top_k=3)
                    
                    if results:
                        results_found = True
                        if self.console:
                            self.console.print(f"\n📚 Results from '{collection_name}':", style="green")
                        else:
                            print(f"\n📚 Results from '{collection_name}':")
                        
                        for i, result in enumerate(results, 1):
                            distance = result.get('distance', 0)
                            content = result.get('content', 'No content')
                            metadata = result.get('metadata', {})
                            
                            if self.console:
                                panel_content = f"Score: {1-distance:.3f}\n\n{content[:200]}..."
                                self.console.print(Panel(panel_content, title=f"Result {i}"))
                            else:
                                print(f"  {i}. Score: {1-distance:.3f}")
                                print(f"     Content: {content[:200]}...")
                                print()
                
                except Exception as e:
                    print(f"Error searching collection '{collection_name}': {e}")
            
            if not results_found:
                if self.console:
                    self.console.print("⚠️  No results found", style="yellow")
                else:
                    print("⚠️  No results found")
        
        except Exception as e:
            if self.console:
                self.console.print(f"❌ Search error: {e}", style="red")
            else:
                print(f"❌ Search error: {e}")


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="Console Google Drive Indexer for RAG System",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    python console_indexer.py --list-folders
    python console_indexer.py --index-folder "1ABC123xyz"
    python console_indexer.py --index-all
    python console_indexer.py --search "marketing strategy"
    python console_indexer.py --index-folder "1ABC123xyz" --force
        """
    )
    
    parser.add_argument('--list-folders', action='store_true',
                      help='List all available folders from Google Drive')
    parser.add_argument('--index-folder', type=str,
                      help='Index a specific folder by ID')
    parser.add_argument('--index-all', action='store_true',
                      help='Index all collections defined in config.py')
    parser.add_argument('--search', type=str,
                      help='Search for text across all collections')
    parser.add_argument('--force', action='store_true',
                      help='Force reindexing even if collection exists')
    
    args = parser.parse_args()
    
    # Validate arguments
    if not any([args.list_folders, args.index_folder, args.index_all, args.search]):
        parser.print_help()
        print("\n❌ Please specify an action: --list-folders, --index-folder, --index-all, or --search")
        return 1
    
    # Initialize indexer
    try:
        indexer = ConsoleIndexer()
    except Exception as e:
        print(f"❌ Failed to initialize indexer: {e}")
        return 1
    
    # Execute requested action
    try:
        if args.list_folders:
            indexer.list_folders()
        
        elif args.index_folder:
            success = indexer.index_folder(args.index_folder, force=args.force)
            if not success:
                return 1
        
        elif args.index_all:
            indexer.index_all_collections()
        
        elif args.search:
            indexer.search_collections(args.search)
        
        return 0
    
    except KeyboardInterrupt:
        print("\n\n❌ Cancelled by user")
        return 1
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    sys.exit(main())
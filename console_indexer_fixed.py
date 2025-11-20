#!/usr/bin/env python3
"""
Fixed Console Google Drive Indexer - Compatible with main RAG system
Uses proper collection naming and maintains indexed_folders.json registry
"""

import os
import sys
import argparse
import json
from datetime import datetime
from typing import List, Dict, Optional

try:
    from rich.console import Console
    from rich.table import Table
    from rich.panel import Panel
    from rich.progress import Progress
    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False
    print("⚠️  Rich not available, using basic console output")

# Import our modules
from google_drive_oauth import get_drive_service
from vector_store import VectorStore
from document_loader import GoogleDriveLoader, extract_text, chunk_text

def safe_drive_call(func, max_retries=3, backoff=2, **kwargs):
    """Safely call Google Drive API with retry logic"""
    import time
    
    for attempt in range(max_retries):
        try:
            result = func()
            return result
        except Exception as e:
            if attempt == max_retries - 1:
                raise e
            print(f"⚠️  API call failed (attempt {attempt + 1}/{max_retries}): {e}")
            time.sleep(backoff ** attempt)
    
    return None

try:
    from vertex_embeddings import VertexEmbedder
    VERTEX_AVAILABLE = True
except ImportError:
    try:
        from embeddings import LocalEmbedder
        VERTEX_AVAILABLE = False
    except ImportError:
        print("❌ No embeddings module available")
        sys.exit(1)

class FixedConsoleIndexer:
    def __init__(self):
        self.console = Console() if RICH_AVAILABLE else None
        self.drive_service = None
        self.embedder = None
        self.vector_store = None
        
    def initialize(self):
        """Initialize all components"""
        try:
            # Header
            if self.console:
                self.console.print(Panel(
                    "[bold blue]🔍 Fixed Console Google Drive Indexer[/bold blue]\\n\\n"
                    "Compatible with main RAG system\\n"
                    "Uses proper collection naming and registry format",
                    title="RAG System Indexer",
                    expand=False
                ))
            else:
                print("="*80)
                print("🔍 Fixed Console Google Drive Indexer")
                print("Compatible with main RAG system")
                print("="*80)
            
            # Connect to Google Drive
            if self.console:
                self.console.print("📂 Connecting to Google Drive...")
            else:
                print("📂 Connecting to Google Drive...")
            
            self.drive_service = get_drive_service()
            if not self.drive_service:
                raise Exception("Failed to connect to Google Drive")
            
            if self.console:
                self.console.print("✅ Connected to Google Drive!")
            else:
                print("✅ Connected to Google Drive!")
            
            # Initialize embeddings
            if self.console:
                self.console.print("🧮 Initializing embeddings...")
            else:
                print("🧮 Initializing embeddings...")
            
            if VERTEX_AVAILABLE:
                self.embedder = VertexEmbedder()
                if self.console:
                    self.console.print(f"✅ Using Vertex AI embeddings ({self.embedder.dimension}-dim)")
                else:
                    print(f"✅ Using Vertex AI embeddings ({self.embedder.dimension}-dim)")
            else:
                self.embedder = LocalEmbedder()
                if self.console:
                    self.console.print(f"✅ Using local embeddings ({self.embedder.dimension}-dim)")
                else:
                    print(f"✅ Using local embeddings ({self.embedder.dimension}-dim)")
            
            # Initialize vector store
            self.vector_store = VectorStore()
            
            return True
            
        except Exception as e:
            if self.console:
                self.console.print(f"❌ Initialization failed: {str(e)}", style="red")
            else:
                print(f"❌ Initialization failed: {str(e)}")
            return False
    
    def list_folders(self):
        """List all available folders from Google Drive"""
        try:
            if self.console:
                self.console.print("📁 Fetching folders from Google Drive...")
            else:
                print("📁 Fetching folders from Google Drive...")
            
            # Get root folders from shared drive
            from config import SHARED_DRIVE_ID
            
            response = safe_drive_call(lambda: self.drive_service.files().list(
                q=f"'{SHARED_DRIVE_ID}' in parents and mimeType='application/vnd.google-apps.folder' and trashed=false",
                driveId=SHARED_DRIVE_ID,
                corpora='drive',
                supportsAllDrives=True,
                includeItemsFromAllDrives=True,
                fields='files(id, name, modifiedTime)',
                pageSize=100
            ).execute())
            
            folders = response.get('files', [])
            
            # Load indexed folders registry to check status
            indexed_folders = {}
            if os.path.exists('indexed_folders.json'):
                try:
                    with open('indexed_folders.json', 'r', encoding='utf-8') as f:
                        indexed_folders = json.load(f)
                except:
                    pass
            
            if self.console:
                table = Table(title="📁 Available Google Drive Folders")
                table.add_column("#", style="dim", width=6)
                table.add_column("Folder Name", style="bold")
                table.add_column("Folder ID", style="dim")
                table.add_column("Last Modified", style="cyan")
                table.add_column("Status", style="green")
                
                for i, folder in enumerate(folders, 1):
                    folder_id = folder['id']
                    folder_name = folder['name']
                    modified_time = folder.get('modifiedTime', 'Unknown')[:19].replace('T', ' ')
                    
                    # Check if indexed
                    if folder_id in indexed_folders:
                        status = "✅ Indexed"
                        collection_name = indexed_folders[folder_id].get('collection_name', 'Unknown')
                    else:
                        status = "⏳ Not indexed"
                    
                    table.add_row(
                        str(i),
                        folder_name,
                        folder_id[:32] + "…",
                        modified_time,
                        status
                    )
                
                self.console.print(table)
                self.console.print(f"\\n💡 Found {len(folders)} folders")
                self.console.print("💡 Use --index-folder <folder_id> to index a specific folder")
            else:
                print("\\n📁 Available Google Drive Folders:")
                print("-" * 100)
                for i, folder in enumerate(folders, 1):
                    folder_id = folder['id']
                    folder_name = folder['name']
                    modified_time = folder.get('modifiedTime', 'Unknown')[:19].replace('T', ' ')
                    
                    # Check if indexed
                    if folder_id in indexed_folders:
                        status = "✅ Indexed"
                    else:
                        status = "⏳ Not indexed"
                    
                    print(f"{i:2}. {folder_name:<25} | {folder_id} | {modified_time} | {status}")
                
                print(f"\\n💡 Found {len(folders)} folders")
                print("💡 Use --index-folder <folder_id> to index a specific folder")
            
            return folders
            
        except Exception as e:
            if self.console:
                self.console.print(f"❌ Error listing folders: {str(e)}", style="red")
            else:
                print(f"❌ Error listing folders: {str(e)}")
            return []
    
    def index_folder(self, folder_id, force=False):
        """Index a specific folder with proper collection naming"""
        try:
            # Get folder information
            folder_info = safe_drive_call(lambda: self.drive_service.files().get(
                fileId=folder_id,
                supportsAllDrives=True,
                fields='id,name'
            ).execute())
            
            if not folder_info:
                if self.console:
                    self.console.print(f"❌ Folder {folder_id} not found", style="red")
                else:
                    print(f"❌ Folder {folder_id} not found")
                return False
            
            folder_name = folder_info.get('name', 'Unknown')
            
            # Use the same collection naming convention as the admin system
            collection_name = f"folder_{folder_id}"
            
            if self.console:
                self.console.print(f"🔄 Indexing folder: [bold]{folder_name}[/bold]", style="blue")
                self.console.print(f"📦 Collection: {collection_name}")
            else:
                print(f"🔄 Indexing folder: {folder_name}")
                print(f"📦 Collection: {collection_name}")
            
            # Check if already exists
            try:
                # Create collection-specific vector store
                collection_vector_store = VectorStore(collection_name=collection_name)
                collections = collection_vector_store.client.list_collections()
                collection_exists = collection_name in [c.name for c in collections]
            except:
                collection_exists = False
            
            if collection_exists and not force:
                if self.console:
                    self.console.print(f"⚠️  Collection already exists. Use --force to reindex.", style="yellow")
                else:
                    print(f"⚠️  Collection already exists. Use --force to reindex.")
                return False
            
            # Delete existing collection if force reindexing
            if collection_exists and force:
                collection_vector_store.delete_collection_by_name(collection_name)
                # Re-create the vector store after deletion
                collection_vector_store = VectorStore(collection_name=collection_name)
                if self.console:
                    self.console.print(f"🗑️  Deleted existing collection", style="yellow")
                else:
                    print(f"🗑️  Deleted existing collection")
            
            # Get all files
            all_files = self._get_all_files_recursive(folder_id, folder_name)
            
            if not all_files:
                if self.console:
                    self.console.print(f"⚠️  No files found in folder", style="yellow")
                else:
                    print(f"⚠️  No files found in folder")
                return False
            
            if self.console:
                self.console.print(f"📄 Found {len(all_files)} files to index", style="green")
            else:
                print(f"📄 Found {len(all_files)} files to index")
            
            # Process files with optimized batching
            loader = GoogleDriveLoader(self.drive_service)
            
            # Process all files and collect results
            processed_results = self._process_files_batch(all_files, folder_name, loader, collection_vector_store)
            
            success_count = processed_results['success_count']
            error_count = processed_results['error_count']
            skipped_count = processed_results['skipped_count']
            
            # Update indexed_folders.json registry
            self._update_registry(folder_id, {
                'collection_name': collection_name,
                'name': folder_name,
                'path': folder_name,
                'location': folder_name,
                'file_count': len(all_files),
                'files_processed': success_count,
                'files_failed': error_count,
                'files_skipped': skipped_count,
                'chunks_created': processed_results.get('total_chunks', 0),
                'indexed_at': datetime.now().isoformat()
            })
            
            # Summary
            if self.console:
                self.console.print(f"\\n✅ Indexing complete for '{folder_name}'", style="green bold")
                self.console.print(f"   📊 Files processed: {success_count}/{len(all_files)}", style="green")
                if error_count > 0:
                    self.console.print(f"   ❌ Files failed: {error_count}", style="red")
                if skipped_count > 0:
                    self.console.print(f"   ⏭️  Files skipped: {skipped_count}", style="yellow")
                self.console.print(f"   📄 Document chunks: {processed_results.get('total_chunks', 0)}", style="cyan")
                self.console.print(f"   🏷️  Collection: {collection_name}", style="blue")
            else:
                print(f"\\n✅ Indexing complete for '{folder_name}'")
                print(f"   📊 Files processed: {success_count}/{len(all_files)}")
                if error_count > 0:
                    print(f"   ❌ Files failed: {error_count}")
                if skipped_count > 0:
                    print(f"   ⏭️  Files skipped: {skipped_count}")
                print(f"   📄 Document chunks: {processed_results.get('total_chunks', 0)}")
                print(f"   🏷️  Collection: {collection_name}")
            
            return True
            
        except Exception as e:
            if self.console:
                self.console.print(f"❌ Error indexing folder: {str(e)}", style="red")
            else:
                print(f"❌ Error indexing folder: {str(e)}")
            return False
    
    def _get_all_files_recursive(self, folder_id, folder_path=""):
        """Get all files recursively from a folder"""
        all_files = []
        
        def get_files_from_folder(current_folder_id, current_path=""):
            try:
                # Get all items in the current folder
                response = safe_drive_call(lambda: self.drive_service.files().list(
                    q=f"'{current_folder_id}' in parents and trashed=false",
                    supportsAllDrives=True,
                    includeItemsFromAllDrives=True,
                    fields="files(id, name, mimeType, size, modifiedTime, webViewLink)",
                    pageSize=1000
                ).execute())
                
                items = response.get('files', [])
                
                for item in items:
                    item_name = item.get('name', 'Untitled')
                    item_path = f"{current_path}/{item_name}" if current_path else item_name
                    
                    if item.get('mimeType') == 'application/vnd.google-apps.folder':
                        # Recursively get files from subfolder
                        get_files_from_folder(item['id'], item_path)
                    else:
                        # Add file info
                        file_info = {
                            'id': item['id'],
                            'name': item_name,
                            'mimeType': item.get('mimeType', ''),
                            'size': int(item.get('size', 0)) if item.get('size') else 0,
                            'modifiedTime': item.get('modifiedTime', ''),
                            'webViewLink': item.get('webViewLink', ''),
                            'path': item_path
                        }
                        all_files.append(file_info)
                        
            except Exception as e:
                print(f"⚠️  Error processing folder {current_folder_id}: {e}")
        
        get_files_from_folder(folder_id, folder_path)
        return all_files
    
    def _update_registry(self, folder_id, folder_info):
        """Update indexed_folders.json registry"""
        registry_file = 'indexed_folders.json'
        
        # Load existing registry
        if os.path.exists(registry_file):
            try:
                with open(registry_file, 'r', encoding='utf-8') as f:
                    registry = json.load(f)
            except:
                registry = {}
        else:
            registry = {}
        
        # Update registry
        registry[folder_id] = folder_info
        
        # Save registry
        try:
            with open(registry_file, 'w', encoding='utf-8') as f:
                json.dump(registry, f, indent=2, ensure_ascii=False)
            
            if self.console:
                self.console.print("📝 Updated indexed folders registry", style="green")
            else:
                print("📝 Updated indexed folders registry")
        except Exception as e:
            if self.console:
                self.console.print(f"❌ Error updating registry: {e}", style="red")
            else:
                print(f"❌ Error updating registry: {e}")

    def _download_and_extract_content(self, file_id, file_name, mime_type, loader):
        """Download and extract content from a Google Drive file"""
        import io
        from googleapiclient.http import MediaIoBaseDownload
        
        try:
            # Handle Google Workspace files that need export
            if mime_type == 'application/vnd.google-apps.document':
                # Google Docs - export as text
                return loader.export_google_doc(file_id)
            elif mime_type == 'application/vnd.google-apps.spreadsheet':
                # Google Sheets - export as CSV
                return loader.export_google_sheets(file_id)
            elif mime_type == 'application/vnd.google-apps.presentation':
                # Google Slides - export as text
                return loader.export_google_slides(file_id)
            else:
                # Regular files - download and extract text
                file_content = loader.download_file(file_id)
                if file_content:
                    return extract_text(file_content, mime_type, file_name, loader.ocr_service)
                else:
                    return None
        except Exception as e:
            if self.console:
                self.console.print(f"  Error downloading {file_name}: {e}", style="yellow")
            else:
                print(f"  Error downloading {file_name}: {e}")
            return None

    def _process_files_batch(self, all_files, folder_name, loader, vector_store):
        """Process files in optimized batches for better performance"""
        # Constants for batching
        BATCH_SIZE = 50  # Process 50 files at once
        EMBEDDING_BATCH_SIZE = 100  # Generate embeddings for up to 100 chunks at once
        
        success_count = 0
        error_count = 0
        skipped_count = 0
        
        # Prepare all chunks from all files first
        all_chunks = []
        all_metadatas = []
        all_ids = []
        file_results = {}  # Track which files were processed
        
        if RICH_AVAILABLE and self.console:
            with Progress(console=self.console) as progress:
                download_task = progress.add_task(f"Downloading files from {folder_name}...", total=len(all_files))
                
                # Phase 1: Download and extract content from all files
                for i, file_info in enumerate(all_files):
                    file_id = file_info['id']
                    file_name = file_info.get('name', 'Untitled')
                    mime_type = file_info.get('mimeType', '')
                    
                    try:
                        # Skip certain file types
                        skip_types = [
                            'application/vnd.google-apps.shortcut',
                            'application/vnd.google-apps.folder'
                        ]
                        
                        if mime_type in skip_types:
                            file_results[file_id] = 'skipped'
                            skipped_count += 1
                            progress.update(download_task, advance=1)
                            continue
                        
                        # Download and extract content
                        content = self._download_and_extract_content(file_id, file_name, mime_type, loader)
                        
                        if not content or len(content.strip()) < 10:
                            file_results[file_id] = 'skipped'
                            skipped_count += 1
                            progress.update(download_task, advance=1)
                            continue
                        
                        # Create base metadata
                        metadata = {
                            'file_id': file_id,
                            'file_name': file_name,
                            'mime_type': mime_type,
                            'path': file_info.get('path', file_name),
                            'size': file_info.get('size', 0),
                            'modified_time': file_info.get('modifiedTime', ''),
                            'web_view_link': file_info.get('webViewLink', '')
                        }
                        
                        # Chunk the content
                        chunks = chunk_text(content)
                        
                        if not chunks:
                            file_results[file_id] = 'skipped'
                            skipped_count += 1
                            progress.update(download_task, advance=1)
                            continue
                        
                        # Add chunks to batch
                        for j, chunk in enumerate(chunks):
                            chunk_metadata = metadata.copy()
                            chunk_metadata['chunk_index'] = j
                            chunk_metadata['total_chunks'] = len(chunks)
                            
                            chunk_id = f"{file_id}_{j}"
                            
                            all_chunks.append(chunk)
                            all_metadatas.append(chunk_metadata)
                            all_ids.append(chunk_id)
                        
                        file_results[file_id] = 'success'
                        success_count += 1
                        
                    except Exception as e:
                        if self.console:
                            self.console.print(f"Error processing {file_name}: {e}", style="yellow")
                        file_results[file_id] = 'error'
                        error_count += 1
                    
                    progress.update(download_task, advance=1)
                
                if all_chunks:
                    # Phase 2: Generate embeddings in batches
                    embedding_task = progress.add_task(f"Generating embeddings...", total=len(all_chunks))
                    
                    all_embeddings = []
                    for i in range(0, len(all_chunks), EMBEDDING_BATCH_SIZE):
                        batch_chunks = all_chunks[i:i + EMBEDDING_BATCH_SIZE]
                        
                        try:
                            batch_embeddings = self.embedder.embed_documents(batch_chunks)
                            if hasattr(batch_embeddings, 'tolist'):
                                batch_embeddings = batch_embeddings.tolist()
                            all_embeddings.extend(batch_embeddings)
                            
                            progress.update(embedding_task, advance=len(batch_chunks))
                        except Exception as e:
                            if self.console:
                                self.console.print(f"Error generating embeddings: {e}", style="red")
                            # Create zero embeddings as fallback
                            embedding_dim = self.embedder.dimension if hasattr(self.embedder, 'dimension') else 768
                            fallback_embeddings = [[0.0] * embedding_dim for _ in batch_chunks]
                            all_embeddings.extend(fallback_embeddings)
                            progress.update(embedding_task, advance=len(batch_chunks))
                    
                    # Phase 3: Add to vector store in batches
                    if len(all_embeddings) == len(all_chunks):
                        store_task = progress.add_task(f"Storing in vector database...", total=len(all_chunks))
                        
                        for i in range(0, len(all_chunks), BATCH_SIZE):
                            batch_docs = all_chunks[i:i + BATCH_SIZE]
                            batch_metas = all_metadatas[i:i + BATCH_SIZE]
                            batch_ids = all_ids[i:i + BATCH_SIZE]
                            batch_embeddings = all_embeddings[i:i + BATCH_SIZE]
                            
                            try:
                                vector_store.add_documents(
                                    documents=batch_docs,
                                    metadatas=batch_metas,
                                    ids=batch_ids,
                                    embeddings=batch_embeddings
                                )
                                progress.update(store_task, advance=len(batch_docs))
                            except Exception as e:
                                if self.console:
                                    self.console.print(f"Error storing batch: {e}", style="red")
                                progress.update(store_task, advance=len(batch_docs))
        else:
            # Non-progress version - simpler but still batched
            print(f"Processing {len(all_files)} files...")
            
            # Download and extract all content
            for i, file_info in enumerate(all_files):
                if (i + 1) % 10 == 0:
                    print(f"Downloaded {i + 1}/{len(all_files)} files...")
                
                file_id = file_info['id']
                file_name = file_info.get('name', 'Untitled')
                mime_type = file_info.get('mimeType', '')
                
                try:
                    # Skip certain file types
                    skip_types = [
                        'application/vnd.google-apps.shortcut',
                        'application/vnd.google-apps.folder'
                    ]
                    
                    if mime_type in skip_types:
                        file_results[file_id] = 'skipped'
                        skipped_count += 1
                        continue
                    
                    content = self._download_and_extract_content(file_id, file_name, mime_type, loader)
                    
                    if not content or len(content.strip()) < 10:
                        file_results[file_id] = 'skipped'
                        skipped_count += 1
                        continue
                    
                    metadata = {
                        'file_id': file_id,
                        'file_name': file_name,
                        'mime_type': mime_type,
                        'path': file_info.get('path', file_name),
                        'size': file_info.get('size', 0),
                        'modified_time': file_info.get('modifiedTime', ''),
                        'web_view_link': file_info.get('webViewLink', '')
                    }
                    
                    chunks = chunk_text(content)
                    
                    if not chunks:
                        file_results[file_id] = 'skipped'
                        skipped_count += 1
                        continue
                    
                    for j, chunk in enumerate(chunks):
                        chunk_metadata = metadata.copy()
                        chunk_metadata['chunk_index'] = j
                        chunk_metadata['total_chunks'] = len(chunks)
                        
                        chunk_id = f"{file_id}_{j}"
                        
                        all_chunks.append(chunk)
                        all_metadatas.append(chunk_metadata)
                        all_ids.append(chunk_id)
                    
                    file_results[file_id] = 'success'
                    success_count += 1
                    
                except Exception as e:
                    print(f"Error processing {file_name}: {e}")
                    file_results[file_id] = 'error'
                    error_count += 1
            
            if all_chunks:
                print(f"Generating embeddings for {len(all_chunks)} chunks...")
                
                # Generate embeddings in batches
                all_embeddings = []
                for i in range(0, len(all_chunks), EMBEDDING_BATCH_SIZE):
                    batch_chunks = all_chunks[i:i + EMBEDDING_BATCH_SIZE]
                    print(f"  Embedding batch {i//EMBEDDING_BATCH_SIZE + 1}/{(len(all_chunks) + EMBEDDING_BATCH_SIZE - 1)//EMBEDDING_BATCH_SIZE}...")
                    
                    try:
                        batch_embeddings = self.embedder.embed_documents(batch_chunks)
                        if hasattr(batch_embeddings, 'tolist'):
                            batch_embeddings = batch_embeddings.tolist()
                        all_embeddings.extend(batch_embeddings)
                    except Exception as e:
                        print(f"Error generating embeddings: {e}")
                        embedding_dim = self.embedder.dimension if hasattr(self.embedder, 'dimension') else 768
                        fallback_embeddings = [[0.0] * embedding_dim for _ in batch_chunks]
                        all_embeddings.extend(fallback_embeddings)
                
                print(f"Storing {len(all_chunks)} chunks in vector database...")
                
                # Store in vector database in batches
                for i in range(0, len(all_chunks), BATCH_SIZE):
                    batch_docs = all_chunks[i:i + BATCH_SIZE]
                    batch_metas = all_metadatas[i:i + BATCH_SIZE]
                    batch_ids = all_ids[i:i + BATCH_SIZE]
                    batch_embeddings = all_embeddings[i:i + BATCH_SIZE]
                    
                    print(f"  Storing batch {i//BATCH_SIZE + 1}/{(len(all_chunks) + BATCH_SIZE - 1)//BATCH_SIZE}...")
                    
                    try:
                        vector_store.add_documents(
                            documents=batch_docs,
                            metadatas=batch_metas,
                            ids=batch_ids,
                            embeddings=batch_embeddings
                        )
                    except Exception as e:
                        print(f"Error storing batch: {e}")
        
        return {
            'success_count': success_count,
            'error_count': error_count,
            'skipped_count': skipped_count,
            'total_chunks': len(all_chunks)
        }

def main():
    parser = argparse.ArgumentParser(description='Console Google Drive Indexer - Fixed Version')
    parser.add_argument('--list-folders', action='store_true', help='List all available folders')
    parser.add_argument('--index-folder', type=str, help='Index a specific folder by ID')
    parser.add_argument('--force', action='store_true', help='Force reindex even if collection exists')
    
    args = parser.parse_args()
    
    # Create and initialize indexer
    indexer = FixedConsoleIndexer()
    
    if not indexer.initialize():
        sys.exit(1)
    
    if args.list_folders:
        indexer.list_folders()
    elif args.index_folder:
        success = indexer.index_folder(args.index_folder, force=args.force)
        if not success:
            sys.exit(1)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
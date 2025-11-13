# chat_api.py - Flask API for the React chat app
from flask import Flask, request, jsonify
from flask_cors import CORS
import json
import traceback
import os
import sys
import argparse

# Add the parent directory to the path to import our RAG system
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from rag_system import EnhancedRAGSystem
from auth import authenticate_google_drive
import re

app = Flask(__name__)
CORS(app)  # Enable CORS for React app

# Global variables to hold the RAG system
rag_system = None
drive_service = None
available_collections = {}

def initialize_rag_system():
    """Initialize the RAG system and load available collections"""
    global rag_system, drive_service, available_collections
    
    try:
        # Authenticate Google Drive
        drive_service = authenticate_google_drive()
        print("[+] Google Drive authenticated")
        
        # Load available collections from indexed_folders.json
        indexed_folders_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'indexed_folders.json')
        print(f"Looking for indexed folders at: {indexed_folders_file}")
        
        if os.path.exists(indexed_folders_file):
            with open(indexed_folders_file, 'r') as f:
                indexed_folders = json.load(f)
            
            for folder_id, folder_info in indexed_folders.items():
                collection_name = folder_info['collection_name']
                available_collections[collection_name] = {
                    'name': folder_info['name'],
                    'location': folder_info.get('location', ''),
                    'files_processed': folder_info.get('files_processed', 0),
                    'indexed_at': folder_info.get('indexed_at', '')
                }
        else:
            print(f"⚠️  indexed_folders.json not found at {indexed_folders_file}")
            print("⚠️  Make sure to run the folder indexer first")
        
        print(f"[+] Found {len(available_collections)} available collections")
        
        # Initialize with the first available collection or default
        if available_collections:
            first_collection = next(iter(available_collections.keys()))
            rag_system = EnhancedRAGSystem(drive_service, first_collection)
            print(f"[+] RAG system initialized with collection: {first_collection}")
        else:
            rag_system = EnhancedRAGSystem(drive_service, 'default_collection')
            print("[+] RAG system initialized with default collection")
            
    except Exception as e:
        print(f"[!] Error initializing RAG system: {e}")
        traceback.print_exc()

def extract_document_links(response_text):
    """Extract document links and metadata from response text"""
    documents = []
    
    # Pattern to match markdown links: [filename](url)
    link_pattern = r'\[([^\]]+)\]\((https?://[^\)]+)\)'
    matches = re.findall(link_pattern, response_text)
    
    for filename, url in matches:
        # Extract file type from filename
        file_ext = filename.split('.')[-1].lower() if '.' in filename else ''
        file_type = {
            'pdf': 'PDF Document',
            'docx': 'Word Document', 
            'doc': 'Word Document',
            'xlsx': 'Excel Spreadsheet',
            'xls': 'Excel Spreadsheet',
            'pptx': 'PowerPoint Presentation',
            'ppt': 'PowerPoint Presentation',
            'txt': 'Text File',
            'png': 'Image',
            'jpg': 'Image', 
            'jpeg': 'Image',
            'gif': 'Image'
        }.get(file_ext, 'Document')
        
        documents.append({
            'filename': filename,
            'url': url,
            'type': file_type,
            'extension': file_ext
        })
    
    return documents

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'rag_initialized': rag_system is not None,
        'collections_available': len(available_collections)
    })

@app.route('/collections', methods=['GET'])
def get_collections():
    """Get available collections"""
    return jsonify({
        'collections': available_collections
    })

@app.route('/chat', methods=['POST'])
def chat():
    """Handle chat messages"""
    global rag_system
    
    try:
        data = request.get_json()
        
        if not data or 'message' not in data:
            return jsonify({'error': 'Message is required'}), 400
        
        message = data['message']
        collection = data.get('collection')
        
        if not rag_system:
            return jsonify({'error': 'RAG system not initialized'}), 500
        
        # Switch collection if requested
        if collection and collection != rag_system.collection_name:
            if collection in available_collections:
                rag_system = EnhancedRAGSystem(drive_service, collection)
                print(f"Switched to collection: {collection}")
            else:
                return jsonify({'error': f'Collection {collection} not found'}), 400
        
        # Query the RAG system
        print(f"Processing query: {message}")
        response = rag_system.query(message)
        
        # Extract answer and documents
        answer = response.get('answer', 'No response generated')
        documents = extract_document_links(answer)
        
        # Get additional context info
        contexts = response.get('contexts', [])
        files_used = response.get('files', [])
        
        return jsonify({
            'answer': answer,
            'documents': documents,
            'contexts': contexts,
            'files_used': files_used,
            'collection_used': rag_system.collection_name,
            'query_type': response.get('query_type', 'agent')
        })
        
    except Exception as e:
        print(f"[!] Error processing chat message: {e}")
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@app.route('/switch-collection', methods=['POST'])
def switch_collection():
    """Switch to a different collection"""
    global rag_system
    
    try:
        data = request.get_json()
        collection = data.get('collection')
        
        if not collection:
            return jsonify({'error': 'Collection name is required'}), 400
        
        if collection not in available_collections:
            return jsonify({'error': f'Collection {collection} not found'}), 400
        
        # Initialize new RAG system with the requested collection
        rag_system = EnhancedRAGSystem(drive_service, collection)
        
        return jsonify({
            'success': True,
            'collection': collection,
            'info': available_collections[collection]
        })
        
    except Exception as e:
        print(f"[!] Error switching collection: {e}")
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@app.route('/folders', methods=['GET'])
def get_folders():
    """Get root folders from Google Drive (lazy loading)"""
    try:
        parent_id = request.args.get('parent_id', '')
        folder_type = request.args.get('type', 'folders')  # 'folders', 'files', or 'both'
        
        print(f"[F] Loading folder contents for parent_id: {parent_id}")
        
        # If no parent_id is specified, return the known 7MM Resources root folders
        if not parent_id or parent_id == '':
            # Return the known indexed folders as root folders
            indexed_folders_data = {}
            try:
                with open('indexed_folders.json', 'r') as f:
                    indexed_folders_data = json.load(f)
            except:
                pass
            
            formatted_items = []
            for folder_id, folder_info in indexed_folders_data.items():
                formatted_item = {
                    'id': folder_id,
                    'name': folder_info['name'],
                    'type': 'folder',
                    'mimeType': 'application/vnd.google-apps.folder',
                    'webViewLink': f'https://drive.google.com/drive/folders/{folder_id}',
                    'modifiedTime': folder_info['indexed_at'],
                    'size': 0,
                    'hasChildren': True,  # These folders definitely have children
                    'parent_id': 'root'
                }
                formatted_items.append(formatted_item)
            
            # Sort alphabetically
            formatted_items.sort(key=lambda x: x['name'].lower())
            
            print(f"[+] Found {len(formatted_items)} root folders from indexed_folders.json")
            
            return jsonify({
                'items': formatted_items,
                'parent_id': 'root',
                'total_count': len(formatted_items)
            })
        
        # For specific folder requests, use Google Drive API
        # Build the query based on what we want to fetch
        if folder_type == 'folders':
            query = f"'{parent_id}' in parents and mimeType='application/vnd.google-apps.folder' and trashed=false"
        elif folder_type == 'files':
            query = f"'{parent_id}' in parents and mimeType!='application/vnd.google-apps.folder' and trashed=false"
        else:  # both
            query = f"'{parent_id}' in parents and trashed=false"
        
        # Use Google Drive API to fetch folders/files
        results = drive_service.files().list(
            q=query,
            pageSize=100,  # Limit to prevent overwhelming
            fields="nextPageToken, files(id, name, mimeType, size, modifiedTime, webViewLink, parents)"
        ).execute()
        
        items = results.get('files', [])
        
        # Format the response
        formatted_items = []
        for item in items:
            is_folder = item['mimeType'] == 'application/vnd.google-apps.folder'
            
            formatted_item = {
                'id': item['id'],
                'name': item['name'],
                'type': 'folder' if is_folder else 'file',
                'mimeType': item['mimeType'],
                'webViewLink': item.get('webViewLink', ''),
                'modifiedTime': item.get('modifiedTime', ''),
                'size': item.get('size', 0) if not is_folder else 0,
                'hasChildren': is_folder,  # Assume folders have children for lazy loading
                'parent_id': parent_id
            }
            formatted_items.append(formatted_item)
        
        # Sort: folders first, then files, both alphabetically
        formatted_items.sort(key=lambda x: (x['type'] == 'file', x['name'].lower()))
        
        print(f"[+] Found {len(formatted_items)} items in folder {parent_id}")
        
        return jsonify({
            'items': formatted_items,
            'parent_id': parent_id,
            'total_count': len(formatted_items)
        })
        
    except Exception as e:
        print(f"[!] Error loading folders: {e}")
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@app.route('/folders/search', methods=['GET'])
def search_folders():
    """Search for folders/files by name (for quick navigation)"""
    try:
        search_term = request.args.get('q', '').strip()
        search_type = request.args.get('type', 'both')  # 'folders', 'files', or 'both'
        
        if not search_term or len(search_term) < 2:
            return jsonify({'error': 'Search term must be at least 2 characters'}), 400
        
        print(f"[?] Searching for: {search_term}")
        
        # Build search query
        if search_type == 'folders':
            query = f"name contains '{search_term}' and mimeType='application/vnd.google-apps.folder' and trashed=false"
        elif search_type == 'files':
            query = f"name contains '{search_term}' and mimeType!='application/vnd.google-apps.folder' and trashed=false"
        else:  # both
            query = f"name contains '{search_term}' and trashed=false"
        
        results = drive_service.files().list(
            q=query,
            pageSize=50,  # Limit search results
            fields="files(id, name, mimeType, webViewLink, parents)"
        ).execute()
        
        items = results.get('files', [])
        
        # Format search results
        formatted_items = []
        for item in items:
            is_folder = item['mimeType'] == 'application/vnd.google-apps.folder'
            
            formatted_item = {
                'id': item['id'],
                'name': item['name'],
                'type': 'folder' if is_folder else 'file',
                'mimeType': item['mimeType'],
                'webViewLink': item.get('webViewLink', ''),
                'parents': item.get('parents', [])
            }
            formatted_items.append(formatted_item)
        
        print(f"[+] Found {len(formatted_items)} search results")
        
        return jsonify({
            'items': formatted_items,
            'search_term': search_term,
            'total_count': len(formatted_items)
        })
        
    except Exception as e:
        print(f"[!] Error searching folders: {e}")
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

def create_app():
    """Application factory for production deployment"""
    initialize_rag_system()
    return app

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='RAG Chat API Server')
    parser.add_argument('--production', action='store_true', help='Run in production mode')
    parser.add_argument('--port', type=int, default=5000, help='Port to run on')
    parser.add_argument('--host', default='0.0.0.0', help='Host to bind to')
    args = parser.parse_args()
    
    print("[*] Starting RAG Chat API Server...")
    print("="*50)
    
    # Initialize the RAG system
    initialize_rag_system()
    
    print("="*50)
    if args.production:
        print(f"[>] Production server starting on {args.host}:{args.port}")
        print("[!] Debug mode: OFF")
    else:
        print(f"[>] Development server starting on http://localhost:{args.port}")
        print("[D] Debug mode: ON")
    
    print("[?] Available endpoints:")
    print("  GET  /health - Health check")
    print("  GET  /collections - List available collections") 
    print("  POST /chat - Send chat messages")
    print("  POST /switch-collection - Switch collections")
    print("  GET  /folders - Lazy-load folders (parent_id, type params)")
    print("  GET  /folders/search - Search folders/files (q, type params)")
    print("="*50)
    
    # Run the Flask app
    app.run(
        debug=not args.production,
        host=args.host,
        port=args.port,
        use_reloader=not args.production
    )
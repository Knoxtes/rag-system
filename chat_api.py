# chat_api.py - Flask API for the React chat app
from flask import Flask, request, jsonify, session
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
import json
import traceback
import os
import sys
import argparse
import time
from threading import Thread, Lock
from datetime import datetime, timedelta
import gzip
import base64
import logging
from logging.handlers import RotatingFileHandler

# Load environment variables first
from dotenv import load_dotenv
load_dotenv()

# Add the parent directory to the path to import our RAG system
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from rag_system import EnhancedRAGSystem, MultiCollectionRAGSystem
from auth import authenticate_google_drive
from oauth_config import require_auth, oauth_config
from auth_routes import auth_bp
from config import SCOPES, CREDENTIALS_FILE, TOKEN_FILE, USE_VERTEX_AI
import re

app = Flask(__name__)

# Production Configuration
app.config['SECRET_KEY'] = os.getenv('FLASK_SECRET_KEY', oauth_config.secret_key)
app.config['SESSION_COOKIE_SECURE'] = os.getenv('FLASK_ENV') == 'production'
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
app.config['SESSION_PERMANENT'] = True
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=24)

# CORS Configuration
cors_origins = os.getenv('CORS_ORIGINS', 'http://localhost:3000').split(',')
CORS(app, origins=cors_origins, supports_credentials=True)

# Rate Limiting
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"]
)
limiter.init_app(app)

# Register authentication blueprint
app.register_blueprint(auth_bp)

# Register Google Drive OAuth blueprint
try:
    from google_drive_oauth import gdrive_oauth_bp
    app.register_blueprint(gdrive_oauth_bp)
except ImportError as e:
    print(f"Warning: Could not load Google Drive OAuth routes: {e}")

# Register admin blueprint
try:
    from admin_routes import admin_bp
    app.register_blueprint(admin_bp)
except ImportError as e:
    print(f"Warning: Could not load admin routes: {e}")

# Health monitoring integrated into main app
# Production Logging
if not app.debug:
    file_handler = RotatingFileHandler('logs/rag_system.log', maxBytes=10240000, backupCount=10)
    file_handler.setFormatter(logging.Formatter(
        '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
    ))
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.setLevel(logging.INFO)
    app.logger.info('RAG System startup')

def analyze_file_with_workspace(file_id: str, user_question: str):
    """
    Analyze a specific Google Drive file using workspace/direct document analysis
    instead of the RAG system for more targeted responses.
    """
    global drive_service
    
    if not drive_service:
        return None
        
    try:
        # Get file metadata from Google Drive
        file_metadata = drive_service.files().get(fileId=file_id).execute()
        file_name = file_metadata.get('name', 'Unknown File')
        mime_type = file_metadata.get('mimeType', '')
        
        print(f"  📋 Analyzing file: {file_name} (type: {mime_type})")
        
        # Download and process the file content
        file_content = download_and_process_file(file_id, file_name, mime_type)
        if not file_content:
            return None
            
        # Use Gemini to analyze the document directly
        workspace_response = query_document_with_gemini(file_content, file_name, user_question)
        
        return {
            'answer': workspace_response,
            'documents': [{
                'filename': file_name,
                'type': 'Direct Analysis',
                'url': f"https://drive.google.com/file/d/{file_id}/view",
                'extension': file_name.split('.')[-1] if '.' in file_name else '',
                'collection': 'workspace_analysis',
                'score': 1.0
            }]
        }
        
    except Exception as e:
        print(f"  ❌ Error in workspace analysis: {e}")
        return None

def download_and_process_file(file_id: str, file_name: str, mime_type: str):
    """Download and extract text content from a Google Drive file"""
    global drive_service
    
    try:
        # Handle different file types
        if mime_type == 'text/csv':
            # Download CSV directly
            request = drive_service.files().get_media(fileId=file_id)
            content = request.execute().decode('utf-8')
            return f"CSV File: {file_name}\n\n{content}"
            
        elif mime_type == 'application/vnd.google-apps.spreadsheet':
            # Export Google Sheets as CSV
            request = drive_service.files().export_media(fileId=file_id, mimeType='text/csv')
            content = request.execute().decode('utf-8')
            return f"Spreadsheet: {file_name}\n\n{content}"
            
        elif mime_type == 'application/vnd.google-apps.document':
            # Export Google Docs as plain text
            request = drive_service.files().export_media(fileId=file_id, mimeType='text/plain')
            content = request.execute().decode('utf-8')
            return f"Document: {file_name}\n\n{content}"
            
        elif mime_type in ['text/plain']:
            # Download text files
            request = drive_service.files().get_media(fileId=file_id)
            content = request.execute().decode('utf-8')
            return f"Text File: {file_name}\n\n{content}"
            
        elif 'application/pdf' in mime_type:
            print(f"  ⚠️ PDF files require special processing - not yet supported for workspace analysis")
            return None
            
        else:
            print(f"  ⚠️ Unsupported file type: {mime_type}")
            print(f"    Supported types: CSV, Google Sheets, Google Docs, Text files")
            return None
            
    except Exception as e:
        print(f"  ❌ Error downloading file: {e}")
        return None

def query_document_with_gemini(document_content: str, file_name: str, user_question: str):
    """Use Gemini to analyze the document content directly"""
    try:
        import google.generativeai as genai
        from config import USE_VERTEX_AI
        
        # Prepare the prompt for document analysis
        analysis_prompt = f"""You are analyzing a specific document for a user. Here is the document content:

=== DOCUMENT: {file_name} ===
{document_content[:15000]}  # Limit content to avoid token limits
=== END DOCUMENT ===

User Question: {user_question}

Please provide a comprehensive answer based ONLY on the content of this specific document. If the information to answer the question is not in this document, please say so clearly. Be specific and cite relevant parts of the document in your response.

Focus on:
1. Direct answers from the document content
2. Specific data, numbers, or details from the document
3. Clear references to sections or data points
4. If the question cannot be answered from this document, explain why

Answer:"""

        if USE_VERTEX_AI:
            # Use Vertex AI
            import vertexai
            from vertexai.generative_models import GenerativeModel
            
            model = GenerativeModel("gemini-1.5-pro")
            response = model.generate_content(analysis_prompt)
            return response.text
        else:
            # Use regular Gemini API
            model = genai.GenerativeModel('gemini-1.5-pro')
            response = model.generate_content(analysis_prompt)
            return response.text
            
    except Exception as e:
        print(f"  ❌ Error in Gemini analysis: {e}")
        return f"I was able to access the document '{file_name}' but encountered an error during analysis: {str(e)}. You can try asking a different question or use the regular chat mode."

# Global variables to hold the RAG system
rag_system = None
multi_collection_rag = None
drive_service = None
available_collections = {}

# Initialization guard to prevent double initialization
_rag_initialized = False

# Folder cache for better performance
folder_cache = {}
cache_lock = Lock()
CACHE_EXPIRY_HOURS = 6  # Cache expires after 6 hours (longer cache)
SHARED_DRIVE_ID = '0AMjLFg-ngmOAUk9PVA'

# Memory cache for frequently accessed items
memory_cache = {}
FREQUENT_ACCESS_THRESHOLD = 3  # Cache items accessed 3+ times in memory

def safe_drive_request(request_func, max_retries=3, base_delay=1):
    """
    Safely execute a Google Drive API request with retry logic for SSL errors
    
    Args:
        request_func: Function that returns a Google API request object
        max_retries: Maximum number of retry attempts
        base_delay: Base delay between retries (exponential backoff)
    
    Returns:
        API response or None if all retries fail
    """
    import ssl
    import socket
    from googleapiclient.errors import HttpError
    
    for attempt in range(max_retries + 1):
        try:
            return request_func().execute()
        except (ssl.SSLError, socket.error, ConnectionError) as e:
            if attempt < max_retries:
                delay = base_delay * (2 ** attempt)  # Exponential backoff
                    # print(f"SSL/Network error on attempt {attempt + 1}: {str(e)}. Retrying in {delay}s...")  # Disabled for production
                time.sleep(min(delay, 0.5))  # Reduce delay for faster retries
                continue
            else:
                    # print(f"SSL/Network error after {max_retries + 1} attempts: {str(e)}")  # Disabled for production
                return None
        except HttpError as e:
                # print(f"Google API HTTP error: {str(e)}")  # Disabled for production
            return None
        except Exception as e:
                # print(f"Unexpected error: {str(e)}")  # Disabled for production
            return None
    
    return None

def compress_response(data):
    """Compress large responses for faster transfer"""
    try:
        if len(str(data)) > 1000:  # Only compress large responses
            json_str = json.dumps(data)
            compressed = gzip.compress(json_str.encode('utf-8'))
            return {
                'compressed': True,
                'data': base64.b64encode(compressed).decode('utf-8')
            }
        return {'compressed': False, 'data': data}
    except Exception as e:
            # print(f"Compression error: {e}")  # Disabled for production
        return {'compressed': False, 'data': data}

def get_cache_key(parent_id, query=None):
    """Generate cache key for folder requests"""
    if query:
        return f"search:{query}:{parent_id}"
    return f"folder:{parent_id}"
    """Generate cache key for folder requests"""
    if query:
        return f"search:{query}:{parent_id}"
    return f"folder:{parent_id}"

def is_cache_expired(cache_entry):
    """Check if cache entry has expired"""
    if not cache_entry or 'timestamp' not in cache_entry:
        return True
    
    expiry_time = cache_entry['timestamp'] + timedelta(hours=CACHE_EXPIRY_HOURS)
    return datetime.now() > expiry_time

def update_cache(cache_key, data):
    """Update cache with new data"""
    with cache_lock:
        folder_cache[cache_key] = {
            'data': data,
            'timestamp': datetime.now()
        }

def get_cached_data(cache_key):
    """Get data from cache if not expired, with memory cache priority"""
    # Check memory cache first (fastest)
    if cache_key in memory_cache:
        memory_cache[cache_key]['access_count'] += 1
        return memory_cache[cache_key]['data']
    
    # Check disk cache
    with cache_lock:
        if cache_key in folder_cache and not is_cache_expired(folder_cache[cache_key]):
            data = folder_cache[cache_key]['data']
            # Promote to memory cache if accessed frequently
            if cache_key not in memory_cache:
                memory_cache[cache_key] = {
                    'data': data,
                    'access_count': 1,
                    'timestamp': datetime.now()
                }
            return data
    return None

def preload_folder_structure():
    """
    Enhanced preload with deeper folder structure caching
    """
    # print("Starting enhanced folder structure preload...")  # Disabled for production
    
    try:
        # Step 1: Start with root folders
        cache_key = get_cache_key(SHARED_DRIVE_ID)
        
        # Load root folders
        def make_request():
            return drive_service.files().list(
                q=f"'{SHARED_DRIVE_ID}' in parents and mimeType='application/vnd.google-apps.folder' and trashed=false",
                driveId=SHARED_DRIVE_ID,
                corpora='drive',
                supportsAllDrives=True,
                includeItemsFromAllDrives=True,
                fields="files(id, name, mimeType, webViewLink)",
                pageSize=100
            )
        
        response = safe_drive_request(make_request)
        if response and 'files' in response:
            root_files = response['files']
            update_cache(cache_key, root_files)
            # print(f"Preloaded {len(root_files)} root folders")  # Disabled for production
            
            # Step 2: Preload first level of top 8 folders (most likely to be accessed)
            priority_folders = root_files[:8]  # Reduced from 10 to avoid overwhelming API
            for i, folder in enumerate(priority_folders):
                try:
                    subfolder_cache_key = get_cache_key(folder['id'])
                    
                    # Skip if already cached
                    if not is_cache_expired(folder_cache.get(subfolder_cache_key, {})):
                        continue
                    
                    def make_subfolder_request():
                        return drive_service.files().list(
                            q=f"'{folder['id']}' in parents and trashed=false",
                            pageSize=25,  # Smaller page size for subfolders
                            fields="files(id, name, mimeType, webViewLink)",
                            supportsAllDrives=True,
                            includeItemsFromAllDrives=True
                        )
                    
                    subfolder_response = safe_drive_request(make_subfolder_request)
                    if subfolder_response and 'files' in subfolder_response:
                        subitems = subfolder_response['files']
                        update_cache(subfolder_cache_key, subitems)
                        # print(f"  → Preloaded {len(subitems)} items in '{folder['name'][:25]}...'")  # Disabled for production
                        
                    # Small delay to be respectful to API rate limits
                    time.sleep(0.01)  # Minimize delay for API friendliness
                    
                except Exception as subfolder_error:
                    # print(f"  → Failed to preload '{folder['name']}': {subfolder_error}")  # Disabled for production
                    continue
        
    except Exception as e:
        # print(f"Error in enhanced preload: {str(e)}")  # Disabled for production
        pass

def start_background_cache_refresh():
    """Start background thread for cache refresh with simplified approach"""
    def refresh_loop():
        while True:
            try:
                if drive_service:
                    preload_folder_structure()
                    
                    # Simple memory cache cleanup
                    current_time = datetime.now()
                    keys_to_remove = []
                    for key, entry in memory_cache.items():
                        age_hours = (current_time - entry['timestamp']).total_seconds() / 3600
                        if age_hours > 2 and entry['access_count'] < FREQUENT_ACCESS_THRESHOLD:
                            keys_to_remove.append(key)
                    
                    for key in keys_to_remove:
                        del memory_cache[key]
                    
                    # print(f"Cache refresh completed. Memory cache: {len(memory_cache)} items")  # Disabled for production
                
                time.sleep(3600)  # Refresh every hour (back to stable interval)
            except Exception as e:
                # print(f"Error in cache refresh: {str(e)}")  # Disabled for production
                time.sleep(600)  # Wait 10 minutes before retry on error
    
    refresh_thread = Thread(target=refresh_loop, daemon=True)
    refresh_thread.start()
    # print("Background cache refresh started")  # Disabled for production

def initialize_rag_system():
    """Initialize the RAG system and load available collections"""
    global rag_system, multi_collection_rag, drive_service, available_collections, _rag_initialized
    
    # Prevent double initialization
    if _rag_initialized:
        print("[!] RAG system already initialized, skipping...")
        return
    
    _rag_initialized = True
    
    try:
        # print("[+] Initializing Google Drive authentication...")  # Disabled for production
        try:
            # Use non-interactive mode during server startup
            drive_service = authenticate_google_drive(interactive=False)
            if drive_service:
                # print("✅ Google Drive authentication successful!")  # Disabled for production
                pass
            else:
                # print("⚠️  Google Drive credentials not found - run 'python auth.py' to set up")  # Disabled for production
                drive_service = None
        except Exception as drive_error:
            # print(f"❌ Google Drive authentication failed: {drive_error}")  # Disabled for production
            # print("    Please run: python auth.py to set up Google Drive credentials")  # Disabled for production
            # print("    Continuing without Google Drive (folders will be unavailable)")  # Disabled for production
            drive_service = None
        
        # Load available collections from indexed_folders.json (if exists)
        indexed_folders_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'indexed_folders.json')
        # print(f"Looking for indexed folders at: {indexed_folders_file}")  # Disabled for production
        
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
            # print(f"⚠️  indexed_folders.json not found at {indexed_folders_file}")  # Disabled for production
            # print("⚠️  Collections will be empty until Google Drive is set up")  # Disabled for production
            pass
        
        # print(f"[+] Found {len(available_collections)} available collections")  # Disabled for production
        
        # Initialize RAG systems for the available collections
        if available_collections:
            try:
                # print("[+] Initializing RAG systems...")  # Disabled for production
                pass
                
                # Initialize individual collection RAG systems
                for collection_name in available_collections:
                    if collection_name != "ALL_COLLECTIONS":
                        try:
                            temp_rag = EnhancedRAGSystem(
                                drive_service=drive_service, 
                                collection_name=collection_name
                            )
                            # print(f"    ✓ Initialized RAG for collection: {collection_name}")  # Disabled for production
                            # Use the first available collection as default if rag_system is None
                            if rag_system is None:
                                rag_system = temp_rag
                        except Exception as e:
                            # print(f"    ⚠️  Failed to initialize RAG for {collection_name}: {e}")  # Disabled for production
                            pass
                
                # Initialize multi-collection RAG if multiple collections available
                collection_names = [k for k in available_collections.keys() if k != "ALL_COLLECTIONS"]
                if len(collection_names) > 1:
                    try:
                        # Pass the collection dict, not just the names
                        collections_dict = {k: v for k, v in available_collections.items() if k != "ALL_COLLECTIONS"}
                        multi_collection_rag = MultiCollectionRAGSystem(
                            drive_service=drive_service,
                            available_collections=collections_dict
                        )
                        # print(f"    ✓ Initialized multi-collection RAG for {len(collection_names)} collections")  # Disabled for production
                    except Exception as e:
                        # print(f"    ⚠️  Failed to initialize multi-collection RAG: {e}")  # Disabled for production
                        import traceback
                        traceback.print_exc()
                        
                # print("✅ RAG system initialization completed")  # Disabled for production
            except Exception as e:
                # print(f"❌ Error during RAG initialization: {e}")  # Disabled for production
                pass
        
        # Add special "ALL_COLLECTIONS" entry
        if len(available_collections) > 1:
            available_collections["ALL_COLLECTIONS"] = {
                'name': f"All Collections Combined ({len(available_collections)} folders)",
                'location': '7MM Resources',
                'files_processed': sum(info['files_processed'] for info in available_collections.values()),
                'indexed_at': 'Combined',
                'is_combined': True
            }
            # print(f"[+] Added combined collection mode with {available_collections['ALL_COLLECTIONS']['files_processed']} total documents")  # Disabled for production
        
        if rag_system is not None:
            pass  # print("✅ RAG system fully initialized and ready for chat")
        else:
            pass  # print("⚠️  RAG system not initialized - chat will be unavailable")
        
    except Exception as e:
        # print(f"[!] Error initializing RAG system: {e}")  # Disabled for production
        raise e

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
        'multi_collection_available': multi_collection_rag is not None,
        'collections_available': len(available_collections),
        'auth_required': True,
        'allowed_domains': oauth_config.allowed_domains if oauth_config.allowed_domains else ['all']
    })

@app.route('/collections', methods=['GET'])
@require_auth
def get_collections():
    """Get available collections"""
    try:
        user_email = getattr(request, 'current_user', {}).get('email', 'unknown')
    except RuntimeError:
        # Handle case where we're outside request context
        user_email = 'unknown'
    
    return jsonify({
        'collections': available_collections,
        'user': user_email
    })

@app.route('/chat', methods=['POST'])
@require_auth
@limiter.limit("30 per minute")
def chat():
    """Handle chat messages"""
    global rag_system, multi_collection_rag
    
    try:
        print(f"[DEBUG] Chat endpoint called")
        print(f"[DEBUG] rag_system: {rag_system is not None}")
        print(f"[DEBUG] multi_collection_rag: {multi_collection_rag is not None}")
        
        data = request.get_json()
        print(f"[DEBUG] Request data: {data}")
        
        if not data or 'message' not in data:
            return jsonify({'error': 'Message is required'}), 400
        
        message = data['message']
        collection = data.get('collection')
        file_id = data.get('file_id')  # Extract file_id for targeted queries
        print(f"[DEBUG] Message: {message}, Collection: {collection}, File ID: {file_id}")
        
        # Check if RAG system is initialized
        if not rag_system:
            print(f"[DEBUG] RAG system not initialized, returning 503")
            return jsonify({
                'error': 'RAG system is still initializing. Please wait a moment and try again.',
                'code': 'SYSTEM_INITIALIZING'
            }), 503  # Service Unavailable
        
        # Handle ALL_COLLECTIONS mode
        if collection == "ALL_COLLECTIONS":
            print(f"[DEBUG] ALL_COLLECTIONS requested, multi_collection_rag available: {multi_collection_rag is not None}")
            if not multi_collection_rag:
                print(f"[DEBUG] Multi-collection not available, returning error")
                return jsonify({'error': 'Multi-collection system not available. Please select a specific collection.'}), 400
            
            print(f"🔍 Multi-collection query: {message}")
            if file_id:
                print(f"  📄 Targeted query for specific file: {file_id}")
            response = multi_collection_rag.process_chat(message, file_id=file_id)
            
            # Extract documents/sources from multi-collection response
            documents = []
            for source in response.get('sources', []):
                metadata = source.get('metadata', {})
                file_info = metadata.get('file_info', {})
                
                documents.append({
                    'filename': source.get('title', 'Untitled'),
                    'url': source.get('url', ''),
                    'type': file_info.get('file_type', 'Document'),
                    'extension': '',  # Not used but expected by frontend
                    'collection': source.get('collection', ''),
                    'score': source.get('score', 0)
                })
            
            return jsonify({
                'answer': response.get('answer', 'No response generated'),
                'documents': documents,
                'contexts': response.get('sources', []),
                'collection_used': 'ALL_COLLECTIONS',
                'search_time': response.get('search_time', 0),
                'multi_collection_summary': response.get('multi_collection_summary', {}),
                'error': response.get('error')
            })
        
        # Switch single collection if requested
        if collection and collection != rag_system.collection_name:
            if collection in available_collections and collection != "ALL_COLLECTIONS":
                rag_system = EnhancedRAGSystem(drive_service, collection)
                print(f"Switched to collection: {collection}")
            else:
                return jsonify({'error': f'Collection {collection} not found'}), 400
        
        # Query single collection RAG system
        print(f"Processing query: {message}")
        if file_id:
            print(f"  📄 Targeted query for specific file: {file_id}")
            
            # Use workspace query for specific file analysis
            try:
                workspace_response = analyze_file_with_workspace(file_id, message)
                if workspace_response:
                    print(f"  ✅ Workspace analysis completed for file: {file_id}")
                    return jsonify({
                        'answer': workspace_response['answer'],
                        'documents': workspace_response.get('documents', []),
                        'query_type': 'workspace',
                        'file_analyzed': file_id,
                        'analysis_method': 'direct_workspace_query'
                    })
                else:
                    print(f"  ⚠️ Workspace analysis failed, falling back to RAG")
            except Exception as workspace_error:
                print(f"  ❌ Workspace query error: {workspace_error}")
                print(f"  🔄 Falling back to RAG system")
        
        response = rag_system.query(message, file_id=file_id)
        
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
@require_auth
def switch_collection():
    """Switch to a different collection"""
    global rag_system, multi_collection_rag
    
    try:
        data = request.get_json()
        collection = data.get('collection')
        
        if not collection:
            return jsonify({'error': 'Collection name is required'}), 400
        
        if collection not in available_collections:
            return jsonify({'error': f'Collection {collection} not found'}), 400
        
        # Handle ALL_COLLECTIONS mode
        if collection == "ALL_COLLECTIONS":
            if not multi_collection_rag:
                return jsonify({'error': 'Multi-collection system not available'}), 500
            
            return jsonify({
                'success': True,
                'collection': collection,
                'info': available_collections[collection],
                'mode': 'multi_collection'
            })
        
        # Initialize new single collection RAG system
        rag_system = EnhancedRAGSystem(drive_service, collection)
        
        return jsonify({
            'success': True,
            'collection': collection,
            'info': available_collections[collection],
            'mode': 'single_collection'
        })
        
    except Exception as e:
        print(f"[!] Error switching collection: {e}")
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@app.route('/folders', methods=['GET'])
@require_auth
def get_folders():
    """Get folders from Google Drive with caching and retry logic for SSL errors"""
    try:
        global drive_service
        
        # Check if Google Drive service is available, try to reinitialize if not
        if drive_service is None:
            print("[!] Drive service not available, attempting to reinitialize...")
            try:
                drive_service = authenticate_google_drive(interactive=False)
            except Exception as e:
                print(f"[!] Drive service reinit failed: {e}")
            
        # If still not available, return unavailable response    
        if drive_service is None:
            return jsonify({
                'error': 'Google Drive service not available',
                'message': 'Google Drive authentication needs to be set up. The chat system will still work with indexed documents.',
                'items': [],
                'cached': False,
                'can_retry': True
            }), 503
        
        parent_id = request.args.get('parent_id', '')
        
        print(f"[F] Loading folder contents for parent_id: {parent_id}")
        
        # Check cache first
        cache_key = get_cache_key(parent_id)
        cached_data = get_cached_data(cache_key)
        
        if cached_data is not None:
            print(f"[C] Returning cached data for {parent_id}")
            # Format cached data for response
            formatted_items = []
            for item in cached_data:
                is_folder = item['mimeType'] == 'application/vnd.google-apps.folder'
                formatted_item = {
                    'id': item['id'],
                    'name': item['name'],
                    'type': 'folder' if is_folder else 'file',
                    'mimeType': item['mimeType'],
                    'webViewLink': item.get('webViewLink', f'https://drive.google.com/{"drive/folders" if is_folder else "file/d"}/{item["id"]}{"" if is_folder else "/view"}'),
                    'hasChildren': is_folder,
                    'parent_id': parent_id
                }
                formatted_items.append(formatted_item)
            
            # Sort: folders first, then files, both alphabetically
            formatted_items.sort(key=lambda x: (x['type'] == 'file', x['name'].lower()))
            
            return jsonify({
                'items': formatted_items,
                'parent_id': parent_id,
                'total_count': len(formatted_items),
                'cached': True
            })
        
        # If no parent_id is specified, return the root folders from 7MM Resources shared drive
        if not parent_id or parent_id == '':
            print(f"[F] Loading root folders from 7MM Resources shared drive ({SHARED_DRIVE_ID})")
            
            # Query for root-level folders in the shared drive
            query = f"'{SHARED_DRIVE_ID}' in parents and mimeType='application/vnd.google-apps.folder' and trashed=false"
            
            def make_request():
                return drive_service.files().list(
                    q=query,
                    driveId=SHARED_DRIVE_ID,
                    corpora='drive',
                    pageSize=100,
                    fields="files(id, name, mimeType, webViewLink)",
                    supportsAllDrives=True,
                    includeItemsFromAllDrives=True
                )
            
            response = safe_drive_request(make_request)
            if response is None:
                return jsonify({'error': 'Failed to load shared drive folders after multiple retries'}), 500
            
            items = response.get('files', [])
            
            # Cache the results
            update_cache(cache_key, items)
            
            # Format the response for root folders
            formatted_items = []
            for item in items:
                formatted_item = {
                    'id': item['id'],
                    'name': item['name'],
                    'type': 'folder',
                    'webViewLink': item.get('webViewLink', f'https://drive.google.com/drive/folders/{item["id"]}'),
                    'hasChildren': True,  # Assume root folders have children
                    'parent_id': SHARED_DRIVE_ID,
                    'shared_drive_id': SHARED_DRIVE_ID
                }
                formatted_items.append(formatted_item)
            
            # Sort alphabetically
            formatted_items.sort(key=lambda x: x['name'].lower())
            
            print(f"[+] Found {len(formatted_items)} root folders in 7MM Resources shared drive")
            
            return jsonify({
                'items': formatted_items,
                'parent_id': 'root',
                'shared_drive_name': '7MM Resources',
                'shared_drive_id': SHARED_DRIVE_ID,
                'total_count': len(formatted_items)
            })
        
        # For specific folder requests, use Google Drive API with retry logic
        print(f"[F] Loading contents of specific folder: {parent_id}")
        
        query = f"'{parent_id}' in parents and trashed=false"
        
        def make_request():
            return drive_service.files().list(
                q=query,
                pageSize=50,
                fields="files(id, name, mimeType, webViewLink)",
                supportsAllDrives=True,
                includeItemsFromAllDrives=True
            )
        
        response = safe_drive_request(make_request)
        if response is None:
            return jsonify({'error': 'Failed to load folder contents after multiple retries'}), 500
        
        items = response.get('files', [])
        
        # Cache the results
        update_cache(cache_key, items)
        
        # Format the response
        formatted_items = []
        for item in items:
            is_folder = item['mimeType'] == 'application/vnd.google-apps.folder'
            
            formatted_item = {
                'id': item['id'],
                'name': item['name'],
                'type': 'folder' if is_folder else 'file',
                'mimeType': item['mimeType'],
                'webViewLink': item.get('webViewLink', f'https://drive.google.com/{"drive/folders" if is_folder else "file/d"}/{item["id"]}{"" if is_folder else "/view"}'),
                'hasChildren': is_folder,
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
@require_auth
def search_folders():
    """Search for folders/files by name in 7MM Resources shared drive with caching and retry logic"""
    try:
        search_term = request.args.get('q', '').strip()
        
        if not search_term or len(search_term) < 2:
            return jsonify({'error': 'Search term must be at least 2 characters'}), 400
        
        print(f"[?] Searching 7MM Resources for: {search_term}")
        
        # Check cache first
        cache_key = get_cache_key('search', search_term)
        cached_data = get_cached_data(cache_key)
        
        if cached_data is not None:
            print(f"[C] Returning cached search results for '{search_term}'")
            return jsonify({
                'items': cached_data,
                'search_term': search_term,
                'shared_drive_name': '7MM Resources',
                'shared_drive_id': SHARED_DRIVE_ID,
                'total_count': len(cached_data),
                'cached': True
            })
        
        # Escape single quotes in search term
        escaped_search_term = search_term.replace("'", "\\'")
        
        # Build search query for the specific shared drive
        query = f"name contains '{escaped_search_term}' and trashed=false"
        
        def make_request():
            return drive_service.files().list(
                q=query,
                driveId=SHARED_DRIVE_ID,
                corpora='drive',
                pageSize=30,
                fields="files(id, name, mimeType, webViewLink)",
                supportsAllDrives=True,
                includeItemsFromAllDrives=True
            )
        
        response = safe_drive_request(make_request)
        if response is None:
            return jsonify({'error': 'Search failed after multiple retries'}), 500
        
        items = response.get('files', [])
        
        # Format search results
        formatted_items = []
        for item in items:
            is_folder = item['mimeType'] == 'application/vnd.google-apps.folder'
            
            formatted_item = {
                'id': item['id'],
                'name': item['name'],
                'type': 'folder' if is_folder else 'file',
                'mimeType': item['mimeType'],
                'webViewLink': item.get('webViewLink', f'https://drive.google.com/{"drive/folders" if is_folder else "file/d"}/{item["id"]}{"" if is_folder else "/view"}'),
                'shared_drive_id': SHARED_DRIVE_ID,
                'isSearchResult': True
            }
            formatted_items.append(formatted_item)
        
        # Sort: folders first, then files, both alphabetically
        formatted_items.sort(key=lambda x: (x['type'] == 'file', x['name'].lower()))
        
        # Cache the search results
        update_cache(cache_key, formatted_items)
        
        print(f"[+] Found {len(formatted_items)} search results in 7MM Resources")
        
        return jsonify({
            'items': formatted_items,
            'search_term': search_term,
            'shared_drive_name': '7MM Resources',
            'shared_drive_id': SHARED_DRIVE_ID,
            'total_count': len(formatted_items)
        })
        
    except Exception as e:
        print(f"[!] Error searching in 7MM Resources: {e}")
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@app.route('/auth/drive-reinit', methods=['POST'])
@require_auth
def reinitialize_drive():
    """Reinitialize Google Drive service after web authentication"""
    try:
        global drive_service
        
        # Try to load credentials that were saved during web auth
        import pickle
        import os
        from googleapiclient.discovery import build
        
        if os.path.exists(TOKEN_FILE):
            print("Loading Google Drive credentials from web auth...")
            with open(TOKEN_FILE, 'rb') as token:
                creds = pickle.load(token)
                
            if creds and creds.valid:
                drive_service = build('drive', 'v3', credentials=creds)
                print("✅ Google Drive service initialized from web auth credentials!")
                return jsonify({
                    'success': True,
                    'message': 'Google Drive service initialized successfully!'
                })
            else:
                return jsonify({
                    'error': 'Invalid credentials',
                    'message': 'Please re-authenticate'
                }), 400
        else:
            return jsonify({
                'error': 'No credentials found',
                'message': 'Please complete authentication first'
            }), 400
            
    except Exception as e:
        print(f"Error reinitializing Google Drive: {str(e)}")
        return jsonify({'error': f'Failed to initialize Google Drive: {str(e)}'}), 500

@app.route('/drive/status', methods=['GET'])
@require_auth 
def drive_status():
    """Check Google Drive service status"""
    global drive_service
    
    try:
        if drive_service is None:
            # Try to initialize
            try:
                drive_service = authenticate_google_drive(interactive=False)
            except:
                pass
                
        if drive_service is None:
            return jsonify({
                'available': False,
                'message': 'Google Drive service not initialized',
                'can_retry': True
            })
        else:
            # Test the service with a simple call
            try:
                drive_service.files().list(pageSize=1).execute()
                return jsonify({
                    'available': True,
                    'message': 'Google Drive service is working',
                    'can_retry': False
                })
            except Exception as e:
                return jsonify({
                    'available': False,
                    'message': f'Google Drive service error: {str(e)}',
                    'can_retry': True
                })
    except Exception as e:
        return jsonify({
            'available': False,
            'message': f'Error checking drive status: {str(e)}',
            'can_retry': True
        })

@app.route('/drive/download/<file_id>', methods=['GET'])
@require_auth
def download_drive_file(file_id):
    """Download a file directly from Google Drive"""
    global drive_service
    
    try:
        if drive_service is None:
            return jsonify({'error': 'Google Drive service not initialized'}), 503
        
        # Get file metadata to get the filename
        file_metadata = drive_service.files().get(fileId=file_id, fields='name,mimeType').execute()
        filename = file_metadata.get('name', 'download')
        mime_type = file_metadata.get('mimeType', 'application/octet-stream')
        
        # Download the file content
        request = drive_service.files().get_media(fileId=file_id)
        
        # Stream the file content
        from io import BytesIO
        file_buffer = BytesIO()
        from googleapiclient.http import MediaIoBaseDownload
        downloader = MediaIoBaseDownload(file_buffer, request)
        
        done = False
        while not done:
            status, done = downloader.next_chunk()
        
        # Prepare response
        file_buffer.seek(0)
        from flask import send_file
        return send_file(
            file_buffer,
            mimetype=mime_type,
            as_attachment=True,
            download_name=filename
        )
        
    except Exception as e:
        print(f"Error downloading file {file_id}: {str(e)}")
        return jsonify({'error': f'Failed to download file: {str(e)}'}), 500

@app.route('/test/workspace', methods=['POST'])
@require_auth
def test_workspace():
    """Test workspace analysis functionality"""
    try:
        data = request.get_json()
        if not data or 'file_id' not in data:
            return jsonify({'error': 'file_id required'}), 400
            
        file_id = data['file_id']
        test_question = data.get('question', 'What is this document about?')
        
        result = analyze_file_with_workspace(file_id, test_question)
        
        if result:
            return jsonify({
                'success': True,
                'result': result,
                'message': 'Workspace analysis completed successfully'
            })
        else:
            return jsonify({
                'success': False,
                'message': 'Workspace analysis failed - file type may not be supported or file is inaccessible'
            })
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'message': 'Error testing workspace functionality'
        }), 500

@app.route('/auth/drive-setup', methods=['GET'])
@require_auth  
def drive_auth_setup():
    """Get Google Drive authentication setup URL"""
    try:
        from google_auth_oauthlib.flow import InstalledAppFlow
        import json
        
        if not os.path.exists(CREDENTIALS_FILE):
            return jsonify({
                'error': 'Credentials file not found',
                'message': 'Please ensure credentials.json is in the project directory'
            }), 500
            
        # Create OAuth flow for Google Drive
        flow = InstalledAppFlow.from_client_secrets_file(
            CREDENTIALS_FILE, SCOPES)
        flow.redirect_uri = 'urn:ietf:wg:oauth:2.0:oob'
        
        auth_url, state = flow.authorization_url(
            access_type='offline',
            include_granted_scopes='true'
        )
        
        # Store the flow in session for later use
        session['drive_auth_flow_state'] = state
        
        return jsonify({
            'auth_url': auth_url,
            'state': state,
            'instructions': 'Visit the URL, authorize access, then paste the authorization code in the next step'
        })
        
    except Exception as e:
        print(f"Error setting up Google Drive auth: {str(e)}")
        return jsonify({'error': f'Failed to setup Google Drive auth: {str(e)}'}), 500

@app.route('/auth/drive-complete', methods=['POST'])
@require_auth
def drive_auth_complete():
    """Complete Google Drive authentication with authorization code"""
    try:
        data = request.get_json()
        auth_code = data.get('code', '').strip()
        
        if not auth_code:
            return jsonify({'error': 'Authorization code required'}), 400
            
        # Recreate the flow
        from google_auth_oauthlib.flow import InstalledAppFlow
        flow = InstalledAppFlow.from_client_secrets_file(
            CREDENTIALS_FILE, SCOPES)
        flow.redirect_uri = 'urn:ietf:wg:oauth:2.0:oob'
        
        # Exchange code for credentials
        flow.fetch_token(code=auth_code)
        creds = flow.credentials
        
        # Save credentials
        import pickle
        with open(TOKEN_FILE, 'wb') as token:
            pickle.dump(creds, token)
            
        # Initialize the global drive service
        global drive_service
        from googleapiclient.discovery import build
        drive_service = build('drive', 'v3', credentials=creds)
        
        print("✅ Google Drive authentication completed via web interface!")
        
        return jsonify({
            'success': True,
            'message': 'Google Drive authentication successful! Folders are now available.'
        })
        
    except Exception as e:
        print(f"Error completing Google Drive auth: {str(e)}")
        return jsonify({'error': f'Failed to complete Google Drive auth: {str(e)}'}), 500

@app.route('/cache/status', methods=['GET'])
def cache_status():
    """Get cache status and statistics"""
    try:
        with cache_lock:
            cache_stats = {
                'total_entries': len(folder_cache),
                'entries': []
            }
            
            for cache_key, cache_entry in folder_cache.items():
                entry_info = {
                    'key': cache_key,
                    'timestamp': cache_entry['timestamp'].isoformat(),
                    'expired': is_cache_expired(cache_entry),
                    'item_count': len(cache_entry['data']) if 'data' in cache_entry else 0
                }
                cache_stats['entries'].append(entry_info)
        
        return jsonify(cache_stats)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/cache/clear', methods=['POST'])
def clear_cache():
    """Clear all cache entries"""
    try:
        with cache_lock:
            folder_cache.clear()
        return jsonify({'message': 'Cache cleared successfully'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/cost/summary', methods=['GET'])
def cost_summary():
    """Get API cost summary (simplified version)"""
    try:
        return jsonify({
            'total_cost': 0.0,
            'monthly_budget': 50.0,
            'percent_used': 0.0,
            'warning_level': 'low',
            'queries_today': 0,
            'using_vertex_ai': USE_VERTEX_AI,
            'message': 'Cost monitoring simplified for production'
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/cost/reset', methods=['POST'])
@require_auth
def reset_cost_tracking():
    """Reset cost tracking (simplified version)"""
    try:
        return jsonify({'message': 'Cost tracking reset (simplified for production)'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/cache/preload', methods=['POST'])
def trigger_preload():
    """Manually trigger cache preload"""
    try:
        # Start preload in background thread
        preload_thread = Thread(target=preload_folder_structure, daemon=True)
        preload_thread.start()
        return jsonify({'message': 'Cache preload started in background'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/folders/batch', methods=['POST'])
@require_auth
def get_folders_batch():
    """Load multiple folders at once for better performance"""
    data = request.get_json()
    folder_ids = data.get('folder_ids', [])
    
    if not folder_ids:
        return jsonify({'error': 'No folder IDs provided'}), 400
    
    results = {}
    
    for folder_id in folder_ids:
        cache_key = get_cache_key(folder_id if folder_id else SHARED_DRIVE_ID)
        
        # Check cache first
        cached_data = get_cached_data(cache_key)
        if cached_data:
            results[folder_id or 'root'] = {
                'items': format_folder_items(cached_data, folder_id),
                'cached': True
            }
            continue
        
        # Load from API if not cached
        try:
            if not folder_id:
                # Root folders
                query = f"'{SHARED_DRIVE_ID}' in parents and mimeType='application/vnd.google-apps.folder' and trashed=false"
                def make_request():
                    return drive_service.files().list(
                        q=query,
                        driveId=SHARED_DRIVE_ID,
                        corpora='drive',
                        pageSize=100,
                        fields="files(id, name, mimeType, webViewLink)",
                        supportsAllDrives=True,
                        includeItemsFromAllDrives=True
                    )
            else:
                # Specific folder
                query = f"'{folder_id}' in parents and trashed=false"
                def make_request():
                    return drive_service.files().list(
                        q=query,
                        pageSize=50,
                        fields="files(id, name, mimeType, webViewLink)",
                        supportsAllDrives=True,
                        includeItemsFromAllDrives=True
                    )
            
            response = safe_drive_request(make_request)
            if response:
                items = response.get('files', [])
                update_cache(cache_key, items)
                results[folder_id or 'root'] = {
                    'items': format_folder_items(items, folder_id),
                    'cached': False
                }
            else:
                results[folder_id or 'root'] = {'error': 'Failed to load'}
                
        except Exception as e:
            results[folder_id or 'root'] = {'error': str(e)}
    
    return jsonify(results)

def format_folder_items(items, parent_id):
    """Helper function to format folder items consistently"""
    formatted_items = []
    for item in items:
        is_folder = item['mimeType'] == 'application/vnd.google-apps.folder'
        formatted_item = {
            'id': item['id'],
            'name': item['name'],
            'type': 'folder' if is_folder else 'file',
            'mimeType': item['mimeType'],
            'webViewLink': item.get('webViewLink', f'https://drive.google.com/{"drive/folders" if is_folder else "file/d"}/{item["id"]}/view'),
            'hasChildren': is_folder,
            'parent_id': parent_id
        }
        formatted_items.append(formatted_item)
    
    # Sort: folders first, then files, both alphabetically
    formatted_items.sort(key=lambda x: (x['type'] == 'file', x['name'].lower()))
    return formatted_items

def create_app():
    """Application factory for production deployment"""
    try:
        initialize_rag_system()
    except Exception as e:
        print(f"[!] Warning: RAG system initialization failed: {e}")
        print("[!] Server will start with limited functionality")
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
    try:
        initialize_rag_system()
    except Exception as e:
        print(f"[!] Warning: RAG system initialization failed: {e}")
        print("[!] Server will start with limited functionality - admin panel will still work")
        print("[!] You can set up Google Drive authentication later")
    
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
"""
Optional Google File Search Integration
Add this to your existing chat_api.py for enhanced capabilities
"""

import os
from typing import Optional, List, Dict, Any
import logging

# Optional imports - only if you want Google File Search
try:
    from google import genai
    from google.genai import types
    GOOGLE_FILE_SEARCH_AVAILABLE = True
except ImportError:
    GOOGLE_FILE_SEARCH_AVAILABLE = False
    logging.info("Google File Search not available. Install with: pip install google-generativeai")

class OptionalGoogleFileSearch:
    """
    Optional Google File Search integration
    Fallback to existing RAG if not available or configured
    """
    
    def __init__(self):
        self.enabled = False
        self.client = None
        self.file_stores = {}
        
        # Only initialize if available and configured
        if GOOGLE_FILE_SEARCH_AVAILABLE and os.getenv('GOOGLE_API_KEY'):
            try:
                self.client = genai.Client(api_key=os.getenv('GOOGLE_API_KEY'))
                self.enabled = True
                logging.info("Google File Search initialized successfully")
            except Exception as e:
                logging.warning(f"Google File Search initialization failed: {e}")
    
    def is_available(self) -> bool:
        """Check if Google File Search is available and configured"""
        return self.enabled and self.client is not None
    
    def should_use_google_search(self, query: str, collection: str = None) -> bool:
        """
        Determine if query should use Google File Search
        Based on query characteristics and configuration
        """
        if not self.is_available():
            return False
        
        # Use Google File Search for citation-heavy queries
        query_lower = query.lower()
        citation_keywords = ['cite', 'source', 'reference', 'according to', 'quote from', 'evidence']
        
        return any(keyword in query_lower for keyword in citation_keywords)
    
    async def search(self, query: str, collection: str = None) -> Optional[Dict[str, Any]]:
        """
        Search using Google File Search
        Returns None if not available or fails
        """
        if not self.is_available():
            return None
        
        try:
            # Use available file stores
            store_names = list(self.file_stores.values()) if self.file_stores else []
            
            if not store_names:
                # No stores configured, return None to fall back to local RAG
                return None
            
            response = self.client.models.generate_content(
                model="gemini-2.5-flash",
                contents=query,
                config=types.GenerateContentConfig(
                    tools=[
                        types.Tool(
                            file_search=types.FileSearch(
                                file_search_store_names=store_names
                            )
                        )
                    ]
                )
            )
            
            if response.text:
                # Extract citations if available
                citations = self._extract_citations(response)
                
                return {
                    'answer': response.text,
                    'sources': [{ 
                        'content': response.text,
                        'source': 'Google File Search',
                        'citations': citations
                    }],
                    'method': 'google_file_search'
                }
        
        except Exception as e:
            logging.error(f"Google File Search query failed: {e}")
        
        return None
    
    def _extract_citations(self, response) -> List[str]:
        """Extract citation information from response"""
        citations = []
        try:
            if hasattr(response, 'candidates') and response.candidates:
                grounding_metadata = getattr(response.candidates[0], 'grounding_metadata', None)
                if grounding_metadata:
                    citations.append(str(grounding_metadata))
        except Exception as e:
            logging.error(f"Citation extraction error: {e}")
        
        return citations

# Global instance (optional)
google_file_search = OptionalGoogleFileSearch()

def enhanced_chat_with_google_fallback(message: str, collection: str = None) -> Dict[str, Any]:
    """
    Enhanced chat function that optionally uses Google File Search
    Falls back to your existing RAG system
    """
    global rag_system, multi_collection_rag, google_file_search
    
    # Try Google File Search for citation queries if available
    if google_file_search.should_use_google_search(message, collection):
        google_result = google_file_search.search(message, collection)
        if google_result:
            logging.info("Used Google File Search for citation query")
            return google_result
    
    # Fall back to your existing excellent RAG system
    try:
        if collection == "ALL_COLLECTIONS":
            if not multi_collection_rag:
                return {'error': 'Multi-collection system not available'}
            
            response = multi_collection_rag.process_chat(message)
            documents = []
            for source in response.get('sources', []):
                documents.append({
                    'title': source.get('title', 'Untitled'),
                    'content': source.get('content', ''),
                    'url': source.get('url', ''),
                    'collection': source.get('collection', ''),
                    'score': source.get('score', 0)
                })
            
            return {
                'answer': response.get('answer', 'No response generated'),
                'documents': documents,
                'sources': response.get('sources', []),
                'method': 'multi_collection_rag'
            }
        else:
            # Single collection RAG
            if not rag_system:
                return {'error': 'RAG system not initialized'}
            
            result = rag_system.process_question(message)
            
            documents = []
            if 'documents' in result:
                for doc in result['documents']:
                    documents.append({
                        'title': doc.get('filename', 'Unknown'),
                        'content': doc.get('content', ''),
                        'url': doc.get('url', ''),
                        'collection': collection or 'default',
                        'score': doc.get('score', 0)
                    })
            
            return {
                'answer': result.get('answer', 'No answer generated'),
                'documents': documents,
                'sources': result.get('contexts', []),
                'method': 'single_collection_rag'
            }
    
    except Exception as e:
        logging.error(f"RAG system error: {e}")
        return {'error': str(e)}

# Optional: Add to your existing chat endpoint
def update_chat_endpoint_with_google_support():
    """
    Example of how to update your existing chat endpoint
    This is OPTIONAL - your current system works great as-is
    """
    
    # In your chat_api.py, you could update the chat route like this:
    """
    @app.route('/chat', methods=['POST'])
    @require_auth
    @limiter.limit("30 per minute")
    def chat():
        global rag_system, multi_collection_rag
        
        try:
            data = request.get_json()
            message = data['message']
            collection = data.get('collection')
            
            # Use enhanced chat function (with optional Google File Search)
            result = enhanced_chat_with_google_fallback(message, collection)
            
            # Return standardized response
            return jsonify(result)
            
        except Exception as e:
            logging.error(f"Chat endpoint error: {e}")
            return jsonify({'error': str(e)}), 500
    """

if __name__ == "__main__":
    # Test Google File Search availability
    print("Google File Search Available:", google_file_search.is_available())
    
    # Example usage
    if google_file_search.is_available():
        print("Google File Search is ready for citation queries!")
    else:
        print("Google File Search not configured - using excellent local RAG system!")
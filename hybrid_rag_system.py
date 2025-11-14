"""
Hybrid RAG System: Integrating Google File Search with Custom RAG
Smart integration strategy for optimal performance and cost
"""

import os
import logging
from typing import List, Dict, Optional, Union
from dataclasses import dataclass
from google import genai
from google.genai import types
import asyncio

@dataclass
class SearchResult:
    content: str
    source: str
    score: float
    citation: Optional[str] = None
    collection: str = ""
    method: str = ""  # 'google_file_search' or 'local_rag'

class HybridRAGSystem:
    """
    Hybrid RAG system that intelligently chooses between Google File Search 
    and local RAG based on content type, size, and query characteristics
    """
    
    def __init__(self, google_api_key: str, local_rag_system, multi_collection_rag):
        self.google_client = genai.Client(api_key=google_api_key)
        self.local_rag = local_rag_system
        self.multi_collection_rag = multi_collection_rag
        
        # Strategy configuration
        self.file_size_threshold = 50_000_000  # 50MB - use Google for larger files
        self.google_file_stores = {}  # Track Google File Search stores
        self.routing_rules = self._setup_routing_rules()
        
    def _setup_routing_rules(self):
        """Define rules for routing queries to appropriate system"""
        return {
            'use_google_file_search': [
                'large_documents',      # >50MB files
                'document_analysis',    # Deep document understanding
                'citation_required',    # When citations are critical
                'new_documents'        # Recently uploaded large docs
            ],
            'use_local_rag': [
                'multi_collection',     # Cross-collection queries
                'realtime_drive',      # Live Google Drive integration
                'custom_metadata',     # Your custom organizational metadata
                'frequent_queries',    # Cached/optimized queries
                'structured_data'      # Spreadsheets, structured content
            ]
        }
    
    async def smart_search(self, query: str, collection: str = None, 
                          force_method: str = None) -> List[SearchResult]:
        """
        Intelligent routing between Google File Search and local RAG
        """
        if force_method:
            if force_method == 'google':
                return await self._google_file_search(query, collection)
            else:
                return await self._local_rag_search(query, collection)
        
        # Smart routing based on query characteristics
        search_strategy = self._analyze_query(query, collection)
        
        if search_strategy == 'google_file_search':
            try:
                results = await self._google_file_search(query, collection)
                if results:
                    return results
                # Fallback to local if Google fails
                logging.warning("Google File Search failed, falling back to local RAG")
            except Exception as e:
                logging.error(f"Google File Search error: {e}, using local RAG")
        
        # Use local RAG (default or fallback)
        return await self._local_rag_search(query, collection)
    
    def _analyze_query(self, query: str, collection: str = None) -> str:
        """
        Analyze query to determine best search strategy
        """
        query_lower = query.lower()
        
        # Use Google File Search for:
        if any(keyword in query_lower for keyword in ['cite', 'source', 'reference', 'according to']):
            return 'google_file_search'
        
        if collection and collection in self.google_file_stores:
            return 'google_file_search'
        
        # Use local RAG for multi-collection or real-time Drive queries
        if collection == 'ALL_COLLECTIONS' or not collection:
            return 'local_rag'
        
        # Default to local RAG for most queries
        return 'local_rag'
    
    async def _google_file_search(self, query: str, collection: str = None) -> List[SearchResult]:
        """Search using Google File Search"""
        results = []
        
        try:
            # Determine which file stores to search
            store_names = [self.google_file_stores[collection]] if collection in self.google_file_stores else list(self.google_file_stores.values())
            
            if not store_names:
                return results
            
            response = self.google_client.models.generate_content(
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
            
            # Extract results with citations
            if response.text:
                results.append(SearchResult(
                    content=response.text,
                    source="Google File Search",
                    score=1.0,
                    citation=self._extract_citations(response),
                    collection=collection or "google_file_search",
                    method="google_file_search"
                ))
            
        except Exception as e:
            logging.error(f"Google File Search error: {e}")
        
        return results
    
    async def _local_rag_search(self, query: str, collection: str = None) -> List[SearchResult]:
        """Search using local RAG system"""
        try:
            if collection == 'ALL_COLLECTIONS':
                # Use multi-collection RAG
                response = self.multi_collection_rag.process_question(query)
                sources = response.get('sources', [])
            else:
                # Use single collection RAG
                response = self.local_rag.process_question(query)
                sources = response.get('sources', [])
            
            results = []
            for source in sources:
                results.append(SearchResult(
                    content=source.get('content', ''),
                    source=source.get('url', source.get('filename', 'Unknown')),
                    score=source.get('score', 0.0),
                    collection=source.get('collection', collection or 'local'),
                    method="local_rag"
                ))
            
            return results
            
        except Exception as e:
            logging.error(f"Local RAG search error: {e}")
            return []
    
    def _extract_citations(self, response) -> str:
        """Extract citation information from Google File Search response"""
        try:
            if hasattr(response, 'candidates') and response.candidates:
                grounding_metadata = getattr(response.candidates[0], 'grounding_metadata', None)
                if grounding_metadata:
                    return str(grounding_metadata)
        except Exception as e:
            logging.error(f"Citation extraction error: {e}")
        return ""
    
    def migrate_large_documents_to_google(self, size_threshold: int = 50_000_000):
        """
        Migrate large documents from local RAG to Google File Search
        for better performance and cost efficiency
        """
        migrated_docs = []
        
        try:
            # Identify large documents in local system
            # This would integrate with your existing Google Drive system
            large_docs = self._identify_large_documents(size_threshold)
            
            for doc in large_docs:
                try:
                    # Create or get file search store
                    store_name = self._get_or_create_store(doc['collection'])
                    
                    # Upload to Google File Search
                    operation = self.google_client.file_search_stores.upload_to_file_search_store(
                        file=doc['path'],
                        file_search_store_name=store_name,
                        config={
                            'display_name': doc['name'],
                            'custom_metadata': doc.get('metadata', [])
                        }
                    )
                    
                    # Wait for completion
                    while not operation.done:
                        await asyncio.sleep(5)
                        operation = self.google_client.operations.get(operation)
                    
                    migrated_docs.append(doc['name'])
                    logging.info(f"Migrated {doc['name']} to Google File Search")
                    
                except Exception as e:
                    logging.error(f"Failed to migrate {doc['name']}: {e}")
            
        except Exception as e:
            logging.error(f"Migration process error: {e}")
        
        return migrated_docs
    
    def _identify_large_documents(self, size_threshold: int) -> List[Dict]:
        """Identify documents larger than threshold in local system"""
        # This would integrate with your existing Google Drive file detection
        # and return list of large documents that should be migrated
        return []
    
    def _get_or_create_store(self, collection_name: str) -> str:
        """Get existing or create new Google File Search store for collection"""
        if collection_name in self.google_file_stores:
            return self.google_file_stores[collection_name]
        
        # Create new store
        store = self.google_client.file_search_stores.create(
            config={'display_name': f'rag-{collection_name}'}
        )
        
        self.google_file_stores[collection_name] = store.name
        return store.name
    
    async def cost_optimized_search(self, query: str, collection: str = None) -> List[SearchResult]:
        """
        Cost-optimized search strategy:
        1. Try local RAG first (free)
        2. Use Google File Search only if local results are insufficient
        """
        # First try local search
        local_results = await self._local_rag_search(query, collection)
        
        # If we have good local results, return them
        if local_results and len(local_results) >= 3:
            for result in local_results:
                result.method = "local_rag_primary"
            return local_results
        
        # If local results are insufficient, try Google File Search
        google_results = await self._google_file_search(query, collection)
        
        # Combine results with preference for local (free) results
        combined = local_results + google_results
        return sorted(combined, key=lambda x: x.score, reverse=True)[:10]

class SmartRAGRouter:
    """
    Smart router that decides between different RAG strategies
    based on query type, cost considerations, and performance needs
    """
    
    def __init__(self, hybrid_system: HybridRAGSystem):
        self.hybrid = hybrid_system
        self.query_cache = {}  # Cache for frequent queries
        self.cost_budget = 100.0  # Daily budget in USD
        self.cost_used = 0.0
        
    async def route_query(self, query: str, collection: str = None, 
                         prefer_cost: bool = True) -> List[SearchResult]:
        """
        Route query to most appropriate system based on multiple factors
        """
        # Check cache first
        cache_key = f"{query}:{collection}"
        if cache_key in self.query_cache:
            return self.query_cache[cache_key]
        
        # Cost-aware routing
        if prefer_cost or self.cost_used >= self.cost_budget * 0.8:
            results = await self.hybrid.cost_optimized_search(query, collection)
        else:
            results = await self.hybrid.smart_search(query, collection)
        
        # Cache results
        self.query_cache[cache_key] = results
        
        return results
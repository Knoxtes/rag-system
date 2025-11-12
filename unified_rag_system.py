#!/usr/bin/env python3
"""
Unified RAG System with Intelligent Folder Routing
Combines all indexed folders into one seamless experience while maintaining folder-aware search optimization
"""

import json
import os
import re
from typing import Dict, List, Tuple, Optional
from config import INDEXED_FOLDERS_FILE
from rag_system import EnhancedRAGSystem
from auth import authenticate_google_drive

class UnifiedRAGSystem:
    """
    Unified RAG system that searches across all indexed collections
    with intelligent folder routing based on query intent
    """
    
    def __init__(self):
        self.drive_service = None
        self.indexed_folders = self.load_indexed_folders()
        self.rag_systems = {}
        self.folder_keywords = self.build_folder_keyword_map()
        
    def load_indexed_folders(self) -> Dict:
        """Load indexed folders configuration"""
        if os.path.exists(INDEXED_FOLDERS_FILE):
            with open(INDEXED_FOLDERS_FILE, 'r') as f:
                return json.load(f)
        return {}
    
    def build_folder_keyword_map(self) -> Dict[str, List[str]]:
        """Build keyword mapping for intelligent folder routing"""
        keyword_map = {}
        
        for folder_id, info in self.indexed_folders.items():
            folder_name = info.get('name', '').lower()
            location = info.get('location', '').lower()
            collection_name = info.get('collection_name', '')
            
            keywords = []
            
            # Extract keywords from folder names
            if 'hr' in folder_name or 'human resources' in folder_name:
                keywords.extend([
                    'hr', 'human resources', 'employee', 'staff', 'benefits', 
                    'vacation', 'pto', 'policy', 'handbook', 'payroll',
                    'hiring', 'onboarding', 'training', 'performance review',
                    'health insurance', 'retirement', '401k', 'holidays'
                ])
            
            if 'admin' in folder_name or 'traffic' in folder_name:
                keywords.extend([
                    'admin', 'administration', 'traffic', 'operations',
                    'procedures', 'workflow', 'management', 'coordination',
                    'scheduling', 'logistics', 'billing', 'invoicing'
                ])
            
            if 'creative' in folder_name or 'marketing' in folder_name:
                keywords.extend([
                    'creative', 'marketing', 'design', 'brand', 'logo',
                    'website', 'video', 'photography', 'graphics',
                    'advertising', 'campaign', 'content', 'social media',
                    'production', 'samples', 'portfolio'
                ])
            
            if 'sales' in folder_name:
                keywords.extend([
                    'sales', 'revenue', 'leads', 'clients', 'customers',
                    'prospects', 'deals', 'contracts', 'pricing',
                    'proposals', 'quotations'
                ])
            
            if 'finance' in folder_name or 'accounting' in folder_name:
                keywords.extend([
                    'finance', 'financial', 'accounting', 'budget',
                    'expenses', 'revenue', 'profit', 'cost',
                    'invoice', 'payment', 'tax', 'audit'
                ])
            
            if 'legal' in folder_name:
                keywords.extend([
                    'legal', 'contract', 'agreement', 'compliance',
                    'regulation', 'law', 'policy', 'terms'
                ])
            
            # Add the folder name and location as keywords
            keywords.extend([folder_name, location])
            
            if collection_name:
                keyword_map[collection_name] = keywords
        
        return keyword_map
    
    def analyze_query_intent(self, query: str) -> List[Tuple[str, float]]:
        """
        Analyze query to determine which folders are most relevant
        Returns list of (collection_name, relevance_score) tuples
        """
        query_lower = query.lower()
        folder_scores = {}
        
        # Score each folder based on keyword matches
        for collection_name, keywords in self.folder_keywords.items():
            score = 0.0
            
            for keyword in keywords:
                if keyword in query_lower:
                    # Exact match gets higher score
                    if keyword == query_lower.strip():
                        score += 2.0
                    # Word boundary match
                    elif re.search(r'\\b' + re.escape(keyword) + r'\\b', query_lower):
                        score += 1.0
                    # Partial match
                    else:
                        score += 0.5
            
            if score > 0:
                folder_scores[collection_name] = score
        
        # Sort by relevance score (highest first)
        sorted_scores = sorted(folder_scores.items(), key=lambda x: x[1], reverse=True)
        
        # Normalize scores to 0-1 range
        if sorted_scores:
            max_score = sorted_scores[0][1]
            normalized_scores = [(name, score/max_score) for name, score in sorted_scores]
            return normalized_scores
        
        # If no specific matches, return all folders with equal weight
        all_folders = [(name, 0.3) for name in self.folder_keywords.keys()]
        return all_folders
    
    def get_folder_display_name(self, collection_name: str) -> str:
        """Get human-readable name for a collection"""
        for folder_id, info in self.indexed_folders.items():
            if info.get('collection_name') == collection_name:
                return f"{info['name']} ({info['location']})"
        return collection_name
    
    def initialize_rag_systems(self):
        """Initialize RAG systems for all indexed folders"""
        print("🚀 Initializing unified RAG system...")
        
        if not self.drive_service:
            print("Authenticating with Google Drive...")
            self.drive_service = authenticate_google_drive()
        
        total_collections = len(self.indexed_folders)
        print(f"📁 Loading {total_collections} indexed collections...")
        
        for i, (folder_id, info) in enumerate(self.indexed_folders.items(), 1):
            collection_name = info.get('collection_name')
            if collection_name:
                try:
                    print(f"  [{i}/{total_collections}] Loading {info['name']}...")
                    rag_system = EnhancedRAGSystem(
                        drive_service=self.drive_service,
                        collection_name=collection_name
                    )
                    self.rag_systems[collection_name] = rag_system
                    print(f"    ✓ Ready ({rag_system.vector_store.get_stats()['total_documents']} documents)")
                except Exception as e:
                    print(f"    ✗ Failed to load {info['name']}: {e}")
        
        print(f"✅ Unified system ready with {len(self.rag_systems)} collections!")
        
    def search_with_routing(self, query: str, max_results_per_folder: int = 10) -> List[Dict]:
        """
        Search across collections with intelligent routing
        """
        print(f"🔍 Analyzing query intent: \"{query}\"")
        
        # Analyze query to determine folder relevance
        folder_relevance = self.analyze_query_intent(query)
        
        if folder_relevance:
            print("📊 Folder relevance analysis:")
            for collection_name, score in folder_relevance[:3]:  # Show top 3
                folder_name = self.get_folder_display_name(collection_name)
                print(f"  • {folder_name}: {score:.2f}")
        
        all_results = []
        
        # Search in order of relevance
        for collection_name, relevance_score in folder_relevance:
            if collection_name in self.rag_systems:
                try:
                    print(f"  🔍 Searching {self.get_folder_display_name(collection_name)}...")
                    
                    # Use the existing rag_search tool
                    rag_system = self.rag_systems[collection_name]
                    search_results = rag_system._tool_rag_search(query)
                    
                    # Parse JSON results
                    if isinstance(search_results, str):
                        try:
                            results_data = json.loads(search_results)
                            if isinstance(results_data, list):
                                # Add folder context and relevance weighting to each result
                                for result in results_data[:max_results_per_folder]:
                                    result['folder_source'] = self.get_folder_display_name(collection_name)
                                    result['folder_relevance'] = relevance_score
                                    result['collection_name'] = collection_name
                                    # Boost relevance score based on folder matching
                                    if 'relevance' in result:
                                        try:
                                            original_relevance = float(result['relevance'])
                                            boosted_relevance = original_relevance * (1 + relevance_score * 0.5)
                                            result['boosted_relevance'] = f"{boosted_relevance:.2f}"
                                        except ValueError:
                                            result['boosted_relevance'] = result['relevance']
                                
                                all_results.extend(results_data[:max_results_per_folder])
                                print(f"    ✓ Found {len(results_data)} results")
                        except json.JSONDecodeError:
                            print(f"    ⚠️ Invalid JSON response from {collection_name}")
                except Exception as e:
                    print(f"    ✗ Error searching {collection_name}: {e}")
        
        # Sort all results by boosted relevance
        try:
            all_results.sort(key=lambda x: float(x.get('boosted_relevance', x.get('relevance', '0'))), reverse=True)
        except (ValueError, TypeError):
            # Fallback to original relevance if boosted fails
            pass
        
        print(f"📋 Total results: {len(all_results)} from {len(set(r.get('folder_source', '') for r in all_results))} folders")
        
        return all_results
    
    def format_response_with_sources(self, query: str, results: List[Dict], max_results: int = 15) -> str:
        """
        Format search results into a comprehensive response with source attribution
        """
        if not results:
            return "❌ No relevant documents found across all indexed folders."
        
        # Take top results
        top_results = results[:max_results]
        
        # Group results by folder for better organization
        folder_groups = {}
        for result in top_results:
            folder = result.get('folder_source', 'Unknown')
            if folder not in folder_groups:
                folder_groups[folder] = []
            folder_groups[folder].append(result)
        
        response_parts = []
        
        # Add header
        response_parts.append(f"📋 **Results for: \"{query}\"**\\n")
        response_parts.append(f"Found {len(top_results)} relevant results across {len(folder_groups)} folders:\\n")
        
        # Add results grouped by folder
        for folder, folder_results in folder_groups.items():
            response_parts.append(f"\\n### 📁 {folder}\\n")
            
            for i, result in enumerate(folder_results[:5], 1):  # Limit per folder
                snippet = result.get('snippet', 'No content available')
                file_info = result.get('file_info', {})
                file_name = file_info.get('file_name', 'Unknown file')
                google_drive_link = file_info.get('google_drive_link', '')
                relevance = result.get('boosted_relevance', result.get('relevance', 'N/A'))
                
                # Format snippet (truncate if too long)
                if len(snippet) > 300:
                    snippet = snippet[:300] + "..."
                
                response_parts.append(f"**{i}. {file_name}** (Relevance: {relevance})")
                response_parts.append(f"{snippet}")
                
                if google_drive_link:
                    response_parts.append(f"📎 [Open Document]({google_drive_link})")
                
                response_parts.append("")  # Empty line
        
        # Add summary of other folders if results span multiple folders
        if len(folder_groups) > 3:
            other_folders = list(folder_groups.keys())[3:]
            response_parts.append(f"\\n*Also found relevant results in: {', '.join(other_folders)}*\\n")
        
        return "\\n".join(response_parts)
    
    def unified_query(self, query: str) -> str:
        """
        Main unified query interface
        """
        try:
            # Search with intelligent routing
            results = self.search_with_routing(query)
            
            # Format comprehensive response
            response = self.format_response_with_sources(query, results)
            
            return response
            
        except Exception as e:
            return f"❌ Error processing query: {str(e)}"


def interactive_unified_mode():
    """
    Interactive mode for the unified RAG system
    """
    print("\\n" + "=" * 80)
    print("🌟 UNIFIED RAG SYSTEM")
    print("Intelligent search across all your indexed folders")
    print("=" * 80)
    
    # Initialize unified system
    unified_system = UnifiedRAGSystem()
    
    if not unified_system.indexed_folders:
        print("\\n⚠️  No folders have been indexed yet!")
        print("Please run the folder indexer first.")
        return
    
    print(f"\\n📁 Available folders:")
    for folder_id, info in unified_system.indexed_folders.items():
        print(f"  • {info['name']} ({info['location']}) - {info.get('files_processed', 'N/A')} files")
    
    # Initialize all RAG systems
    unified_system.initialize_rag_systems()
    
    print("\\n" + "=" * 80)
    print("🤖 Ready! Ask questions about any topic from your indexed folders.")
    print("The system will automatically search the most relevant folders first.")
    print("Commands: 'quit' or 'exit' to stop")
    print("=" * 80)
    
    while True:
        try:
            print("\\n💬 Your query: ", end="")
            query = input().strip()
            
            if query.lower() in ['quit', 'exit', 'q']:
                print("👋 Goodbye!")
                break
            
            if not query:
                print("Please enter a question.")
                continue
            
            print("\\n" + "=" * 80)
            print(f"🔍 Processing: {query}")
            print("=" * 80)
            
            # Process query
            response = unified_system.unified_query(query)
            
            print("\\n📝 **Response:**\\n")
            print(response)
            
        except KeyboardInterrupt:
            print("\\n\\n👋 Interrupted. Goodbye!")
            break
        except Exception as e:
            print(f"\\n❌ Error: {e}")


if __name__ == "__main__":
    interactive_unified_mode()
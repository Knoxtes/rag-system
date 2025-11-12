#!/usr/bin/env python3
"""
Test script for the Unified RAG System
Demonstrates intelligent folder routing and cross-collection search
"""

from unified_rag_system import UnifiedRAGSystem

def test_intent_analysis():
    """Test the query intent analysis system"""
    print("🧪 Testing Intent Analysis System")
    print("=" * 50)
    
    # Create unified system instance
    unified_system = UnifiedRAGSystem()
    
    if not unified_system.indexed_folders:
        print("❌ No indexed folders found. Please index some folders first.")
        return
    
    # Test queries for different intents
    test_queries = [
        "What are the vacation policies?",
        "How do I request time off?",
        "Creative brief template",
        "Logo design guidelines",
        "Employee onboarding process",
        "Marketing campaign examples",
        "HR handbook",
        "Design samples",
        "Holiday calendar",
        "Benefits information"
    ]
    
    print("Available folders and keywords:")
    for collection_name, keywords in unified_system.folder_keywords.items():
        folder_name = unified_system.get_folder_display_name(collection_name)
        print(f"  📁 {folder_name}")
        print(f"     Keywords: {', '.join(keywords[:10])}")
        if len(keywords) > 10:
            print(f"     ... and {len(keywords) - 10} more")
        print()
    
    print("Testing query intent analysis:")
    print("-" * 40)
    
    for query in test_queries:
        print(f"\n🔍 Query: \"{query}\"")
        intent_results = unified_system.analyze_query_intent(query)
        
        if intent_results:
            print("   Top matches:")
            for collection_name, score in intent_results[:3]:
                folder_name = unified_system.get_folder_display_name(collection_name)
                print(f"     • {folder_name}: {score:.2f}")
        else:
            print("   No specific folder matches found")

def test_unified_search():
    """Test the unified search functionality"""
    print("\n\n🔍 Testing Unified Search")
    print("=" * 50)
    
    # Create unified system instance
    unified_system = UnifiedRAGSystem()
    
    if not unified_system.indexed_folders:
        print("❌ No indexed folders found. Please index some folders first.")
        return
    
    print("Initializing RAG systems...")
    unified_system.initialize_rag_systems()
    
    # Test searches
    test_queries = [
        "employee benefits",
        "creative guidelines",
        "vacation policy"
    ]
    
    for query in test_queries:
        print(f"\n{'='*60}")
        print(f"Testing search: \"{query}\"")
        print("="*60)
        
        try:
            # Get search results
            results = unified_system.search_with_routing(query, max_results_per_folder=3)
            
            if results:
                print(f"\n📋 Found {len(results)} total results")
                print("\nTop results:")
                
                for i, result in enumerate(results[:5], 1):
                    folder_source = result.get('folder_source', 'Unknown')
                    file_name = result.get('file_info', {}).get('file_name', 'Unknown')
                    relevance = result.get('boosted_relevance', result.get('relevance', 'N/A'))
                    snippet = result.get('snippet', 'No content')[:150] + "..."
                    
                    print(f"\n  {i}. {file_name}")
                    print(f"     From: {folder_source}")
                    print(f"     Relevance: {relevance}")
                    print(f"     Content: {snippet}")
            else:
                print("No results found")
                
        except Exception as e:
            print(f"❌ Error testing search: {e}")

def test_response_formatting():
    """Test the response formatting system"""
    print("\n\n📝 Testing Response Formatting")
    print("=" * 50)
    
    # Create unified system instance
    unified_system = UnifiedRAGSystem()
    
    if not unified_system.indexed_folders:
        print("❌ No indexed folders found. Please index some folders first.")
        return
    
    print("Initializing RAG systems...")
    unified_system.initialize_rag_systems()
    
    # Test a complete query flow
    test_query = "employee handbook"
    print(f"Testing complete query flow: \"{test_query}\"")
    
    try:
        response = unified_system.unified_query(test_query)
        print("\n📄 Formatted Response:")
        print("-" * 40)
        print(response)
        
    except Exception as e:
        print(f"❌ Error testing response formatting: {e}")

def main():
    """Run all tests"""
    print("🧪 UNIFIED RAG SYSTEM TESTS")
    print("=" * 80)
    
    try:
        test_intent_analysis()
        test_unified_search()
        test_response_formatting()
        
        print("\n\n✅ All tests completed!")
        print("🚀 Ready to use the unified system!")
        
    except Exception as e:
        print(f"\n❌ Test suite failed: {e}")

if __name__ == "__main__":
    main()
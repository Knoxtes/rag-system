"""
Test script for multi-document synthesis capabilities.
Tests the new multi-query generation and cross-encoder fusion features.
"""

import sys
from rag_system import EnhancedRAGSystem, _get_system_prompt
from auth import authenticate_google_drive
from config import (
    ENABLE_MULTI_QUERY, 
    ENABLE_CROSS_ENCODER_FUSION,
    SYNTHESIS_CONTEXT_WINDOW,
    MIN_SOURCES_FOR_SYNTHESIS
)

def print_header(text):
    """Print a formatted header."""
    print("\n" + "=" * 80)
    print(f"  {text}")
    print("=" * 80)

def test_synthesis_detection():
    """Test the synthesis query detection logic."""
    print_header("TEST 1: Synthesis Query Detection")
    
    # Create a minimal RAG system instance just for testing
    drive_service = authenticate_google_drive()
    rag = EnhancedRAGSystem(drive_service, "folder_test")
    
    test_queries = [
        ("Summarize Q1, Q2, and Q3 reports", True),
        ("Compare Elmira and Mansfield markets", True),
        ("List all packages in 2025", True),
        ("What are the total sales?", False),
        ("Explain the January projections", False),
        ("Summarize the annual report", True),
        ("Compare all regions", True),
        ("What is the market share?", False)
    ]
    
    print("\nQuery Detection Results:")
    for query, expected in test_queries:
        is_synthesis = rag._is_synthesis_query(query)
        status = "✅ PASS" if is_synthesis == expected else "❌ FAIL"
        print(f"  {status}: '{query}' → {'Synthesis' if is_synthesis else 'Regular'}")
    
    print("\n✅ Synthesis detection test complete")

def test_multi_query_generation():
    """Test the multi-query generation for synthesis tasks."""
    print_header("TEST 2: Multi-Query Generation")
    
    drive_service = authenticate_google_drive()
    rag = EnhancedRAGSystem(drive_service, "folder_test")
    
    test_queries = [
        "Summarize Q1, Q2, and Q3 financial reports",
        "Compare Elmira and Mansfield market performance",
        "List all packages available in 2025",
        "What are the total sales for January, February, and March?"
    ]
    
    for query in test_queries:
        print(f"\n📝 Original Query: '{query}'")
        generated_queries = rag._generate_multi_queries(query)
        print(f"   Generated {len(generated_queries)} variations:")
        for i, q in enumerate(generated_queries, 1):
            print(f"   {i}. {q}")
    
    print("\n✅ Multi-query generation test complete")

def test_config_values():
    """Test that synthesis config values are set correctly."""
    print_header("TEST 3: Configuration Values")
    
    configs = [
        ("ENABLE_MULTI_QUERY", ENABLE_MULTI_QUERY, True),
        ("ENABLE_CROSS_ENCODER_FUSION", ENABLE_CROSS_ENCODER_FUSION, True),
        ("SYNTHESIS_CONTEXT_WINDOW", SYNTHESIS_CONTEXT_WINDOW, 20000),
        ("MIN_SOURCES_FOR_SYNTHESIS", MIN_SOURCES_FOR_SYNTHESIS, 3)
    ]
    
    print("\nConfiguration Status:")
    all_good = True
    for name, value, expected in configs:
        match = "✅" if value == expected else "❌"
        print(f"  {match} {name}: {value} (expected: {expected})")
        if value != expected:
            all_good = False
    
    if all_good:
        print("\n✅ All synthesis configurations are correct")
    else:
        print("\n❌ Some configurations need adjustment")

def test_system_prompt():
    """Test that system prompt includes synthesis instructions."""
    print_header("TEST 4: System Prompt Synthesis Instructions")
    
    prompt = _get_system_prompt()
    
    required_keywords = [
        "SYNTHESIS",
        "multi-document",
        "USE ALL OF THEM",
        "Synthesize across sources",
        "LARGER context windows"
    ]
    
    print("\nChecking for synthesis-related instructions:")
    all_found = True
    for keyword in required_keywords:
        found = keyword.lower() in prompt.lower()
        status = "✅" if found else "❌"
        print(f"  {status} '{keyword}' → {'Found' if found else 'Missing'}")
        if not found:
            all_found = False
    
    if all_found:
        print("\n✅ System prompt contains all synthesis instructions")
    else:
        print("\n❌ System prompt missing some synthesis instructions")

def run_all_tests():
    """Run all synthesis tests."""
    print_header("MULTI-DOCUMENT SYNTHESIS TEST SUITE")
    
    try:
        test_config_values()
        test_system_prompt()
        test_synthesis_detection()
        test_multi_query_generation()
        
        print_header("ALL TESTS COMPLETE")
        print("\n✨ Synthesis improvements are ready for testing!")
        print("\nNext Steps:")
        print("  1. Run the main agent with synthesis queries")
        print("  2. Try: 'Summarize Elmira, Mansfield, and Bowling Green 2025 reports'")
        print("  3. Try: 'Compare Q1 and Q2 sales projections across all markets'")
        print("  4. Monitor console output for multi-query messages")
        
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True

if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)

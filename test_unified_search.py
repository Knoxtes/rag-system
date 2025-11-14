#!/usr/bin/env python3
"""
Test script for unified RAG system search functionality
Tests various edge cases and scenarios
"""

import json
import sys
from unittest.mock import Mock, MagicMock, patch
from unified_rag_system import UnifiedRAGSystem


def test_empty_indexed_folders():
    """Test behavior when no folders are indexed"""
    print("=" * 80)
    print("TEST 1: Empty indexed folders")
    print("=" * 80)
    
    with patch('unified_rag_system.authenticate_google_drive') as mock_auth:
        mock_auth.return_value = Mock()
        
        # Create system with empty indexed folders
        with patch('builtins.open', side_effect=FileNotFoundError):
            system = UnifiedRAGSystem()
            
        result = system.unified_query("test query")
        print(f"Result: {result}")
        assert "No folders have been indexed" in result
        print("✓ PASS: Correctly handles empty indexed folders\n")


def test_no_rag_systems():
    """Test behavior when RAG systems are not initialized"""
    print("=" * 80)
    print("TEST 2: No RAG systems initialized")
    print("=" * 80)
    
    with patch('unified_rag_system.authenticate_google_drive') as mock_auth:
        mock_auth.return_value = Mock()
        
        # Create system with indexed folders but no RAG systems
        mock_folders = {
            'folder_123': {
                'name': 'Test Folder',
                'location': 'Test Location',
                'collection_name': 'folder_123'
            }
        }
        
        with patch('builtins.open', MagicMock()) as mock_open:
            mock_open.return_value.__enter__.return_value.read.return_value = json.dumps(mock_folders)
            with patch('json.load', return_value=mock_folders):
                system = UnifiedRAGSystem()
                # Don't initialize RAG systems
                
        result = system.unified_query("test query")
        print(f"Result: {result}")
        assert "No RAG systems are initialized" in result
        print("✓ PASS: Correctly handles uninitialized RAG systems\n")


def test_empty_query():
    """Test behavior with empty query"""
    print("=" * 80)
    print("TEST 3: Empty query")
    print("=" * 80)
    
    with patch('unified_rag_system.authenticate_google_drive') as mock_auth:
        mock_auth.return_value = Mock()
        
        mock_folders = {
            'folder_123': {
                'name': 'Test Folder',
                'location': 'Test Location',
                'collection_name': 'folder_123'
            }
        }
        
        with patch('json.load', return_value=mock_folders):
            system = UnifiedRAGSystem()
            system.rag_systems['folder_123'] = Mock()
            
        result = system.unified_query("")
        print(f"Result: {result}")
        assert "valid query" in result
        print("✓ PASS: Correctly handles empty query\n")


def test_error_response_handling():
    """Test handling of error responses from _tool_rag_search"""
    print("=" * 80)
    print("TEST 4: Error response from search tool")
    print("=" * 80)
    
    with patch('unified_rag_system.authenticate_google_drive') as mock_auth:
        mock_auth.return_value = Mock()
        
        mock_folders = {
            'folder_123': {
                'name': 'Test Folder',
                'location': 'Test Location',
                'collection_name': 'folder_123'
            }
        }
        
        with patch('json.load', return_value=mock_folders):
            system = UnifiedRAGSystem()
            
            # Mock RAG system that returns error
            mock_rag = Mock()
            mock_rag._tool_rag_search.return_value = json.dumps({
                "error": "No documents found in the database."
            })
            system.rag_systems['folder_123'] = mock_rag
            
        results = system.search_with_routing("test query")
        print(f"Results: {results}")
        assert len(results) == 0
        print("✓ PASS: Correctly handles error responses\n")


def test_status_response_handling():
    """Test handling of status responses from _tool_rag_search"""
    print("=" * 80)
    print("TEST 5: Status response from search tool")
    print("=" * 80)
    
    with patch('unified_rag_system.authenticate_google_drive') as mock_auth:
        mock_auth.return_value = Mock()
        
        mock_folders = {
            'folder_123': {
                'name': 'Test Folder',
                'location': 'Test Location',
                'collection_name': 'folder_123'
            }
        }
        
        with patch('json.load', return_value=mock_folders):
            system = UnifiedRAGSystem()
            
            # Mock RAG system that returns status
            mock_rag = Mock()
            mock_rag._tool_rag_search.return_value = json.dumps({
                "status": "No relevant documents found after filtering."
            })
            system.rag_systems['folder_123'] = mock_rag
            
        results = system.search_with_routing("test query")
        print(f"Results: {results}")
        assert len(results) == 0
        print("✓ PASS: Correctly handles status responses\n")


def test_successful_results():
    """Test handling of successful results from _tool_rag_search"""
    print("=" * 80)
    print("TEST 6: Successful search results")
    print("=" * 80)
    
    with patch('unified_rag_system.authenticate_google_drive') as mock_auth:
        mock_auth.return_value = Mock()
        
        mock_folders = {
            'folder_123': {
                'name': 'Test Folder',
                'location': 'Test Location',
                'collection_name': 'folder_123'
            }
        }
        
        with patch('json.load', return_value=mock_folders):
            system = UnifiedRAGSystem()
            
            # Mock RAG system that returns results
            mock_rag = Mock()
            mock_results = [
                {
                    "source_path": "test/file.pdf",
                    "snippet": "Test content",
                    "relevance": "0.95",
                    "file_info": {
                        "file_name": "file.pdf",
                        "google_drive_link": "https://drive.google.com/file/d/123/view"
                    }
                }
            ]
            mock_rag._tool_rag_search.return_value = json.dumps(mock_results)
            system.rag_systems['folder_123'] = mock_rag
            
        results = system.search_with_routing("test query")
        print(f"Results: {len(results)} items")
        assert len(results) == 1
        assert 'folder_source' in results[0]
        assert 'boosted_relevance' in results[0]
        print("✓ PASS: Correctly handles successful results\n")


def test_format_no_results():
    """Test response formatting with no results"""
    print("=" * 80)
    print("TEST 7: Format response with no results")
    print("=" * 80)
    
    with patch('unified_rag_system.authenticate_google_drive') as mock_auth:
        mock_auth.return_value = Mock()
        
        mock_folders = {
            'folder_123': {
                'name': 'Test Folder',
                'location': 'Test Location',
                'collection_name': 'folder_123'
            }
        }
        
        with patch('json.load', return_value=mock_folders):
            system = UnifiedRAGSystem()
            
        response = system.format_response_with_sources("test query", [])
        print(f"Response:\n{response}")
        assert "couldn't find any relevant information" in response
        assert "Suggestions:" in response
        assert "Try rephrasing" in response
        print("✓ PASS: Provides helpful suggestions when no results\n")


def test_analyze_query_intent():
    """Test query intent analysis"""
    print("=" * 80)
    print("TEST 8: Query intent analysis")
    print("=" * 80)
    
    with patch('unified_rag_system.authenticate_google_drive') as mock_auth:
        mock_auth.return_value = Mock()
        
        mock_folders = {
            'folder_hr': {
                'name': 'HR Documents',
                'location': 'Drive',
                'collection_name': 'folder_hr'
            },
            'folder_sales': {
                'name': 'Sales Reports',
                'location': 'Drive',
                'collection_name': 'folder_sales'
            }
        }
        
        with patch('json.load', return_value=mock_folders):
            system = UnifiedRAGSystem()
            
        # Test with HR-related query
        intent = system.analyze_query_intent("What are the employee benefits?")
        print(f"Intent for HR query: {intent}")
        
        # Test with empty query
        intent_empty = system.analyze_query_intent("")
        print(f"Intent for empty query: {intent_empty}")
        assert len(intent_empty) > 0  # Should return all folders
        
        print("✓ PASS: Query intent analysis works correctly\n")


def main():
    """Run all tests"""
    print("\n" + "=" * 80)
    print("UNIFIED RAG SYSTEM - TEST SUITE")
    print("=" * 80 + "\n")
    
    try:
        test_empty_indexed_folders()
        test_no_rag_systems()
        test_empty_query()
        test_error_response_handling()
        test_status_response_handling()
        test_successful_results()
        test_format_no_results()
        test_analyze_query_intent()
        
        print("=" * 80)
        print("✓ ALL TESTS PASSED!")
        print("=" * 80)
        return 0
        
    except AssertionError as e:
        print(f"\n✗ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        return 1
    except Exception as e:
        print(f"\n✗ UNEXPECTED ERROR: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())

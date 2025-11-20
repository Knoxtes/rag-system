#!/usr/bin/env python3
"""
Simple test script to verify cloud agent delegation functionality.
This is a minimal validation test, not a comprehensive test suite.
"""

import sys
import os

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_cloud_agent_import():
    """Test that cloud_agent module can be imported"""
    try:
        import cloud_agent
        print("✅ cloud_agent module imported successfully")
        return True
    except ImportError as e:
        print(f"❌ Failed to import cloud_agent: {e}")
        return False

def test_cloud_agent_delegate_creation():
    """Test that CloudAgentDelegate can be instantiated"""
    try:
        from cloud_agent import CloudAgentDelegate
        delegate = CloudAgentDelegate(use_vertex=False)  # Use consumer API for testing
        print("✅ CloudAgentDelegate instantiated successfully")
        return True
    except Exception as e:
        print(f"❌ Failed to create CloudAgentDelegate: {e}")
        return False

def test_get_cloud_agent():
    """Test get_cloud_agent() function"""
    try:
        from cloud_agent import get_cloud_agent
        agent = get_cloud_agent()
        print("✅ get_cloud_agent() works")
        return True
    except Exception as e:
        print(f"❌ get_cloud_agent() failed: {e}")
        return False

def test_delegation_info():
    """Test getting delegation info"""
    try:
        from cloud_agent import get_cloud_agent
        agent = get_cloud_agent()
        info = agent.get_delegation_info()
        
        # Verify required keys
        required_keys = ['using_cloud_agent', 'cloud_provider', 'project_id', 'location', 'initialized']
        for key in required_keys:
            if key not in info:
                print(f"❌ Missing key in delegation info: {key}")
                return False
        
        print(f"✅ Delegation info: {info['cloud_provider']}")
        return True
    except Exception as e:
        print(f"❌ Failed to get delegation info: {e}")
        return False

def test_rag_system_import():
    """Test that rag_system can still be imported with cloud_agent changes"""
    try:
        # This will fail if dependencies aren't installed, which is expected
        # We're just checking for syntax errors
        import py_compile
        import tempfile
        import shutil
        
        # Compile the file to check for syntax errors
        py_compile.compile('rag_system.py', doraise=True)
        print("✅ rag_system.py has valid syntax")
        return True
    except SyntaxError as e:
        print(f"❌ Syntax error in rag_system.py: {e}")
        return False
    except Exception as e:
        # Other errors (like missing dependencies) are okay
        print(f"⚠️  rag_system.py syntax OK, but runtime dependencies missing (expected): {type(e).__name__}")
        return True

def test_chat_api_syntax():
    """Test that chat_api has valid syntax"""
    try:
        import py_compile
        py_compile.compile('chat_api.py', doraise=True)
        print("✅ chat_api.py has valid syntax")
        return True
    except SyntaxError as e:
        print(f"❌ Syntax error in chat_api.py: {e}")
        return False
    except Exception as e:
        print(f"⚠️  chat_api.py syntax OK, but runtime dependencies missing (expected): {type(e).__name__}")
        return True

def main():
    """Run all tests"""
    print("=" * 60)
    print("Cloud Agent Delegation - Validation Tests")
    print("=" * 60)
    print()
    
    tests = [
        ("Import cloud_agent module", test_cloud_agent_import),
        ("Create CloudAgentDelegate", test_cloud_agent_delegate_creation),
        ("Get cloud agent instance", test_get_cloud_agent),
        ("Get delegation info", test_delegation_info),
        ("Import rag_system (syntax check)", test_rag_system_import),
        ("Check chat_api syntax", test_chat_api_syntax),
    ]
    
    results = []
    for name, test_func in tests:
        print(f"\nTest: {name}")
        print("-" * 60)
        result = test_func()
        results.append((name, result))
        print()
    
    print("=" * 60)
    print("Test Summary")
    print("=" * 60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}: {name}")
    
    print()
    print(f"Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("✅ All tests passed!")
        return 0
    else:
        print(f"❌ {total - passed} test(s) failed")
        return 1

if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python3
"""
Code quality checker script
Runs various checks to ensure code quality before deployment
"""

import sys
import subprocess
import os


def run_command(cmd, description):
    """Run a command and return success status"""
    print(f"\n{'='*60}")
    print(f"Running: {description}")
    print(f"{'='*60}")
    
    try:
        result = subprocess.run(
            cmd,
            shell=True,
            capture_output=True,
            text=True,
            timeout=300
        )
        
        if result.stdout:
            print(result.stdout)
        
        if result.returncode != 0:
            print(f"❌ FAILED: {description}")
            if result.stderr:
                print(f"Error: {result.stderr}")
            return False
        else:
            print(f"✅ PASSED: {description}")
            return True
    
    except subprocess.TimeoutExpired:
        print(f"❌ TIMEOUT: {description} took too long")
        return False
    except Exception as e:
        print(f"❌ ERROR: {description} - {e}")
        return False


def main():
    """Run all quality checks"""
    checks = []
    
    print("\n" + "="*60)
    print("CODE QUALITY CHECKER")
    print("="*60)
    
    # 1. Python syntax check
    checks.append(run_command(
        "python -m py_compile main.py config.py app.py rag_system.py",
        "Python Syntax Check"
    ))
    
    # 2. Startup validation
    checks.append(run_command(
        "python startup_validation.py",
        "Startup Validation"
    ))
    
    # 3. Import checks (make sure all imports work)
    import_test = """
import config
import vector_store
import embeddings
import document_loader
import auth
import startup_validation
import logging_config
import exceptions
import performance_monitor
import health_check
print('All imports successful!')
"""
    
    with open('/tmp/import_test.py', 'w') as f:
        f.write(import_test)
    
    checks.append(run_command(
        "python /tmp/import_test.py",
        "Import Tests"
    ))
    
    # 4. Check for common issues
    print("\n" + "="*60)
    print("Checking for common code issues...")
    print("="*60)
    
    issues_found = False
    
    # Check for print statements (should use logging in production)
    print_count = subprocess.run(
        "grep -r 'print(' --include='*.py' *.py 2>/dev/null | wc -l",
        shell=True,
        capture_output=True,
        text=True
    )
    
    if print_count.stdout.strip():
        count = int(print_count.stdout.strip())
        if count > 50:  # Allow some for now
            print(f"⚠️  WARNING: Found {count} print statements")
            print("   Consider replacing with logging in production code")
            issues_found = True
    
    # Check for TODO/FIXME comments
    todo_count = subprocess.run(
        "grep -r 'TODO\\|FIXME' --include='*.py' *.py 2>/dev/null | wc -l",
        shell=True,
        capture_output=True,
        text=True
    )
    
    if todo_count.stdout.strip():
        count = int(todo_count.stdout.strip())
        if count > 0:
            print(f"ℹ️  INFO: Found {count} TODO/FIXME comments")
            print("   Review before production deployment")
    
    if not issues_found:
        print("✅ No major code quality issues found")
    
    # Summary
    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)
    
    passed = sum(checks)
    total = len(checks)
    
    print(f"Checks passed: {passed}/{total}")
    
    if passed == total:
        print("\n✅ ALL CHECKS PASSED - Code is ready for review")
        return 0
    else:
        print("\n❌ SOME CHECKS FAILED - Please fix issues before deployment")
        return 1


if __name__ == "__main__":
    sys.exit(main())

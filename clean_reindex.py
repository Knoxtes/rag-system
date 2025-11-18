"""
Clean Re-indexing Script
Ensures fresh code is used (no cached bytecode)
"""

import os
import sys
import subprocess

print("="*80)
print("  CLEAN RE-INDEXING SCRIPT")
print("="*80)

# Step 1: Clear Python cache
print("\n📦 Step 1: Clearing Python cache...")
try:
    if os.path.exists('__pycache__'):
        import shutil
        shutil.rmtree('__pycache__')
        print("   ✓ Cleared __pycache__")
    else:
        print("   ✓ No __pycache__ to clear")
except Exception as e:
    print(f"   ⚠ Could not clear cache: {e}")

# Step 2: Check if database is locked
print("\n🔒 Step 2: Checking database...")
db_path = './chroma_db'
if os.path.exists(db_path):
    print(f"   ⚠ Database exists at: {db_path}")
    print(f"   📝 The folder_indexer will handle cleanup")
else:
    print("   ✓ No existing database (fresh start)")

# Step 3: Verify CSV chunking code is present
print("\n🔍 Step 3: Verifying CSV chunking code...")
try:
    with open('document_loader.py', 'r', encoding='utf-8') as f:
        content = f.read()
        if 'CSV CHUNK' in content:
            print("   ✓ CSV chunking code found in document_loader.py")
        else:
            print("   ❌ CSV chunking code NOT found!")
            sys.exit(1)
    
    with open('folder_indexer.py', 'r', encoding='utf-8') as f:
        content = f.read()
        if "'is_csv': is_csv" in content:
            print("   ✓ CSV flag code found in folder_indexer.py")
        else:
            print("   ❌ CSV flag code NOT found!")
            sys.exit(1)
            
except Exception as e:
    print(f"   ❌ Error checking files: {e}")
    sys.exit(1)

# Step 4: Launch folder indexer with fresh Python instance
print("\n🚀 Step 4: Launching folder indexer...")
print("\n" + "="*80)
print("  IMPORTANT INSTRUCTIONS:")
print("="*80)
print("  1. Select your SHARED DRIVE (e.g., '7MM Resources')")
print("  2. Select the folder containing CSVs")
print("  3. Choose: '2. Full Re-indexing'")
print("  4. Wait for completion")
print("="*80)

input("\nPress Enter to start the folder indexer...")

# Start fresh Python process (no cached modules)
result = subprocess.run(
    [sys.executable, '-B', 'folder_indexer.py'],  # -B = don't write .pyc files
    cwd=os.getcwd()
)

if result.returncode == 0:
    print("\n" + "="*80)
    print("  ✅ INDEXING COMPLETE!")
    print("="*80)
    print("\n📋 Next steps:")
    print("   1. Run: python verify_csv_autofetch.py")
    print("   2. Should see: '✅ ALL TESTS PASSED!'")
    print("   3. Test in chat: 'What is January 2025 Altoona sales?'")
    print("   4. Expected: $450,866.30")
else:
    print("\n❌ Indexing failed or was cancelled")

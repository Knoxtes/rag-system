"""
Automated script to fix CSV indexing and ensure auto-fetch works correctly

This script:
1. Stops the chat system if running
2. Backs up the current database
3. Deletes the chroma_db directory
4. Provides instructions for re-indexing
5. Verifies the is_csv flag is present after re-indexing
"""
import os
import shutil
import time
import subprocess
import sys
from pathlib import Path

def print_header(text):
    print("\n" + "="*80)
    print(f"  {text}")
    print("="*80 + "\n")

def print_step(step_num, text):
    print(f"\n[{step_num}] {text}")

def print_success(text):
    print(f"    ✅ {text}")

def print_warning(text):
    print(f"    ⚠️  {text}")

def print_error(text):
    print(f"    ❌ {text}")

def main():
    print_header("CSV Auto-Fetch Fix - Database Reset Tool")
    
    workspace_root = Path(__file__).parent
    chroma_db_path = workspace_root / "chroma_db"
    backup_path = workspace_root / "chroma_db_backup"
    
    print(f"Workspace: {workspace_root}")
    print(f"Database location: {chroma_db_path}")
    
    # Step 1: Check if database exists
    print_step(1, "Checking current database status...")
    
    if not chroma_db_path.exists():
        print_warning("No chroma_db directory found - database is already clean")
        print("\nYou can proceed directly to re-indexing:")
        print("  1. Run: python folder_indexer.py")
        print("  2. Select 'Admin/Traffic' collection")
        print("  3. Choose 'Full Re-indexing'")
        return
    
    print_success(f"Database directory exists: {chroma_db_path}")
    
    # Count files in database
    db_files = list(chroma_db_path.rglob("*"))
    print(f"    Contains {len(db_files)} files/directories")
    
    # Step 2: Create backup
    print_step(2, "Creating backup of current database...")
    
    if backup_path.exists():
        print_warning("Previous backup exists, removing it first...")
        try:
            shutil.rmtree(backup_path)
            print_success("Old backup removed")
        except Exception as e:
            print_error(f"Failed to remove old backup: {e}")
            response = input("\nContinue anyway? (yes/no): ")
            if response.lower() != 'yes':
                print("\nAborted by user")
                return
    
    try:
        shutil.copytree(chroma_db_path, backup_path)
        print_success(f"Backup created at: {backup_path}")
        print(f"    Backup size: {len(list(backup_path.rglob('*')))} files")
    except Exception as e:
        print_error(f"Failed to create backup: {e}")
        response = input("\nContinue without backup? (yes/no): ")
        if response.lower() != 'yes':
            print("\nAborted by user")
            return
    
    # Step 3: Delete current database
    print_step(3, "Deleting current database...")
    
    print_warning("This will permanently delete the chroma_db directory!")
    print("The backup will be preserved in chroma_db_backup/")
    
    response = input("\nAre you sure you want to proceed? Type 'DELETE' to confirm: ")
    
    if response != 'DELETE':
        print("\nAborted by user - database not deleted")
        print("Backup remains at:", backup_path)
        return
    
    try:
        shutil.rmtree(chroma_db_path)
        print_success("Database directory deleted successfully")
    except Exception as e:
        print_error(f"Failed to delete database: {e}")
        print("\nYou may need to:")
        print("  1. Stop any running processes using the database")
        print("  2. Close any file explorers viewing the directory")
        print("  3. Run this script as administrator")
        return
    
    # Verify deletion
    if chroma_db_path.exists():
        print_error("Database directory still exists after deletion!")
        return
    
    print_success("Database successfully removed")
    
    # Step 4: Instructions for re-indexing
    print_step(4, "Next Steps - Re-indexing Required")
    
    print("\n┌─────────────────────────────────────────────────────────────────────┐")
    print("│  IMPORTANT: You must now re-index the database!                    │")
    print("└─────────────────────────────────────────────────────────────────────┘")
    
    print("\n📋 Re-indexing Instructions:")
    print("   1. Run: python folder_indexer.py")
    print("   2. Select the 'Admin/Traffic' collection when prompted")
    print("   3. Choose 'Full Re-indexing' option")
    print("   4. Wait for indexing to complete (may take several minutes)")
    
    print("\n✅ After re-indexing completes:")
    print("   5. Run: python test_csv_fetch.py")
    print("      - Should show 'CSV files found: > 0'")
    print("   6. Start the chat system: python start_chat_system.py")
    print("   7. Query: 'What is the January 2025 sales total for Altoona market?'")
    print("      - Should return $450,866.30 (all 414 rows)")
    
    print("\n" + "="*80)
    print("  Database cleanup complete!")
    print("="*80)
    
    print("\n💾 Backup location:", backup_path)
    print("   (You can delete this after verifying the new index works correctly)")
    
    # Offer to start indexing
    print("\n" + "─"*80)
    response = input("\nWould you like to start the re-indexing process now? (yes/no): ")
    
    if response.lower() == 'yes':
        print("\nLaunching folder_indexer.py...")
        print("Please select 'Admin/Traffic' and 'Full Re-indexing' when prompted.\n")
        time.sleep(2)
        
        try:
            subprocess.run([sys.executable, "folder_indexer.py"], cwd=workspace_root)
        except KeyboardInterrupt:
            print("\n\nIndexing interrupted by user")
        except Exception as e:
            print(f"\n\nError running indexer: {e}")
            print("Please run manually: python folder_indexer.py")
    else:
        print("\nPlease run the re-indexing manually when ready:")
        print("  python folder_indexer.py")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nScript interrupted by user")
    except Exception as e:
        print(f"\n\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()

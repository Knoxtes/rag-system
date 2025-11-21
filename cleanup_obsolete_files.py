#!/usr/bin/env python3
"""
Cleanup Script - Remove Obsolete Development Files

This script safely removes old utility scripts, test files, and superseded versions
that are no longer needed for production deployment.

SAFE TO RUN: Only removes files that are not imported by the main application.
"""

import os
import shutil
from pathlib import Path

# Files to remove (verified as not imported by production code)
OBSOLETE_FILES = [
    # Old indexer versions (superseded by console_indexer_fixed.py and live_batch_indexer.py)
    "console_indexer.py",
    "batch_indexer.py",
    "batch_index_selected.py",
    "index_all_except_market.py",
    "reindex_with_vertex.py",
    "create_indexed_folders.py",
    
    # Debug/test/utility scripts
    "check_sports.py",
    "check_all_collections.py",
    "cleanup_collections.py",
    "cleanup_only.py",
    "complete_cleanup_reindex.py",
    "get_ids.py",
    "estimate_cost.py",
    "actual_cost_estimate.py",
    "debug_retrieval.py",
    "test_synthesis.py",
    
    # Superseded application files
    "app.py",  # Replaced by chat-app React frontend
    
    # Old/unused configuration
    "main.py",  # Console interface, not needed for web deployment
]

# Documentation files to archive (optional - can consolidate later)
DOCS_TO_ARCHIVE = [
    "FIXES_APPLIED.md",
    "INDEXER_FIXES_APPLIED.md",
    "FULL_INDEXING_GUIDE.md",
    "REINDEX_QUICK_GUIDE.md",
    "SAFE_DATABASE_CLEAR.md",
    "DOCUMENTAI_SETUP.md",
    "VERTEX_AI_MIGRATION.md",
]

# Files to keep for reference but warn about
OPTIONAL_CLEANUP = [
    "answer_log.json",  # Old answer logging, now using answer_logger.py
    "token.pickle",  # OAuth tokens (will regenerate)
]


def safe_remove(filepath):
    """Safely remove a file if it exists"""
    try:
        if os.path.exists(filepath):
            os.remove(filepath)
            return True, f"✓ Removed: {filepath}"
        else:
            return False, f"⊘ Not found: {filepath}"
    except Exception as e:
        return False, f"✗ Error removing {filepath}: {e}"


def archive_docs(base_dir):
    """Move documentation files to archive folder"""
    archive_dir = os.path.join(base_dir, "docs_archive")
    
    if not os.path.exists(archive_dir):
        os.makedirs(archive_dir)
        print(f"\n📁 Created archive directory: {archive_dir}")
    
    archived = []
    for doc in DOCS_TO_ARCHIVE:
        filepath = os.path.join(base_dir, doc)
        if os.path.exists(filepath):
            try:
                shutil.move(filepath, os.path.join(archive_dir, doc))
                archived.append(doc)
            except Exception as e:
                print(f"✗ Error archiving {doc}: {e}")
    
    return archived


def main():
    print("=" * 80)
    print("🧹 RAG SYSTEM CLEANUP SCRIPT")
    print("=" * 80)
    print("\nThis script will remove obsolete development files that are")
    print("no longer needed for production deployment.\n")
    
    # Get project root
    project_root = Path(__file__).parent
    os.chdir(project_root)
    
    # Show what will be removed
    print("📋 Files to be removed:")
    for f in OBSOLETE_FILES:
        status = "✓" if os.path.exists(f) else "⊘"
        print(f"  {status} {f}")
    
    print(f"\n📊 Total: {len(OBSOLETE_FILES)} files")
    print(f"   Existing: {sum(1 for f in OBSOLETE_FILES if os.path.exists(f))}")
    
    # Confirm
    response = input("\n⚠️  Proceed with cleanup? (y/N): ").strip().lower()
    if response not in ['y', 'yes']:
        print("❌ Cleanup cancelled")
        return 0
    
    print("\n🔄 Starting cleanup...")
    
    # Remove obsolete files
    removed = 0
    failed = 0
    
    for filepath in OBSOLETE_FILES:
        success, message = safe_remove(filepath)
        print(f"  {message}")
        if success:
            removed += 1
        elif "Error" in message:
            failed += 1
    
    # Archive documentation
    print("\n📚 Archiving old documentation...")
    archived_docs = archive_docs(project_root)
    if archived_docs:
        print(f"  ✓ Archived {len(archived_docs)} documentation files")
        for doc in archived_docs:
            print(f"    • {doc}")
    else:
        print("  ⊘ No documentation files to archive")
    
    # Summary
    print("\n" + "=" * 80)
    print("📊 CLEANUP SUMMARY")
    print("=" * 80)
    print(f"✅ Removed: {removed} files")
    if failed > 0:
        print(f"❌ Failed: {failed} files")
    if archived_docs:
        print(f"📁 Archived: {len(archived_docs)} documentation files")
    
    # Show optional cleanup suggestions
    if any(os.path.exists(f) for f in OPTIONAL_CLEANUP):
        print("\n💡 Optional cleanup (manual):")
        for f in OPTIONAL_CLEANUP:
            if os.path.exists(f):
                print(f"  • {f}")
    
    print("\n✅ Cleanup complete!")
    print("\n🚀 Your system is now optimized for production deployment.")
    print("=" * 80)
    
    return 0


if __name__ == "__main__":
    try:
        exit(main())
    except KeyboardInterrupt:
        print("\n\n❌ Cleanup interrupted by user")
        exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        exit(1)

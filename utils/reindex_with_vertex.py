"""
Complete Database Reindexing with Vertex AI Embeddings

This script:
1. Backs up the current ChromaDB database
2. Clears all existing collections
3. Re-indexes all documents using Vertex AI 768-dimensional embeddings

Usage:
    python reindex_with_vertex.py [--backup-only] [--clear-only]

Options:
    --backup-only: Only create backup, don't clear or reindex
    --clear-only: Only backup and clear database, don't reindex
    --skip-backup: Skip backup step (dangerous!)
"""

import os
import sys
import shutil
import argparse
from datetime import datetime
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def backup_database(backup_dir='chroma_db_backups'):
    """Backup the current ChromaDB database"""
    print("\n" + "="*60)
    print("STEP 1: Backing Up Database")
    print("="*60)
    
    chroma_path = Path('./chroma_db')
    
    if not chroma_path.exists():
        print("⚠️  No existing database found at ./chroma_db")
        return None
    
    # Create backup directory
    backup_root = Path(backup_dir)
    backup_root.mkdir(exist_ok=True)
    
    # Create timestamped backup folder
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_path = backup_root / f"backup_{timestamp}"
    
    print(f"📦 Creating backup at: {backup_path}")
    
    try:
        shutil.copytree(chroma_path, backup_path)
        
        # Get size
        total_size = sum(f.stat().st_size for f in backup_path.rglob('*') if f.is_file())
        size_mb = total_size / (1024 * 1024)
        
        print(f"✅ Backup complete! Size: {size_mb:.2f} MB")
        print(f"📁 Backup location: {backup_path.absolute()}")
        
        return backup_path
    
    except Exception as e:
        print(f"❌ Backup failed: {e}")
        return None


def clear_database():
    """Clear the ChromaDB database"""
    print("\n" + "="*60)
    print("STEP 2: Clearing Database")
    print("="*60)
    
    chroma_path = Path('./chroma_db')
    
    if not chroma_path.exists():
        print("⚠️  Database directory doesn't exist, nothing to clear")
        return True
    
    print(f"🗑️  Deleting: {chroma_path.absolute()}")
    
    try:
        shutil.rmtree(chroma_path)
        print("✅ Database cleared successfully!")
        
        # Recreate empty directory
        chroma_path.mkdir()
        print("📁 Created empty database directory")
        
        return True
    
    except Exception as e:
        print(f"❌ Failed to clear database: {e}")
        return False


def verify_vertex_config():
    """Verify Vertex AI is properly configured"""
    print("\n" + "="*60)
    print("STEP 3: Verifying Vertex AI Configuration")
    print("="*60)
    
    try:
        import config
        
        if not hasattr(config, 'USE_VERTEX_EMBEDDINGS'):
            print("❌ USE_VERTEX_EMBEDDINGS not found in config.py")
            return False
        
        if not config.USE_VERTEX_EMBEDDINGS:
            print("⚠️  USE_VERTEX_EMBEDDINGS is set to False!")
            print("    Please set USE_VERTEX_EMBEDDINGS = True in config.py")
            return False
        
        print("✅ USE_VERTEX_EMBEDDINGS = True")
        
        # Try to import vertex embeddings
        try:
            import vertex_embeddings
            print("✅ vertex_embeddings.py module found")
        except ImportError:
            print("❌ vertex_embeddings.py not found!")
            return False
        
        # Check Google Cloud credentials
        if os.path.exists('credentials.json'):
            print("✅ credentials.json found")
        else:
            print("⚠️  credentials.json not found - may cause issues")
        
        print("\n✅ Vertex AI configuration looks good!")
        return True
    
    except Exception as e:
        print(f"❌ Configuration check failed: {e}")
        return False


def reindex_collections():
    """Re-index all collections with Vertex AI embeddings"""
    print("\n" + "="*60)
    print("STEP 4: Re-indexing with Vertex AI Embeddings")
    print("="*60)
    
    print("\n⚠️  IMPORTANT:")
    print("   The actual re-indexing happens when you restart the server")
    print("   and access each collection. The RAG system will automatically")
    print("   create collections with the new 768-dimensional embeddings.")
    
    print("\n📋 To complete the reindexing:")
    print("   1. Restart your server: npm start")
    print("   2. Access the web interface")
    print("   3. Click on each collection to trigger indexing")
    print("   4. Or use the admin panel to re-index all collections")
    
    print("\n💡 Collections will be created with:")
    print("   • Embedding Model: Vertex AI text-embedding-004")
    print("   • Dimensions: 768 (vs old 384)")
    print("   • Provider: Google Cloud Vertex AI")
    
    return True


def show_collections_info():
    """Show information about collections that will be reindexed"""
    print("\n" + "="*60)
    print("Collection Information")
    print("="*60)
    
    try:
        import config
        
        if hasattr(config, 'COLLECTIONS') and config.COLLECTIONS:
            print(f"\n📚 Found {len(config.COLLECTIONS)} collections to reindex:")
            for i, coll in enumerate(config.COLLECTIONS, 1):
                name = coll.get('name', 'Unknown')
                folder_id = coll.get('folder_id', 'Unknown')
                print(f"   {i}. {name}")
                print(f"      Folder ID: {folder_id}")
        else:
            print("\n⚠️  No collections found in config.py")
            print("   Collections will be auto-discovered on server restart")
    
    except Exception as e:
        print(f"\n⚠️  Could not load collections info: {e}")


def main():
    parser = argparse.ArgumentParser(
        description='Reindex ChromaDB with Vertex AI embeddings',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python reindex_with_vertex.py                 # Full reindex
  python reindex_with_vertex.py --backup-only   # Only backup
  python reindex_with_vertex.py --clear-only    # Backup and clear only
  python reindex_with_vertex.py --skip-backup   # Dangerous! Skip backup
        """
    )
    
    parser.add_argument('--backup-only', action='store_true',
                      help='Only create backup, do not clear or reindex')
    parser.add_argument('--clear-only', action='store_true',
                      help='Backup and clear database only, do not reindex')
    parser.add_argument('--skip-backup', action='store_true',
                      help='Skip backup step (DANGEROUS!)')
    
    args = parser.parse_args()
    
    print("\n" + "="*60)
    print("🔄 ChromaDB Vertex AI Reindexing Tool")
    print("="*60)
    print(f"📅 Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Show what will happen
    if args.backup_only:
        print("🎯 Mode: BACKUP ONLY")
    elif args.clear_only:
        print("🎯 Mode: BACKUP + CLEAR")
    elif args.skip_backup:
        print("🎯 Mode: FULL REINDEX (NO BACKUP) ⚠️")
    else:
        print("🎯 Mode: FULL REINDEX (with backup)")
    
    # Confirm
    print("\n⚠️  WARNING: This will clear your existing database!")
    if not args.skip_backup:
        print("   (A backup will be created first)")
    
    response = input("\nContinue? (yes/no): ").strip().lower()
    if response not in ['yes', 'y']:
        print("\n❌ Cancelled by user")
        return 1
    
    # Step 1: Backup
    if not args.skip_backup:
        backup_path = backup_database()
        if not backup_path:
            print("\n❌ Backup failed! Aborting for safety.")
            return 1
    else:
        print("\n⚠️  SKIPPING BACKUP (as requested)")
    
    if args.backup_only:
        print("\n✅ Backup complete! Exiting (backup-only mode)")
        return 0
    
    # Step 2: Clear database
    if not clear_database():
        print("\n❌ Failed to clear database! Aborting.")
        return 1
    
    if args.clear_only:
        print("\n✅ Backup and clear complete! Exiting (clear-only mode)")
        return 0
    
    # Step 3: Verify Vertex AI config
    if not verify_vertex_config():
        print("\n❌ Vertex AI configuration issues detected!")
        print("   Please fix configuration before proceeding.")
        return 1
    
    # Step 4: Instructions for reindexing
    reindex_collections()
    
    # Show collection info
    show_collections_info()
    
    # Final instructions
    print("\n" + "="*60)
    print("✅ DATABASE CLEARED - READY FOR VERTEX AI REINDEXING")
    print("="*60)
    
    print("\n📋 Next Steps:")
    print("   1. Verify config.py has USE_VERTEX_EMBEDDINGS = True")
    print("   2. Stop your current server (Ctrl+C)")
    print("   3. Restart server: npm start")
    print("   4. Wait for collections to initialize with Vertex AI")
    print("   5. Test queries to verify 768-dimensional embeddings work")
    
    print("\n💰 Cost Monitoring:")
    print("   • Google Cloud Console → Vertex AI → Usage")
    print("   • Expected cost: ~$1-3/month for typical usage")
    
    print("\n🔄 Rollback (if needed):")
    if not args.skip_backup:
        print(f"   1. Stop server")
        print(f"   2. Delete: ./chroma_db")
        print(f"   3. Restore: cp -r {backup_path} ./chroma_db")
        print(f"   4. Set USE_VERTEX_EMBEDDINGS = False in config.py")
        print(f"   5. Restart server")
    else:
        print("   ⚠️  No backup available - cannot rollback!")
    
    print("\n" + "="*60)
    print("✨ Ready to go!")
    print("="*60 + "\n")
    
    return 0


if __name__ == '__main__':
    try:
        exit_code = main()
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n\n❌ Interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

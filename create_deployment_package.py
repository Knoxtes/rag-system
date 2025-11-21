#!/usr/bin/env python3
"""
Create a clean deployment package for Plesk upload via ZIP
Excludes unnecessary files while keeping database and credentials
"""

import os
import zipfile
from pathlib import Path

def should_exclude(file_path):
    """Check if file should be excluded from package"""
    exclude_patterns = [
        '__pycache__',
        '.git',
        'node_modules',
        '.pytest_cache',
        '.vscode',
        '.idea',
        '.pyc',
        '.log',
        '.DS_Store',
        'Thumbs.db',
        '.swp',
        '.swo',
        'test_cache.py',
        'test_optimizations.py',
        'chroma_db_backups',
        'docs_archive',
        'embedding_cache',
        'csv_cache',
        'logs/',
        'deployment_package',
        'rag-system-plesk-deployment.zip',
    ]
    
    path_str = str(file_path)
    return any(pattern in path_str for pattern in exclude_patterns)

def create_deployment_package():
    """Create a ZIP file directly with only production-necessary files"""
    
    print("📦 Creating Plesk deployment ZIP package...")
    print("=" * 60)
    
    zip_filename = 'rag-system-plesk-deployment.zip'
    
    # Remove old ZIP if exists
    if Path(zip_filename).exists():
        os.remove(zip_filename)
        print(f"  🗑️  Removed old {zip_filename}")
    
    copied_files = []
    skipped_files = []
    
    # Create ZIP file directly
    with zipfile.ZipFile(zip_filename, 'w', zipfile.ZIP_DEFLATED) as zipf:
        source_dir = Path('.')
        
        for item in source_dir.rglob('*'):
            if item.is_file():
                if should_exclude(item):
                    skipped_files.append(str(item))
                else:
                    # Add to ZIP
                    arcname = item.relative_to(source_dir)
                    zipf.write(item, arcname)
                    copied_files.append(str(arcname))
    
    # Calculate size
    size_mb = os.path.getsize(zip_filename) / (1024 * 1024)
    
    print("\n" + "=" * 60)
    print(f"✅ Deployment package created: {zip_filename}")
    print(f"📦 Size: {size_mb:.2f} MB")
    print(f"📄 Files included: {len(copied_files)}")
    print(f"🚫 Files excluded: {len(skipped_files)}")
    
    print("\n📋 Package includes:")
    print("   ✓ All Python backend files")
    print("   ✓ Node.js proxy server")
    print("   ✓ React frontend build (chat-app/build/)")
    print("   ✓ Your credentials.json ⭐")
    print("   ✓ Your .env configuration ⭐")
    print("   ✓ Your ChromaDB database ⭐")
    print("   ✓ Your token.pickle ⭐")
    print("   ✓ Your indexed_folders.json ⭐")
    print("   ✓ All documentation")
    
    print("\n🚀 Upload to Plesk:")
    print("   1. Login to Plesk → File Manager")
    print("   2. Navigate to your app directory (e.g., /httpdocs)")
    print("   3. Click 'Upload' → Select rag-system-plesk-deployment.zip")
    print("   4. After upload, right-click ZIP → Extract")
    print("   5. SSH into server and run:")
    print("      cd /path/to/app")
    print("      npm install")
    print("      pip install -r requirements-production.txt")
    print("      npm start")
    
    print("\n💡 Your database and credentials are preserved!")
    print("   No need to re-authenticate or re-index documents")
    print("=" * 60)

if __name__ == '__main__':
    create_deployment_package()
        if item.is_file():
            # Check if should be excluded
            should_exclude = False
            rel_path = item.relative_to(source_dir)
            
            for pattern in exclude_patterns:
                if pattern.startswith('*'):
                    # File extension pattern
                    if str(rel_path).endswith(pattern[1:]):
                        should_exclude = True
                        break
                elif pattern in str(rel_path):
                    should_exclude = True
                    break
            
            if not should_exclude:
                # Copy to output directory
                dest_path = output_dir / rel_path
                dest_path.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(item, dest_path)
                copied_files.append(str(rel_path))
            else:
                skipped_files.append(str(rel_path))
    
    print(f"✅ Copied {len(copied_files)} files")
    print(f"⏭️  Skipped {len(skipped_files)} unnecessary files")
    
    # Create ZIP file
    zip_path = Path('rag-system-deployment.zip')
    if zip_path.exists():
        zip_path.unlink()
    
    print(f"\n📦 Creating ZIP archive: {zip_path}")
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for file_path in copied_files:
            source_file = output_dir / file_path
            zipf.write(source_file, file_path)
    
    # Calculate size
    zip_size_mb = zip_path.stat().st_size / (1024 * 1024)
    
    # Cleanup temp directory
    shutil.rmtree(output_dir)
    
    print(f"✅ ZIP created: {zip_path} ({zip_size_mb:.2f} MB)")
    print("\n" + "=" * 60)
    print("📋 IMPORTANT FILES INCLUDED:")
    print("=" * 60)
    
    important_files = [
        'credentials.json',
        '.env',
        'chroma_db/',
        'indexed_folders.json',
        'token.pickle',
        'chat-app/build/',
    ]
    
    for file in important_files:
        exists = any(file in f for f in copied_files)
        status = "✅" if exists else "❌"
        print(f"{status} {file}")
    
    print("\n" + "=" * 60)
    print("🎯 NEXT STEPS:")
    print("=" * 60)
    print(f"1. Upload {zip_path} to Plesk File Manager")
    print("2. Extract the ZIP in your application directory")
    print("3. Run: npm install")
    print("4. Run: pip install -r requirements-production.txt")
    print("5. Run: npm start")
    print("\nYour database (chroma_db/) and credentials are preserved! ✅")

if __name__ == "__main__":
    create_deployment_package()

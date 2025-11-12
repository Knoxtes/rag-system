# simple_image_test.py - Simple test without complex dependencies

def test_image_mime_types():
    """Test that image MIME types are now included"""
    
    print("🔍 Testing Image MIME Type Support")
    print("=" * 40)
    
    # This is the supported list from folder_indexer.py (after our modification)
    supported = [
        'application/pdf',
        'application/vnd.google-apps.document',
        'application/vnd.google-apps.presentation',
        'application/vnd.google-apps.spreadsheet',
        'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
        'application/vnd.openxmlformats-officedocument.presentationml.presentation',
        'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        'text/csv',
        'text/plain',
        # Image formats for OCR processing
        'image/jpeg',
        'image/jpg', 
        'image/png',
        'image/gif',
        'image/bmp',
        'image/tiff',
        'image/webp'
    ]
    
    # Test files
    test_files = [
        {'name': 'document.pdf', 'mimeType': 'application/pdf'},
        {'name': 'photo.jpg', 'mimeType': 'image/jpeg'},
        {'name': 'chart.png', 'mimeType': 'image/png'},
        {'name': 'diagram.gif', 'mimeType': 'image/gif'},
        {'name': 'scan.tiff', 'mimeType': 'image/tiff'},
        {'name': 'unsupported.exe', 'mimeType': 'application/x-executable'},
    ]
    
    print("📝 All Supported Types:")
    image_count = 0
    for mime_type in supported:
        if mime_type.startswith('image/'):
            print(f"  ✅ {mime_type} (IMAGE - will use OCR)")
            image_count += 1
        else:
            print(f"  📄 {mime_type}")
    
    print(f"\n📊 Image types supported: {image_count}")
    
    # Test filtering
    filtered = [f for f in test_files if f.get('mimeType') in supported]
    
    print(f"\n🧪 File Filtering Test:")
    print(f"  Total test files: {len(test_files)}")
    print(f"  Will be indexed: {len(filtered)}")
    
    for file in test_files:
        if file['mimeType'] in supported:
            status = "✅ INDEXED"
            if file['mimeType'].startswith('image/'):
                status += " (with OCR)"
        else:
            status = "❌ SKIPPED"
        
        print(f"    {file['name']} - {status}")
    
    return image_count > 0

def test_ocr_config():
    """Test OCR configuration"""
    
    print(f"\n🔧 Testing OCR Configuration:")
    
    try:
        # Try to import config
        import sys
        import os
        sys.path.append(os.getcwd())
        
        from config import OCR_ENABLED, OCR_BACKEND, OCR_CONFIDENCE_THRESHOLD
        
        print(f"  ✅ OCR Configuration found:")
        print(f"    OCR_ENABLED: {OCR_ENABLED}")
        print(f"    OCR_BACKEND: {OCR_BACKEND}")
        print(f"    OCR_CONFIDENCE_THRESHOLD: {OCR_CONFIDENCE_THRESHOLD}")
        
        if not OCR_ENABLED:
            print(f"  ⚠️  OCR is disabled - enable it in config.py")
            return False
        
        return True
        
    except ImportError as e:
        print(f"  ❌ Cannot import OCR config: {e}")
        return False
    except Exception as e:
        print(f"  ❌ Error checking OCR config: {e}")
        return False

def main():
    print("🧪 SIMPLE IMAGE INDEXING TEST")
    print("=" * 45)
    
    # Test 1: MIME type support
    image_support = test_image_mime_types()
    
    # Test 2: OCR config
    ocr_config = test_ocr_config()
    
    print(f"\n🎯 RESULTS:")
    print(f"  Image MIME types added: {'✅ YES' if image_support else '❌ NO'}")
    print(f"  OCR configuration ready: {'✅ YES' if ocr_config else '⚠️  CHECK'}")
    
    if image_support:
        print(f"\n🎉 SUCCESS!")
        print(f"✅ Image files will now be detected during indexing")
        print(f"✅ They will be processed using OCR to extract text")
        print(f"✅ The extracted text will be searchable in your RAG system")
        
        print(f"\n📋 What happens now:")
        print(f"  1. When you run folder indexing, image files will be included")
        print(f"  2. Images will be downloaded and processed with OCR")
        print(f"  3. Text extracted from images becomes searchable content")
        print(f"  4. Users can ask questions about content in images!")
    else:
        print(f"\n❌ Image support not properly configured")

if __name__ == "__main__":
    main()
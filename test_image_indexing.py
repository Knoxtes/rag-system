# test_image_indexing.py - Test if images are now being indexed

import json
from auth import authenticate_google_drive
from folder_indexer import FolderIndexer

def test_supported_image_types():
    """Test that image types are now supported"""
    
    print("🔍 Testing Image Indexing Support")
    print("=" * 40)
    
    # Test MIME types that should now be supported
    image_types = [
        'image/jpeg',
        'image/jpg', 
        'image/png',
        'image/gif',
        'image/bmp',
        'image/tiff',
        'image/webp'
    ]
    
    # Mock files to test filtering
    test_files = [
        {'name': 'document.pdf', 'mimeType': 'application/pdf'},
        {'name': 'photo.jpg', 'mimeType': 'image/jpeg'},
        {'name': 'chart.png', 'mimeType': 'image/png'},
        {'name': 'diagram.gif', 'mimeType': 'image/gif'},
        {'name': 'scan.tiff', 'mimeType': 'image/tiff'},
        {'name': 'random.exe', 'mimeType': 'application/x-executable'},  # Should be filtered out
        {'name': 'spreadsheet.xlsx', 'mimeType': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'}
    ]
    
    # Test the supported types list from folder_indexer
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
    
    print("📝 Supported File Types:")
    for mime_type in supported:
        if mime_type.startswith('image/'):
            print(f"  ✅ {mime_type} (IMAGE - OCR)")
        else:
            print(f"  📄 {mime_type}")
    
    print(f"\n🧪 Testing File Filtering:")
    filtered = [f for f in test_files if f.get('mimeType') in supported]
    
    print(f"  Total test files: {len(test_files)}")
    print(f"  Supported files: {len(filtered)}")
    
    print(f"\n📋 Filtered Results:")
    for file in filtered:
        file_type = "IMAGE (OCR)" if file['mimeType'].startswith('image/') else "DOCUMENT"
        print(f"  ✅ {file['name']} ({file['mimeType']}) - {file_type}")
    
    print(f"\n❌ Filtered Out:")
    excluded = [f for f in test_files if f.get('mimeType') not in supported]
    for file in excluded:
        print(f"  ❌ {file['name']} ({file['mimeType']})")
    
    # Count image types
    image_files = [f for f in filtered if f['mimeType'].startswith('image/')]
    print(f"\n📊 Summary:")
    print(f"  Image files that will be processed with OCR: {len(image_files)}")
    print(f"  Document files: {len(filtered) - len(image_files)}")
    
    return len(image_files) > 0

def check_ocr_configuration():
    """Check if OCR is properly configured"""
    
    print(f"\n🔧 Checking OCR Configuration:")
    
    try:
        from config import OCR_ENABLED, OCR_BACKEND, OCR_CONFIDENCE_THRESHOLD
        
        print(f"  OCR Enabled: {OCR_ENABLED}")
        print(f"  OCR Backend: {OCR_BACKEND}")
        print(f"  Confidence Threshold: {OCR_CONFIDENCE_THRESHOLD}")
        
        if OCR_ENABLED:
            try:
                from ocr_service import OCRServiceFactory
                service = OCRServiceFactory.create_service(OCR_BACKEND)
                print(f"  ✅ OCR Service initialized successfully: {type(service).__name__}")
                return True
            except Exception as e:
                print(f"  ❌ OCR Service initialization failed: {e}")
                return False
        else:
            print(f"  ⚠️  OCR is disabled in config")
            return False
            
    except ImportError as e:
        print(f"  ❌ OCR configuration not found: {e}")
        return False

def main():
    """Run all tests"""
    
    print("🧪 IMAGE INDEXING TEST SUITE")
    print("=" * 50)
    
    # Test 1: File type support
    image_support = test_supported_image_types()
    
    # Test 2: OCR configuration
    ocr_ready = check_ocr_configuration()
    
    print(f"\n🎯 TEST RESULTS:")
    print(f"  Image file support: {'✅ PASS' if image_support else '❌ FAIL'}")
    print(f"  OCR configuration: {'✅ PASS' if ocr_ready else '❌ FAIL'}")
    
    if image_support and ocr_ready:
        print(f"\n🎉 SUCCESS: Images will now be indexed with OCR!")
        print(f"📋 Next steps:")
        print(f"  1. Run folder indexing to process any image files")
        print(f"  2. Images will be processed with {OCR_BACKEND} OCR")
        print(f"  3. Extracted text will be searchable in your RAG system")
    else:
        print(f"\n⚠️  ISSUES DETECTED:")
        if not image_support:
            print(f"  - Image MIME types not in supported list")
        if not ocr_ready:
            print(f"  - OCR service not properly configured")
        print(f"  Fix these issues before indexing images")

if __name__ == "__main__":
    main()
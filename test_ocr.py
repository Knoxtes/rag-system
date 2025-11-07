# test_ocr.py - Test OCR functionality

import os
import sys
import logging
from PIL import Image, ImageDraw, ImageFont
import io

# Add the current directory to the path for imports
sys.path.append(os.getcwd())

from ocr_service import OCRServiceFactory, EasyOCRService, TesseractOCRService
from config import OCR_BACKEND, OCR_CONFIDENCE_THRESHOLD, OCR_LANGUAGES

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_test_image(text: str = "Hello World!\nThis is a test image.\nOCR should recognize this text."):
    """Create a simple test image with text"""
    # Create a new image with white background
    img = Image.new('RGB', (400, 200), color='white')
    draw = ImageDraw.Draw(img)
    
    try:
        # Try to use a default font
        font = ImageFont.truetype("arial.ttf", 16)
    except (OSError, IOError):
        # Fallback to default font if specific font not found
        font = ImageFont.load_default()
    
    # Draw the text
    draw.multiline_text((10, 10), text, fill='black', font=font)
    
    return img

def test_ocr_service(service, service_name: str):
    """Test a specific OCR service"""
    logger.info(f"\n--- Testing {service_name} ---")
    
    if not service.is_available():
        logger.warning(f"{service_name} is not available")
        return False
    
    try:
        # Create test image
        test_image = create_test_image()
        
        # Convert to bytes
        img_byte_arr = io.BytesIO()
        test_image.save(img_byte_arr, format='PNG')
        image_bytes = img_byte_arr.getvalue()
        
        # Extract text
        result = service.extract_text(image_bytes)
        
        logger.info(f"✓ Extracted text: {repr(result.text)}")
        logger.info(f"✓ Confidence: {result.confidence:.2f}")
        logger.info(f"✓ Language: {result.language}")
        
        # Basic validation
        if result.text and "Hello" in result.text:
            logger.info(f"✓ {service_name} test PASSED")
            return True
        else:
            logger.warning(f"✗ {service_name} test FAILED - Expected text not found")
            return False
            
    except Exception as e:
        logger.error(f"✗ {service_name} test FAILED with error: {e}")
        return False

def test_image_detection():
    """Test image file detection functions"""
    from ocr_service import is_image_file, get_image_format_from_mime
    
    logger.info("\n--- Testing Image Detection ---")
    
    # Test MIME type detection
    test_cases = [
        ('image/jpeg', 'test.jpg', True),
        ('image/png', 'test.png', True),
        ('image/tiff', 'test.tiff', True),
        ('application/pdf', 'test.pdf', False),
        ('text/plain', 'test.txt', False),
        ('', 'image.jpg', True),
        ('', 'document.docx', False)
    ]
    
    for mime_type, filename, expected in test_cases:
        result = is_image_file(mime_type, filename)
        status = "✓" if result == expected else "✗"
        logger.info(f"{status} {mime_type} / {filename} -> {result} (expected {expected})")
    
    # Test format conversion
    format_tests = [
        ('image/jpeg', 'jpg'),
        ('image/png', 'png'),
        ('image/tiff', 'tiff'),
        ('application/pdf', None)
    ]
    
    for mime_type, expected_format in format_tests:
        result = get_image_format_from_mime(mime_type)
        status = "✓" if result == expected_format else "✗"
        logger.info(f"{status} {mime_type} -> {result} (expected {expected_format})")

def test_factory():
    """Test OCR service factory"""
    logger.info("\n--- Testing OCR Factory ---")
    
    # Test factory creation
    try:
        easyocr_service = OCRServiceFactory.create_service('easyocr')
        logger.info("✓ EasyOCR service created successfully")
    except Exception as e:
        logger.error(f"✗ EasyOCR service creation failed: {e}")
    
    try:
        tesseract_service = OCRServiceFactory.create_service('tesseract')
        logger.info("✓ Tesseract service created successfully")
    except Exception as e:
        logger.error(f"✗ Tesseract service creation failed: {e}")
    
    # Test available backends
    available = OCRServiceFactory.get_available_backends()
    logger.info(f"✓ Available backends: {available}")

def test_document_loader_integration():
    """Test OCR integration with document loader"""
    logger.info("\n--- Testing Document Loader Integration ---")
    
    try:
        from document_loader import extract_text_from_image, extract_text
        from ocr_service import OCRServiceFactory
        
        # Create OCR service
        ocr_service = OCRServiceFactory.create_service(OCR_BACKEND)
        
        # Create test image
        test_image = create_test_image("Document Loader Test\nThis tests integration.")
        
        # Convert to bytes
        img_byte_arr = io.BytesIO()
        test_image.save(img_byte_arr, format='PNG')
        img_byte_arr.seek(0)
        
        # Test direct OCR function
        result = extract_text_from_image(img_byte_arr, ocr_service, "test_image.png")
        
        logger.info(f"✓ Document loader OCR result:")
        logger.info(f"  {result}")
        
        # Test full extract_text function
        img_byte_arr.seek(0)
        full_result = extract_text(img_byte_arr, 'image/png', 'test_image.png', ocr_service)
        
        logger.info(f"✓ Full extract_text result:")
        logger.info(f"  {full_result}")
        
        return True
        
    except Exception as e:
        logger.error(f"✗ Document loader integration test failed: {e}")
        return False

def main():
    """Run all OCR tests"""
    logger.info("🔍 Starting OCR Integration Tests")
    logger.info(f"Configuration: Backend={OCR_BACKEND}, Threshold={OCR_CONFIDENCE_THRESHOLD}, Languages={OCR_LANGUAGES}")
    
    test_results = []
    
    # Test image detection utilities
    test_image_detection()
    
    # Test factory
    test_factory()
    
    # Test individual services
    try:
        easyocr_service = EasyOCRService(confidence_threshold=OCR_CONFIDENCE_THRESHOLD)
        test_results.append(test_ocr_service(easyocr_service, "EasyOCR"))
    except Exception as e:
        logger.error(f"Failed to create EasyOCR service: {e}")
        test_results.append(False)
    
    try:
        tesseract_service = TesseractOCRService(confidence_threshold=OCR_CONFIDENCE_THRESHOLD)
        test_results.append(test_ocr_service(tesseract_service, "Tesseract"))
    except Exception as e:
        logger.error(f"Failed to create Tesseract service: {e}")
        test_results.append(False)
    
    # Test document loader integration
    test_results.append(test_document_loader_integration())
    
    # Summary
    passed = sum(test_results)
    total = len(test_results)
    
    logger.info(f"\n🎯 Test Summary: {passed}/{total} tests passed")
    
    if passed == total:
        logger.info("🎉 All tests PASSED! OCR integration is working correctly.")
    else:
        logger.warning("⚠️  Some tests FAILED. Check the logs above for details.")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
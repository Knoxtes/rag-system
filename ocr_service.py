# ocr_service.py - OCR service abstraction with local and cloud backends

import io
import logging
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from PIL import Image
import numpy as np

@dataclass
class OCRResult:
    """Standardized OCR result format"""
    text: str
    confidence: float
    bounding_boxes: List[Dict[str, Any]] = None
    language: str = None
    
    def __str__(self):
        return f"OCRResult(text_length={len(self.text)}, confidence={self.confidence:.2f})"


class BaseOCRService(ABC):
    """Abstract base class for OCR services"""
    
    @abstractmethod
    def extract_text(self, image_data: bytes, languages: List[str] = None) -> OCRResult:
        """
        Extract text from image data
        
        Args:
            image_data: Image bytes
            languages: Optional list of language codes (e.g., ['en', 'es'])
            
        Returns:
            OCRResult containing extracted text and metadata
        """
        pass
    
    @abstractmethod
    def is_available(self) -> bool:
        """Check if the OCR service is available and ready to use"""
        pass
    
    @abstractmethod
    def get_supported_formats(self) -> List[str]:
        """Get list of supported image formats"""
        pass


class EasyOCRService(BaseOCRService):
    """Local OCR service using EasyOCR"""
    
    def __init__(self, gpu_enabled: bool = True, confidence_threshold: float = 0.5):
        self.gpu_enabled = gpu_enabled
        self.confidence_threshold = confidence_threshold
        self._reader = None
        self._logger = logging.getLogger(__name__)
        
    def _get_reader(self, languages: List[str] = None):
        """Lazy initialization of EasyOCR reader"""
        if self._reader is None:
            try:
                import easyocr
                
                # Default to English if no languages specified
                if not languages:
                    languages = ['en']
                
                self._logger.info(f"Initializing EasyOCR with languages: {languages}")
                self._reader = easyocr.Reader(
                    languages, 
                    gpu=self.gpu_enabled,
                    verbose=False
                )
                
            except ImportError:
                raise ImportError(
                    "EasyOCR not installed. Install with: pip install easyocr"
                )
            except Exception as e:
                self._logger.error(f"Failed to initialize EasyOCR: {e}")
                raise
                
        return self._reader
    
    def _preprocess_image(self, image_data: bytes) -> np.ndarray:
        """Preprocess image for better OCR results"""
        try:
            # Convert bytes to PIL Image
            image = Image.open(io.BytesIO(image_data))
            
            # Convert to RGB if necessary
            if image.mode != 'RGB':
                image = image.convert('RGB')
            
            # Convert to numpy array
            image_array = np.array(image)
            
            return image_array
            
        except Exception as e:
            self._logger.error(f"Image preprocessing failed: {e}")
            raise
    
    def extract_text(self, image_data: bytes, languages: List[str] = None) -> OCRResult:
        """Extract text using EasyOCR"""
        try:
            # Preprocess image
            image_array = self._preprocess_image(image_data)
            
            # Get OCR reader
            reader = self._get_reader(languages)
            
            # Perform OCR
            results = reader.readtext(image_array)
            
            # Process results
            text_parts = []
            confidences = []
            bounding_boxes = []
            
            for (bbox, text, confidence) in results:
                if confidence >= self.confidence_threshold:
                    text_parts.append(text.strip())
                    confidences.append(confidence)
                    bounding_boxes.append({
                        'bbox': bbox,
                        'text': text.strip(),
                        'confidence': confidence
                    })
            
            # Combine text with newlines between detected text blocks
            combined_text = '\n'.join(text_parts)
            
            # Calculate average confidence
            avg_confidence = sum(confidences) / len(confidences) if confidences else 0.0
            
            # Detect primary language (simplified - use first language if multiple)
            detected_language = languages[0] if languages else 'en'
            
            return OCRResult(
                text=combined_text,
                confidence=avg_confidence,
                bounding_boxes=bounding_boxes,
                language=detected_language
            )
            
        except Exception as e:
            self._logger.error(f"EasyOCR text extraction failed: {e}")
            return OCRResult(text="", confidence=0.0)
    
    def is_available(self) -> bool:
        """Check if EasyOCR is available"""
        try:
            import easyocr
            return True
        except ImportError:
            return False
    
    def get_supported_formats(self) -> List[str]:
        """Get supported image formats"""
        return ['png', 'jpg', 'jpeg', 'tiff', 'bmp', 'gif', 'webp']


class GoogleVisionOCRService(BaseOCRService):
    """Google Vision OCR service (future implementation)"""
    
    def __init__(self, credentials_path: str = None, project_id: str = None):
        self.credentials_path = credentials_path
        self.project_id = project_id
        self._client = None
        self._logger = logging.getLogger(__name__)
        
    def extract_text(self, image_data: bytes, languages: List[str] = None) -> OCRResult:
        """Extract text using Google Vision OCR"""
        # TODO: Implement Google Vision OCR integration
        self._logger.warning("Google Vision OCR not yet implemented")
        return OCRResult(text="", confidence=0.0)
    
    def is_available(self) -> bool:
        """Check if Google Vision OCR is available"""
        try:
            # TODO: Check for google-cloud-vision and credentials
            return False  # Not implemented yet
        except ImportError:
            return False
    
    def get_supported_formats(self) -> List[str]:
        """Get supported image formats for Google Vision"""
        return ['png', 'jpg', 'jpeg', 'tiff', 'bmp', 'gif', 'webp', 'pdf']


class TesseractOCRService(BaseOCRService):
    """Alternative local OCR service using Tesseract (pytesseract)"""
    
    def __init__(self, confidence_threshold: float = 0.5, tesseract_cmd: str = None):
        self.confidence_threshold = confidence_threshold
        self.tesseract_cmd = tesseract_cmd
        self._logger = logging.getLogger(__name__)
        
    def extract_text(self, image_data: bytes, languages: List[str] = None) -> OCRResult:
        """Extract text using Tesseract OCR"""
        try:
            import pytesseract
            from PIL import Image
            
            # Set custom tesseract command if provided
            if self.tesseract_cmd:
                pytesseract.pytesseract.tesseract_cmd = self.tesseract_cmd
            
            # Convert bytes to PIL Image
            image = Image.open(io.BytesIO(image_data))
            
            # Prepare language parameter
            lang = '+'.join(languages) if languages else 'eng'
            
            # Extract text with confidence data
            data = pytesseract.image_to_data(
                image, 
                lang=lang, 
                output_type=pytesseract.Output.DICT
            )
            
            # Filter by confidence and combine text
            text_parts = []
            confidences = []
            
            for i, conf in enumerate(data['conf']):
                if int(conf) >= (self.confidence_threshold * 100):
                    text = data['text'][i].strip()
                    if text:
                        text_parts.append(text)
                        confidences.append(int(conf) / 100.0)
            
            combined_text = ' '.join(text_parts)
            avg_confidence = sum(confidences) / len(confidences) if confidences else 0.0
            
            return OCRResult(
                text=combined_text,
                confidence=avg_confidence,
                language=languages[0] if languages else 'en'
            )
            
        except ImportError:
            self._logger.error("pytesseract not installed. Install with: pip install pytesseract")
            return OCRResult(text="", confidence=0.0)
        except Exception as e:
            self._logger.error(f"Tesseract OCR failed: {e}")
            return OCRResult(text="", confidence=0.0)
    
    def is_available(self) -> bool:
        """Check if Tesseract is available"""
        try:
            import pytesseract
            # Try to get version to verify tesseract is installed
            pytesseract.get_tesseract_version()
            return True
        except (ImportError, pytesseract.TesseractNotFoundError):
            return False
    
    def get_supported_formats(self) -> List[str]:
        """Get supported image formats"""
        return ['png', 'jpg', 'jpeg', 'tiff', 'bmp', 'gif']


class OCRServiceFactory:
    """Factory class to create and manage OCR services"""
    
    @staticmethod
    def create_service(backend: str = 'easyocr', **kwargs) -> BaseOCRService:
        """
        Create OCR service instance
        
        Args:
            backend: OCR backend ('easyocr', 'tesseract', 'google_vision')
            **kwargs: Backend-specific configuration
        
        Returns:
            OCR service instance
        """
        backend = backend.lower()
        
        if backend == 'easyocr':
            return EasyOCRService(**kwargs)
        elif backend == 'tesseract':
            return TesseractOCRService(**kwargs)
        elif backend == 'google_vision':
            return GoogleVisionOCRService(**kwargs)
        else:
            raise ValueError(f"Unsupported OCR backend: {backend}")
    
    @staticmethod
    def get_available_backends() -> List[str]:
        """Get list of available OCR backends"""
        backends = []
        
        # Check EasyOCR
        if EasyOCRService().is_available():
            backends.append('easyocr')
            
        # Check Tesseract
        if TesseractOCRService().is_available():
            backends.append('tesseract')
            
        # Check Google Vision
        if GoogleVisionOCRService().is_available():
            backends.append('google_vision')
            
        return backends


# Utility functions for image handling
def is_image_file(mime_type: str, filename: str = "") -> bool:
    """Check if a file is an image based on MIME type or filename"""
    image_mime_types = {
        'image/jpeg', 'image/jpg', 'image/png', 'image/tiff', 
        'image/bmp', 'image/gif', 'image/webp'
    }
    
    image_extensions = {'.jpg', '.jpeg', '.png', '.tiff', '.tif', '.bmp', '.gif', '.webp'}
    
    # Check MIME type
    if mime_type and mime_type.lower() in image_mime_types:
        return True
    
    # Check file extension
    if filename:
        extension = '.' + filename.lower().split('.')[-1]
        return extension in image_extensions
    
    return False


def get_image_format_from_mime(mime_type: str) -> Optional[str]:
    """Convert MIME type to image format string"""
    mime_to_format = {
        'image/jpeg': 'jpg',
        'image/jpg': 'jpg', 
        'image/png': 'png',
        'image/tiff': 'tiff',
        'image/bmp': 'bmp',
        'image/gif': 'gif',
        'image/webp': 'webp'
    }
    
    return mime_to_format.get(mime_type.lower())
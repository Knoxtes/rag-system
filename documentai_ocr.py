"""
Google Document AI OCR Service
Provides OCR functionality using Google Cloud Document AI for superior document processing
"""

import logging
from typing import List, Optional
from dataclasses import dataclass
from io import BytesIO

try:
    from google.cloud import documentai_v1 as documentai
    from google.api_core.client_options import ClientOptions
    DOCUMENTAI_AVAILABLE = True
except ImportError:
    DOCUMENTAI_AVAILABLE = False

logger = logging.getLogger(__name__)


@dataclass
class OCRResult:
    """Result from OCR processing"""
    text: str
    confidence: float
    language: Optional[str] = None


class DocumentAIOCRService:
    """
    Google Document AI OCR Service
    
    Uses Google Cloud Document AI for high-quality OCR processing.
    Handles PDFs and images with advanced features like table extraction,
    form detection, and layout preservation.
    """
    
    def __init__(self, 
                 project_id: str,
                 location: str = "us",
                 processor_id: Optional[str] = None,
                 confidence_threshold: float = 0.5):
        """
        Initialize Document AI OCR Service
        
        Args:
            project_id: Google Cloud project ID
            location: Processor location (us, eu, asia)
            processor_id: Specific processor ID (optional, will create default if not provided)
            confidence_threshold: Minimum confidence score for text inclusion
        """
        if not DOCUMENTAI_AVAILABLE:
            raise ImportError(
                "google-cloud-documentai not installed. "
                "Install with: pip install google-cloud-documentai"
            )
        
        self.project_id = project_id
        self.location = location
        self.processor_id = processor_id
        self.confidence_threshold = confidence_threshold
        
        # Initialize Document AI client
        opts = ClientOptions(api_endpoint=f"{location}-documentai.googleapis.com")
        self.client = documentai.DocumentProcessorServiceClient(client_options=opts)
        
        # If no processor ID provided, use the default OCR processor type
        if not self.processor_id:
            logger.info("No processor_id provided, will use OCR_PROCESSOR type")
            # Format: projects/{project}/locations/{location}/processors/{processor}
            # We'll construct this on first use with a default processor
        
        logger.info(f"Document AI OCR Service initialized for project {project_id} in {location}")
    
    def _get_processor_name(self) -> str:
        """Get the full processor resource name"""
        if self.processor_id:
            return self.client.processor_path(
                self.project_id,
                self.location,
                self.processor_id
            )
        else:
            # Use default OCR processor - Document AI will handle this
            return self.client.processor_path(
                self.project_id,
                self.location,
                "ocr"  # Default OCR processor
            )
    
    def extract_text(self, 
                    image_data: bytes, 
                    languages: Optional[List[str]] = None,
                    mime_type: str = "image/png") -> OCRResult:
        """
        Extract text from image or document using Document AI
        
        Args:
            image_data: Raw image/document bytes
            languages: Language hints (e.g., ["en", "es"])
            mime_type: MIME type of the document
            
        Returns:
            OCRResult with extracted text and confidence
        """
        try:
            # Prepare document for processing
            raw_document = documentai.RawDocument(
                content=image_data,
                mime_type=mime_type
            )
            
            # Configure processing request
            request = documentai.ProcessRequest(
                name=self._get_processor_name(),
                raw_document=raw_document
            )
            
            # Process document
            result = self.client.process_document(request=request)
            document = result.document
            
            # Extract text with confidence
            text_parts = []
            total_confidence = 0.0
            confidence_count = 0
            detected_language = None
            
            # Process pages
            for page in document.pages:
                # Get page text
                page_text = self._extract_page_text(page, document.text)
                
                # Track confidence
                if hasattr(page, 'confidence') and page.confidence:
                    total_confidence += page.confidence
                    confidence_count += 1
                
                # Detect language from first page
                if not detected_language and hasattr(page, 'detected_languages'):
                    if page.detected_languages:
                        detected_language = page.detected_languages[0].language_code
                
                if page_text.strip():
                    text_parts.append(page_text)
            
            # Combine text
            full_text = "\n\n".join(text_parts)
            
            # Calculate average confidence
            avg_confidence = total_confidence / confidence_count if confidence_count > 0 else 0.0
            
            # Apply confidence threshold
            if avg_confidence < self.confidence_threshold:
                logger.info(f"Document AI result below confidence threshold: {avg_confidence:.2f}")
                return OCRResult(text="", confidence=avg_confidence, language=detected_language)
            
            logger.info(f"Document AI extracted {len(full_text)} characters (confidence: {avg_confidence:.2f})")
            
            return OCRResult(
                text=full_text,
                confidence=avg_confidence,
                language=detected_language
            )
            
        except Exception as e:
            logger.error(f"Document AI processing error: {e}")
            return OCRResult(text="", confidence=0.0)
    
    def _extract_page_text(self, page, document_text: str) -> str:
        """
        Extract text from a single page with layout preservation
        
        Args:
            page: Document AI page object
            document_text: Full document text for reference
            
        Returns:
            Extracted and formatted page text
        """
        text_parts = []
        
        # Try to extract structured elements first (tables, forms, etc.)
        if hasattr(page, 'tables') and page.tables:
            for table in page.tables:
                table_text = self._extract_table(table, document_text)
                if table_text:
                    text_parts.append(f"[TABLE]\n{table_text}\n[/TABLE]")
        
        if hasattr(page, 'form_fields') and page.form_fields:
            for field in page.form_fields:
                field_text = self._extract_form_field(field, document_text)
                if field_text:
                    text_parts.append(field_text)
        
        # Extract paragraphs/blocks
        if hasattr(page, 'paragraphs') and page.paragraphs:
            for paragraph in page.paragraphs:
                para_text = self._get_text_from_layout(paragraph.layout, document_text)
                if para_text.strip():
                    text_parts.append(para_text)
        elif hasattr(page, 'blocks') and page.blocks:
            # Fallback to blocks if no paragraphs
            for block in page.blocks:
                block_text = self._get_text_from_layout(block.layout, document_text)
                if block_text.strip():
                    text_parts.append(block_text)
        
        return "\n\n".join(text_parts)
    
    def _get_text_from_layout(self, layout, document_text: str) -> str:
        """Extract text from a layout element"""
        try:
            if not hasattr(layout, 'text_anchor') or not layout.text_anchor:
                return ""
            
            text_segments = []
            for segment in layout.text_anchor.text_segments:
                start_index = int(segment.start_index) if hasattr(segment, 'start_index') else 0
                end_index = int(segment.end_index) if hasattr(segment, 'end_index') else len(document_text)
                text_segments.append(document_text[start_index:end_index])
            
            return "".join(text_segments)
        except Exception as e:
            logger.warning(f"Error extracting text from layout: {e}")
            return ""
    
    def _extract_table(self, table, document_text: str) -> str:
        """Extract and format table data"""
        try:
            rows = []
            for row in table.body_rows:
                cells = []
                for cell in row.cells:
                    cell_text = self._get_text_from_layout(cell.layout, document_text)
                    cells.append(cell_text.strip())
                if cells:
                    rows.append(" | ".join(cells))
            
            return "\n".join(rows)
        except Exception as e:
            logger.warning(f"Error extracting table: {e}")
            return ""
    
    def _extract_form_field(self, field, document_text: str) -> str:
        """Extract form field key-value pair"""
        try:
            field_name = ""
            field_value = ""
            
            if hasattr(field, 'field_name') and field.field_name:
                field_name = self._get_text_from_layout(field.field_name, document_text).strip()
            
            if hasattr(field, 'field_value') and field.field_value:
                field_value = self._get_text_from_layout(field.field_value, document_text).strip()
            
            if field_name and field_value:
                return f"{field_name}: {field_value}"
            elif field_value:
                return field_value
            
            return ""
        except Exception as e:
            logger.warning(f"Error extracting form field: {e}")
            return ""
    
    def process_pdf(self, pdf_data: bytes) -> OCRResult:
        """
        Process a PDF document with Document AI
        
        Args:
            pdf_data: Raw PDF bytes
            
        Returns:
            OCRResult with extracted text
        """
        return self.extract_text(pdf_data, mime_type="application/pdf")


def create_documentai_service(project_id: str,
                              location: str = "us",
                              processor_id: Optional[str] = None,
                              confidence_threshold: float = 0.5) -> DocumentAIOCRService:
    """
    Factory function to create Document AI OCR service
    
    Args:
        project_id: Google Cloud project ID
        location: Processor location
        processor_id: Specific processor ID (optional)
        confidence_threshold: Minimum confidence for text
        
    Returns:
        DocumentAIOCRService instance
    """
    return DocumentAIOCRService(
        project_id=project_id,
        location=location,
        processor_id=processor_id,
        confidence_threshold=confidence_threshold
    )

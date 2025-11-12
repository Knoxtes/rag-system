#!/usr/bin/env python3
"""
Text Clarification Service
AI-powered text clarification and improvement for OCR extracted content
"""

import re
import logging
from typing import Optional, Dict, Any
import google.generativeai as genai
from config import (
    GOOGLE_API_KEY, PROJECT_ID, TEXT_CLARIFICATION_ENABLED,
    CLARIFICATION_MODEL_TEMPERATURE, CLARIFICATION_MAX_TOKENS,
    AUTO_CLARIFY_OCR, CLARIFICATION_MIN_LENGTH
)

logger = logging.getLogger(__name__)


class TextClarificationService:
    """
    Service that uses AI to improve and clarify extracted text,
    especially text from OCR that may be abstract or hard to understand
    """
    
    def __init__(self):
        self.model = None
        self._initialize_ai_model()
    
    def _initialize_ai_model(self):
        """Initialize the AI model for text clarification"""
        try:
            if not TEXT_CLARIFICATION_ENABLED:
                logger.info("Text clarification is disabled in configuration")
                return
                
            if not GOOGLE_API_KEY:
                logger.warning("GOOGLE_API_KEY not set - text clarification disabled")
                return
            
            genai.configure(api_key=GOOGLE_API_KEY)
            self.model = genai.GenerativeModel('gemini-2.0-flash')
            logger.info("Text clarification service initialized with Gemini 2.0 Flash")
            
        except Exception as e:
            logger.warning(f"Failed to initialize text clarification service: {e}")
            self.model = None
    
    def should_clarify_text(self, text: str, source_type: str = "") -> bool:
        """
        Determine if text needs clarification based on various heuristics
        """
        if not TEXT_CLARIFICATION_ENABLED or not text or len(text.strip()) < CLARIFICATION_MIN_LENGTH:
            return False
        
        # Always clarify OCR text if auto-clarify is enabled
        if AUTO_CLARIFY_OCR and any(indicator in source_type.lower() for indicator in ['ocr', 'image', 'scanned']):
            return True
        
        # Check for common OCR issues that suggest clarification is needed
        ocr_issues = [
            # Fragmented words
            len(re.findall(r'\b\w{1,2}\b', text)) / max(len(text.split()), 1) > 0.3,
            # Excessive special characters
            len(re.findall(r'[^\w\s]', text)) / max(len(text), 1) > 0.2,
            # Too many short lines (poor formatting)
            text.count('\n') / max(len(text.split('\n')), 1) > 0.8,
            # Repeated characters (OCR artifacts)
            bool(re.search(r'(.)\1{3,}', text)),
            # Numbers mixed with letters inappropriately
            bool(re.search(r'\d[a-zA-Z]\d|\w\d\w', text)),
            # Excessive spacing issues
            bool(re.search(r'\s{3,}', text)),
        ]
        
        # If multiple OCR issues are detected, clarification is needed
        return sum(ocr_issues) >= 2
    
    def clarify_text(self, 
                    text: str, 
                    filename: str = "", 
                    source_type: str = "",
                    context: str = "") -> str:
        """
        Use AI to clarify and improve extracted text
        """
        if not self.model:
            logger.debug("AI model not available for text clarification")
            return text
        
        if not self.should_clarify_text(text, source_type):
            logger.debug("Text doesn't need clarification")
            return text
        
        try:
            # Build context-aware prompt
            prompt = self._build_clarification_prompt(text, filename, source_type, context)
            
            # Generate clarified text
            response = self.model.generate_content(
                prompt,
                generation_config=genai.types.GenerationConfig(
                    temperature=CLARIFICATION_MODEL_TEMPERATURE,
                    max_output_tokens=CLARIFICATION_MAX_TOKENS,
                )
            )
            
            clarified_text = response.text.strip()
            
            if clarified_text and len(clarified_text) > 20:
                logger.info(f"Text clarified for {filename} ({len(text)} -> {len(clarified_text)} chars)")
                
                # Add clarification metadata
                metadata_header = f"[CLARIFIED TEXT from {source_type}: {filename}]\n"
                metadata_header += f"Original length: {len(text)} chars | Clarified length: {len(clarified_text)} chars\n\n"
                
                return metadata_header + clarified_text
            else:
                logger.warning(f"AI clarification produced poor result for {filename}")
                return text
                
        except Exception as e:
            logger.error(f"Error during text clarification for {filename}: {e}")
            return text
    
    def _build_clarification_prompt(self, 
                                  text: str, 
                                  filename: str, 
                                  source_type: str,
                                  context: str) -> str:
        """
        Build an intelligent prompt for text clarification
        """
        # Determine document type context
        doc_type_hints = self._get_document_type_hints(filename, context)
        
        # Check if this appears to be a structured business document
        is_business_process = self._is_business_process_document(text)
        
        if is_business_process:
            prompt_parts = [
                "You are an expert at converting fragmented business process documents into clear, actionable formats.",
                "",
                "TASK: Transform this fragmented OCR text into a well-structured, readable business document.",
                "",
                "INSTRUCTIONS:",
                "1. Identify the process steps and put them in logical order",
                "2. Create clear step-by-step instructions with proper numbering",
                "3. Make each step actionable and descriptive", 
                "4. Group related information together",
                "5. Add context and details to make steps clear for business users",
                "6. Format as a proper business process document",
                "7. If steps reference other processes, explain what each involves",
                "",
                "EXAMPLE TRANSFORMATION:",
                "FROM: 'STEP STEP STEP 01 02 03 PLANNING EXECUTION REVIEW'",
                "TO: 'Business Process Steps:",
                "     1. Planning - Define project scope and requirements",
                "     2. Execution - Implement the planned activities", 
                "     3. Review - Evaluate results and gather feedback'",
                "",
                f"DOCUMENT CONTEXT:",
                f"- Filename: {filename}",
                f"- Source: {source_type}",
                f"- Document type: {doc_type_hints}",
            ]
        else:
            prompt_parts = [
                "You are an expert text clarification specialist. Your task is to improve text that was extracted from documents, especially OCR text that may be unclear or fragmented.",
                "",
                "INSTRUCTIONS:",
                "1. Fix OCR errors (fragmented words, spacing issues, character recognition mistakes)",
                "2. Improve clarity and readability while preserving all original meaning", 
                "3. Maintain the original structure and organization",
                "4. Fix grammar and formatting issues",
                "5. Make technical terms and instructions clearer and more actionable",
                "6. Preserve all specific details, numbers, dates, and proper nouns",
                "7. If the text contains procedures or instructions, make them step-by-step and clear",
                "",
                f"DOCUMENT CONTEXT:",
                f"- Filename: {filename}",
                f"- Source: {source_type}",
                f"- Document type: {doc_type_hints}",
            ]
        
        if context:
            prompt_parts.append(f"- Additional context: {context}")
        
        prompt_parts.extend([
            "",
            "ORIGINAL TEXT TO CLARIFY:",
            "=" * 50,
            text,
            "=" * 50,
            "",
            "Please provide the clarified and improved version of this text. Focus on making it clear and actionable while preserving all original information:"
        ])
        
        return "\n".join(prompt_parts)
    
    def _is_business_process_document(self, text: str) -> bool:
        """
        Detect if this appears to be a business process document that needs restructuring
        """
        text_lower = text.lower()
        
        # Look for indicators of fragmented business processes
        process_indicators = [
            # Step/phase patterns
            text.count('STEP') >= 3,
            text.count('PHASE') >= 2, 
            # Sequential numbering
            bool(re.search(r'\b(01|02|03|04|05)\b', text)),
            bool(re.search(r'\b(1|2|3|4|5)\b', text)),
            # Business process terms
            any(term in text_lower for term in [
                'onboarding', 'development', 'brief', 'presentation', 
                'finalization', 'approval', 'implementation', 'review'
            ]),
            # Short repeated words (suggesting fragmented layout)
            len([word for word in text.split() if len(word) <= 4]) > len(text.split()) * 0.4
        ]
        
        return sum(process_indicators) >= 3
    
    def _get_document_type_hints(self, filename: str, context: str) -> str:
        """
        Determine document type to provide better context for clarification
        """
        filename_lower = filename.lower()
        context_lower = context.lower()
        
        type_indicators = {
            'policy': ['policy', 'handbook', 'guidelines', 'rules', 'procedures'],
            'manual': ['manual', 'guide', 'instructions', 'how-to', 'tutorial'],
            'form': ['form', 'application', 'request', 'template'],
            'report': ['report', 'analysis', 'summary', 'findings'],
            'contract': ['contract', 'agreement', 'terms', 'legal'],
            'calendar': ['calendar', 'schedule', 'events', 'meetings'],
            'financial': ['budget', 'expense', 'invoice', 'financial', 'cost'],
            'hr': ['hr', 'employee', 'benefits', 'payroll', 'vacation'],
            'creative': ['design', 'creative', 'marketing', 'brand', 'logo'],
            'technical': ['technical', 'specification', 'documentation', 'api']
        }
        
        detected_types = []
        
        for doc_type, indicators in type_indicators.items():
            if any(indicator in filename_lower or indicator in context_lower 
                   for indicator in indicators):
                detected_types.append(doc_type)
        
        if detected_types:
            return f"{', '.join(detected_types)} document"
        else:
            return "business document"
    
    def clarify_batch(self, text_items: list) -> list:
        """
        Clarify multiple text items in batch for efficiency
        """
        if not self.model:
            return text_items
        
        clarified_items = []
        
        for item in text_items:
            if isinstance(item, dict):
                text = item.get('text', '')
                filename = item.get('filename', '')
                source_type = item.get('source_type', '')
                context = item.get('context', '')
            else:
                text = str(item)
                filename = ''
                source_type = ''
                context = ''
            
            clarified_text = self.clarify_text(text, filename, source_type, context)
            
            if isinstance(item, dict):
                clarified_item = item.copy()
                clarified_item['text'] = clarified_text
                clarified_item['clarified'] = True
                clarified_items.append(clarified_item)
            else:
                clarified_items.append(clarified_text)
        
        return clarified_items


# Global service instance
_clarification_service = None

def get_clarification_service() -> TextClarificationService:
    """Get global text clarification service instance"""
    global _clarification_service
    if _clarification_service is None:
        _clarification_service = TextClarificationService()
    return _clarification_service
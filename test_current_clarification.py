#!/usr/bin/env python3
"""
Test how the current text clarification handles the brand development text
"""

from text_clarification import get_clarification_service

test_text = """BRAND DEVELOPMENT
STEP
STEP
STEP
STEP
STEP
01
02
03
04
05
ONBOARDING
INTERNAL CREATIVE BRIEF
BRAND CONCEPT PRESENTATION
VISUAL DEVELOPMENT
FINALIZATION"""

clarification_service = get_clarification_service()

if clarification_service.model:
    print("Original OCR Text:")
    print("=" * 50)
    print(test_text)
    print("=" * 50)
    
    print("\nAttempting clarification...")
    
    clarified_text = clarification_service.clarify_text(
        text=test_text,
        filename="brand_development_process.png",
        source_type="OCR Image",
        context="Business process document for client onboarding"
    )
    
    print("\nClarified Text:")
    print("=" * 50) 
    print(clarified_text)
    print("=" * 50)
    
else:
    print("Text clarification service not available (check GOOGLE_API_KEY)")
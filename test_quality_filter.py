#!/usr/bin/env python3
"""
Test script for Text Quality Filtering
Demonstrates filtering of low-quality and nonsensical text from OCR
"""

from text_quality_filter import get_quality_filter
import logging

logging.basicConfig(level=logging.INFO)

def test_quality_filtering_examples():
    """Test with various quality examples"""
    
    # Sample texts representing different quality levels
    test_samples = [
        {
            'filename': 'good_document.pdf',
            'source_type': 'PDF',
            'text': '''Company Policy Manual
            
            This document outlines the key policies and procedures for all employees.
            Please review these guidelines carefully and contact HR if you have any questions.
            
            Vacation Policy:
            All full-time employees are eligible for paid vacation time after 6 months of employment.
            Vacation requests must be submitted at least 2 weeks in advance through the HR portal.
            Maximum of 15 days per calendar year.
            
            Contact Information:
            HR Department: hr@company.com
            Phone: (555) 123-4567''',
            'expected': True,
            'description': 'High-quality business document'
        },
        {
            'filename': 'corrupted_ocr.jpg',
            'source_type': 'OCR Image', 
            'text': '''3mp|0y33 H4ndb00k
            
            Th|$ |$ @ c0rrupt3d 0CR 3xtr4ct|0n w|th m4ny 3rr0r$ 4nd
            |nc0rr3ct ch4r4ct3r$ th4t m4k3 |t h4rd t0 und3r$t4nd.
            
            P0||cy 1: V4c4t|0n T|m3
            - A|| 3mp|0y33$ 4r3 3||g|b|3 f0r v4c4t|0n
            - R3qu3$t$ mu$t b3 $ubm|tt3d |n 4dv4nc3
            
            C0nt4ct: hr@c0mp4ny.c0m''',
            'expected': False,
            'description': 'Heavily corrupted OCR text'
        },
        {
            'filename': 'fragmented_scan.png',
            'source_type': 'OCR Image',
            'text': '''Em p|o ye e  Ha nd bo ok
            
            W e|c om e  t o  ou r  c om pa ny
            
            Po | ic y  1:  Va ca ti on
            - A ||  em p|o ye es  ar e  e||i g|b |e
            - Ma x|m um  of  1 0  da ys
            
            HR  De pa rt me nt  55 5- 12 3- 45 67''',
            'expected': False, 
            'description': 'Fragmented OCR with excessive spacing'
        },
        {
            'filename': 'nonsense_ocr.tiff',
            'source_type': 'OCR Image',
            'text': '''xJk9mP2nQ w8Rt5LcV bN3xZ7fH
            
            qW1eR2tY u9I0oP aS3dF4gH
            z6X7cV8bN m1Q2w3E r5T6y7U
            
            !@#$%^&*() []{}|\\:";'<>?,./
            1234567890 aBcDeFgHiJkLmN
            
            zzzzzzzzz aaaaaaaaaa tttttttt''',
            'expected': False,
            'description': 'Complete nonsense/random characters'
        },
        {
            'filename': 'minimal_content.jpg',
            'source_type': 'OCR Image',
            'text': '''Logo
            
            Company Name''',
            'expected': False,
            'description': 'Too little meaningful content'
        },
        {
            'filename': 'acceptable_ocr.png', 
            'source_type': 'OCR Image',
            'text': '''Employee Handbook
            
            Welcome to our company. This handbook contains important
            information about your employment with us.
            
            Vacation Policy:
            All employees are eligible for vacation time after six months.
            Requests must be submitted two weeks in advance.
            Maximum of ten days per year.
            
            Contact HR department for questions: 555-123-4567''',
            'expected': True,
            'description': 'Acceptable quality OCR text'
        },
        {
            'filename': 'poor_formatting.gif',
            'source_type': 'OCR Image',
            'text': '''COMPANY!!!HANDBOOK???
            
            WELCOME@@@TO###OUR$$$COMPANY
            
            VACATION***POLICY:
            ALL&&&EMPLOYEES%%%ARE^^^ELIGIBLE
            FOR(((VACATION)))TIME+++AFTER===SIX|||MONTHS
            
            CONTACT!!!HR!!!DEPARTMENT!!!555-123-4567!!!''',
            'expected': False,
            'description': 'Excessive special characters from poor OCR'
        },
        {
            'filename': 'repetitive_errors.bmp',
            'source_type': 'OCR Image', 
            'text': '''Employee Employee Employee Employee Employee Employee
            Handbook Handbook Handbook Handbook Handbook Handbook
            Company Company Company Company Company Company
            Policy Policy Policy Policy Policy Policy
            Vacation Vacation Vacation Vacation Vacation Vacation''',
            'expected': False,
            'description': 'Excessive word repetition from OCR errors'
        }
    ]
    
    quality_filter = get_quality_filter()
    
    print("🔍 Testing Text Quality Filtering")
    print("=" * 80)
    
    correct_predictions = 0
    total_tests = len(test_samples)
    
    for i, sample in enumerate(test_samples, 1):
        print(f"\n📄 Test {i}: {sample['filename']}")
        print(f"Description: {sample['description']}")
        print(f"Source: {sample['source_type']}")
        print("-" * 60)
        
        # Assess quality
        assessment = quality_filter.assess_text_quality(
            text=sample['text'],
            filename=sample['filename'],
            source_type=sample['source_type']
        )
        
        # Check prediction accuracy
        predicted = assessment['should_include']
        expected = sample['expected']
        is_correct = predicted == expected
        
        if is_correct:
            correct_predictions += 1
            status = "✅ CORRECT"
        else:
            status = "❌ INCORRECT"
        
        print(f"Expected: {'INCLUDE' if expected else 'EXCLUDE'}")
        print(f"Predicted: {'INCLUDE' if predicted else 'EXCLUDE'} ({status})")
        print(f"Quality Score: {assessment['quality_score']:.3f}")
        print(f"Reason: {assessment['reason']}")
        
        # Show key metrics
        metrics = assessment['metrics']
        if metrics:
            print(f"\nKey Metrics:")
            print(f"  • Readable ratio: {metrics.get('readable_ratio', 0):.3f}")
            print(f"  • Special char ratio: {metrics.get('special_char_ratio', 0):.3f}")
            print(f"  • Coherence score: {metrics.get('coherence_score', 0):.3f}")
            print(f"  • OCR error score: {metrics.get('ocr_error_score', 0):.3f}")
            print(f"  • Content length: {metrics.get('meaningful_content_length', 0)}")
        
        if 'text_preview' in assessment:
            print(f"\nText Preview:")
            print(f"  {assessment['text_preview']}")
        
        print("-" * 60)
    
    # Summary
    accuracy = correct_predictions / total_tests * 100
    print(f"\n🎯 SUMMARY")
    print("=" * 40)
    print(f"Correct predictions: {correct_predictions}/{total_tests}")
    print(f"Accuracy: {accuracy:.1f}%")
    
    if accuracy >= 85:
        print("✅ Quality filter working well!")
    elif accuracy >= 70:
        print("⚠️ Quality filter needs some tuning")
    else:
        print("❌ Quality filter needs significant improvement")

def test_configuration_impact():
    """Test how configuration changes affect filtering behavior"""
    
    print(f"\n🛠️ Testing Configuration Impact")
    print("=" * 60)
    
    # Test with a borderline quality text
    test_text = '''Em p|oyee Ha ndb ook
    
    Po|icy 1: Vac ation Time
    - A|| emp|oyees are e||ig|b|e for vacation
    - Requests must be subm|tted in advance
    
    Contact HR department for questions'''
    
    quality_filter = get_quality_filter()
    
    # Test with default settings
    assessment = quality_filter.assess_text_quality(
        text=test_text,
        filename="test_document.png",
        source_type="OCR Image"
    )
    
    print(f"Default Settings:")
    print(f"  Decision: {'INCLUDE' if assessment['should_include'] else 'EXCLUDE'}")
    print(f"  Quality Score: {assessment['quality_score']:.3f}")
    print(f"  Reason: {assessment['reason']}")
    
    # Show current configuration values
    from config import (
        TEXT_QUALITY_FILTER_ENABLED, QUALITY_MIN_READABLE_RATIO,
        QUALITY_MAX_SPECIAL_CHAR_RATIO, QUALITY_MIN_COHERENCE_SCORE,
        QUALITY_MIN_CONTENT_LENGTH, QUALITY_MIN_OVERALL_SCORE,
        QUALITY_OCR_THRESHOLD
    )
    
    print(f"\nCurrent Configuration:")
    print(f"  • Filter Enabled: {TEXT_QUALITY_FILTER_ENABLED}")
    print(f"  • Min Readable Ratio: {QUALITY_MIN_READABLE_RATIO}")
    print(f"  • Max Special Char Ratio: {QUALITY_MAX_SPECIAL_CHAR_RATIO}")
    print(f"  • Min Coherence Score: {QUALITY_MIN_COHERENCE_SCORE}")
    print(f"  • Min Content Length: {QUALITY_MIN_CONTENT_LENGTH}")
    print(f"  • Min Overall Score: {QUALITY_MIN_OVERALL_SCORE}")
    print(f"  • OCR Threshold: {QUALITY_OCR_THRESHOLD}")

def main():
    """Main test function"""
    try:
        test_quality_filtering_examples()
        test_configuration_impact()
        
        print(f"\n🎉 Quality filtering tests completed!")
        print(f"\nHow quality filtering protects your database:")
        print("1. 🚫 Blocks corrupted OCR text with excessive errors")
        print("2. 🚫 Filters out nonsensical character sequences")
        print("3. 🚫 Removes content with poor readability")
        print("4. ✅ Allows high-quality text to pass through")
        print("5. ⚙️ Configurable thresholds for your specific needs")
        
        print(f"\nDuring indexing, you'll see:")
        print("  ✓ Text passed quality check (score: 0.75)")
        print("  ❌ Text filtered out (poor quality)")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")

if __name__ == "__main__":
    main()
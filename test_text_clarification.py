#!/usr/bin/env python3
"""
Test script for Text Clarification Service
Demonstrates AI-powered improvement of OCR extracted text
"""

from text_clarification import get_clarification_service
import logging

logging.basicConfig(level=logging.INFO)

def test_ocr_text_samples():
    """Test with simulated OCR text samples that need clarification"""
    
    # Sample problematic OCR texts that might be extracted from images
    test_samples = [
        {
            'filename': 'employee_handbook_page1.png',
            'source_type': 'OCR Image',
            'text': '''Em p|oyee H andb ook
            
            W e|come to our c ompany! Th is handb ook conta ins
            import ant inf orm ation ab out y our empl oyment.
            
            Pol icy 1: Vac ation Time
            - A|| emp|oyees are e||ig|b|e f0r vac4tion t|me after
              6 m0nths 0f empl0yment
            - Vac4tion requests must be subm|tted 2 weeks |n adv4nce
            - M4x|mum 0f 10 days per ye4r
            
            C0nt4ct HR d3p4rtm3nt f0r qu3st|0ns'''
        },
        {
            'filename': 'procedure_checklist.jpg', 
            'source_type': 'OCR Image',
            'text': '''PR0CEDURE CHECKLIST
            
            St3p 1: Ch3ck a|| |nput dat4
            St3p 2: Ver|fy us3r cr3d3nt|a|s  
            St3p 3: Run va||dat|0n ch3cks
            St3p 4: G3n3rat3 0utput r3p0rt
            St3p 5: S3nd t0 manag3r f0r appr0va|
            
            N0T3: If any st3p fa||s, st0p pr0c3ss and
            a|3rt syst3m adm|n|strat0r'''
        },
        {
            'filename': 'meeting_notes.png',
            'source_type': 'Scanned PDF OCR',
            'text': '''M33t|ng N0t3s - Jan 15th
            
            At t3nd33s: J0hn, Mary, B0b, S4rah
            
            Ag3nda |t3ms:
            1. Budg3t r3v|3w f0r Q1
            2. N3w pr0j3ct t|m3||n3s
            3. St4ff|ng upd4t3s
            
            A ct|0n |t3ms:
            - Mary w||| pr3p4r3 c0st 3st|m4t3s by Fr|day
            - B0b t0 sch3du|3 c||3nt m33t|ng
            - J0hn w||| f|na||z3 c0ntr4ct t3rms
            
            N3xt m33t|ng: Jan 22nd at 10 AM'''
        },
        {
            'filename': 'software_guide.tiff',
            'source_type': 'OCR Image', 
            'text': '''S0FTW4R3 |NST4LL4T|0N GU|D3
            
            R3qu|r3m3nts:
            - W|nd0ws 10 0r |at3r
            - 4GB RAM m|n|mum
            - 500MB d|sk sp4c3
            
            |nsta||at|0n St3ps:
            1. D0wn|0ad th3 |nsta||3r f||3
            2. R|ght-c||ck and s3|3ct "Run as adm|n|strat0r" 
            3. F0||0w th3 0n-scr33n |nstruct|0ns
            4. R3start c0mput3r wh3n pr0mpt3d
            5. V3r|fy |nsta||at|0n by 0p3n|ng th3 app||cat|0n
            
            Tr0ub|3sh00t|ng:
            If |nsta||at|0n fa||s, ch3ck f|r3wa|| s3tt|ngs'''
        }
    ]
    
    clarification_service = get_clarification_service()
    
    if not clarification_service.model:
        print("❌ Text clarification service not available (check GOOGLE_API_KEY)")
        return
    
    print("🧪 Testing AI Text Clarification Service")
    print("=" * 80)
    
    for i, sample in enumerate(test_samples, 1):
        print(f"\n📄 Test Sample {i}: {sample['filename']}")
        print(f"Source: {sample['source_type']}")
        print("-" * 60)
        
        print("ORIGINAL OCR TEXT:")
        print(">" + "=" * 40)
        print(sample['text'])
        print(">" + "=" * 40)
        
        print("\n🤖 Clarifying text...")
        
        try:
            clarified_text = clarification_service.clarify_text(
                text=sample['text'],
                filename=sample['filename'],
                source_type=sample['source_type'],
                context="Test sample for text clarification"
            )
            
            print("\n✨ CLARIFIED TEXT:")
            print(">" + "=" * 40)
            print(clarified_text)
            print(">" + "=" * 40)
            
            # Show improvement metrics
            original_length = len(sample['text'])
            clarified_length = len(clarified_text)
            improvement_ratio = clarified_length / original_length if original_length > 0 else 0
            
            print(f"\n📊 Metrics:")
            print(f"   Original length: {original_length} chars")
            print(f"   Clarified length: {clarified_length} chars")
            print(f"   Length ratio: {improvement_ratio:.2f}x")
            print(f"   Status: {'✅ Improved' if clarified_text != sample['text'] else '⚠️ No change'}")
            
        except Exception as e:
            print(f"❌ Error clarifying text: {e}")
        
        print("\n" + "=" * 80)

def test_clarification_detection():
    """Test the text quality detection logic"""
    
    print("\n🔍 Testing Text Quality Detection")
    print("=" * 60)
    
    clarification_service = get_clarification_service()
    
    test_texts = [
        ("Good quality text", "This is well-formatted, clear text that doesn't need clarification.", False),
        ("OCR fragments", "Th|s |s fr4gm3nt3d t3xt w|th 0CR 3rr0rs", True),
        ("Excessive symbols", "Text!@#$%^&*()with!!!too???many###symbols", True), 
        ("Short fragments", "a b c d e f g h i j k l", True),
        ("Repeated chars", "Thissss texttttt hasssss repeateddddd charrrrrs", True),
        ("Normal document", "This is a normal business document with proper formatting and clear language.", False)
    ]
    
    for description, text, expected_clarification in test_texts:
        should_clarify = clarification_service.should_clarify_text(text, "OCR Image")
        status = "✅ Correct" if should_clarify == expected_clarification else "❌ Wrong"
        
        print(f"{description:20} | Should clarify: {should_clarify:5} | {status}")

def main():
    """Main test function"""
    try:
        test_clarification_detection()
        test_ocr_text_samples()
        
        print("\n🎉 Text clarification testing completed!")
        print("\nHow to use in your system:")
        print("1. OCR text is now automatically clarified when TEXT_CLARIFICATION_ENABLED=True")
        print("2. Both image files and scanned PDFs will benefit from clarification")
        print("3. The AI improves readability while preserving all original information")
        print("4. Configure settings in config.py for fine-tuning")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")

if __name__ == "__main__":
    main()
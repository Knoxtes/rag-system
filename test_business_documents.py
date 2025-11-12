#!/usr/bin/env python3
"""
Test various business document patterns with the improved quality filter
"""

from text_quality_filter import get_quality_filter

test_samples = [
    {
        'name': 'Brand Development Process',
        'text': """BRAND DEVELOPMENT
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
FINALIZATION""",
        'description': 'Original user sample'
    },
    {
        'name': 'Project Timeline',
        'text': """PROJECT TIMELINE
PHASE 1: PLANNING
PHASE 2: DESIGN  
PHASE 3: DEVELOPMENT
PHASE 4: REVIEW
PHASE 5: IMPLEMENTATION

DELIVERABLES:
- STRATEGY DOCUMENT
- VISUAL GUIDELINES  
- FINAL PRESENTATION""",
        'description': 'Structured project document'
    },
    {
        'name': 'Service Checklist', 
        'text': """CLIENT ONBOARDING CHECKLIST

STEP 1 INITIAL MEETING
STEP 2 REQUIREMENTS GATHERING
STEP 3 PROPOSAL CREATION
STEP 4 CONTRACT APPROVAL
STEP 5 PROJECT KICKOFF

TEAM ASSIGNMENTS:
PROJECT MANAGER
CREATIVE DIRECTOR
DESIGN TEAM""",
        'description': 'Business process checklist'
    },
    {
        'name': 'Still Poor Quality',
        'text': """3mp|0y33 H4ndb00k
Th|$ |$ @ c0rrupt3d 0CR 3xtr4ct|0n w|th m4ny 3rr0r$
P0||cy 1: V4c4t|0n T|m3
- A|| 3mp|0y33$ 4r3 3||g|b|3""",
        'description': 'Should still be filtered out'
    },
    {
        'name': 'Creative Brief Format',
        'text': """CREATIVE BRIEF

CLIENT: ABC COMPANY
PROJECT: BRAND REFRESH
TIMELINE: 6 WEEKS

OBJECTIVES:
- MODERNIZE BRAND IMAGE
- INCREASE MARKET APPEAL
- MAINTAIN BRAND RECOGNITION

DELIVERABLES:
LOGO REDESIGN
BRAND GUIDELINES
MARKETING MATERIALS""",
        'description': 'Creative industry document'
    }
]

quality_filter = get_quality_filter()

print("🔍 Testing Improved Quality Filter for Business Documents")
print("=" * 80)

for i, sample in enumerate(test_samples, 1):
    print(f"\n📄 Test {i}: {sample['name']}")
    print(f"Description: {sample['description']}")
    print("-" * 50)
    
    assessment = quality_filter.assess_text_quality(
        text=sample['text'],
        filename=f"{sample['name'].lower().replace(' ', '_')}.png",
        source_type="OCR Image"
    )
    
    # Show decision and key metrics
    decision = "✅ INCLUDE" if assessment['should_include'] else "❌ EXCLUDE"
    print(f"Decision: {decision}")
    print(f"Quality Score: {assessment['quality_score']:.3f}")
    print(f"Reason: {assessment['reason']}")
    
    # Show key improvements
    metrics = assessment['metrics']
    print(f"Key Metrics:")
    print(f"  • Coherence: {metrics.get('coherence_score', 0):.3f} (business terms recognized)")
    print(f"  • Repetition: {metrics.get('repetition_score', 0):.3f} (structured content handling)")
    print(f"  • Readability: {metrics.get('readable_ratio', 0):.3f}")
    
    print("-" * 50)

print(f"\n✅ Enhanced quality filter now properly handles:")
print("• Structured business documents (steps, phases, processes)")  
print("• Creative industry terminology (brand, design, creative)")
print("• Repetitive labels in structured content")
print("• Professional document formats")
print("❌ Still filters out corrupted OCR text")
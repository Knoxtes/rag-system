#!/usr/bin/env python3
"""
Test the specific brand development text sample
"""

from text_quality_filter import get_quality_filter

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

quality_filter = get_quality_filter()
assessment = quality_filter.assess_text_quality(test_text, 'brand_process.png', 'OCR Image')

print('Text sample:')
print('=' * 40)
print(test_text)
print('=' * 40)
print()
print('Quality Assessment:')
print(f'  Should Include: {assessment["should_include"]}')
print(f'  Quality Score: {assessment["quality_score"]:.3f}')
print(f'  Reason: {assessment["reason"]}')
print()
print('Detailed Metrics:')
for key, value in assessment['metrics'].items():
    if isinstance(value, float):
        print(f'  {key}: {value:.3f}')
    else:
        print(f'  {key}: {value}')
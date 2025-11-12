#!/usr/bin/env python3
"""
Text Quality Filter
Intelligent filtering to exclude low-quality, nonsensical, or corrupted text from indexing
"""

import re
import logging
from typing import Dict, List, Tuple, Optional
import string
from collections import Counter
from config import (
    TEXT_QUALITY_FILTER_ENABLED, QUALITY_MIN_READABLE_RATIO,
    QUALITY_MAX_SPECIAL_CHAR_RATIO, QUALITY_MIN_COHERENCE_SCORE,
    QUALITY_MIN_CONTENT_LENGTH, QUALITY_MIN_OVERALL_SCORE,
    QUALITY_OCR_THRESHOLD
)

logger = logging.getLogger(__name__)


class TextQualityFilter:
    """
    Analyzes text quality and determines if it should be included in the database
    """
    
    def __init__(self):
        # Quality thresholds from configuration
        self.min_word_length = 2
        self.min_readable_ratio = QUALITY_MIN_READABLE_RATIO
        self.max_special_char_ratio = QUALITY_MAX_SPECIAL_CHAR_RATIO 
        self.min_coherence_score = QUALITY_MIN_COHERENCE_SCORE
        self.min_meaningful_content_length = QUALITY_MIN_CONTENT_LENGTH
        self.min_overall_score = QUALITY_MIN_OVERALL_SCORE
        self.ocr_threshold = QUALITY_OCR_THRESHOLD
        
        # Common word patterns for coherence checking
        self.common_words = {
            'the', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with',
            'a', 'an', 'is', 'are', 'was', 'were', 'be', 'been', 'have', 'has', 'had',
            'this', 'that', 'these', 'those', 'it', 'they', 'we', 'you', 'he', 'she',
            'can', 'will', 'would', 'should', 'could', 'may', 'might', 'must',
            'one', 'two', 'first', 'last', 'new', 'old', 'good', 'great', 'small',
            'company', 'business', 'work', 'time', 'day', 'year', 'month', 'week',
            'policy', 'procedure', 'process', 'information', 'document', 'file',
            # Business/Creative terminology
            'brand', 'development', 'design', 'creative', 'concept', 'presentation',
            'visual', 'finalization', 'onboarding', 'brief', 'step', 'phase',
            'project', 'client', 'marketing', 'strategy', 'planning', 'review',
            'approval', 'guidelines', 'standards', 'requirements', 'deliverables',
            'timeline', 'schedule', 'meeting', 'team', 'department', 'manager',
            'employee', 'staff', 'service', 'solution', 'implementation'
        }
    
    def assess_text_quality(self, text: str, filename: str = "", source_type: str = "") -> Dict:
        """
        Comprehensive text quality assessment
        Returns assessment dict with quality metrics and decision
        """
        if not TEXT_QUALITY_FILTER_ENABLED:
            return {
                'should_include': True,
                'reason': 'Quality filtering disabled',
                'quality_score': 1.0,
                'metrics': {}
            }
            
        if not text or len(text.strip()) < 10:
            return {
                'should_include': False,
                'reason': 'Text too short or empty',
                'quality_score': 0.0,
                'metrics': {}
            }
        
        # Clean text for analysis
        text_clean = text.strip()
        
        # Calculate various quality metrics
        metrics = {
            'length': len(text_clean),
            'word_count': len(text_clean.split()),
            'readable_ratio': self._calculate_readable_ratio(text_clean),
            'special_char_ratio': self._calculate_special_char_ratio(text_clean),
            'coherence_score': self._calculate_coherence_score(text_clean),
            'repetition_score': self._calculate_repetition_score(text_clean),
            'ocr_error_score': self._calculate_ocr_error_score(text_clean),
            'meaningful_content_length': self._calculate_meaningful_content_length(text_clean),
            'language_coherence': self._assess_language_coherence(text_clean)
        }
        
        # Calculate overall quality score (0-1)
        quality_score = self._calculate_overall_quality_score(metrics)
        
        # Determine if text should be included
        should_include, reason = self._make_inclusion_decision(metrics, quality_score, source_type)
        
        return {
            'should_include': should_include,
            'reason': reason,
            'quality_score': quality_score,
            'metrics': metrics,
            'text_preview': text_clean[:100] + "..." if len(text_clean) > 100 else text_clean
        }
    
    def _calculate_readable_ratio(self, text: str) -> float:
        """Calculate ratio of readable words to total words"""
        words = re.findall(r'\b[a-zA-Z]+\b', text.lower())
        if not words:
            return 0.0
        
        readable_count = 0
        for word in words:
            # Consider word readable if it has reasonable character patterns
            if (len(word) >= self.min_word_length and 
                not re.search(r'(.)\1{3,}', word) and  # No excessive repetition
                re.match(r'^[a-z]+$', word)):  # Only letters
                readable_count += 1
        
        return readable_count / len(words)
    
    def _calculate_special_char_ratio(self, text: str) -> float:
        """Calculate ratio of special characters to total characters"""
        if not text:
            return 0.0
        
        special_chars = sum(1 for char in text if char not in string.ascii_letters + string.digits + string.whitespace)
        return special_chars / len(text)
    
    def _calculate_coherence_score(self, text: str) -> float:
        """Calculate text coherence based on common word presence"""
        words = re.findall(r'\b[a-zA-Z]+\b', text.lower())
        if not words:
            return 0.0
        
        common_word_count = sum(1 for word in words if word in self.common_words)
        base_coherence = min(common_word_count / len(words), 1.0)
        
        # Special handling for structured business documents
        # Check for business process indicators
        business_patterns = [
            r'\bstep\s*\d+\b',  # "step 1", "step 01", etc.
            r'\bphase\s*\d+\b', # "phase 1", etc.
            r'\bstage\s*\d+\b', # "stage 1", etc.
            r'\d+\s*\.\s*\w+',  # "1. Something", "01. Something"
            r'\b(development|design|creative|brand|process|procedure)\b',
            r'\b(onboarding|brief|presentation|finalization|implementation)\b',
            r'\b(strategy|planning|review|approval|guidelines)\b'
        ]
        
        # Boost coherence for structured business content
        business_indicators = 0
        text_lower = text.lower()
        for pattern in business_patterns:
            if re.search(pattern, text_lower):
                business_indicators += 1
        
        # Apply business content boost
        if business_indicators >= 2:
            business_boost = min(0.4, business_indicators * 0.1)  # Up to 0.4 boost
            base_coherence = min(1.0, base_coherence + business_boost)
        
        return base_coherence
    
    def _calculate_repetition_score(self, text: str) -> float:
        """Calculate excessive repetition score (higher = more repetitive = worse)"""
        words = re.findall(r'\b\w+\b', text.lower())
        if len(words) < 5:
            return 0.0
        
        word_counts = Counter(words)
        most_common = word_counts.most_common(1)[0][1] if word_counts else 1
        most_common_word = word_counts.most_common(1)[0][0] if word_counts else ""
        
        # Check if repetition is from structured content (labels, steps, etc.)
        structured_words = ['step', 'phase', 'stage', 'part', 'section', 'item', 'point']
        is_structured_repetition = most_common_word in structured_words
        
        # Normalize by text length
        repetition_score = most_common / len(words)
        
        # Reduce penalty for structured repetition
        if is_structured_repetition and repetition_score > 0.1:
            repetition_score *= 0.5  # Reduce penalty by half for structured content
        
        return min(repetition_score, 1.0)
    
    def _calculate_ocr_error_score(self, text: str) -> float:
        """Calculate OCR error indicators (higher = more errors = worse)"""
        error_indicators = [
            # Excessive mixed alphanumeric
            len(re.findall(r'\w*\d\w*[a-zA-Z]\w*', text)) / max(len(text.split()), 1),
            # Single character "words"
            len(re.findall(r'\b\w\b', text)) / max(len(text.split()), 1),
            # Excessive punctuation clustering
            len(re.findall(r'[^\w\s]{2,}', text)) / max(len(text), 1),
            # Common OCR character substitutions
            len(re.findall(r'[0-9][a-zA-Z]|[a-zA-Z][0-9]', text)) / max(len(text), 1)
        ]
        
        return min(sum(error_indicators), 1.0)
    
    def _calculate_meaningful_content_length(self, text: str) -> int:
        """Calculate length of meaningful content (excluding metadata, headers, etc.)"""
        # Remove common metadata patterns
        content = text
        
        # Remove file metadata patterns
        content = re.sub(r'\[.*?FILE:.*?\]', '', content)
        content = re.sub(r'OCR Confidence:.*?\n', '', content)
        content = re.sub(r'Detected Language:.*?\n', '', content)
        content = re.sub(r'--- .*? ---', '', content)
        
        # Remove excessive whitespace
        content = re.sub(r'\s+', ' ', content).strip()
        
        return len(content)
    
    def _assess_language_coherence(self, text: str) -> float:
        """Assess if text follows basic language patterns"""
        words = re.findall(r'\b[a-zA-Z]{2,}\b', text.lower())
        if len(words) < 3:
            return 0.0
        
        # Check for reasonable word length distribution
        word_lengths = [len(word) for word in words]
        avg_length = sum(word_lengths) / len(word_lengths)
        
        # Reasonable average word length (2-8 characters)
        length_score = 1.0 if 2 <= avg_length <= 8 else 0.5
        
        # Check for vowel presence (basic language indicator)
        vowel_words = [word for word in words if any(vowel in word for vowel in 'aeiou')]
        vowel_ratio = len(vowel_words) / len(words)
        
        # Most words should have vowels
        vowel_score = min(vowel_ratio * 2, 1.0)
        
        return (length_score + vowel_score) / 2
    
    def _calculate_overall_quality_score(self, metrics: Dict) -> float:
        """Calculate weighted overall quality score"""
        weights = {
            'readable_ratio': 0.25,
            'coherence_score': 0.20,
            'language_coherence': 0.20,
            'special_char_ratio': -0.15,  # Negative weight (more = worse)
            'repetition_score': -0.10,    # Negative weight
            'ocr_error_score': -0.10      # Negative weight
        }
        
        score = 0.0
        for metric, weight in weights.items():
            if metric in metrics:
                score += metrics[metric] * weight
        
        # Adjust for content length (very short content gets penalty)
        if metrics.get('meaningful_content_length', 0) < self.min_meaningful_content_length:
            score *= 0.7
        
        return max(0.0, min(1.0, score))
    
    def _make_inclusion_decision(self, metrics: Dict, quality_score: float, source_type: str) -> Tuple[bool, str]:
        """Make final decision on whether to include text in database"""
        
        # Hard exclusion criteria
        if metrics.get('meaningful_content_length', 0) < 20:
            return False, "Content too short after cleanup"
        
        if metrics.get('readable_ratio', 0) < 0.3:
            return False, f"Too many unreadable words ({metrics.get('readable_ratio', 0):.2f} readable ratio)"
        
        if metrics.get('special_char_ratio', 1) > 0.5:
            return False, f"Excessive special characters ({metrics.get('special_char_ratio', 0):.2f} ratio)"
        
        if metrics.get('ocr_error_score', 1) > 0.4:
            return False, f"High OCR error indicators ({metrics.get('ocr_error_score', 0):.2f} error score)"
        
        # Quality-based decision
        if quality_score < self.min_overall_score:
            return False, f"Overall quality too low ({quality_score:.2f})"
        
        # Lower threshold for known OCR sources (they're expected to be imperfect)
        if "ocr" in source_type.lower() or "image" in source_type.lower() or "scanned" in source_type.lower():
            if quality_score >= self.ocr_threshold:
                return True, f"OCR content meets minimum quality ({quality_score:.2f})"
            else:
                return False, f"OCR content quality too low ({quality_score:.2f})"
        
        # Standard threshold for other content
        if quality_score >= self.min_overall_score:
            return True, f"Content meets quality standards ({quality_score:.2f})"
        
        return False, f"Content quality below threshold ({quality_score:.2f})"
    
    def filter_text_batch(self, text_items: List[Dict]) -> List[Dict]:
        """Filter a batch of text items, returning only high-quality ones"""
        filtered_items = []
        stats = {'included': 0, 'excluded': 0, 'reasons': Counter()}
        
        for item in text_items:
            assessment = self.assess_text_quality(
                item.get('text', ''),
                item.get('filename', ''),
                item.get('source_type', '')
            )
            
            if assessment['should_include']:
                item['quality_assessment'] = assessment
                filtered_items.append(item)
                stats['included'] += 1
            else:
                stats['excluded'] += 1
                stats['reasons'][assessment['reason']] += 1
                logger.info(f"Excluded text from {item.get('filename', 'unknown')}: {assessment['reason']}")
        
        logger.info(f"Quality filter results: {stats['included']} included, {stats['excluded']} excluded")
        if stats['excluded'] > 0:
            logger.info(f"Exclusion reasons: {dict(stats['reasons'])}")
        
        return filtered_items


# Global filter instance
_quality_filter = None

def get_quality_filter() -> TextQualityFilter:
    """Get global text quality filter instance"""
    global _quality_filter
    if _quality_filter is None:
        _quality_filter = TextQualityFilter()
    return _quality_filter
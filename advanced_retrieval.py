# advanced_retrieval.py - Self-RAG and adaptive retrieval strategies

import numpy as np
from typing import List, Dict, Any, Optional, Tuple, Union
from dataclasses import dataclass, field
from enum import Enum
import logging
from sentence_transformers import CrossEncoder
import re
from collections import defaultdict
import time

logger = logging.getLogger(__name__)

class RetrievalQuality(Enum):
    """Quality assessment for retrieval results"""
    EXCELLENT = "excellent"
    GOOD = "good" 
    PARTIAL = "partial"
    POOR = "poor"
    INSUFFICIENT = "insufficient"

class QueryComplexity(Enum):
    """Query complexity classification"""
    SIMPLE = "simple"           # Single fact lookup
    MODERATE = "moderate"       # Multi-fact or filtered search  
    COMPLEX = "complex"         # Synthesis or comparison
    VERY_COMPLEX = "very_complex"  # Multi-hop reasoning

@dataclass
class RetrievalResult:
    """Enhanced retrieval result with quality metrics"""
    chunks: List[Dict[str, Any]]
    quality_score: float
    confidence: float
    coverage_score: float  # How well query is covered
    diversity_score: float # Source diversity
    retrieval_strategy: str
    reasoning_trace: List[str] = field(default_factory=list)
    
@dataclass  
class QueryIntent:
    """Classified query intent for adaptive retrieval"""
    intent_type: str  # search, synthesis, comparison, listing, etc.
    complexity: QueryComplexity
    requires_multiple_sources: bool
    expected_answer_type: str  # factual, list, summary, analysis
    domain_specific: bool
    temporal_scope: Optional[str]  # recent, historical, specific_date
    
class QueryClassifier:
    """
    Classifies queries to determine optimal retrieval strategy.
    Uses both rule-based and learned patterns.
    """
    
    def __init__(self):
        # Intent patterns (could be learned from data)
        self.intent_patterns = {
            'search': [
                r'\bwhat is\b', r'\bwho is\b', r'\bwhere is\b', r'\bwhen is\b',
                r'\bfind\b', r'\bshow me\b', r'\btell me\b'
            ],
            'synthesis': [
                r'\bsummarize\b', r'\bsummary\b', r'\boverview\b', r'\baggregate\b',
                r'\bcombine\b', r'\bmerge\b', r'\bunify\b'
            ],
            'comparison': [
                r'\bcompare\b', r'\bversus\b', r'\bvs\b', r'\bdifference\b',
                r'\bsimilar\b', r'\bcontrast\b', r'\bbetter\b', r'\bworse\b'
            ],
            'listing': [
                r'\blist\b', r'\bshow all\b', r'\ball\b.*\bthat\b', r'\bevery\b',
                r'\benumerate\b', r'\bcount\b', r'\bhow many\b'
            ],
            'analysis': [
                r'\banalyze\b', r'\bexplain why\b', r'\bhow does\b', r'\bwhat causes\b',
                r'\bimpact\b', r'\beffect\b', r'\breason\b'
            ]
        }
        
        self.complexity_indicators = {
            QueryComplexity.SIMPLE: [
                r'^\w+\s+(is|was|are|were)\s+', r'^\w+\s+definition', 
                r'^define\s+', r'^what\s+is\s+\w+\??$'
            ],
            QueryComplexity.MODERATE: [
                r'\bfor\s+\w+\s+market\b', r'\bin\s+(january|february|march|april|may|june|july|august|september|october|november|december)\b',
                r'\b(last|this|next)\s+(year|month|quarter)\b'
            ],
            QueryComplexity.COMPLEX: [
                r'\bcompare\b.*\band\b', r'\bsummarize\b.*\bacross\b', r'\ball\b.*\bfor\b',
                r'\bboth\b.*\band\b', r'\beach\b.*\bmarket\b'
            ],
            QueryComplexity.VERY_COMPLEX: [
                r'\banalyze\b.*\bimpact\b', r'\bhow\s+does\b.*\baffect\b', 
                r'\brelationship\s+between\b', r'\bcorrelation\b'
            ]
        }
    
    def classify_query(self, query: str) -> QueryIntent:
        """Classify query intent and complexity"""
        query_lower = query.lower()
        
        # Determine intent type
        intent_type = 'search'  # default
        for intent, patterns in self.intent_patterns.items():
            for pattern in patterns:
                if re.search(pattern, query_lower, re.IGNORECASE):
                    intent_type = intent
                    break
            if intent_type != 'search':
                break
        
        # Determine complexity
        complexity = QueryComplexity.SIMPLE  # default
        for comp_level, patterns in self.complexity_indicators.items():
            for pattern in patterns:
                if re.search(pattern, query_lower, re.IGNORECASE):
                    complexity = comp_level
                    break
            if complexity != QueryComplexity.SIMPLE:
                break
        
        # Additional complexity factors
        word_count = len(query.split())
        if word_count > 15:
            complexity = max(complexity, QueryComplexity.MODERATE)
        if word_count > 25:
            complexity = max(complexity, QueryComplexity.COMPLEX)
        
        # Check if requires multiple sources
        requires_multiple = any([
            intent_type in ['synthesis', 'comparison', 'analysis'],
            'all' in query_lower,
            'compare' in query_lower,
            'across' in query_lower,
            complexity == QueryComplexity.COMPLEX
        ])
        
        # Determine expected answer type
        if intent_type == 'listing':
            answer_type = 'list'
        elif intent_type == 'synthesis':
            answer_type = 'summary'  
        elif intent_type == 'comparison':
            answer_type = 'analysis'
        elif intent_type == 'analysis':
            answer_type = 'analysis'
        else:
            answer_type = 'factual'
        
        # Check for domain specificity
        domain_indicators = ['market', 'sales', 'revenue', 'project', 'client', 'budget']
        domain_specific = any(indicator in query_lower for indicator in domain_indicators)
        
        # Detect temporal scope
        temporal_scope = None
        if re.search(r'\b(recent|latest|new|current)\b', query_lower):
            temporal_scope = 'recent'
        elif re.search(r'\b(historical|past|previous|old)\b', query_lower):
            temporal_scope = 'historical'  
        elif re.search(r'\b(january|february|march|april|may|june|july|august|september|october|november|december|\d{4})\b', query_lower):
            temporal_scope = 'specific_date'
        
        return QueryIntent(
            intent_type=intent_type,
            complexity=complexity,
            requires_multiple_sources=requires_multiple,
            expected_answer_type=answer_type,
            domain_specific=domain_specific,
            temporal_scope=temporal_scope
        )

class RetrievalQualityAssessor:
    """
    Assesses the quality of retrieval results using multiple criteria.
    Used by Self-RAG to determine if re-retrieval is needed.
    """
    
    def __init__(self, model_name: str = "cross-encoder/ms-marco-MiniLM-L-6-v2"):
        """Initialize with a cross-encoder for quality assessment"""
        self.cross_encoder = CrossEncoder(model_name)
        
    def assess_retrieval_quality(self, 
                               query: str, 
                               chunks: List[Dict[str, Any]], 
                               intent: QueryIntent) -> RetrievalResult:
        """
        Comprehensive quality assessment of retrieval results.
        
        Args:
            query: Original user query
            chunks: Retrieved document chunks
            intent: Classified query intent
            
        Returns:
            RetrievalResult with quality metrics
        """
        if not chunks:
            return RetrievalResult(
                chunks=[],
                quality_score=0.0,
                confidence=0.0,
                coverage_score=0.0,
                diversity_score=0.0,
                retrieval_strategy="none"
            )
        
        # 1. Relevance Assessment
        relevance_scores = self._assess_relevance(query, chunks)
        avg_relevance = np.mean(relevance_scores)
        
        # 2. Coverage Assessment  
        coverage_score = self._assess_coverage(query, chunks, intent)
        
        # 3. Diversity Assessment
        diversity_score = self._assess_diversity(chunks)
        
        # 4. Sufficiency Assessment (enough information for answer)
        sufficiency_score = self._assess_sufficiency(query, chunks, intent)
        
        # 5. Coherence Assessment (results work well together)
        coherence_score = self._assess_coherence(chunks)
        
        # Overall quality score (weighted combination)
        quality_score = (
            avg_relevance * 0.3 +
            coverage_score * 0.25 +
            sufficiency_score * 0.25 +
            diversity_score * 0.1 +
            coherence_score * 0.1
        )
        
        # Confidence score (how sure we are about the assessment)
        confidence = self._calculate_confidence(chunks, relevance_scores, intent)
        
        # Generate reasoning trace
        reasoning_trace = [
            f"Relevance: {avg_relevance:.2f} (avg of {len(relevance_scores)} chunks)",
            f"Coverage: {coverage_score:.2f}",
            f"Sufficiency: {sufficiency_score:.2f}",
            f"Diversity: {diversity_score:.2f} ({len(set(c.get('source_path', '') for c in chunks))} unique sources)",
            f"Coherence: {coherence_score:.2f}",
            f"Overall Quality: {quality_score:.2f}"
        ]
        
        return RetrievalResult(
            chunks=chunks,
            quality_score=quality_score,
            confidence=confidence,
            coverage_score=coverage_score,
            diversity_score=diversity_score,
            retrieval_strategy="standard",
            reasoning_trace=reasoning_trace
        )
    
    def _assess_relevance(self, query: str, chunks: List[Dict[str, Any]]) -> List[float]:
        """Assess relevance of each chunk to the query"""
        if not chunks:
            return []
        
        # Extract text content from chunks
        texts = [chunk.get('snippet', chunk.get('context', '')) for chunk in chunks]
        
        # Use cross-encoder to score relevance
        pairs = [[query, text] for text in texts]
        scores = self.cross_encoder.predict(pairs)
        
        # Normalize scores to 0-1 range
        normalized_scores = [(score + 1) / 2 for score in scores]  # Cross-encoder returns -1 to 1
        
        return normalized_scores
    
    def _assess_coverage(self, query: str, chunks: List[Dict[str, Any]], intent: QueryIntent) -> float:
        """Assess how well the chunks cover the query requirements"""
        
        # Extract key concepts from query
        query_concepts = self._extract_concepts(query)
        
        # Extract concepts from retrieved chunks
        chunk_texts = [chunk.get('snippet', chunk.get('context', '')) for chunk in chunks]
        chunk_concepts = set()
        for text in chunk_texts:
            chunk_concepts.update(self._extract_concepts(text))
        
        # Calculate coverage
        if not query_concepts:
            return 1.0
        
        covered_concepts = query_concepts.intersection(chunk_concepts)
        coverage_ratio = len(covered_concepts) / len(query_concepts)
        
        # Boost coverage for multi-source requirements
        if intent.requires_multiple_sources:
            unique_sources = len(set(c.get('source_path', '') for c in chunks))
            source_diversity_bonus = min(unique_sources / 3.0, 0.3)  # Up to 30% bonus
            coverage_ratio += source_diversity_bonus
        
        return min(coverage_ratio, 1.0)
    
    def _assess_diversity(self, chunks: List[Dict[str, Any]]) -> float:
        """Assess diversity of sources and content"""
        if len(chunks) <= 1:
            return 0.0
        
        # Source diversity
        unique_sources = set(chunk.get('source_path', '') for chunk in chunks)
        source_diversity = len(unique_sources) / len(chunks)
        
        # Content diversity (simple text similarity)
        texts = [chunk.get('snippet', chunk.get('context', ''))[:200] for chunk in chunks]
        diversity_sum = 0.0
        count = 0
        
        for i in range(len(texts)):
            for j in range(i + 1, len(texts)):
                # Simple diversity measure (could use embeddings for better accuracy)
                text1_words = set(texts[i].lower().split())
                text2_words = set(texts[j].lower().split())
                if text1_words and text2_words:
                    jaccard = len(text1_words.intersection(text2_words)) / len(text1_words.union(text2_words))
                    diversity_sum += (1 - jaccard)  # Higher diversity = lower overlap
                    count += 1
        
        content_diversity = diversity_sum / max(count, 1)
        
        # Combine source and content diversity
        return (source_diversity * 0.6) + (content_diversity * 0.4)
    
    def _assess_sufficiency(self, query: str, chunks: List[Dict[str, Any]], intent: QueryIntent) -> float:
        """Assess if there's sufficient information to answer the query"""
        
        # Total content length
        total_chars = sum(len(chunk.get('snippet', chunk.get('context', ''))) for chunk in chunks)
        
        # Expected content thresholds by intent type
        thresholds = {
            'search': 500,        # Simple fact lookup
            'synthesis': 2000,    # Need substantial content for synthesis
            'comparison': 1500,   # Need content from multiple sources
            'listing': 800,       # Need comprehensive list
            'analysis': 1800      # Need detailed information
        }
        
        expected_length = thresholds.get(intent.intent_type, 800)
        length_score = min(total_chars / expected_length, 1.0)
        
        # Source count requirement
        source_count = len(set(c.get('source_path', '') for c in chunks))
        
        expected_sources = {
            'search': 1,
            'synthesis': 3,
            'comparison': 2, 
            'listing': 2,
            'analysis': 2
        }
        
        required_sources = expected_sources.get(intent.intent_type, 1)
        source_score = min(source_count / required_sources, 1.0)
        
        # Combine length and source scores
        return (length_score * 0.7) + (source_score * 0.3)
    
    def _assess_coherence(self, chunks: List[Dict[str, Any]]) -> float:
        """Assess if chunks work well together (not contradictory)"""
        if len(chunks) <= 1:
            return 1.0
        
        # Simple coherence check - look for contradictory terms
        contradictory_pairs = [
            ('increase', 'decrease'), ('up', 'down'), ('more', 'less'),
            ('positive', 'negative'), ('good', 'bad'), ('success', 'failure')
        ]
        
        texts = [chunk.get('snippet', chunk.get('context', '')).lower() for chunk in chunks]
        combined_text = ' '.join(texts)
        
        contradiction_score = 0
        for term1, term2 in contradictory_pairs:
            if term1 in combined_text and term2 in combined_text:
                contradiction_score += 1
        
        # Simple coherence score (could be much more sophisticated)
        coherence = max(0, 1.0 - (contradiction_score * 0.2))
        return coherence
    
    def _extract_concepts(self, text: str) -> set:
        """Simple concept extraction (could use NER or more advanced methods)"""
        # Remove common words and extract meaningful terms
        stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'is', 'are', 'was', 'were'}
        words = re.findall(r'\b[a-zA-Z]{3,}\b', text.lower())
        concepts = {word for word in words if word not in stop_words and len(word) > 3}
        return concepts
    
    def _calculate_confidence(self, chunks: List[Dict[str, Any]], relevance_scores: List[float], intent: QueryIntent) -> float:
        """Calculate confidence in the quality assessment"""
        if not chunks or not relevance_scores:
            return 0.0
        
        # Factors affecting confidence
        score_variance = np.var(relevance_scores) if len(relevance_scores) > 1 else 0
        avg_score = np.mean(relevance_scores)
        chunk_count = len(chunks)
        
        # High confidence when:
        # - High average relevance scores
        # - Low variance in scores (consistent quality)
        # - Appropriate number of chunks for intent
        
        score_confidence = avg_score
        variance_confidence = max(0, 1 - score_variance)  # Lower variance = higher confidence
        
        # Expected chunk count by intent
        expected_chunks = {
            'search': 3,
            'synthesis': 8,
            'comparison': 5,
            'listing': 6,
            'analysis': 5
        }
        
        target_chunks = expected_chunks.get(intent.intent_type, 5)
        count_confidence = 1 - abs(chunk_count - target_chunks) / max(target_chunks, chunk_count)
        
        overall_confidence = (score_confidence * 0.5 + variance_confidence * 0.3 + count_confidence * 0.2)
        return max(0, min(1, overall_confidence))

class AdaptiveRetriever:
    """
    Adaptive retrieval engine that uses Self-RAG principles to iteratively improve results.
    Automatically adjusts parameters and strategies based on query requirements and result quality.
    """
    
    def __init__(self, 
                 base_retriever,  # Your existing RAG system
                 quality_assessor: RetrievalQualityAssessor,
                 query_classifier: QueryClassifier,
                 min_quality_threshold: float = 0.7,
                 max_iterations: int = 3):
        """
        Initialize adaptive retriever.
        
        Args:
            base_retriever: Existing retrieval system (RAG system)
            quality_assessor: Quality assessment component
            query_classifier: Query intent classifier
            min_quality_threshold: Minimum quality to accept results
            max_iterations: Maximum self-refinement iterations
        """
        self.base_retriever = base_retriever
        self.quality_assessor = quality_assessor
        self.query_classifier = query_classifier
        self.min_quality_threshold = min_quality_threshold
        self.max_iterations = max_iterations
        
        # Adaptive parameters
        self.strategy_stats = defaultdict(list)  # Track strategy performance
        
    def retrieve_adaptive(self, query: str, **kwargs) -> RetrievalResult:
        """
        Adaptive retrieval with quality gates and iterative refinement.
        
        Args:
            query: User query
            **kwargs: Additional parameters for base retriever
            
        Returns:
            RetrievalResult with best available results
        """
        logger.info(f"Starting adaptive retrieval for: '{query[:50]}...'")
        
        # 1. Classify query intent
        intent = self.query_classifier.classify_query(query)
        logger.info(f"Query classification: {intent.intent_type} ({intent.complexity.value})")
        
        # 2. Determine initial retrieval strategy
        retrieval_params = self._get_strategy_params(intent)
        logger.info(f"Initial strategy: {retrieval_params}")
        
        best_result = None
        iteration = 0
        
        while iteration < self.max_iterations:
            iteration += 1
            logger.info(f"Retrieval iteration {iteration}/{self.max_iterations}")
            
            # 3. Execute retrieval with current parameters
            try:
                chunks = self._execute_retrieval(query, retrieval_params, **kwargs)
                
                # 4. Assess quality
                result = self.quality_assessor.assess_retrieval_quality(query, chunks, intent)
                result.retrieval_strategy = retrieval_params.get('strategy_name', 'unknown')
                
                logger.info(f"Quality assessment - Score: {result.quality_score:.2f}, Confidence: {result.confidence:.2f}")
                
                # 5. Check if result meets quality threshold
                if result.quality_score >= self.min_quality_threshold or result.quality_score > (best_result.quality_score if best_result else 0):
                    best_result = result
                    
                    if result.quality_score >= self.min_quality_threshold:
                        logger.info("Quality threshold met - stopping iterations")
                        break
                
                # 6. If quality insufficient, adapt strategy for next iteration
                if iteration < self.max_iterations:
                    retrieval_params = self._adapt_strategy(query, result, intent, iteration)
                    logger.info(f"Adapting strategy: {retrieval_params}")
                
            except Exception as e:
                logger.error(f"Retrieval iteration {iteration} failed: {e}")
                break
        
        # 7. Record strategy performance for learning
        if best_result:
            self._record_performance(intent, best_result)
        
        # 8. Return best result found
        if best_result is None:
            logger.warning("No successful retrieval results obtained")
            return RetrievalResult(
                chunks=[],
                quality_score=0.0,
                confidence=0.0,
                coverage_score=0.0,
                diversity_score=0.0,
                retrieval_strategy="failed"
            )
        
        logger.info(f"Adaptive retrieval complete - Final quality: {best_result.quality_score:.2f}")
        return best_result
    
    def _get_strategy_params(self, intent: QueryIntent) -> Dict[str, Any]:
        """Determine optimal retrieval parameters based on intent"""
        
        base_params = {
            'strategy_name': 'default',
            'top_k': 20,
            'rerank_top_k': 10,
            'diversity_threshold': 0.85,
            'use_hybrid': True,
            'use_multi_query': False,
            'context_window': 8000
        }
        
        # Adapt based on intent type
        if intent.intent_type == 'synthesis':
            base_params.update({
                'strategy_name': 'synthesis',
                'top_k': 30,
                'rerank_top_k': 20,
                'use_multi_query': True,
                'context_window': 15000,
                'diversity_threshold': 0.75
            })
        
        elif intent.intent_type == 'comparison':
            base_params.update({
                'strategy_name': 'comparison', 
                'top_k': 25,
                'rerank_top_k': 15,
                'use_multi_query': True,
                'diversity_threshold': 0.70,
                'ensure_multiple_sources': True
            })
        
        elif intent.intent_type == 'listing':
            base_params.update({
                'strategy_name': 'listing',
                'top_k': 35,
                'rerank_top_k': 25,
                'diversity_threshold': 0.60,
                'favor_comprehensive': True
            })
        
        elif intent.complexity == QueryComplexity.SIMPLE:
            base_params.update({
                'strategy_name': 'simple',
                'top_k': 10,
                'rerank_top_k': 5,
                'context_window': 4000
            })
        
        # Temporal scope adaptations
        if intent.temporal_scope == 'recent':
            base_params['favor_recent'] = True
        elif intent.temporal_scope == 'specific_date':
            base_params['date_filtering'] = True
        
        return base_params
    
    def _execute_retrieval(self, query: str, params: Dict[str, Any], **kwargs) -> List[Dict[str, Any]]:
        """Execute retrieval with specified parameters"""
        
        # This would integrate with your existing RAG system
        # For now, simulating the interface
        
        try:
            # Call your existing retrieval method with adapted parameters
            if hasattr(self.base_retriever, '_tool_rag_search'):
                # Use your existing RAG search
                result_json = self.base_retriever._tool_rag_search(query)
                import json
                if isinstance(result_json, str):
                    chunks = json.loads(result_json)
                    if isinstance(chunks, list):
                        return chunks
                    elif isinstance(chunks, dict) and 'error' not in chunks:
                        return []
                    else:
                        return []
                else:
                    return result_json or []
            
            else:
                # Fallback to basic retrieval
                logger.warning("Using fallback retrieval method")
                return []
                
        except Exception as e:
            logger.error(f"Retrieval execution failed: {e}")
            return []
    
    def _adapt_strategy(self, query: str, current_result: RetrievalResult, intent: QueryIntent, iteration: int) -> Dict[str, Any]:
        """Adapt retrieval strategy based on current result quality"""
        
        # Start with current successful strategy params
        base_params = self._get_strategy_params(intent).copy()
        
        # Diagnose issues and adapt
        if current_result.coverage_score < 0.5:
            # Poor coverage - need more diverse results
            base_params.update({
                'top_k': min(base_params['top_k'] * 1.5, 50),
                'diversity_threshold': max(base_params['diversity_threshold'] - 0.1, 0.5),
                'use_multi_query': True
            })
            base_params['strategy_name'] += '_expanded_coverage'
            
        elif current_result.diversity_score < 0.3 and intent.requires_multiple_sources:
            # Low diversity - need more sources
            base_params.update({
                'diversity_threshold': base_params['diversity_threshold'] - 0.15,
                'ensure_multiple_sources': True,
                'favor_source_diversity': True
            })
            base_params['strategy_name'] += '_increased_diversity'
            
        elif len(current_result.chunks) < 3:
            # Too few results - expand search
            base_params.update({
                'top_k': base_params['top_k'] * 2,
                'lower_threshold': True
            })
            base_params['strategy_name'] += '_expanded_search'
            
        else:
            # Try alternative strategies
            if iteration == 2:
                # Second iteration - try different approach
                base_params.update({
                    'strategy_name': 'alternative_approach',
                    'use_alternative_embeddings': True,
                    'different_chunking': True
                })
            elif iteration == 3:
                # Final iteration - most permissive
                base_params.update({
                    'strategy_name': 'permissive',
                    'top_k': 50,
                    'diversity_threshold': 0.3,
                    'lower_quality_threshold': True
                })
        
        return base_params
    
    def _record_performance(self, intent: QueryIntent, result: RetrievalResult):
        """Record strategy performance for learning"""
        strategy_key = f"{intent.intent_type}_{intent.complexity.value}"
        
        performance_record = {
            'strategy': result.retrieval_strategy,
            'quality_score': result.quality_score,
            'confidence': result.confidence,
            'timestamp': time.time()
        }
        
        self.strategy_stats[strategy_key].append(performance_record)
        
        # Keep only recent records (last 100 per strategy)
        if len(self.strategy_stats[strategy_key]) > 100:
            self.strategy_stats[strategy_key] = self.strategy_stats[strategy_key][-100:]
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """Get performance statistics for all strategies"""
        stats = {}
        
        for strategy_key, records in self.strategy_stats.items():
            if records:
                qualities = [r['quality_score'] for r in records]
                confidences = [r['confidence'] for r in records]
                
                stats[strategy_key] = {
                    'count': len(records),
                    'avg_quality': np.mean(qualities),
                    'avg_confidence': np.mean(confidences),
                    'success_rate': sum(1 for q in qualities if q >= self.min_quality_threshold) / len(qualities),
                    'recent_trend': np.mean(qualities[-10:]) if len(qualities) >= 10 else np.mean(qualities)
                }
        
        return stats


# Example usage and testing
if __name__ == "__main__":
    # Initialize components
    classifier = QueryClassifier()
    assessor = RetrievalQualityAssessor()
    
    # Test query classification
    test_queries = [
        "What is the Q1 sales figure for Elmira?",
        "Compare Mansfield and Elmira market performance",
        "Summarize all 2025 projects across markets",
        "List packages available for Christmas promotion",
        "How does market size affect revenue projections?"
    ]
    
    print("=== Query Classification Test ===")
    for query in test_queries:
        intent = classifier.classify_query(query)
        print(f"\nQuery: {query}")
        print(f"  Intent: {intent.intent_type}")
        print(f"  Complexity: {intent.complexity.value}")
        print(f"  Multi-source: {intent.requires_multiple_sources}")
        print(f"  Answer type: {intent.expected_answer_type}")
        print(f"  Temporal: {intent.temporal_scope}")
    
    # Test quality assessment with mock data
    print("\n=== Quality Assessment Test ===")
    
    mock_chunks = [
        {
            'snippet': 'Q1 sales for Elmira market reached $2.1M, up 15% from previous quarter.',
            'source_path': '/sales/Q1_reports/elmira_summary.pdf',
            'relevance': 0.95
        },
        {
            'snippet': 'Elmira market showed strong performance in January and February.',
            'source_path': '/sales/monthly/elmira_jan_feb.xlsx', 
            'relevance': 0.82
        },
        {
            'snippet': 'Marketing campaigns in Elmira resulted in increased customer acquisition.',
            'source_path': '/marketing/campaigns/elmira_results.docx',
            'relevance': 0.71
        }
    ]
    
    test_query = "What is the Q1 sales figure for Elmira?"
    test_intent = classifier.classify_query(test_query)
    
    assessment = assessor.assess_retrieval_quality(test_query, mock_chunks, test_intent)
    
    print(f"Query: {test_query}")
    print(f"Quality Score: {assessment.quality_score:.2f}")
    print(f"Confidence: {assessment.confidence:.2f}")
    print(f"Coverage: {assessment.coverage_score:.2f}")
    print(f"Diversity: {assessment.diversity_score:.2f}")
    print("\nReasoning Trace:")
    for trace in assessment.reasoning_trace:
        print(f"  - {trace}")
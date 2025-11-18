"""
Performance monitoring utilities for production
Tracks query performance, cache hit rates, and API costs
"""

import time
import json
import os
from datetime import datetime
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict
from collections import defaultdict


@dataclass
class QueryMetrics:
    """Metrics for a single query"""
    timestamp: str
    query: str
    response_time: float
    cache_hit: bool
    api_calls: int
    tokens_used: int
    cost_usd: float
    collection: str
    success: bool
    error: Optional[str] = None


class PerformanceMonitor:
    """
    Monitor and track system performance metrics
    """
    
    def __init__(self, metrics_file: str = 'logs/performance_metrics.json'):
        self.metrics_file = metrics_file
        self.metrics: List[QueryMetrics] = []
        self.session_stats = {
            'queries_total': 0,
            'queries_cached': 0,
            'queries_failed': 0,
            'total_response_time': 0,
            'total_api_calls': 0,
            'total_tokens': 0,
            'total_cost': 0,
        }
        
        # Create logs directory if it doesn't exist
        os.makedirs(os.path.dirname(metrics_file), exist_ok=True)
    
    def record_query(self, metrics: QueryMetrics):
        """Record metrics for a single query"""
        self.metrics.append(metrics)
        
        # Update session stats
        self.session_stats['queries_total'] += 1
        if metrics.cache_hit:
            self.session_stats['queries_cached'] += 1
        if not metrics.success:
            self.session_stats['queries_failed'] += 1
        self.session_stats['total_response_time'] += metrics.response_time
        self.session_stats['total_api_calls'] += metrics.api_calls
        self.session_stats['total_tokens'] += metrics.tokens_used
        self.session_stats['total_cost'] += metrics.cost_usd
    
    def get_cache_hit_rate(self) -> float:
        """Calculate cache hit rate percentage"""
        if self.session_stats['queries_total'] == 0:
            return 0.0
        return (self.session_stats['queries_cached'] / self.session_stats['queries_total']) * 100
    
    def get_average_response_time(self) -> float:
        """Calculate average response time in seconds"""
        if self.session_stats['queries_total'] == 0:
            return 0.0
        return self.session_stats['total_response_time'] / self.session_stats['queries_total']
    
    def get_error_rate(self) -> float:
        """Calculate error rate percentage"""
        if self.session_stats['queries_total'] == 0:
            return 0.0
        return (self.session_stats['queries_failed'] / self.session_stats['queries_total']) * 100
    
    def get_summary(self) -> Dict:
        """Get summary of performance metrics"""
        return {
            'total_queries': self.session_stats['queries_total'],
            'cache_hit_rate_percent': round(self.get_cache_hit_rate(), 2),
            'average_response_time_seconds': round(self.get_average_response_time(), 2),
            'error_rate_percent': round(self.get_error_rate(), 2),
            'total_api_calls': self.session_stats['total_api_calls'],
            'total_tokens_used': self.session_stats['total_tokens'],
            'total_cost_usd': round(self.session_stats['total_cost'], 4),
        }
    
    def save_metrics(self):
        """Save metrics to file"""
        try:
            data = {
                'summary': self.get_summary(),
                'session_start': self.metrics[0].timestamp if self.metrics else None,
                'session_end': self.metrics[-1].timestamp if self.metrics else None,
                'queries': [asdict(m) for m in self.metrics]
            }
            
            with open(self.metrics_file, 'w') as f:
                json.dump(data, f, indent=2)
            
            return True
        except Exception as e:
            print(f"Failed to save metrics: {e}")
            return False
    
    def load_metrics(self) -> bool:
        """Load metrics from file"""
        try:
            if not os.path.exists(self.metrics_file):
                return False
            
            with open(self.metrics_file, 'r') as f:
                data = json.load(f)
            
            # Reconstruct metrics
            self.metrics = [
                QueryMetrics(**m) for m in data.get('queries', [])
            ]
            
            # Recalculate session stats
            for m in self.metrics:
                self.session_stats['queries_total'] += 1
                if m.cache_hit:
                    self.session_stats['queries_cached'] += 1
                if not m.success:
                    self.session_stats['queries_failed'] += 1
                self.session_stats['total_response_time'] += m.response_time
                self.session_stats['total_api_calls'] += m.api_calls
                self.session_stats['total_tokens'] += m.tokens_used
                self.session_stats['total_cost'] += m.cost_usd
            
            return True
        except Exception as e:
            print(f"Failed to load metrics: {e}")
            return False
    
    def print_summary(self):
        """Print performance summary"""
        summary = self.get_summary()
        
        print("\n" + "=" * 60)
        print("PERFORMANCE SUMMARY")
        print("=" * 60)
        print(f"Total Queries:        {summary['total_queries']}")
        print(f"Cache Hit Rate:       {summary['cache_hit_rate_percent']}%")
        print(f"Avg Response Time:    {summary['average_response_time_seconds']}s")
        print(f"Error Rate:           {summary['error_rate_percent']}%")
        print(f"Total API Calls:      {summary['total_api_calls']}")
        print(f"Total Tokens:         {summary['total_tokens_used']:,}")
        print(f"Total Cost:           ${summary['total_cost_usd']:.4f}")
        print("=" * 60 + "\n")


# Global performance monitor instance
_monitor = None


def get_performance_monitor() -> PerformanceMonitor:
    """Get or create global performance monitor instance"""
    global _monitor
    if _monitor is None:
        _monitor = PerformanceMonitor()
    return _monitor


# Context manager for timing operations
class Timer:
    """Context manager for timing code blocks"""
    
    def __init__(self, name: str = "Operation"):
        self.name = name
        self.start_time = None
        self.elapsed = None
    
    def __enter__(self):
        self.start_time = time.time()
        return self
    
    def __exit__(self, *args):
        self.elapsed = time.time() - self.start_time
    
    def __str__(self):
        return f"{self.name}: {self.elapsed:.3f}s"


# Example usage:
# from performance_monitor import get_performance_monitor, QueryMetrics, Timer
# 
# monitor = get_performance_monitor()
# 
# with Timer("Query execution") as t:
#     # ... perform query ...
#     pass
# 
# metrics = QueryMetrics(
#     timestamp=datetime.now().isoformat(),
#     query="What is the Q1 report?",
#     response_time=t.elapsed,
#     cache_hit=False,
#     api_calls=1,
#     tokens_used=1500,
#     cost_usd=0.002,
#     collection="sales_data",
#     success=True
# )
# 
# monitor.record_query(metrics)
# monitor.print_summary()
# monitor.save_metrics()

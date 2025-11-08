"""
TruthLens Enhanced AI Services

Lightweight AI enhancement system for improved performance and accuracy
while maintaining minimal resource usage.
"""

# Import core components
try:
    from .lightweight_enhancer import lightweight_ai
    from .cache_manager import ai_cache
    from .batch_processor import queue_analysis, process_urgent, flush_queue, get_processing_status
    from .performance_monitor import performance_monitor, monitor_performance
    
    ENHANCED_AI_AVAILABLE = True
except ImportError as e:
    print(f"Enhanced AI services not available: {e}")
    ENHANCED_AI_AVAILABLE = False

__all__ = [
    'lightweight_ai',
    'ai_cache', 
    'queue_analysis',
    'process_urgent',
    'flush_queue',
    'get_processing_status',
    'performance_monitor',
    'monitor_performance',
    'ENHANCED_AI_AVAILABLE'
]
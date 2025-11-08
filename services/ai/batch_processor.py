import asyncio
import time
from typing import List, Dict, Any, Tuple
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass

from .lightweight_enhancer import lightweight_ai
from .cache_manager import ai_cache, batch_cache_analysis


@dataclass
class BatchAnalysisRequest:
    content: str
    url: str = ""
    market_id: str = ""
    priority: int = 1  # 1=high, 2=medium, 3=low


class OptimizedBatchProcessor:
    """Optimized batch processing for AI analysis"""
    
    def __init__(self, max_workers: int = 3, batch_size: int = 10):
        self.max_workers = max_workers
        self.batch_size = batch_size
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
        self.processing_queue = []
        
    def add_to_queue(self, request: BatchAnalysisRequest):
        """Add analysis request to processing queue"""
        self.processing_queue.append(request)
        
        # Auto-process when batch is full
        if len(self.processing_queue) >= self.batch_size:
            return self.process_batch()
        
        return None
    
    def process_batch(self) -> List[Dict[str, Any]]:
        """Process entire queue in optimized batches"""
        if not self.processing_queue:
            return []
        
        # Sort by priority
        self.processing_queue.sort(key=lambda x: x.priority)
        
        # Split into batches
        batches = [
            self.processing_queue[i:i + self.batch_size]
            for i in range(0, len(self.processing_queue), self.batch_size)
        ]
        
        all_results = []
        
        # Process batches in parallel
        future_to_batch = {}
        
        for batch in batches:
            future = self.executor.submit(self._process_single_batch, batch)
            future_to_batch[future] = batch
        
        # Collect results
        for future in as_completed(future_to_batch):
            batch_results = future.result()
            all_results.extend(batch_results)
        
        # Clear queue
        self.processing_queue.clear()
        
        return all_results
    
    def _process_single_batch(self, batch: List[BatchAnalysisRequest]) -> List[Dict[str, Any]]:
        """Process a single batch efficiently"""
        results = []
        
        # Prepare batch items for caching analysis
        batch_items = [(req.content, req.url) for req in batch]
        
        # Use intelligent batch caching
        cached_results = batch_cache_analysis(
            analysis_func=self._analyze_single_item,
            items=batch_items,
            ttl=1800
        )
        
        # Combine with request metadata
        for i, (result, request) in enumerate(zip(cached_results, batch)):
            if result:
                result['market_id'] = request.market_id
                result['priority'] = request.priority
                result['batch_index'] = i
                results.append(result)
        
        return results
    
    def _analyze_single_item(self, content: str, url: str = "") -> Dict[str, Any]:
        """Analyze single item with fallback strategy"""
        try:
            # Try fast pattern analysis first
            pattern_result = lightweight_ai.fast_pattern_analysis(content)
            domain_result = lightweight_ai.fast_domain_analysis(url) if url else {}
            
            # If high confidence from patterns, use fast analysis
            if pattern_result.get('overall_manipulation_risk', 0) > 0.7 or \
               domain_result.get('domain_score', 50) < 30:
                return lightweight_ai._fast_fallback_analysis(content, url)
            
            # Otherwise, use enhanced AI if needed
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            try:
                result = loop.run_until_complete(
                    lightweight_ai.analyze_content_enhanced(content, url)
                )
                return result
            finally:
                loop.close()
                
        except Exception as e:
            print(f"Batch analysis error: {e}")
            return lightweight_ai._fast_fallback_analysis(content, url)
    
    def process_high_priority(self, requests: List[BatchAnalysisRequest]) -> List[Dict[str, Any]]:
        """Fast-track processing for high priority requests"""
        
        # Filter high priority items
        high_priority = [req for req in requests if req.priority == 1]
        
        if not high_priority:
            return []
        
        # Process immediately with maximum parallel execution
        futures = []
        
        for req in high_priority:
            future = self.executor.submit(
                self._analyze_single_item, 
                req.content, 
                req.url
            )
            futures.append((future, req))
        
        results = []
        for future, req in futures:
            try:
                result = future.result(timeout=5)  # 5 second timeout
                result['market_id'] = req.market_id
                result['priority'] = req.priority
                result['fast_track'] = True
                results.append(result)
            except Exception as e:
                print(f"High priority analysis failed: {e}")
                # Add fallback result
                fallback = lightweight_ai._fast_fallback_analysis(req.content, req.url)
                fallback['market_id'] = req.market_id
                fallback['priority'] = req.priority
                fallback['fast_track'] = True
                fallback['fallback_used'] = True
                results.append(fallback)
        
        return results
    
    def get_queue_status(self) -> Dict[str, Any]:
        """Get current queue status"""
        return {
            'queue_length': len(self.processing_queue),
            'batch_size': self.batch_size,
            'max_workers': self.max_workers,
            'priority_distribution': {
                'high': len([r for r in self.processing_queue if r.priority == 1]),
                'medium': len([r for r in self.processing_queue if r.priority == 2]),
                'low': len([r for r in self.processing_queue if r.priority == 3])
            }
        }
    
    def cleanup_cache(self):
        """Clean up expired cache entries"""
        ai_cache.cleanup()
    
    def shutdown(self):
        """Shutdown the batch processor"""
        self.executor.shutdown(wait=True)


# Global batch processor instance
batch_processor = OptimizedBatchProcessor(max_workers=2, batch_size=5)


# Convenience functions for easy integration
def queue_analysis(content: str, url: str = "", market_id: str = "", priority: int = 2) -> Dict[str, Any]:
    """Queue content for batch analysis"""
    request = BatchAnalysisRequest(
        content=content,
        url=url,
        market_id=market_id,
        priority=priority
    )
    
    result = batch_processor.add_to_queue(request)
    return result or {"queued": True, "status": "pending"}


def process_urgent(content: str, url: str = "", market_id: str = "") -> Dict[str, Any]:
    """Process urgent analysis immediately"""
    request = BatchAnalysisRequest(
        content=content,
        url=url,
        market_id=market_id,
        priority=1
    )
    
    results = batch_processor.process_high_priority([request])
    return results[0] if results else {"error": "Processing failed"}


def flush_queue() -> List[Dict[str, Any]]:
    """Process all queued items immediately"""
    return batch_processor.process_batch()


def get_processing_status() -> Dict[str, Any]:
    """Get current processing status"""
    return batch_processor.get_queue_status()
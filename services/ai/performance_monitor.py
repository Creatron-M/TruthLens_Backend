import time
import threading
from typing import Dict, Any, List
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta

# Optional psutil for system monitoring
try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False
    print("psutil not available - system monitoring disabled")


@dataclass
class PerformanceMetrics:
    """Performance metrics for AI operations"""
    total_requests: int = 0
    cache_hits: int = 0
    cache_misses: int = 0
    avg_response_time: float = 0.0
    ai_calls_made: int = 0
    fallback_used: int = 0
    error_count: int = 0
    cpu_usage: float = 0.0
    memory_usage: float = 0.0
    timestamp: datetime = None


class PerformanceMonitor:
    """Lightweight performance monitoring for AI services"""
    
    def __init__(self):
        self.metrics = PerformanceMetrics()
        self.request_times = []
        self.max_history = 100
        self.lock = threading.Lock()
        
        # Start monitoring thread
        self.monitoring_active = True
        self.monitor_thread = threading.Thread(target=self._monitor_system, daemon=True)
        self.monitor_thread.start()
    
    def record_request(self, response_time: float, cache_hit: bool = False, 
                      ai_used: bool = False, fallback_used: bool = False, 
                      error_occurred: bool = False):
        """Record metrics for a request"""
        with self.lock:
            self.metrics.total_requests += 1
            
            if cache_hit:
                self.metrics.cache_hits += 1
            else:
                self.metrics.cache_misses += 1
            
            if ai_used:
                self.metrics.ai_calls_made += 1
            
            if fallback_used:
                self.metrics.fallback_used += 1
            
            if error_occurred:
                self.metrics.error_count += 1
            
            # Track response times
            self.request_times.append(response_time)
            if len(self.request_times) > self.max_history:
                self.request_times.pop(0)
            
            # Update average response time
            self.metrics.avg_response_time = sum(self.request_times) / len(self.request_times)
    
    def _monitor_system(self):
        """Monitor system resources"""
        while self.monitoring_active:
            try:
                if PSUTIL_AVAILABLE:
                    # Get CPU and memory usage
                    cpu_percent = psutil.cpu_percent(interval=1)
                    memory_percent = psutil.virtual_memory().percent
                else:
                    # Fallback values when psutil not available
                    cpu_percent = 50.0
                    memory_percent = 50.0
                
                with self.lock:
                    self.metrics.cpu_usage = cpu_percent
                    self.metrics.memory_usage = memory_percent
                    self.metrics.timestamp = datetime.now()
                
                time.sleep(5)  # Update every 5 seconds
                
            except Exception as e:
                print(f"Performance monitoring error: {e}")
                time.sleep(10)
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get current performance metrics"""
        with self.lock:
            metrics_dict = asdict(self.metrics)
            
            # Add calculated metrics
            total_requests = self.metrics.total_requests
            if total_requests > 0:
                metrics_dict['cache_hit_rate'] = (self.metrics.cache_hits / total_requests) * 100
                metrics_dict['error_rate'] = (self.metrics.error_count / total_requests) * 100
                metrics_dict['ai_usage_rate'] = (self.metrics.ai_calls_made / total_requests) * 100
                metrics_dict['fallback_rate'] = (self.metrics.fallback_used / total_requests) * 100
            else:
                metrics_dict['cache_hit_rate'] = 0
                metrics_dict['error_rate'] = 0
                metrics_dict['ai_usage_rate'] = 0
                metrics_dict['fallback_rate'] = 0
            
            # Performance status
            if self.metrics.avg_response_time < 1.0:
                status = "excellent"
            elif self.metrics.avg_response_time < 3.0:
                status = "good"
            elif self.metrics.avg_response_time < 5.0:
                status = "fair"
            else:
                status = "poor"
            
            metrics_dict['performance_status'] = status
            metrics_dict['timestamp'] = self.metrics.timestamp.isoformat() if self.metrics.timestamp else None
            
            return metrics_dict
    
    def get_optimization_suggestions(self) -> List[str]:
        """Get suggestions for performance optimization"""
        suggestions = []
        
        with self.lock:
            # Cache performance
            if self.metrics.total_requests > 10:
                cache_rate = (self.metrics.cache_hits / self.metrics.total_requests) * 100
                if cache_rate < 30:
                    suggestions.append("Low cache hit rate - consider increasing cache TTL")
                elif cache_rate > 80:
                    suggestions.append("Excellent cache performance!")
            
            # Response time
            if self.metrics.avg_response_time > 5.0:
                suggestions.append("High response times - consider using batch processing")
            elif self.metrics.avg_response_time > 3.0:
                suggestions.append("Moderate response times - consider optimizing prompts")
            
            # Error rate
            if self.metrics.total_requests > 0:
                error_rate = (self.metrics.error_count / self.metrics.total_requests) * 100
                if error_rate > 10:
                    suggestions.append("High error rate - check AI service stability")
                elif error_rate > 5:
                    suggestions.append("Moderate error rate - consider adding more fallbacks")
            
            # Fallback usage
            if self.metrics.total_requests > 0:
                fallback_rate = (self.metrics.fallback_used / self.metrics.total_requests) * 100
                if fallback_rate > 50:
                    suggestions.append("High fallback usage - AI service may be unreliable")
            
            # System resources
            if self.metrics.cpu_usage > 80:
                suggestions.append("High CPU usage - consider reducing concurrent requests")
            if self.metrics.memory_usage > 80:
                suggestions.append("High memory usage - consider clearing cache more frequently")
        
        return suggestions if suggestions else ["Performance is optimal!"]
    
    def reset_metrics(self):
        """Reset all metrics"""
        with self.lock:
            self.metrics = PerformanceMetrics()
            self.request_times = []
    
    def stop_monitoring(self):
        """Stop performance monitoring"""
        self.monitoring_active = False
        if self.monitor_thread.is_alive():
            self.monitor_thread.join(timeout=5)


# Global performance monitor
performance_monitor = PerformanceMonitor()


def monitor_performance(func):
    """Decorator to monitor function performance"""
    def wrapper(*args, **kwargs):
        start_time = time.time()
        cache_hit = False
        ai_used = False
        fallback_used = False
        error_occurred = False
        
        try:
            result = func(*args, **kwargs)
            
            # Detect metrics from result
            if isinstance(result, dict):
                cache_hit = result.get('cache_hit', False)
                ai_used = result.get('enhanced_analysis', False) or result.get('ai_version', '') != ''
                fallback_used = result.get('fallback_used', False) or result.get('fallback_mode', False)
            
            return result
            
        except Exception as e:
            error_occurred = True
            raise e
            
        finally:
            response_time = time.time() - start_time
            performance_monitor.record_request(
                response_time=response_time,
                cache_hit=cache_hit,
                ai_used=ai_used,
                fallback_used=fallback_used,
                error_occurred=error_occurred
            )
    
    return wrapper
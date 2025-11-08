import hashlib
import json
import time
from typing import Dict, Any, Optional
from functools import wraps
import pickle
import os

class IntelligentCache:
    """Lightweight caching system for AI results"""
    
    def __init__(self, cache_dir: str = "cache", default_ttl: int = 3600):
        self.cache_dir = cache_dir
        self.default_ttl = default_ttl
        self.memory_cache = {}
        self._ensure_cache_dir()
    
    def _ensure_cache_dir(self):
        """Ensure cache directory exists"""
        if not os.path.exists(self.cache_dir):
            os.makedirs(self.cache_dir)
    
    def _get_cache_key(self, *args, **kwargs) -> str:
        """Generate cache key from function arguments"""
        key_data = str(args) + str(sorted(kwargs.items()))
        return hashlib.md5(key_data.encode()).hexdigest()
    
    def _get_cache_path(self, cache_key: str) -> str:
        """Get file path for cache key"""
        return os.path.join(self.cache_dir, f"{cache_key}.cache")
    
    def get(self, cache_key: str) -> Optional[Dict]:
        """Get cached result"""
        
        # Check memory cache first
        if cache_key in self.memory_cache:
            entry = self.memory_cache[cache_key]
            if time.time() - entry['timestamp'] < entry['ttl']:
                return entry['data']
            else:
                del self.memory_cache[cache_key]
        
        # Check file cache
        cache_path = self._get_cache_path(cache_key)
        if os.path.exists(cache_path):
            try:
                with open(cache_path, 'rb') as f:
                    entry = pickle.load(f)
                
                if time.time() - entry['timestamp'] < entry['ttl']:
                    # Load into memory cache
                    self.memory_cache[cache_key] = entry
                    return entry['data']
                else:
                    # Remove expired cache
                    os.remove(cache_path)
            except Exception as e:
                print(f"Cache read error: {e}")
        
        return None
    
    def set(self, cache_key: str, data: Dict, ttl: Optional[int] = None):
        """Set cached result"""
        ttl = ttl or self.default_ttl
        
        entry = {
            'data': data,
            'timestamp': time.time(),
            'ttl': ttl
        }
        
        # Store in memory cache
        self.memory_cache[cache_key] = entry
        
        # Store in file cache for persistence
        cache_path = self._get_cache_path(cache_key)
        try:
            with open(cache_path, 'wb') as f:
                pickle.dump(entry, f)
        except Exception as e:
            print(f"Cache write error: {e}")
    
    def cleanup(self):
        """Clean up expired cache entries"""
        current_time = time.time()
        
        # Clean memory cache
        expired_keys = [
            key for key, entry in self.memory_cache.items()
            if current_time - entry['timestamp'] > entry['ttl']
        ]
        
        for key in expired_keys:
            del self.memory_cache[key]
        
        # Clean file cache
        if os.path.exists(self.cache_dir):
            for filename in os.listdir(self.cache_dir):
                if filename.endswith('.cache'):
                    filepath = os.path.join(self.cache_dir, filename)
                    try:
                        with open(filepath, 'rb') as f:
                            entry = pickle.load(f)
                        
                        if current_time - entry['timestamp'] > entry['ttl']:
                            os.remove(filepath)
                    except:
                        # Remove corrupted cache files
                        try:
                            os.remove(filepath)
                        except:
                            pass

# Global cache instance
ai_cache = IntelligentCache()

def cached_ai_analysis(ttl: int = 1800):
    """Decorator for caching AI analysis results"""
    
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Generate cache key
            cache_key = ai_cache._get_cache_key(func.__name__, *args, **kwargs)
            
            # Try to get from cache
            cached_result = ai_cache.get(cache_key)
            if cached_result is not None:
                cached_result['cache_hit'] = True
                return cached_result
            
            # Execute function
            result = func(*args, **kwargs)
            
            # Cache the result
            if result and isinstance(result, dict):
                result['cache_hit'] = False
                ai_cache.set(cache_key, result, ttl)
            
            return result
        
        return wrapper
    return decorator

def batch_cache_analysis(analysis_func, items: list, ttl: int = 1800) -> list:
    """Efficient batch processing with caching"""
    results = []
    uncached_items = []
    uncached_indices = []
    
    # Check cache for all items
    for i, item in enumerate(items):
        cache_key = ai_cache._get_cache_key(analysis_func.__name__, *item if isinstance(item, tuple) else item)
        cached_result = ai_cache.get(cache_key)
        
        if cached_result:
            cached_result['cache_hit'] = True
            results.append(cached_result)
        else:
            results.append(None)  # Placeholder
            uncached_items.append(item)
            uncached_indices.append(i)
    
    # Process uncached items
    if uncached_items:
        for item, index in zip(uncached_items, uncached_indices):
            if isinstance(item, tuple):
                result = analysis_func(*item)
            else:
                result = analysis_func(item)
            
            result['cache_hit'] = False
            results[index] = result
            
            # Cache the result
            cache_key = ai_cache._get_cache_key(analysis_func.__name__, *item if isinstance(item, tuple) else item)
            ai_cache.set(cache_key, result, ttl)
    
    return results
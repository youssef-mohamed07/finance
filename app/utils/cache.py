"""
Caching utilities
"""
import time
import hashlib
from typing import Optional, Any, Dict
from functools import wraps
from app.core.logging import get_logger
from app.config import settings

logger = get_logger("cache")


class SimpleCache:
    """Simple in-memory cache with TTL support"""
    
    def __init__(self, max_size: int = 1000, default_ttl: int = 3600):
        self.cache: Dict[str, Dict[str, Any]] = {}
        self.max_size = max_size
        self.default_ttl = default_ttl
    
    def _is_expired(self, entry: Dict[str, Any]) -> bool:
        """Check if cache entry is expired"""
        return time.time() > entry['expires_at']
    
    def _cleanup_expired(self):
        """Remove expired entries"""
        current_time = time.time()
        expired_keys = [
            key for key, entry in self.cache.items()
            if current_time > entry['expires_at']
        ]
        
        for key in expired_keys:
            del self.cache[key]
        
        if expired_keys:
            logger.debug(f"Cleaned up {len(expired_keys)} expired cache entries")
    
    def _evict_oldest(self):
        """Evict oldest entries if cache is full"""
        if len(self.cache) >= self.max_size:
            # Remove 10% of oldest entries
            entries_to_remove = max(1, len(self.cache) // 10)
            oldest_keys = sorted(
                self.cache.keys(),
                key=lambda k: self.cache[k]['created_at']
            )[:entries_to_remove]
            
            for key in oldest_keys:
                del self.cache[key]
            
            logger.debug(f"Evicted {len(oldest_keys)} oldest cache entries")
    
    def get(self, key: str) -> Optional[Any]:
        """Get value from cache"""
        if key not in self.cache:
            return None
        
        entry = self.cache[key]
        
        if self._is_expired(entry):
            del self.cache[key]
            return None
        
        # Update access time
        entry['last_accessed'] = time.time()
        
        logger.debug(f"Cache hit for key: {key[:20]}...")
        return entry['value']
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """Set value in cache"""
        if ttl is None:
            ttl = self.default_ttl
        
        current_time = time.time()
        
        # Cleanup expired entries
        self._cleanup_expired()
        
        # Evict if necessary
        self._evict_oldest()
        
        self.cache[key] = {
            'value': value,
            'created_at': current_time,
            'last_accessed': current_time,
            'expires_at': current_time + ttl
        }
        
        logger.debug(f"Cache set for key: {key[:20]}... (TTL: {ttl}s)")
    
    def delete(self, key: str) -> bool:
        """Delete key from cache"""
        if key in self.cache:
            del self.cache[key]
            logger.debug(f"Cache delete for key: {key[:20]}...")
            return True
        return False
    
    def clear(self) -> None:
        """Clear all cache entries"""
        self.cache.clear()
        logger.debug("Cache cleared")
    
    def stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        current_time = time.time()
        expired_count = sum(
            1 for entry in self.cache.values()
            if current_time > entry['expires_at']
        )
        
        return {
            'total_entries': len(self.cache),
            'expired_entries': expired_count,
            'active_entries': len(self.cache) - expired_count,
            'max_size': self.max_size,
            'memory_usage_estimate': len(str(self.cache))
        }


# Global cache instance
cache = SimpleCache(
    max_size=settings.cache_max_size,
    default_ttl=settings.cache_ttl
)


def cache_key_for_text(text: str, language: str = "ar") -> str:
    """Generate cache key for text analysis"""
    content = f"{text}:{language}"
    return f"text_analysis:{hashlib.sha256(content.encode()).hexdigest()}"


def cached_text_analysis(ttl: int = None):
    """Decorator for caching text analysis results"""
    def decorator(func):
        @wraps(func)
        async def wrapper(text: str, *args, **kwargs):
            # Generate cache key
            cache_key = cache_key_for_text(text, kwargs.get('language', 'ar'))
            
            # Try to get from cache
            cached_result = cache.get(cache_key)
            if cached_result is not None:
                logger.info(f"Returning cached analysis for text: {text[:30]}...")
                return cached_result
            
            # Execute function
            result = await func(text, *args, **kwargs)
            
            # Cache result
            cache.set(cache_key, result, ttl)
            
            return result
        return wrapper
    return decorator


def cache_key_for_audio(content_hash: str, filename: str) -> str:
    """Generate cache key for audio analysis"""
    return f"audio_analysis:{content_hash}:{filename}"


def get_content_hash(content: bytes) -> str:
    """Generate hash for content"""
    return hashlib.sha256(content).hexdigest()[:16]  # First 16 chars for brevity
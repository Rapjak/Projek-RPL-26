from functools import wraps
from django.core.cache import cache
from django.conf import settings
import hashlib
import json


def cache_response(timeout=None, key_prefix='view'):
    """
    Cache decorator for view methods.
    
    Args:
        timeout: Cache timeout in seconds (None uses default)
        key_prefix: Prefix for cache key
    """
    def decorator(func):
        @wraps(func)
        def wrapper(self, request, *args, **kwargs):
            # Skip cache if disabled
            if not getattr(settings, 'ENABLE_CACHE', True):
                return func(self, request, *args, **kwargs)
            
            # Build cache key from request
            cache_key_data = {
                'view': func.__name__,
                'user_id': request.user.id if request.user.is_authenticated else None,
                'path': request.path,
                'query': dict(request.query_params),
                'args': args,
                'kwargs': kwargs,
            }
            cache_key_hash = hashlib.md5(
                json.dumps(cache_key_data, sort_keys=True).encode()
            ).hexdigest()
            cache_key = f'{key_prefix}:{cache_key_hash}'
            
            # Try to get from cache
            cached_response = cache.get(cache_key)
            if cached_response is not None:
                return cached_response
            
            # Call the view and cache result
            response = func(self, request, *args, **kwargs)
            
            # Only cache successful responses
            if response.status_code == 200:
                cache_timeout = timeout or getattr(settings, 'CACHE_TIMEOUT', 300)
                cache.set(cache_key, response, cache_timeout)
            
            return response
        
        return wrapper
    return decorator


def invalidate_cache_pattern(pattern):
    """
    Invalidate all cache keys matching pattern.
    
    Args:
        pattern: Cache key pattern to invalidate
    """
    try:
        # Note: This requires redis backend with delete_pattern support
        cache.delete_pattern(f'{pattern}:*')
    except AttributeError:
        # Fallback if delete_pattern not available
        pass


def get_user_cache_key(user_id, prefix='user'):
    """Generate cache key for user-specific data."""
    return f'{prefix}:user_{user_id}'


def get_list_cache_key(model_name, filters=None):
    """Generate cache key for list views."""
    if filters:
        filter_hash = hashlib.md5(
            json.dumps(filters, sort_keys=True).encode()
        ).hexdigest()
        return f'list:{model_name}:{filter_hash}'
    return f'list:{model_name}:all'

from rest_framework.throttling import AnonRateThrottle, UserRateThrottle
from django.conf import settings
import logging

logger = logging.getLogger(__name__)


class BurstRateThrottle(UserRateThrottle):
    """Short burst limit for authenticated users."""
    scope = 'burst'
    
    def allow_request(self, request, view):
        try:
            return super().allow_request(request, view)
        except Exception as e:
            logger.warning(f"Throttling cache error: {e}")
            return True  # Allow request if cache fails


class SustainedRateThrottle(UserRateThrottle):
    """Sustained rate limit for authenticated users."""
    scope = 'sustained'
    
    def allow_request(self, request, view):
        try:
            return super().allow_request(request, view)
        except Exception as e:
            logger.warning(f"Throttling cache error: {e}")
            return True  # Allow request if cache fails


class AnonBurstRateThrottle(AnonRateThrottle):
    """Short burst limit for anonymous users."""
    scope = 'anon_burst'
    
    def allow_request(self, request, view):
        try:
            return super().allow_request(request, view)
        except Exception as e:
            logger.warning(f"Throttling cache error: {e}")
            return True  # Allow request if cache fails


class AnonSustainedRateThrottle(AnonRateThrottle):
    """Sustained rate limit for anonymous users."""
    scope = 'anon_sustained'
    
    def allow_request(self, request, view):
        try:
            return super().allow_request(request, view)
        except Exception as e:
            logger.warning(f"Throttling cache error: {e}")
            return True  # Allow request if cache fails


class UploadRateThrottle(UserRateThrottle):
    """Special rate limit for file uploads."""
    scope = 'upload'
    
    def allow_request(self, request, view):
        try:
            return super().allow_request(request, view)
        except Exception as e:
            logger.warning(f"Throttling cache error: {e}")
            return True  # Allow request if cache fails

"""
Test settings - override production settings for test suite.
"""
from .settings import *

# Disable throttling untuk test
REST_FRAMEWORK['DEFAULT_THROTTLE_CLASSES'] = []

# Use LocMemCache backend (no Redis required, but persists within process)
# This let us test rate-limiting and caching logic deterministically.
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'pilah-test-cache',
    }
}

# Disable logging file handlers untuk test (hanya console)
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'WARNING',
    },
}

# Disable DEBUG untuk test
DEBUG = False

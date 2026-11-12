import os
from pathlib import Path

# Build paths
BASE_DIR = Path(__file__).resolve().parent.parent.parent
LOG_DIR = os.path.join(BASE_DIR, 'logs')

# Create logs directory if not exists
os.makedirs(LOG_DIR, exist_ok=True)

LOGGING_CONFIG = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '[{levelname}] {asctime} {module} {process:d} {thread:d} - {message}',
            'style': '{',
        },
        'simple': {
            'format': '[{levelname}] {asctime} - {message}',
            'style': '{',
        },
    },
    'filters': {
        'require_debug_false': {
            '()': 'django.utils.log.RequireDebugFalse',
        },
        'require_debug_true': {
            '()': 'django.utils.log.RequireDebugTrue',
        },
    },
    'handlers': {
        'console': {
            'level': 'INFO',
            'class': 'logging.StreamHandler',
            'formatter': 'simple',
        },
        'file_general': {
            'level': 'INFO',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': os.path.join(LOG_DIR, 'general.log'),
            'maxBytes': 10485760,  # 10MB
            'backupCount': 5,
            'formatter': 'verbose',
        },
        'file_error': {
            'level': 'ERROR',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': os.path.join(LOG_DIR, 'error.log'),
            'maxBytes': 10485760,  # 10MB
            'backupCount': 5,
            'formatter': 'verbose',
        },
        'file_api': {
            'level': 'INFO',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': os.path.join(LOG_DIR, 'api.log'),
            'maxBytes': 10485760,  # 10MB
            'backupCount': 5,
            'formatter': 'verbose',
        },
        'file_security': {
            'level': 'WARNING',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': os.path.join(LOG_DIR, 'security.log'),
            'maxBytes': 10485760,  # 10MB
            'backupCount': 10,
            'formatter': 'verbose',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['console', 'file_general'],
            'level': 'INFO',
            'propagate': False,
        },
        'django.request': {
            'handlers': ['file_error'],
            'level': 'ERROR',
            'propagate': False,
        },
        'django.security': {
            'handlers': ['file_security'],
            'level': 'WARNING',
            'propagate': False,
        },
        'apps': {
            'handlers': ['console', 'file_api'],
            'level': 'INFO',
            'propagate': False,
        },
        'apps.users': {
            'handlers': ['file_api', 'file_security'],
            'level': 'INFO',
            'propagate': False,
        },
        'apps.uploads': {
            'handlers': ['file_api'],
            'level': 'INFO',
            'propagate': False,
        },
        'apps.classifications': {
            'handlers': ['file_api'],
            'level': 'INFO',
            'propagate': False,
        },
        'apps.rewards': {
            'handlers': ['file_api'],
            'level': 'INFO',
            'propagate': False,
        },
        'apps.education': {
            'handlers': ['file_api'],
            'level': 'INFO',
            'propagate': False,
        },
    },
    'root': {
        'handlers': ['console', 'file_general'],
        'level': 'INFO',
    },
}

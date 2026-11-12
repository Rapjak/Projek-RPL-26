import logging
from rest_framework.views import exception_handler
from rest_framework.response import Response
from rest_framework import status
from django.core.exceptions import ValidationError
from django.http import Http404

logger = logging.getLogger(__name__)


def custom_exception_handler(exc, context):
    """Enhanced exception handler with logging."""
    response = exception_handler(exc, context)
    
    # Get request info
    request = context.get('request')
    view = context.get('view')
    
    # Log the exception
    if response is not None:
        logger.warning(
            f"API Error: {exc.__class__.__name__} - {str(exc)} - "
            f"Path: {request.path if request else 'N/A'} - "
            f"Status: {response.status_code}",
            exc_info=True
        )
    else:
        logger.error(
            f"Unhandled Exception: {exc.__class__.__name__} - {str(exc)} - "
            f"Path: {request.path if request else 'N/A'}",
            exc_info=True
        )
    
    # Handle Django ValidationError
    if isinstance(exc, ValidationError) and response is None:
        response = Response(
            {'error': 'Validation error', 'detail': exc.messages},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Handle Django Http404
    if isinstance(exc, Http404) and response is None:
        response = Response(
            {'error': 'Not found', 'detail': str(exc)},
            status=status.HTTP_404_NOT_FOUND
        )
    
    # Standardize error response format
    if response is not None:
        custom_response_data = {
            'status': 'error',
            'code': response.status_code,
        }
        
        # Handle detail field
        if 'detail' in response.data:
            custom_response_data['message'] = response.data['detail']
        else:
            custom_response_data['errors'] = response.data
        
        response.data = custom_response_data
    
    return response

from rest_framework.pagination import PageNumberPagination


class StandardResultsSetPagination(PageNumberPagination):
    """Standard pagination with configurable page size."""
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 100


class SmallResultsSetPagination(PageNumberPagination):
    """Pagination for lists with fewer items."""
    page_size = 5
    page_size_query_param = 'page_size'
    max_page_size = 20


class LargeResultsSetPagination(PageNumberPagination):
    """Pagination for large result sets."""
    page_size = 50
    page_size_query_param = 'page_size'
    max_page_size = 500

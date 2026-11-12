import django_filters
from .models import Upload


class UploadFilter(django_filters.FilterSet):
    """Advanced filters for Upload model."""
    created_after = django_filters.DateTimeFilter(field_name='created_at', lookup_expr='gte')
    created_before = django_filters.DateTimeFilter(field_name='created_at', lookup_expr='lte')
    file_size_min = django_filters.NumberFilter(field_name='file_size', lookup_expr='gte')
    file_size_max = django_filters.NumberFilter(field_name='file_size', lookup_expr='lte')
    
    class Meta:
        model = Upload
        fields = ['status', 'created_after', 'created_before', 'file_size_min', 'file_size_max']

import django_filters
from .models import RewardRedemption, PointTransaction


class RewardRedemptionFilter(django_filters.FilterSet):
    """Advanced filters for RewardRedemption model."""
    created_after = django_filters.DateTimeFilter(field_name='created_at', lookup_expr='gte')
    created_before = django_filters.DateTimeFilter(field_name='created_at', lookup_expr='lte')
    
    class Meta:
        model = RewardRedemption
        fields = ['status', 'created_after', 'created_before']


class PointTransactionFilter(django_filters.FilterSet):
    """Advanced filters for PointTransaction model."""
    created_after = django_filters.DateTimeFilter(field_name='created_at', lookup_expr='gte')
    created_before = django_filters.DateTimeFilter(field_name='created_at', lookup_expr='lte')
    points_min = django_filters.NumberFilter(field_name='points', lookup_expr='gte')
    points_max = django_filters.NumberFilter(field_name='points', lookup_expr='lte')
    
    class Meta:
        model = PointTransaction
        fields = ['transaction_type', 'created_after', 'created_before', 'points_min', 'points_max']

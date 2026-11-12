"""Education views - API-014 (list), API-015 (detail)."""
import logging
from rest_framework import generics, permissions, filters
from django_filters.rest_framework import DjangoFilterBackend
from .models import EducationMaterial
from .serializers import EducationMaterialSerializer, EducationMaterialListSerializer
from apps.utils.pagination import StandardResultsSetPagination

logger = logging.getLogger(__name__)


class EducationMaterialListView(generics.ListAPIView):
    """API-014 - list education materials. Public read."""
    serializer_class = EducationMaterialListSerializer
    permission_classes = [permissions.AllowAny]
    pagination_class = StandardResultsSetPagination
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ['kategori_sampah']
    search_fields = ['judul', 'konten']

    def get_queryset(self):
        return EducationMaterial.objects.filter(is_published=True)


class EducationMaterialDetailView(generics.RetrieveAPIView):
    """API-015 - retrieve single education material."""
    serializer_class = EducationMaterialSerializer
    permission_classes = [permissions.AllowAny]

    def get_queryset(self):
        return EducationMaterial.objects.filter(is_published=True)

    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

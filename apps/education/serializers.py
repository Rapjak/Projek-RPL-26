"""Serializers for education app - API-014, API-015."""
from rest_framework import serializers
from .models import EducationMaterial


class EducationMaterialListSerializer(serializers.ModelSerializer):
    """API-014 - list view (judul, kategori, ringkasan)."""

    class Meta:
        model = EducationMaterial
        fields = ('id', 'judul', 'kategori_sampah', 'ringkasan', 'image', 'created_at')
        read_only_fields = ('id', 'created_at')


class EducationMaterialSerializer(serializers.ModelSerializer):
    """API-015 - detail view."""

    class Meta:
        model = EducationMaterial
        fields = ('id', 'judul', 'kategori_sampah', 'konten', 'url_media', 'image', 'is_published', 'created_at', 'updated_at')
        read_only_fields = ('id', 'created_at', 'updated_at')

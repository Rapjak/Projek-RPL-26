"""Serializers for classifications app."""
from rest_framework import serializers
from .models import ClassificationResult


class ClassificationResultSerializer(serializers.ModelSerializer):
    class Meta:
        model = ClassificationResult
        fields = ('id', 'upload', 'kategori_sampah', 'confidence_score', 'is_valid',
                  'points_awarded', 'handling_instructions', 'waktu_proses')
        read_only_fields = ('id', 'waktu_proses')

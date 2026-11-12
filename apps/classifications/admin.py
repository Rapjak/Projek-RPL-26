from django.contrib import admin
from .models import ClassificationResult


@admin.register(ClassificationResult)
class ClassificationResultAdmin(admin.ModelAdmin):
    list_display = ('id', 'upload', 'kategori_sampah', 'confidence_score', 'is_valid', 'points_awarded', 'waktu_proses')
    list_filter = ('kategori_sampah', 'is_valid')
    search_fields = ('upload__user__npm_nip', 'upload__user__name')
    readonly_fields = ('id', 'waktu_proses')

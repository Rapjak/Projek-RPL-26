from django.contrib import admin
from .models import EducationMaterial


@admin.register(EducationMaterial)
class EducationMaterialAdmin(admin.ModelAdmin):
    list_display = ('judul', 'kategori_sampah', 'is_published', 'created_at')
    list_filter = ('kategori_sampah', 'is_published')
    search_fields = ('judul', 'konten')
    readonly_fields = ('id', 'created_at', 'updated_at')

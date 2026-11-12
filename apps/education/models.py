"""
EducationMaterial model - data dictionary (education_materials).
kategori_sampah: organik | anorganik | residu | umum
"""
import uuid
from django.db import models
from django.utils import timezone


class EduCategory(models.TextChoices):
    ORGANIK = 'organik', 'Organik'
    ANORGANIK = 'anorganik', 'Anorganik'
    RESIDU = 'residu', 'Residu'
    UMUM = 'umum', 'Umum'


class EducationMaterial(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    judul = models.CharField('Judul', max_length=150)
    kategori_sampah = models.CharField(
        'Kategori', max_length=20, choices=EduCategory.choices, default=EduCategory.UMUM,
    )
    konten = models.TextField('Konten')
    url_media = models.URLField(blank=True, null=True)
    ringkasan = models.CharField('Ringkasan', max_length=255, blank=True, default='')
    image = models.ImageField(upload_to='education/', blank=True, null=True)
    is_published = models.BooleanField(default=True)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'education_materials'
        ordering = ['-created_at']

    def __str__(self):
        return self.judul

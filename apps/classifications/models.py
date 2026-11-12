"""
ClassificationResult model - data dictionary (classification_results).

Fields: id_klasifikasi (UUID), id_unggahan (FK 1:1), kategori_sampah, confidence_score,
        is_valid, points_awarded, waktu_proses.
"""
import uuid
from django.db import models
from django.utils import timezone
from django.core.validators import MinValueValidator, MaxValueValidator


class KategoriSampah(models.TextChoices):
    ORGANIK = 'organik', 'Organik'
    ANORGANIK = 'anorganik', 'Anorganik'
    RESIDU = 'residu', 'Residu'
    TIDAK_DIKENAL = 'tidak_dikenal', 'Tidak Dikenal'


class ClassificationResult(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    upload = models.OneToOneField(
        'uploads.Upload', on_delete=models.CASCADE, related_name='classification_result',
        db_column='id_unggahan',
    )
    kategori_sampah = models.CharField(
        'Kategori Sampah', max_length=20, choices=KategoriSampah.choices,
        default=KategoriSampah.TIDAK_DIKENAL,
    )
    confidence_score = models.DecimalField(
        'Confidence Score', max_digits=5, decimal_places=4,
        validators=[MinValueValidator(0), MaxValueValidator(1)],
    )
    is_valid = models.BooleanField('Is Valid', default=False)
    points_awarded = models.IntegerField('Poin Diperoleh', default=0)
    handling_instructions = models.TextField('Arahan Pembuangan', blank=True, default='')
    waktu_proses = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = 'classification_results'
        ordering = ['-waktu_proses']

    def __str__(self):
        return f'{self.kategori_sampah} ({self.confidence_score})'

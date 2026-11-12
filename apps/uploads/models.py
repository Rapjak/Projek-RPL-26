"""
Upload model for Pilah.in - data dictionary (uploads table).

Fields: id_unggahan (UUID), id_pengguna (FK), url_foto, status_proses, created_at.
File physical storage = local MEDIA_ROOT (substitute for Cloud Object Storage).
DB only stores reference path via ImageField.
"""
import uuid
import os
from django.db import models
from django.utils import timezone
from django.conf import settings


def upload_file_path(instance, filename):
    """Generate storage path: uploads/<user_id>/<uuid>.<ext>"""
    ext = os.path.splitext(filename)[1].lower()
    return f'uploads/{instance.user_id}/{uuid.uuid4()}{ext}'


class UploadStatus(models.TextChoices):
    PENDING = 'pending', 'Pending'
    PROCESSING = 'processing', 'Processing'
    COMPLETED = 'completed', 'Completed'
    FAILED = 'failed', 'Failed'


class Upload(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='uploads',
        db_column='id_pengguna',
    )
    file = models.ImageField(upload_to=upload_file_path)
    status = models.CharField(
        'Status Proses', max_length=20, choices=UploadStatus.choices,
        default=UploadStatus.PENDING,
    )
    created_at = models.DateTimeField(default=timezone.now)

    # Optional metadata
    file_size = models.IntegerField(default=0)
    updated_at = models.DateTimeField(auto_now=True)
    error_message = models.TextField(blank=True, null=True)

    class Meta:
        db_table = 'uploads'
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.file.name} - {self.user.npm_nip} ({self.status})'

    @property
    def url_foto(self):
        try:
            return self.file.url
        except ValueError:
            return ''

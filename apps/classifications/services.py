"""
Classification service - orchestrates ML inference + point award.

Flow:
1. Fetch upload
2. Call ML service (via MLServiceClient) -> returns kategori/confidence
3. Threshold check: confidence >= 0.70 => is_valid=True
4. If valid => award POINTS_PER_CLASSIFICATION points atomically + log PointTransaction
5. Update upload.status = 'completed' or 'failed'
6. Idempotent: if upload.classification_result already exists, skip re-processing & re-awarding (TC-049).

This keeps API code (views) thin and business logic centralized here.
"""
import logging
import os
from django.db import transaction

from apps.uploads.models import Upload
from apps.utils.ml_client import MLServiceClient
from .models import ClassificationResult, KategoriSampah

logger = logging.getLogger(__name__)

# Threshold constants (per spec: 70% minimum confidence)
MIN_CONFIDENCE_THRESHOLD = 0.70
POINTS_PER_CLASSIFICATION = 10  # +10 per successful classification

HANDLING_MESSAGES = {
    'organik': 'Foto teridentifikasi sebagai sampah organik. Sampah organik mudah terurai secara alami. Buang pada tempat sampah berwarna hijau.',
    'anorganik': 'Foto teridentifikasi sebagai sampah anorganik (plastik/kertas/logam/kaca). Bersihkan dan buang pada tempat sampah berwarna biru agar dapat didaur ulang.',
    'residu': 'Foto teridentifikasi sebagai sampah residu. Sampah ini sulit didaur ulang dan harus dibuang pada tempat sampah berwarna abu-abu.',
    'tidak_dikenal': 'Foto belum dapat dikenali sebagai sampah. Coba ambil foto ulang dengan objek tunggal, pencahayaan cukup, dan latar belakang jelas.',
}


def _ml_category_to_kategori(ml_kategori: str) -> str:
    """
    ML service now returns 'kategori_sampah' directly with values
    organik/anorganik/residu/tidak_dikenal. Keep robust fallback mapping too.
    """
    val = (ml_kategori or '').lower()
    if val in ('organik', 'anorganik', 'residu', 'tidak_dikenal'):
        return val
    # Legacy fallback: some models may return class names
    if 'organik' in val or 'organic' in val:
        return KategoriSampah.ORGANIK.value
    if 'anorganik' in val or 'inorganic' in val or 'plastic' in val or 'paper' in val \
            or 'metal' in val or 'glass' in val or 'cardboard' in val or 'cloth' in val:
        return KategoriSampah.ANORGANIK.value
    if 'residu' in val or 'residue' in val or 'ceramic' in val or 'electronic' in val \
            or 'battery' in val:
        return KategoriSampah.RESIDU.value
    return KategoriSampah.TIDAK_DIKENAL.value


def process_classification_async(upload_id: str, user_id: str):
    """
    Entry point called after upload creation. Synchronous implementation but designed
    to be replaced with Celery/RQ worker in production.
    """
    process_classification_sync(upload_id, user_id)


def process_classification_sync(upload_id: str, user_id: str):
    """Perform classification and point award atomically."""
    try:
        upload = Upload.objects.get(id=upload_id)
    except Upload.DoesNotExist:
        logger.error(f'process_classification: upload {upload_id} not found')
        return

    # Idempotency: skip if result already recorded (TC-049)
    if hasattr(upload, 'classification_result'):
        logger.info(f'process_classification: upload {upload_id} already processed, skipping.')
        return

    upload.status = 'processing'
    upload.save(update_fields=['status'])

    # Prepare ML call
    ml_client = MLServiceClient()
    kategori = KategoriSampah.TIDAK_DIKENAL.value
    confidence = 0.0
    is_valid = False
    ml_error = None

    try:
        if not ml_client.health_check():
            raise RuntimeError('ML_SERVICE_UNAVAILABLE')

        image_path = upload.file.path
        ext = os.path.splitext(upload.file.name)[1].lower()
        mime_map = {'.jpg': 'image/jpeg', '.jpeg': 'image/jpeg', '.png': 'image/png'}
        mime = mime_map.get(ext, 'image/jpeg')

        ml_result = ml_client.classify_image(image_path, mime)
        kategori = _ml_category_to_kategori(ml_result.get('kategori_sampah', ''))
        confidence = float(ml_result.get('confidence_score', 0.0))

    except FileNotFoundError as e:
        ml_error = 'Berkas gambar tidak ditemukan.'
        logger.error(f'process_classification: {e}')
    except Exception as e:
        ml_error = 'LAYANAN_UNAVAILABLE' if 'ML_SERVICE_UNAVAILABLE' in str(e) else str(e)
        logger.error(f'process_classification: ML error: {e}', exc_info=True)

    # If ML unavailable -> don't crash; mark failed (TC-019, TC-035)
    if ml_error:
        upload.status = 'failed'
        upload.error_message = ml_error
        upload.save(update_fields=['status', 'error_message'])
        return

    # Threshold check (TC-033: exactly 0.70 is valid; TC-034: 0.69 is invalid)
    is_valid = confidence >= MIN_CONFIDENCE_THRESHOLD
    if not is_valid:
        kategori = KategoriSampah.TIDAK_DIKENAL.value

    points_awarded = 0

    try:
        with transaction.atomic():
            result = ClassificationResult.objects.create(
                upload=upload,
                kategori_sampah=kategori,
                confidence_score=confidence,
                is_valid=is_valid,
                points_awarded=points_awarded,
                handling_instructions=HANDLING_MESSAGES.get(kategori, HANDLING_MESSAGES['tidak_dikenal']),
            )

            if is_valid:
                # Award points atomically (FR-005/FR-006)
                from django.contrib.auth import get_user_model
                from apps.rewards.models import PointTransaction
                User = get_user_model()

                user = User.objects.select_for_update().get(id=user_id)
                user.add_points(POINTS_PER_CLASSIFICATION)

                PointTransaction.objects.create(
                    user=user,
                    points=POINTS_PER_CLASSIFICATION,
                    transaction_type='penambahan',
                    description=f'Perolehan poin dari klasifikasi {kategori} (upload {upload.id})',
                    reference_id=upload.id,
                )

                result.points_awarded = POINTS_PER_CLASSIFICATION
                result.save(update_fields=['points_awarded'])
                points_awarded = POINTS_PER_CLASSIFICATION

            upload.status = 'completed'
            upload.save(update_fields=['status'])

        logger.info(
            f'Classification done: upload={upload_id}, kategori={kategori}, '
            f'confidence={confidence:.2f}, valid={is_valid}, points={points_awarded}'
        )
    except Exception as e:
        logger.error(f'process_classification: DB error persisting result: {e}', exc_info=True)
        upload.status = 'failed'
        upload.error_message = 'Gagal menyimpan hasil klasifikasi.'
        upload.save(update_fields=['status', 'error_message'])

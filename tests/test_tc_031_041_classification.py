"""
Test suite for FR-003 + FR-004: Klasifikasi + Tampil Hasil
Covers TC-031..TC-041.
"""
import os
import tempfile
from unittest import mock

from django.test import TestCase, override_settings
from rest_framework import status

from apps.uploads.models import Upload
from apps.classifications.models import ClassificationResult, KategoriSampah
from apps.classifications.services import (
    process_classification_sync, MIN_CONFIDENCE_THRESHOLD,
)
from .helpers import (
    create_civitas_user, auth_client,
    make_image_file, make_padded_image_file,
    mock_ml_classify, mock_ml_health, mock_ml_down,
)

UPLOAD_URL = '/api/v1/classifications/upload/'
POLL_URL = '/api/v1/classifications/{upload_id}/'

TEMP_MEDIA = tempfile.mkdtemp(prefix='pilah_test_media_clf_')


@override_settings(MEDIA_ROOT=TEMP_MEDIA)
class ClassificationBase(TestCase):
    def setUp(self):
        self.user = create_civitas_user()
        self.client = auth_client(self.user)

    def _upload_for_processing(self, image_name='daun.jpg', kategori='organik', conf=0.85):
        """Upload and run classification. Returns the Upload instance."""
        from .helpers import make_image_file
        with mock_ml_health(True), mock_ml_classify(kategori, conf):
            f = make_image_file('JPEG', image_name, size=(400, 300))
            r = self.client.post(UPLOAD_URL, {'file': f}, format='multipart')
        self.assertEqual(r.status_code, status.HTTP_202_ACCEPTED, msg=r.data)
        return Upload.objects.get(id=r.data['upload_id'])


# ---------------------------------------------------------------------------
# TC-031..TC-036: Classification variants
# ---------------------------------------------------------------------------
class TC031_ValidSingleObjectClassificationTest(ClassificationBase):
    """TC-031 - Foto objek tunggal valid -> organik, completed, poin awarded."""

    def test_tc031_classification_completed(self):
        u = self._upload_for_processing('daun.jpg', 'organik', 0.85)
        r = self.client.get(POLL_URL.format(upload_id=u.id))
        self.assertEqual(r.status_code, status.HTTP_200_OK)
        self.assertEqual(r.data['status'], 'completed')
        self.assertEqual(r.data['kategori'], 'organik')
        self.assertGreaterEqual(float(r.data['confidence']), 0.7)


class TC032_BlurOrNonWasteImageTest(ClassificationBase):
    """TC-032 - Low-confidence image -> tidak_dikenal, no poin."""

    def test_tc032_confidence_below_threshold(self):
        u = self._upload_for_processing('pemandangan.jpg', 'tidak_dikenal', 0.40)
        r = self.client.get(POLL_URL.format(upload_id=u.id))
        self.assertEqual(r.status_code, status.HTTP_200_OK)
        self.assertEqual(r.data['status'], 'completed')
        self.assertEqual(r.data['kategori'], 'tidak_dikenal')
        self.assertEqual(r.data['poin_diperoleh'], 0)


class TC033_ExactlyAtThresholdTest(ClassificationBase):
    """TC-033 - confidence exactly 0.70 -> valid (BVA exactly min)."""

    def test_tc033_confidence_exactly_70(self):
        u = self._upload_for_processing('kertas.jpg', 'anorganik', 0.70)
        r = self.client.get(POLL_URL.format(upload_id=u.id))
        self.assertEqual(r.status_code, status.HTTP_200_OK)
        self.assertEqual(r.data['status'], 'completed')
        self.assertEqual(r.data['kategori'], 'anorganik')
        # is_valid -> poin should be 10
        self.assertEqual(r.data['poin_diperoleh'], 10)
        cr = u.classification_result
        self.assertTrue(cr.is_valid)


class TC034_JustBelowThresholdTest(ClassificationBase):
    """TC-034 - confidence 0.69 -> is_valid=False, no poin (BVA just below)."""

    def test_tc034_confidence_69(self):
        u = self._upload_for_processing('botol.jpg', 'anorganik', 0.69)
        r = self.client.get(POLL_URL.format(upload_id=u.id))
        self.assertEqual(r.status_code, status.HTTP_200_OK)
        self.assertEqual(r.data['kategori'], 'tidak_dikenal')  # downgraded
        self.assertEqual(r.data['poin_diperoleh'], 0)
        cr = u.classification_result
        self.assertFalse(cr.is_valid)


class TC035_MLDownDuringProcessingTest(ClassificationBase):
    """TC-035 - ML down during polling -> status failed, 503 implicit."""

    def test_tc035_ml_down_during_processing(self):
        # Upload normally, then break ML before classification completes
        from .helpers import make_image_file
        with mock_ml_health(True), mock_ml_classify('organik', 0.85):
            f = make_image_file('JPEG', 'kardus.jpg', size=(400, 300))
            r = self.client.post(UPLOAD_URL, {'file': f}, format='multipart')
        # The synchronous service runs immediately. Force a re-run with ML down:
        u = Upload.objects.get(id=r.data['upload_id'])
        # Delete the existing result so we can re-process
        if hasattr(u, 'classification_result'):
            u.classification_result.delete()
        u.status = 'pending'
        u.save()
        # Now run classification with ML unavailable
        with mock_ml_down():
            process_classification_sync(str(u.id), self.user.id)
        u.refresh_from_db()
        self.assertEqual(u.status, 'failed')
        # Subsequent poll returns failed
        r = self.client.get(POLL_URL.format(upload_id=u.id))
        self.assertEqual(r.status_code, status.HTTP_200_OK)
        self.assertEqual(r.data['status'], 'failed')


class TC036_HappyPathDecisionTableTest(ClassificationBase):
    """TC-036 - Happy path: valid object, ML stable, confidence >= 70%."""

    def test_tc036_happy_path(self):
        u = self._upload_for_processing('kardus.jpg', 'anorganik', 0.92)
        r = self.client.get(POLL_URL.format(upload_id=u.id))
        self.assertEqual(r.status_code, status.HTTP_200_OK)
        self.assertEqual(r.data['status'], 'completed')
        self.assertEqual(r.data['kategori'], 'anorganik')
        self.assertEqual(r.data['poin_diperoleh'], 10)
        # User got +10
        self.user.refresh_from_db()
        self.assertEqual(self.user.total_poin, 10)


# ---------------------------------------------------------------------------
# TC-037..TC-041: Hasil Klasifikasi display
# ---------------------------------------------------------------------------
class TC037_DisplayOrganikResultTest(ClassificationBase):
    """TC-037 - Display completed organik result."""

    def test_tc037_organik_display(self):
        u = self._upload_for_processing('daun.jpg', 'organik', 0.92)
        r = self.client.get(POLL_URL.format(upload_id=u.id))
        self.assertEqual(r.status_code, status.HTTP_200_OK)
        self.assertEqual(r.data['kategori'], 'organik')
        self.assertIn('confidence', r.data)
        self.assertIn('deskripsi', r.data)


class TC038_DisplayAnorganikResultTest(ClassificationBase):
    """TC-038 - Display completed anorganik result."""

    def test_tc038_anorganik_display(self):
        u = self._upload_for_processing('botol.jpg', 'anorganik', 0.85)
        r = self.client.get(POLL_URL.format(upload_id=u.id))
        self.assertEqual(r.data['kategori'], 'anorganik')
        self.assertIn('deskripsi', r.data)


class TC039_ProcessingStateTest(ClassificationBase):
    """TC-039 - Status processing -> no result yet."""

    def test_tc039_processing_status(self):
        from .helpers import make_image_file
        with mock_ml_health(True), mock_ml_classify('organik', 0.85):
            f = make_image_file('JPEG', 'daun.jpg', size=(400, 300))
            r = self.client.post(UPLOAD_URL, {'file': f}, format='multipart')
        u = Upload.objects.get(id=r.data['upload_id'])
        # Force back to processing
        u.status = 'processing'
        u.save()
        r = self.client.get(POLL_URL.format(upload_id=u.id))
        self.assertEqual(r.status_code, status.HTTP_200_OK)
        self.assertEqual(r.data['status'], 'processing')


class TC040_LowConfidenceDisplayTest(ClassificationBase):
    """TC-040 - Confidence < 70% -> tidak_dikenal + tips."""

    def test_tc040_low_confidence_result(self):
        u = self._upload_for_processing('random.jpg', 'tidak_dikenal', 0.40)
        r = self.client.get(POLL_URL.format(upload_id=u.id))
        self.assertEqual(r.data['status'], 'completed')
        self.assertEqual(r.data['kategori'], 'tidak_dikenal')


class TC041_DisplayServerErrorHandlingTest(ClassificationBase):
    """TC-041 - Request failed -> retry available."""

    def test_tc041_404_for_unknown_upload(self):
        from uuid import uuid4
        r = self.client.get(POLL_URL.format(upload_id=str(uuid4())))
        self.assertEqual(r.status_code, status.HTTP_404_NOT_FOUND)

    def test_tc041_no_auth(self):
        from rest_framework.test import APIClient
        client = APIClient()
        from uuid import uuid4
        r = client.get(POLL_URL.format(upload_id=str(uuid4())))
        self.assertEqual(r.status_code, status.HTTP_401_UNAUTHORIZED)

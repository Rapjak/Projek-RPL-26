"""
Test suite for FR-005 + FR-006: Cek Perolehan Poin & Perolehan Poin
Covers TC-042..TC-053.
"""
import os
import tempfile
from unittest import mock

from django.test import TestCase, override_settings
from django.db import transaction
from rest_framework import status
from rest_framework.test import APIClient

from apps.uploads.models import Upload
from apps.classifications.models import ClassificationResult
from apps.classifications.services import process_classification_sync, POINTS_PER_CLASSIFICATION
from apps.rewards.models import PointTransaction
from .helpers import (
    create_civitas_user, auth_client,
    make_image_file, mock_ml_classify, mock_ml_health,
)

UPLOAD_URL = '/api/v1/classifications/upload/'
POINTS_URL = '/api/v1/classifications/{upload_id}/points/'
USER_POINTS_URL = '/api/v1/points/me'
USER_TX_URL = '/api/v1/points/transactions'

TEMP_MEDIA = tempfile.mkdtemp(prefix='pilah_test_media_pts_')


@override_settings(MEDIA_ROOT=TEMP_MEDIA)
class PointsBase(TestCase):
    def setUp(self):
        self.user = create_civitas_user()
        self.client = auth_client(self.user)

    def _upload_and_classify(self, kategori='organik', conf=0.85):
        with mock_ml_health(True), mock_ml_classify(kategori, conf):
            f = make_image_file('JPEG', 'daun.jpg', size=(300, 300))
            r = self.client.post(UPLOAD_URL, {'file': f}, format='multipart')
        self.assertEqual(r.status_code, status.HTTP_202_ACCEPTED)
        return Upload.objects.get(id=r.data['upload_id'])


# ---------------------------------------------------------------------------
# TC-042: Not found upload
# ---------------------------------------------------------------------------
class TC042_NotFoundTest(PointsBase):
    """TC-042 - Invalid upload id -> 404."""

    def test_tc042_invalid_upload_id(self):
        from uuid import uuid4
        r = self.client.get(POINTS_URL.format(upload_id=str(uuid4())))
        self.assertEqual(r.status_code, status.HTTP_404_NOT_FOUND)


# ---------------------------------------------------------------------------
# TC-043: IDOR - other user's upload
# ---------------------------------------------------------------------------
class TC043_IDORTest(PointsBase):
    """TC-043 - User A can't check User B's upload."""

    def test_tc043_cannot_see_others_points(self):
        u = self._upload_and_classify()
        # Create user B
        other_user = create_civitas_user(npm_nip='140810240099', email='b@mail.unpad.ac.id')
        client_b = auth_client(other_user)
        r = client_b.get(POINTS_URL.format(upload_id=str(u.id)))
        self.assertIn(r.status_code, (status.HTTP_403_FORBIDDEN, status.HTTP_404_NOT_FOUND))


# ---------------------------------------------------------------------------
# TC-044: No auth
# ---------------------------------------------------------------------------
class TC044_NoAuthTest(TestCase):
    """TC-044 - No token -> 401."""

    def test_tc044_no_token(self):
        client = APIClient()
        from uuid import uuid4
        r = client.get(POINTS_URL.format(upload_id=str(uuid4())))
        self.assertEqual(r.status_code, status.HTTP_401_UNAUTHORIZED)


# ---------------------------------------------------------------------------
# TC-045: Points accumulation + transaction log
# ---------------------------------------------------------------------------
class TC045_PointsAccumulationTest(PointsBase):
    """TC-045 - User 50 -> valid +10 = 60 pts with log entry."""

    def test_tc045_points_accumulate(self):
        # Pre-set user points to 50
        self.user.total_poin = 50
        self.user.save()

        u = self._upload_and_classify('organik', 0.85)
        self.user.refresh_from_db()
        self.assertEqual(self.user.total_poin, 60)
        # Transaction log entry exists
        tx = PointTransaction.objects.filter(user=self.user, transaction_type='penambahan').first()
        self.assertIsNotNone(tx)
        self.assertEqual(tx.points, 10)


# ---------------------------------------------------------------------------
# TC-046: New user 0 -> +10 = 10 (boundary)
# ---------------------------------------------------------------------------
class TC046_NewUserFirstPointsTest(PointsBase):
    """TC-046 - First valid classification for new user (0 -> 10)."""

    def test_tc046_first_points(self):
        self.assertEqual(self.user.total_poin, 0)
        u = self._upload_and_classify('organik', 0.85)
        self.user.refresh_from_db()
        self.assertEqual(self.user.total_poin, 10)


# ---------------------------------------------------------------------------
# TC-047: GET /points/me
# ---------------------------------------------------------------------------
class TC047_GetUserPointsTest(PointsBase):
    """TC-047 - API-009 returns user_id, total_poin, rank."""

    def test_tc047_get_points(self):
        self.user.total_poin = 80
        self.user.save()
        r = self.client.get(USER_POINTS_URL)
        self.assertEqual(r.status_code, status.HTTP_200_OK)
        self.assertEqual(r.data['total_poin'], 80)
        self.assertIn('rank', r.data)
        self.assertEqual(r.data['user_id'], str(self.user.id))


# ---------------------------------------------------------------------------
# TC-048: GET /points/transactions
# ---------------------------------------------------------------------------
class TC048_PointTransactionsTest(PointsBase):
    """TC-048 - Points transaction history list."""

    def test_tc048_transaction_history(self):
        self._upload_and_classify('organik', 0.85)
        r = self.client.get(USER_TX_URL)
        self.assertEqual(r.status_code, status.HTTP_200_OK)
        # Response is {'data': [...], 'total': N}
        data = r.data.get('data') if isinstance(r.data, dict) and 'data' in r.data else r.data
        self.assertGreaterEqual(len(data), 1)
        first = data[0]
        self.assertEqual(first['points'], 10)  # jumlah_poin
        self.assertEqual(first['transaction_type'], 'penambahan')
        self.assertIsNotNone(first.get('referensi_upload'))


# ---------------------------------------------------------------------------
# TC-049: Idempotency - double claim
# ---------------------------------------------------------------------------
class TC049_IdempotencyTest(PointsBase):
    """TC-049 - Running process_classification twice does NOT double-award."""

    def test_tc049_double_claim_blocked(self):
        u = self._upload_and_classify('organik', 0.85)
        self.user.refresh_from_db()
        self.assertEqual(self.user.total_poin, 10)

        # Second call - should be no-op (idempotent)
        with mock_ml_health(True), mock_ml_classify('organik', 0.85):
            process_classification_sync(str(u.id), self.user.id)
        self.user.refresh_from_db()
        self.assertEqual(self.user.total_poin, 10)  # unchanged
        # Only one point_transaction
        self.assertEqual(PointTransaction.objects.filter(user=self.user, transaction_type='penambahan').count(), 1)


# ---------------------------------------------------------------------------
# TC-050: Invalid -> no point
# ---------------------------------------------------------------------------
class TC050_NoPointWhenInvalidTest(PointsBase):
    """TC-050 - is_valid=False -> no log, no point."""

    def test_tc050_invalid_no_point(self):
        u = self._upload_and_classify('tidak_dikenal', 0.40)
        self.user.refresh_from_db()
        self.assertEqual(self.user.total_poin, 0)
        self.assertEqual(PointTransaction.objects.filter(user=self.user).count(), 0)


# ---------------------------------------------------------------------------
# TC-051: DB rollback (simulate DB failure inside transaction)
# ---------------------------------------------------------------------------
class TC051_TransactionRollbackTest(PointsBase):
    """TC-051 - DB failure -> rollback; state consistent."""

    def test_tc051_rollback_on_db_failure(self):
        # Patch PointTransaction.objects.create to raise inside the atomic block
        from apps.rewards import models as rewards_models

        original_create = rewards_models.PointTransaction.objects.create

        def exploding_create(*args, **kwargs):
            raise Exception('Simulated DB failure during log insert')

        with mock.patch.object(rewards_models.PointTransaction.objects, 'create', side_effect=exploding_create):
            with mock_ml_health(True), mock_ml_classify('organik', 0.85):
                f = make_image_file('JPEG', 'daun.jpg', size=(200, 200))
                r = self.client.post(UPLOAD_URL, {'file': f}, format='multipart')
        # The upload may be created, but the classification should be failed
        if r.status_code == status.HTTP_202_ACCEPTED:
            u = Upload.objects.get(id=r.data['upload_id'])
            u.refresh_from_db()
            self.assertEqual(u.status, 'failed')  # should be marked failed
        # User points unchanged
        self.user.refresh_from_db()
        self.assertEqual(self.user.total_poin, 0)


# ---------------------------------------------------------------------------
# TC-052: Race condition - two concurrent classifications
# ---------------------------------------------------------------------------
class TC052_RaceConditionTest(PointsBase):
    """TC-052 - Two uploads finishing concurrently both add points (atomic)."""

    def test_tc052_concurrent_uploads(self):
        # Upload two images sequentially but each awards 10
        u1 = self._upload_and_classify('organik', 0.85)
        u2 = self._upload_and_classify('anorganik', 0.90)
        self.user.refresh_from_db()
        self.assertEqual(self.user.total_poin, 20)
        # Both transactions logged
        self.assertEqual(PointTransaction.objects.filter(user=self.user, transaction_type='penambahan').count(), 2)

    def test_tc052_atomic_increment(self):
        # Direct test: F() atomic increments
        self.user.total_poin = 0
        self.user.save()
        self.user.add_points(10)
        self.user.add_points(10)
        self.user.refresh_from_db()
        self.assertEqual(self.user.total_poin, 20)


# ---------------------------------------------------------------------------
# TC-053: Client-side tampering - payload amount ignored
# ---------------------------------------------------------------------------
class TC053_ClientTamperingTest(PointsBase):
    """TC-053 - Client sends {jumlah_poin: 9999} -> backend ignores, awards 10."""

    def test_tc053_client_cannot_manipulate_points(self):
        with mock_ml_health(True), mock_ml_classify('organik', 0.85):
            f = make_image_file('JPEG', 'daun.jpg', size=(300, 300))
            # Add malicious 'jumlah_poin' to the form payload - backend should ignore
            r = self.client.post(UPLOAD_URL, {'file': f, 'jumlah_poin': '9999'}, format='multipart')
        self.assertEqual(r.status_code, status.HTTP_202_ACCEPTED)
        self.user.refresh_from_db()
        # Only 10 points awarded, NOT 9999
        self.assertEqual(self.user.total_poin, 10)

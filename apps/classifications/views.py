"""
Classification views for API-008 (cek perolehan poin).
Also houses list/detail views (re-exported from uploads.views for URL compatibility).
"""
import logging
from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.uploads.models import Upload
from .models import ClassificationResult

logger = logging.getLogger(__name__)


class ClassificationPointsView(APIView):
    """
    API-008: Check whether this upload's classification earned points.
    Returns stateless result (idempotent, does not mutate points) - TC-042..TC-044, TC-050.
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, upload_id):
        try:
            upload = Upload.objects.select_related('classification_result').get(id=upload_id)
        except Upload.DoesNotExist:
            return Response(
                {'error': {'code': 'ERR_NOT_FOUND', 'message': 'Data unggahan tidak ditemukan'}},
                status=status.HTTP_404_NOT_FOUND,
            )
        except (ValueError, AssertionError):
            return Response(
                {'error': {'code': 'ERR_NOT_FOUND', 'message': 'Data unggahan tidak ditemukan'}},
                status=status.HTTP_404_NOT_FOUND,
            )

        # IDOR check (TC-043): user cannot check points of other users' uploads
        if upload.user_id != request.user.id:
            return Response(
                {'error': {'code': 'ERR_NOT_FOUND', 'message': 'Data unggahan tidak ditemukan'}},
                status=status.HTTP_404_NOT_FOUND,
            )

        # Logic based on upload + classification state (TC-039 processing, TC-040 invalid, TC-045..TC-050)
        if upload.status in ('pending', 'processing'):
            return Response({
                'upload_id': str(upload.id),
                'memenuhi_syarat': False,
                'jumlah_poin': 0,
                'alasan': 'Proses klasifikasi belum selesai. Mohon tunggu.',
            })

        if upload.status == 'failed' or not hasattr(upload, 'classification_result'):
            return Response({
                'upload_id': str(upload.id),
                'memenuhi_syarat': False,
                'jumlah_poin': 0,
                'alasan': 'Klasifikasi gagal atau tidak dapat diproses. Tidak ada poin.',
            })

        result = upload.classification_result
        if not result.is_valid:
            return Response({
                'upload_id': str(upload.id),
                'memenuhi_syarat': False,
                'jumlah_poin': 0,
                'alasan': 'Tingkat keyakinan model di bawah 70%. Tidak ada poin.',
            })

        return Response({
            'upload_id': str(upload.id),
            'memenuhi_syarat': True,
            'jumlah_poin': result.points_awarded,
            'alasan': 'Aktivitas memenuhi ketentuan pemilahan. Poin telah ditambahkan ke akun Anda.',
        })

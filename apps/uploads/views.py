"""
Upload views - API-005 (POST /api/v1/classifications upload) & API-007 (GET /api/v1/classifications).

Note: Combined the upload + classify initiation under one POST endpoint to match API-005.
Flow:
  - POST /api/v1/classifications (form-data: foto) -> saves upload, kicks off classification,
    returns upload_id with status 202 Accepted
  - GET /api/v1/classifications/{upload_id} -> returns current status + result if completed (polling)
  - GET /api/v1/classifications?kategori=...&page=1&limit=10 -> list history (API-007)
"""
import logging
from django.db import transaction
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.views import APIView
from rest_framework.exceptions import PermissionDenied
from apps.classifications.services import process_classification_async
from apps.utils.pagination import StandardResultsSetPagination
from .models import Upload
from .serializers import UploadSerializer, UploadDetailSerializer

logger = logging.getLogger(__name__)


class UploadCreateView(APIView):
    """API-005 - Upload & initiate classification. Returns 202 + upload_id."""
    permission_classes = [permissions.IsAuthenticated]
    parser_classes = (MultiPartParser, FormParser)

    def post(self, request):
        serializer = UploadSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        with transaction.atomic():
            upload = serializer.save(user=request.user)

        # Kick off classification (synchronous now, async-ready structure)
        # We do it after the response commits the upload record to avoid lost records.
        # For TC-019 (ML down) the service handles 503 gracefully.
        try:
            process_classification_async(str(upload.id), request.user.id)
        except Exception as e:
            logger.error(f"Classification trigger failed for upload {upload.id}: {e}")
            # Not a fatal error - status remains pending/processing, frontend can poll

        return Response({
            'message': 'Foto berhasil diunggah dan sedang diproses',
            'upload_id': str(upload.id),
            'status': 'processing',
            'url_foto': upload.url_foto,
        }, status=status.HTTP_202_ACCEPTED)


class UploadDetailView(APIView):
    """API-006 - Poll classification status by upload_id."""
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, upload_id):
        try:
            upload = Upload.objects.select_related('user', 'classification_result').get(id=upload_id)
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

        # IDOR check (TC-043)
        if upload.user_id != request.user.id:
            return Response(
                {'error': {'code': 'ERR_NOT_FOUND', 'message': 'Data unggahan tidak ditemukan'}},
                status=status.HTTP_404_NOT_FOUND,
            )

        data = {
            'upload_id': str(upload.id),
            'status': upload.status,
            'waktu_upload': upload.created_at.isoformat(),
        }

        if upload.status == 'completed' and hasattr(upload, 'classification_result'):
            result = upload.classification_result
            data.update({
                'kategori': result.kategori_sampah,
                'confidence': float(result.confidence_score),
                'is_valid': result.is_valid,
                'deskripsi': result.handling_instructions,
                'poin_diperoleh': result.points_awarded,
            })
        elif upload.status == 'failed':
            data['error'] = upload.error_message or 'Klasifikasi gagal'

        return Response(data, status=status.HTTP_200_OK)


class UploadListView(generics.ListAPIView):
    """API-007 - Riwayat unggahan (history). Filter by kategori."""
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = UploadDetailSerializer
    pagination_class = StandardResultsSetPagination

    def get_queryset(self):
        qs = Upload.objects.filter(user=self.request.user).select_related('user')
        # Optional filter by kategori (via classification result)
        kategori = self.request.query_params.get('kategori', 'semua')
        if kategori and kategori != 'semua':
            qs = qs.filter(classification_result__kategori_sampah=kategori)
        return qs.order_by('-created_at')

    def list(self, request, *args, **kwargs):
        response = super().list(request, *args, **kwargs)
        # Augment response with summary totals (API-007 output spec)
        qs = self.get_queryset()
        total_unggahan = qs.count()
        # Sum points from related classification results
        total_poin = sum(
            cr.points_awarded for cr in (
                r.classification_result for r in qs if hasattr(r, 'classification_result')
            ) if cr
        )
        response.data = {
            'data': response.data.get('results', response.data),
            'total_unggahan': total_unggahan,
            'total_poin_diperoleh': total_poin,
            'total': response.data.get('count', 0),
            'page': int(self.request.query_params.get('page', 1)),
        }
        return response

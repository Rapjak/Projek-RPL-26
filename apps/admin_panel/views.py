"""
Admin / monitoring views - API-016 (dashboard), API-017 (activities),
API-018 (CRUD rewards), API-019 (CRUD education).

Permission: only role=admin_gogreen OR role=pimpinan.
"""
import logging
from datetime import datetime, timedelta
from django.db.models import Count, Sum, Q
from django.utils import timezone
from django.contrib.auth import get_user_model
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.uploads.models import Upload
from apps.classifications.models import ClassificationResult
from apps.rewards.models import Reward, PointTransaction
from apps.education.models import EducationMaterial
from apps.education.serializers import EducationMaterialSerializer
from apps.rewards.serializers import RewardSerializer
from apps.utils.pagination import StandardResultsSetPagination

logger = logging.getLogger(__name__)
User = get_user_model()


class IsAdminOrPimpinan(permissions.BasePermission):
    """Allows only admin_gogreen or pimpinan roles."""

    def has_permission(self, request, view):
        return (
            request.user and
            request.user.is_authenticated and
            request.user.role in ('admin_gogreen', 'pimpinan')
        )


class AdminDashboardView(APIView):
    """API-016 - aggregate dashboard statistics."""
    permission_classes = [permissions.IsAuthenticated, IsAdminOrPimpinan]

    def get(self, request):
        today = timezone.localdate()
        total_pengguna = User.objects.filter(role='civitas').count()

        # Optional date filters
        tanggal_mulai = request.query_params.get('tanggal_mulai')
        tanggal_akhir = request.query_params.get('tanggal_akhir')
        uploads = Upload.objects.all()
        if tanggal_mulai:
            try:
                dt = datetime.strptime(tanggal_mulai, '%Y-%m-%d')
                uploads = uploads.filter(created_at__date__gte=dt.date())
            except ValueError:
                pass
        if tanggal_akhir:
            try:
                dt = datetime.strptime(tanggal_akhir, '%Y-%m-%d')
                uploads = uploads.filter(created_at__date__lte=dt.date())
            except ValueError:
                pass

        total_upload_hari_ini = uploads.filter(created_at__date=today).count()
        total_upload = uploads.count()

        # Points distributed
        poin_qs = PointTransaction.objects.filter(transaction_type='penambahan')
        if tanggal_mulai:
            try:
                dt = datetime.strptime(tanggal_mulai, '%Y-%m-%d')
                poin_qs = poin_qs.filter(created_at__date__gte=dt.date())
            except ValueError:
                pass
        total_poin_terdistribusi = poin_qs.aggregate(s=Sum('points'))['s'] or 0

        # Category distribution
        distribusi = {}
        for row in ClassificationResult.objects.filter(upload__in=uploads).values('kategori_sampah').annotate(c=Count('id')):
            distribusi[row['kategori_sampah']] = row['c']

        # Accuracy
        agg = ClassificationResult.objects.filter(upload__in=uploads).aggregate(
            avg_conf=Sum('confidence_score') / Count('id') if ClassificationResult.objects.filter(upload__in=uploads).exists() else None
        )
        # Simpler: average confidence
        from django.db.models import Avg
        avg_conf = ClassificationResult.objects.filter(upload__in=uploads).aggregate(a=Avg('confidence_score'))['a']
        akurasi_rata_rata = float(avg_conf) if avg_conf else 0.0

        # Weekly trend (7 days)
        tren = []
        for i in range(6, -1, -1):
            d = today - timedelta(days=i)
            count = Upload.objects.filter(created_at__date=d).count()
            tren.append({'tanggal': d.isoformat(), 'jumlah': count})

        return Response({
            'total_pengguna': total_pengguna,
            'total_upload': total_upload,
            'total_upload_hari_ini': total_upload_hari_ini,
            'total_poin_terdistribusi': total_poin_terdistribusi,
            'akurasi_rata_rata': round(akurasi_rata_rata, 4),
            'distribusi_kategori': distribusi,
            'tren_mingguan': tren,
        })


class AdminActivitiesView(generics.ListAPIView):
    """API-017 - user activity data with filters."""
    permission_classes = [permissions.IsAuthenticated, IsAdminOrPimpinan]
    pagination_class = StandardResultsSetPagination

    def get_queryset(self):
        qs = Upload.objects.select_related('user', 'classification_result').all()
        params = self.request.query_params

        unit = params.get('unit_gedung')
        if unit:
            qs = qs.filter(user__unit_gedung__icontains=unit)

        tanggal_mulai = params.get('tanggal_mulai')
        if tanggal_mulai:
            try:
                dt = datetime.strptime(tanggal_mulai, '%Y-%m-%d')
                qs = qs.filter(created_at__date__gte=dt.date())
            except ValueError:
                pass

        tanggal_akhir = params.get('tanggal_akhir')
        if tanggal_akhir:
            try:
                dt = datetime.strptime(tanggal_akhir, '%Y-%m-%d')
                qs = qs.filter(created_at__date__lte=dt.date())
            except ValueError:
                pass

        kategori = params.get('kategori')
        if kategori:
            qs = qs.filter(classification_result__kategori_sampah=kategori)

        return qs.order_by('-created_at')

    def get_serializer_class(self):
        # Not used directly - we build the response in list()
        return None

    def list(self, request, *args, **kwargs):
        qs = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(qs)
        uploads = page if page is not None else list(qs)

        data = []
        for u in uploads:
            cr = getattr(u, 'classification_result', None)
            data.append({
                'user_id': str(u.user_id),
                'npm_nip': u.user.npm_nip,
                'nama': u.user.name,
                'unit_gedung': u.user.unit_gedung,
                'waktu_upload': u.created_at.isoformat(),
                'kategori': cr.kategori_sampah if cr else None,
                'confidence': float(cr.confidence_score) if cr else None,
                'poin_diperoleh': cr.points_awarded if cr else 0,
            })

        total = qs.count()
        return Response({
            'data': data,
            'total': total,
            'page': int(request.query_params.get('page', 1)),
        })


class AdminRewardView(APIView):
    """API-018 - Create/update/delete rewards."""
    permission_classes = [permissions.IsAuthenticated, IsAdminOrPimpinan]

    def post(self, request):
        serializer = RewardSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        reward = serializer.save()
        return Response({
            'message': 'Reward berhasil ditambahkan',
            'reward_id': str(reward.id),
            'reward': RewardSerializer(reward).data,
        }, status=status.HTTP_201_CREATED)


class AdminRewardDetailView(APIView):
    """API-018 - Update / delete existing reward."""
    permission_classes = [permissions.IsAuthenticated, IsAdminOrPimpinan]

    def put(self, request, reward_id):
        try:
            reward = Reward.objects.get(id=reward_id)
        except Reward.DoesNotExist:
            return Response({'error': {'code': 'ERR_NOT_FOUND', 'message': 'Reward tidak ditemukan'}},
                            status=status.HTTP_404_NOT_FOUND)
        serializer = RewardSerializer(reward, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({'message': 'Reward berhasil diperbarui', 'reward': serializer.data})

    def delete(self, request, reward_id):
        try:
            reward = Reward.objects.get(id=reward_id)
        except Reward.DoesNotExist:
            return Response({'error': {'code': 'ERR_NOT_FOUND', 'message': 'Reward tidak ditemukan'}},
                            status=status.HTTP_404_NOT_FOUND)
        reward.is_active = False
        reward.save(update_fields=['is_active'])
        return Response({'message': 'Reward berhasil dihapus'})


class AdminEducationView(APIView):
    """API-019 - Create/update/delete education material."""
    permission_classes = [permissions.IsAuthenticated, IsAdminOrPimpinan]

    def post(self, request):
        serializer = EducationMaterialSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        material = serializer.save()
        return Response({
            'message': 'Materi edukasi berhasil dipublikasikan',
            'id_edukasi': str(material.id),
        }, status=status.HTTP_201_CREATED)


class AdminEducationDetailView(APIView):
    """API-019 - Update / delete education material."""
    permission_classes = [permissions.IsAuthenticated, IsAdminOrPimpinan]

    def put(self, request, edu_id):
        try:
            material = EducationMaterial.objects.get(id=edu_id)
        except EducationMaterial.DoesNotExist:
            return Response({'error': {'code': 'ERR_NOT_FOUND', 'message': 'Materi tidak ditemukan'}},
                            status=status.HTTP_404_NOT_FOUND)
        serializer = EducationMaterialSerializer(material, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({'message': 'Materi berhasil diperbarui'})

    def delete(self, request, edu_id):
        try:
            material = EducationMaterial.objects.get(id=edu_id)
        except EducationMaterial.DoesNotExist:
            return Response({'error': {'code': 'ERR_NOT_FOUND', 'message': 'Materi tidak ditemukan'}},
                            status=status.HTTP_404_NOT_FOUND)
        material.delete()
        return Response({'message': 'Materi berhasil dihapus'})

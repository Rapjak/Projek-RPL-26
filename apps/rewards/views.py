"""
Rewards + Points + Leaderboard views - API-010, API-011, API-012, API-013, API-018.
"""
import secrets
import logging
from django.db import transaction
from django.db.models import Sum, Count, F
from django.contrib.auth import get_user_model
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Reward, RewardRedemption, PointTransaction
from .serializers import (
    RewardSerializer, RewardRedemptionSerializer, RedeemSerializer, PointTransactionSerializer,
)
from apps.utils.pagination import StandardResultsSetPagination

logger = logging.getLogger(__name__)
User = get_user_model()


class RewardListView(generics.ListAPIView):
    """API-012 - Rewards catalog. Only available rewards shown."""
    serializer_class = RewardSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = StandardResultsSetPagination

    def get_queryset(self):
        qs = Reward.objects.filter(is_active=True)
        return qs.filter(stock__gt=0)


class RedeemRewardView(APIView):
    """API-013 - Redeem a reward by id."""
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, reward_id):
        user = request.user

        with transaction.atomic():
            # select_for_update must be inside the transaction
            try:
                reward = Reward.objects.select_for_update().get(id=reward_id)
            except Reward.DoesNotExist:
                return Response(
                    {'error': {'code': 'ERR_NOT_FOUND', 'message': 'Reward tidak ditemukan'}},
                    status=status.HTTP_404_NOT_FOUND,
                )

            # Re-fetch user inside the transaction for atomicity
            from django.contrib.auth import get_user_model
            User = get_user_model()
            user = User.objects.select_for_update().get(id=user.id)

            if not reward.is_active or reward.stock <= 0:
                return Response(
                    {'error': {'code': 'ERR_REWARD_UNAVAILABLE', 'message': 'Reward sudah habis atau sudah tidak berlaku.'}},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            if user.total_poin < reward.points_required:
                return Response(
                    {'error': {
                        'code': 'ERR_INSUFFICIENT_POINTS',
                        'message': f'Poin tidak mencukupi. Dibutuhkan {reward.points_required} poin, poin Anda saat ini {user.total_poin}.'
                    }},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            voucher = f'RWD-{secrets.token_hex(3).upper()}-{reward.id.hex[:4].upper()}'
            redemption = RewardRedemption.objects.create(
                user=user, reward=reward, kode_voucher=voucher, status='aktif',
            )
            # Deduct points atomically
            user.deduct_points(reward.points_required)
            reward.stock -= 1
            reward.save(update_fields=['stock'])

            PointTransaction.objects.create(
                user=user,
                points=reward.points_required,
                transaction_type='pengurangan',
                description=f'Penukaran reward: {reward.name}',
                reference_id=redemption.id,
            )

        return Response({
            'message': 'Reward berhasil digunakan',
            'sisa_poin': user.total_poin,
            'kode_reward': voucher,
            'nama_reward': reward.name,
            'redemption_id': str(redemption.id),
        }, status=status.HTTP_200_OK)


class RedemptionListView(generics.ListAPIView):
    """List user's redemptions."""
    serializer_class = RewardRedemptionSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = StandardResultsSetPagination

    def get_queryset(self):
        return RewardRedemption.objects.filter(user=self.request.user).select_related('reward')


class PointTransactionListView(generics.ListAPIView):
    """API-010 - Points transaction history."""
    serializer_class = PointTransactionSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = StandardResultsSetPagination

    def get_queryset(self):
        return PointTransaction.objects.filter(user=self.request.user).order_by('-created_at')

    def list(self, request, *args, **kwargs):
        response = super().list(request, *args, **kwargs)
        response.data = {
            'data': response.data.get('results', response.data),
            'total': response.data.get('count', 0),
        }
        return response


class LeaderboardView(APIView):
    """API-011 - Leaderboard (type=user or type=building)."""
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        leaderboard_type = request.query_params.get('type', 'user')
        page = int(request.query_params.get('page', 1))
        limit = int(request.query_params.get('limit', 10))
        offset = (page - 1) * limit

        if leaderboard_type == 'building':
            return self._building_leaderboard(request, offset, limit)
        return self._user_leaderboard(request, offset, limit)

    def _user_leaderboard(self, request, offset, limit):
        user = request.user
        qs = User.objects.filter(role='civitas', is_active=True).order_by('-total_poin', 'name')
        total = qs.count()

        # Build ranked data (in-memory ranking is fine for reasonable user counts)
        ranked_all = list(qs.values('id', 'name', 'unit_gedung', 'total_poin'))
        for idx, row in enumerate(ranked_all, start=1):
            row['rank'] = idx
            row['id'] = str(row['id'])

        # Compute current user's rank
        my_rank = next((r['rank'] for r in ranked_all if r['id'] == str(user.id)), None)

        paginated = ranked_all[offset:offset + limit]

        return Response({
            'type': 'user',
            'data': paginated,
            'user_rank': my_rank,
            'user_poin': user.total_poin,
            'total_peserta': total,
            'page': offset // limit + 1 if limit else 1,
        })

    def _building_leaderboard(self, request, offset, limit):
        qs = (
            User.objects.filter(role='civitas', is_active=True)
            .values('unit_gedung')
            .annotate(total_poin=Sum('total_poin'))
            .order_by('-total_poin')
        )
        ranked = []
        for idx, row in enumerate(qs, start=1):
            ranked.append({
                'rank': idx,
                'unit_gedung': row['unit_gedung'],
                'total_poin': row['total_poin'] or 0,
            })
        # Determine current user's building rank
        user_building = request.user.unit_gedung
        my_rank = next((r['rank'] for r in ranked if r['unit_gedung'] == user_building), None)

        paginated = ranked[offset:offset + limit]
        return Response({
            'type': 'building',
            'data': paginated,
            'user_building_rank': my_rank,
            'user_building': user_building,
            'page': offset // limit + 1 if limit else 1,
        })

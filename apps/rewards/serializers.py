"""Serializers for rewards + point transactions + leaderboard."""
import secrets
from rest_framework import serializers
from .models import Reward, RewardRedemption, PointTransaction


class RewardSerializer(serializers.ModelSerializer):
    ketersediaan = serializers.SerializerMethodField()

    class Meta:
        model = Reward
        fields = ('id', 'name', 'description', 'points_required', 'ketersediaan',
                  'stock', 'masa_berlaku', 'is_active', 'image')
        read_only_fields = ('id', 'ketersediaan')

    def get_ketersediaan(self, obj):
        return obj.is_available


class RewardRedemptionSerializer(serializers.ModelSerializer):
    nama_reward = serializers.CharField(source='reward.name', read_only=True)

    class Meta:
        model = RewardRedemption
        fields = ('id', 'reward', 'nama_reward', 'kode_voucher', 'status',
                  'tanggal_penukaran', 'tanggal_digunakan')
        read_only_fields = ('id', 'kode_voucher', 'status', 'tanggal_penukaran', 'tanggal_digunakan')


class RedeemSerializer(serializers.Serializer):
    """Request body for redemption (API-013)."""
    reward_id = serializers.UUIDField(required=True)


class PointTransactionSerializer(serializers.ModelSerializer):
    referensi_upload = serializers.UUIDField(source='reference_id', read_only=True)

    class Meta:
        model = PointTransaction
        fields = ('id', 'points', 'transaction_type', 'description',
                  'referensi_upload', 'created_at')
        read_only_fields = ('id', 'points', 'transaction_type', 'description',
                            'referensi_upload', 'created_at')

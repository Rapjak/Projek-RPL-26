from django.contrib import admin
from .models import Reward, RewardRedemption, PointTransaction


@admin.register(Reward)
class RewardAdmin(admin.ModelAdmin):
    list_display = ('name', 'points_required', 'stock', 'masa_berlaku', 'is_active', 'created_at')
    list_filter = ('is_active',)
    search_fields = ('name', 'description')
    readonly_fields = ('id', 'created_at')


@admin.register(RewardRedemption)
class RewardRedemptionAdmin(admin.ModelAdmin):
    list_display = ('kode_voucher', 'user', 'reward', 'status', 'tanggal_penukaran', 'tanggal_digunakan')
    list_filter = ('status',)
    search_fields = ('kode_voucher', 'user__npm_nip', 'reward__name')
    readonly_fields = ('id', 'kode_voucher', 'tanggal_penukaran')


@admin.register(PointTransaction)
class PointTransactionAdmin(admin.ModelAdmin):
    list_display = ('user', 'points', 'transaction_type', 'description', 'created_at')
    list_filter = ('transaction_type',)
    search_fields = ('user__npm_nip', 'description')
    readonly_fields = ('id', 'created_at')

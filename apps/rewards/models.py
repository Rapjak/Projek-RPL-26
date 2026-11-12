"""
Rewards models - data dictionary (rewards, reward_redemptions, point_transactions).

reward: id_reward, nama_reward, deskripsi, poin_dibutuhkan, stok, masa_berlaku, is_active
redemption: id_penukaran, id_pengguna, id_reward, kode_voucher (unique), status,
            tanggal_penukaran, tanggal_digunakan
point_transaction: id_transaksi, id_pengguna, id_referensi, jumlah_poin, jenis_transaksi,
                   deskripsi, created_at
"""
import uuid
from django.db import models
from django.utils import timezone
from django.conf import settings


class Reward(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField('Nama Reward', max_length=100)
    description = models.TextField('Deskripsi', blank=True, default='')
    points_required = models.IntegerField('Poin Dibutuhkan')
    image = models.ImageField(upload_to='rewards/', blank=True, null=True)
    stock = models.IntegerField('Stok', default=0)
    masa_berlaku = models.DateField('Masa Berlaku', default=timezone.localdate)
    is_active = models.BooleanField('Aktif', default=True)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = 'rewards'
        ordering = ['points_required']

    def __str__(self):
        return f'{self.name} ({self.points_required} poin)'

    @property
    def is_available(self):
        return self.is_active and self.stock > 0 and self.masa_berlaku >= timezone.localdate()


class RewardRedemption(models.Model):
    STATUS_CHOICES = [
        ('aktif', 'Aktif'),
        ('terpakai', 'Terpakai'),
        ('kedaluwarsa', 'Kedaluwarsa'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='redemptions',
        db_column='id_pengguna',
    )
    reward = models.ForeignKey(Reward, on_delete=models.CASCADE, related_name='redemptions', db_column='id_reward')
    kode_voucher = models.CharField('Kode Voucher', max_length=50, unique=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='aktif')
    tanggal_penukaran = models.DateTimeField(default=timezone.now)
    tanggal_digunakan = models.DateTimeField(blank=True, null=True)

    class Meta:
        db_table = 'reward_redemptions'
        ordering = ['-tanggal_penukaran']

    def __str__(self):
        return f'{self.user.npm_nip} - {self.reward.name} ({self.kode_voucher})'


class PointTransaction(models.Model):
    TRANSACTION_TYPES = [
        ('penambahan', 'Penambahan'),
        ('pengurangan', 'Pengurangan'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='point_transactions',
        db_column='id_pengguna',
    )
    reference_id = models.UUIDField(null=True, blank=True)  # id_unggahan OR id_penukaran
    points = models.IntegerField('Jumlah Poin')
    transaction_type = models.CharField('Jenis Transaksi', max_length=20, choices=TRANSACTION_TYPES)
    description = models.CharField('Deskripsi', max_length=255, blank=True, default='')
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = 'point_transactions'
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.user.npm_nip} - {self.transaction_type} +{self.points}'

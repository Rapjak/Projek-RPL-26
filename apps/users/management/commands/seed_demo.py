"""
Management command: seed_demo

Mengisi data demo agar aplikasi langsung bisa dicoba setelah clone:
- Akun admin GoGreen (admin.gogreen@unpad.ac.id / AdminPass123!)
- 3 materi edukasi (organik, anorganik, residu)
- 3 reward contoh

Idempotent: aman dijalankan berkali-kali (tidak menduplikasi data).

Usage:
    python manage.py seed_demo
"""
from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta

from apps.users.models import User
from apps.education.models import EducationMaterial, EduCategory
from apps.rewards.models import Reward


ADMIN = dict(
    npm_nip='ADM-001',
    name='Admin GoGreen',
    email='admin.gogreen@unpad.ac.id',
    unit_gedung='Pimpinan',
    password='AdminPass123!',
)

EDUCATION = [
    dict(
        judul='Memilah Sampah Organik dengan Benar',
        kategori_sampah=EduCategory.ORGANIK,
        ringkasan='Panduan memilah dan mengolah sampah organik rumah tangga.',
        konten=(
            'Sampah organik adalah sampah yang mudah terurai secara alami, seperti sisa makanan, '
            'daun, dan ranting. Pisahkan sampah organik dari anorganik dan residu. '
            'Sampah organik dapat diolah menjadi kompos yang bermanfaat untuk tanaman. '
            'Buang sampah organik ke tempat sampah berwarna hijau.'
        ),
    ),
    dict(
        judul='Daur Ulang Sampah Anorganik',
        kategori_sampah=EduCategory.ANORGANIK,
        ringkasan='Cara mendaur ulang plastik, kertas, dan logam.',
        konten=(
            'Sampah anorganik adalah sampah yang sulit terurai, seperti plastik, kertas, kaca, dan logam. '
            'Bersihkan dan keringkan sebelum didaur ulang. Pisahkan berdasarkan jenis material. '
            'Buang sampah anorganik ke tempat sampah berwarna biru.'
        ),
    ),
    dict(
        judul='Sampah Residu dan Penanganannya',
        kategori_sampah=EduCategory.RESIDU,
        ringkasan='Penanganan sampah yang tidak dapat didaur ulang.',
        konten=(
            'Sampah residu adalah sampah yang tidak dapat terurai maupun didaur ulang, '
            'seperti puntung rokok, popok, dan styrofoam. Kurangi penggunaannya, '
            'dan buang ke tempat sampah berwarna abu-abu.'
        ),
    ),
]

REWARDS = [
    dict(name='Diskon Kantin 10%', description='Potongan harga 10% di kantin kampus.',
         points_required=5, stock=10),
    dict(name='Voucher Fotokopi', description='Gratis fotokopi 20 lembar.',
         points_required=10, stock=15),
    dict(name='Tumbler Eksklusif', description='Tumbler Pilah.in edisi terbatas.',
         points_required=50, stock=5),
]


class Command(BaseCommand):
    help = 'Seed data demo: admin GoGreen, materi edukasi, dan reward contoh.'

    def handle(self, *args, **options):
        # --- Admin ---
        admin, created = User.objects.get_or_create(
            email=ADMIN['email'],
            defaults=dict(
                npm_nip=ADMIN['npm_nip'],
                name=ADMIN['name'],
                unit_gedung=ADMIN['unit_gedung'],
                role='admin_gogreen',
                is_staff=True,
            ),
        )
        if created:
            admin.set_password(ADMIN['password'])
            admin.save()
            self.stdout.write(self.style.SUCCESS(
                f'[OK] Admin dibuat: {ADMIN["email"]} / {ADMIN["password"]}'
            ))
        else:
            self.stdout.write(f'[SKIP] Admin sudah ada: {ADMIN["email"]}')

        # --- Education materials ---
        edu_created = 0
        for item in EDUCATION:
            exists = EducationMaterial.objects.filter(judul=item['judul']).exists()
            if not exists:
                EducationMaterial.objects.create(
                    judul=item['judul'],
                    kategori_sampah=item['kategori_sampah'],
                    ringkasan=item['ringkasan'],
                    konten=item['konten'],
                    is_published=True,
                )
                edu_created += 1
        self.stdout.write(f'[OK] Materi edukasi ditambahkan: {edu_created} (total: {EducationMaterial.objects.count()})')

        # --- Rewards ---
        reward_created = 0
        for item in REWARDS:
            exists = Reward.objects.filter(name=item['name']).exists()
            if not exists:
                Reward.objects.create(
                    name=item['name'],
                    description=item['description'],
                    points_required=item['points_required'],
                    stock=item['stock'],
                    masa_berlaku=timezone.localdate() + timedelta(days=365),
                    is_active=True,
                )
                reward_created += 1
        self.stdout.write(f'[OK] Reward ditambahkan: {reward_created} (total: {Reward.objects.count()})')

        self.stdout.write(self.style.SUCCESS('\nSeed demo selesai!'))
        self.stdout.write('Login admin: admin.gogreen@unpad.ac.id / AdminPass123!')
        self.stdout.write('Login civitas: daftar dulu lewat halaman Register.')

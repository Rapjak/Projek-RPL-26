"""
User model for Pilah.in - follows data dictionary spec (DATA-001).

Table: users
Fields: id_pengguna (UUID), npm_nip, nama, email, password_hash, peran,
        unit_gedung, total_poin, created_at, updated_at
"""
import uuid
from django.db import models
from django.utils import timezone
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin


class RoleChoices(models.TextChoices):
    CIVITAS = 'civitas', 'Civitas Akademika'
    ADMIN_GOGREEN = 'admin_gogreen', 'Admin GoGreen'
    PIMPINAN = 'pimpinan', 'Pimpinan Fakultas'


class UserManager(BaseUserManager):
    """Custom user manager where email is the unique identifier."""

    def create_user(self, npm_nip, name, email, unit_gedung, password=None, **extra_fields):
        if not email:
            raise ValueError('Email wajib diisi')
        if not npm_nip:
            raise ValueError('NPM/NIP wajib diisi')
        email = self.normalize_email(email)
        # Force role to civitas on public registration unless explicitly set
        extra_fields.setdefault('role', RoleChoices.CIVITAS)
        user = self.model(
            npm_nip=npm_nip,
            name=name,
            email=email,
            unit_gedung=unit_gedung,
            **extra_fields,
        )
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_admin(self, npm_nip, name, email, unit_gedung, password=None, role=RoleChoices.ADMIN_GOGREEN, **extra_fields):
        """Create admin/pimpinan account (for seeding only, not public registration)."""
        extra_fields.setdefault('is_staff', True)
        extra_fields['role'] = role
        return self.create_user(npm_nip, name, email, unit_gedung, password, **extra_fields)

    def create_superuser(self, npm_nip, name, email, unit_gedung, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)
        extra_fields['role'] = RoleChoices.ADMIN_GOGREEN
        return self.create_user(npm_nip, name, email, unit_gedung, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    npm_nip = models.CharField('NPM/NIP', max_length=20, unique=True)
    name = models.CharField('Nama', max_length=100)
    email = models.EmailField('Email', max_length=100, unique=True)
    role = models.CharField(
        'Peran', max_length=20, choices=RoleChoices.choices,
        default=RoleChoices.CIVITAS,
    )
    unit_gedung = models.CharField('Unit/Gedung', max_length=50)
    total_poin = models.IntegerField('Total Poin', default=0)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    objects = UserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['npm_nip', 'name', 'unit_gedung']

    class Meta:
        db_table = 'users'
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.name} ({self.npm_nip})'

    def add_points(self, amount: int):
        """Atomic increment of points using F() to avoid lost updates (TC-052)."""
        from django.db.models import F
        User.objects.filter(pk=self.pk).update(total_poin=F('total_poin') + amount)
        self.refresh_from_db(fields=['total_poin'])

    def deduct_points(self, amount: int):
        from django.db.models import F
        User.objects.filter(pk=self.pk).update(total_poin=F('total_poin') - amount)
        self.refresh_from_db(fields=['total_poin'])

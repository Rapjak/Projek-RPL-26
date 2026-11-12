"""
Shared helpers for TC-001..TC-053 test suite.

Provides:
- image generators (JPEG/PNG of specific sizes, invalid files, spoofed files)
- authenticated API client factory
- ML service mock/simulation utilities
"""
import io
import os
import tempfile
from unittest import mock

from PIL import Image
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework.test import APIClient

User = get_user_model()


# ---------------------------------------------------------------------------
# Image / file generators
# ---------------------------------------------------------------------------
def make_image_bytes(fmt: str = 'JPEG', size: tuple = (100, 100), color=(30, 200, 60)) -> bytes:
    """Create an in-memory valid image."""
    img = Image.new('RGB', size, color)
    buf = io.BytesIO()
    img.save(buf, format=fmt)
    return buf.getvalue()


def make_image_file(fmt: str = 'JPEG', name: str = None, size: tuple = (100, 100), color=(30, 200, 60)) -> SimpleUploadedFile:
    """Create a Django SimpleUploadedFile with a real image inside."""
    ext = 'jpg' if fmt.upper() == 'JPEG' else fmt.lower()
    content_type = 'image/jpeg' if fmt.upper() == 'JPEG' else 'image/png'
    if name is None:
        name = f'foto.{ext}'
    return SimpleUploadedFile(name, make_image_bytes(fmt, size, color), content_type=content_type)


def make_padded_image_file(target_bytes: int, fmt: str = 'JPEG', name: str = None) -> SimpleUploadedFile:
    """
    Build an image file whose total size is >= target_bytes.
    Uses a large canvas + JPEG quality to reach roughly the target size.
    (Used for 5MB boundary testing TC-023 / TC-024.)
    """
    ext = 'jpg' if fmt.upper() == 'JPEG' else fmt.lower()
    content_type = 'image/jpeg' if fmt.upper() == 'JPEG' else 'image/png'
    if name is None:
        name = f'foto.{ext}'

    # Binary-search the canvas size / quality to hit approximate target
    # Use incompressible random noise so size grows predictably.
    import random
    random.seed(42)

    if fmt.upper() == 'PNG':
        # PNG with random noise is incompressible: ~3 bytes/pixel
        side = int((target_bytes / 3) ** 0.5) + 1
        side = min(side, 4000)
        img = Image.frombytes('RGB', (side, side), bytes(random.getrandbits(8) for _ in range(side * side * 3)))
        buf = io.BytesIO()
        img.save(buf, format='PNG')
    else:
        # JPEG noise, quality 100
        side = int((target_bytes / 2.5) ** 0.5) + 1
        side = min(side, 4000)
        img = Image.frombytes('RGB', (side, side), bytes(random.getrandbits(8) for _ in range(side * side * 3)))
        buf = io.BytesIO()
        img.save(buf, format='JPEG', quality=100)

    data = buf.getvalue()
    return SimpleUploadedFile(name, data, content_type=content_type)


def make_invalid_pdf_file(name: str = 'dokumen.pdf', size: int = 1000) -> SimpleUploadedFile:
    data = b'%PDF-1.4\n' + b'x' * max(0, size - 9)
    return SimpleUploadedFile(name, data, content_type='application/pdf')


def make_spoofed_jpg_file(name: str = 'foto.jpg') -> SimpleUploadedFile:
    """Text/executable content masquerading as .jpg (TC-029)."""
    data = b'#!/bin/sh\necho "this is not an image"\n' + b'A' * 500
    return SimpleUploadedFile(name, data, content_type='image/jpeg')


def make_empty_jpg_file(name: str = 'sampah_kosong.jpg') -> SimpleUploadedFile:
    """0-byte file (TC-026)."""
    return SimpleUploadedFile(name, b'', content_type='image/jpeg')


# ---------------------------------------------------------------------------
# User / client factories
# ---------------------------------------------------------------------------
def create_civitas_user(npm_nip='140810240015', email='ahmad@mail.unpad.ac.id', password='Password123!',
                        name='Ahmad Dahlan', unit_gedung='FMIPA'):
    return User.objects.create_user(
        npm_nip=npm_nip, name=name, email=email, unit_gedung=unit_gedung, password=password,
    )


def create_admin_user(npm_nip='ADM-001', email='admin.gogreen@unpad.ac.id', password='AdminPass123!',
                      name='Admin GoGreen', unit_gedung='FMIPA'):
    user = User.objects.create_user(
        npm_nip=npm_nip, name=name, email=email, unit_gedung=unit_gedung, password=password,
        role='admin_gogreen', is_staff=True,
    )
    return user


def auth_client(user) -> APIClient:
    """Return an APIClient already authenticated via JWT for the given user."""
    from rest_framework_simplejwt.tokens import RefreshToken
    client = APIClient()
    refresh = RefreshToken.for_user(user)
    client.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}')
    return client


def get_jwt_for(user):
    from rest_framework_simplejwt.tokens import RefreshToken
    return RefreshToken.for_user(user)


# ---------------------------------------------------------------------------
# ML service simulation
# ---------------------------------------------------------------------------
def mock_ml_classify(kategori: str, confidence: float):
    """
    Context manager that patches the MLServiceClient used by classification service
    to return controlled results. Use this to deterministically test TC-031..TC-036,
    TC-049, TC-052, TC-053.
    """
    return mock.patch(
        'apps.utils.ml_client.MLServiceClient.classify_image',
        return_value={
            'kategori_sampah': kategori,
            'confidence_score': confidence,
            'is_recyclable': kategori == 'anorganik',
            'handling_instructions': 'Mocked',
        },
    )


def mock_ml_health(ok=True):
    return mock.patch('apps.utils.ml_client.MLServiceClient.health_check', return_value=ok)


def mock_ml_down():
    """Simulate ML service unavailable (TC-019, TC-035)."""
    return mock.patch(
        'apps.utils.ml_client.MLServiceClient.health_check',
        return_value=False,
    )

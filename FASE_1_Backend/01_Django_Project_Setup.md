# FASE 1 - Task 1: Django Project Setup

## Metadata
- **Task**: Django Project Setup & Configuration
- **Date**: 2026-10-24
- **Status**: ✅ Completed
- **Developer**: AI Assistant

---

## 1. Tujuan Task
Setup struktur Django project dengan konfigurasi lengkap untuk aplikasi Pilah.in, meliputi:
- Instalasi dependencies Python
- Struktur project Django dengan multiple apps
- Konfigurasi database PostgreSQL
- Konfigurasi Redis cache
- Konfigurasi REST Framework & JWT authentication
- Custom User model

---

## 2. Dependency Installation

### 2.1 Requirements
File: `requirements.txt`

```txt
Django==4.2.8
djangorestframework==3.14.0
django-cors-headers==4.3.1
psycopg[binary]==3.2.13
redis==5.0.1
django-redis==5.4.0
python-dotenv==1.0.0
Pillow==10.4.0
python-dateutil==2.8.2
pytz==2023.3.post1
requests==2.31.0
drf-yasg==1.21.7
django-filter==23.5
djangorestframework-simplejwt==5.5.1
cryptography==41.0.7
```

### 2.2 Perubahan Versi untuk Python 3.13
**Masalah**: Versi awal tidak compatible dengan Python 3.13

**Solusi**:
1. `psycopg2-binary` → `psycopg[binary]==3.2.13` (psycopg-binary 3.1.18 tidak tersedia)
2. `Pillow==10.1.0` → `Pillow==10.4.0` (KeyError __version__ pada 10.1.0)
3. `djangorestframework-simplejwt==5.3.2` → `5.5.1` (versi 5.3.2 tidak exist di PyPI)

### 2.3 Command Installation
```bash
pip install -r requirements.txt --timeout=120
```

**Output**: Semua dependencies berhasil terinstall dengan warning minor (conflicts dengan pdfplumber/datasets tidak relevan untuk project ini).

---

## 3. Struktur Project Django

### 3.1 Inisialisasi Project
```bash
python -m django startproject config .
```

Struktur yang dihasilkan:
```
Projek-RPL-26/
├── config/
│   ├── __init__.py
│   ├── asgi.py
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
├── manage.py
└── requirements.txt
```

### 3.2 Pembuatan Apps
```bash
mkdir apps
mkdir apps/users apps/uploads apps/classifications apps/rewards apps/education
python manage.py startapp users apps/users
python manage.py startapp uploads apps/uploads
python manage.py startapp classifications apps/classifications
python manage.py startapp rewards apps/rewards
python manage.py startapp education apps/education
```

### 3.3 Fix App Configuration
**Masalah**: `ImproperlyConfigured: Cannot import 'users'. Check that 'apps.users.apps.UsersConfig.name' is correct.`

**Solusi**: Update `apps.py` di setiap app untuk menggunakan full path:

```python
# apps/users/apps.py
class UsersConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.users'  # Bukan 'users'
```

Berlaku untuk semua apps: users, uploads, classifications, rewards, education.

### 3.4 Struktur Direktori Final
```
Projek-RPL-26/
├── apps/
│   ├── users/
│   ├── uploads/
│   ├── classifications/
│   ├── rewards/
│   └── education/
├── config/
│   ├── __init__.py
│   ├── settings.py
│   ├── urls.py
│   ├── wsgi.py
│   └── asgi.py
├── media/
├── static/
├── manage.py
├── requirements.txt
└── .env
```

---

## 4. Konfigurasi Settings

### 4.1 Environment Variables
File: `config/settings.py` (top section)

```python
from pathlib import Path
import os
from dotenv import load_dotenv
from datetime import timedelta

# Load environment variables
load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent
```

### 4.2 Database Configuration (PostgreSQL)
```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.getenv('DATABASE_NAME', 'pilah_in'),
        'USER': os.getenv('DATABASE_USER', 'postgres'),
        'PASSWORD': os.getenv('DATABASE_PASSWORD', 'pilah_postgres_dev'),
        'HOST': os.getenv('DATABASE_HOST', 'localhost'),
        'PORT': os.getenv('DATABASE_PORT', '5432'),
    }
}
```

**Catatan**: Password default `pilah_postgres_dev` sesuai docker-compose.yml

### 4.3 Installed Apps
```python
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    
    # Third-party
    'rest_framework',
    'corsheaders',
    'drf_yasg',
    'django_filters',
    
    # Local apps
    'apps.users',
    'apps.classifications',
    'apps.uploads',
    'apps.rewards',
    'apps.education',
]
```

### 4.4 Middleware (CORS)
```python
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'corsheaders.middleware.CorsMiddleware',  # Added for React frontend
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]
```

### 4.5 Redis Cache Configuration
```python
CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': f"redis://{os.getenv('REDIS_HOST', 'localhost')}:{os.getenv('REDIS_PORT', '6379')}/1",
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
        }
    }
}
```

### 4.6 Static & Media Files
```python
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_DIRS = [BASE_DIR / 'static']

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'
```

**Note**: Menggunakan local file storage (bukan MinIO) karena Docker Hub access denied.

### 4.7 CORS Configuration
```python
CORS_ALLOWED_ORIGINS = [
    'http://localhost:3000',
    'http://127.0.0.1:3000',
]
CORS_ALLOW_CREDENTIALS = True
```

### 4.8 REST Framework Configuration
```python
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 10,
    'DEFAULT_FILTER_BACKENDS': [
        'django_filters.rest_framework.DjangoFilterBackend',
        'rest_framework.filters.SearchFilter',
        'rest_framework.filters.OrderingFilter',
    ],
}
```

### 4.9 JWT Configuration
```python
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(hours=1),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': True,
    'ALGORITHM': 'HS256',
    'SIGNING_KEY': SECRET_KEY,
    'AUTH_HEADER_TYPES': ('Bearer',),
}
```

### 4.10 Custom User Model
```python
AUTH_USER_MODEL = 'users.User'
```

---

## 5. Custom User Model

### 5.1 Implementasi User Model
File: `apps/users/models.py`

```python
from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.utils import timezone


class UserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('Email must be set')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)
        return self.create_user(email, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    email = models.EmailField(unique=True)
    name = models.CharField(max_length=100)
    phone_number = models.CharField(max_length=15, blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    date_joined = models.DateTimeField(default=timezone.now)
    last_login = models.DateTimeField(blank=True, null=True)
    points = models.IntegerField(default=0)

    objects = UserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['name']

    def __str__(self):
        return self.email
```

### 5.2 Fitur Custom User
- Email sebagai username (bukan username tradisional)
- Field `points` untuk reward system
- Custom UserManager untuk create_user dan create_superuser
- Extends AbstractBaseUser & PermissionsMixin untuk permissions

---

## 6. Database Migrations

### 6.1 Create Initial Migrations
```bash
python manage.py makemigrations
```

**Output**:
```
Migrations for 'users':
  apps\users\migrations\0001_initial.py
    - Create model User
```

### 6.2 Apply Migrations
```bash
python manage.py migrate
```

**Output**:
```
Operations to perform:
  Apply all migrations: admin, auth, contenttypes, sessions, users
Running migrations:
  Applying contenttypes.0001_initial... OK
  Applying contenttypes.0002_remove_content_type_name... OK
  Applying auth.0001_initial... OK
  [... truncated ...]
  Applying users.0001_initial... OK
  Applying admin.0001_initial... OK
  [... truncated ...]
  Applying sessions.0001_initial... OK
```

---

## 7. Testing & Verification

### 7.1 Run Development Server
```bash
python manage.py runserver
```

**Output**:
```
Watching for file changes with StatReloader
Performing system checks...

System check identified no issues (0 silenced).
October 24, 2026 - 09:33:41
Django version 4.2.8, using settings 'config.settings'
Starting development server at http://127.0.0.1:8000/
Quit the server with CTRL-BREAK.
```

**Status**: ✅ Server berjalan tanpa error

### 7.2 Database Connection Test
- PostgreSQL: ✅ Connected (migrations berhasil)
- Redis: ✅ Configured (akan ditest di Task berikutnya)

---

## 8. Troubleshooting Log

### 8.1 Issue: PowerShell && Operator
**Error**: `The token '&&' is not a valid statement separator in this version.`

**Cause**: PowerShell tidak support `&&` operator seperti bash.

**Solution**: Run commands separately atau gunakan `;` untuk PowerShell.

### 8.2 Issue: pip Pillow KeyError
**Error**: `KeyError: __version__` saat install Pillow 10.1.0

**Cause**: Pillow 10.1.0 tidak compatible dengan Python 3.13.

**Solution**: Upgrade ke Pillow 10.4.0.

### 8.3 Issue: psycopg-binary Not Found
**Error**: `Could not find a version that satisfies the requirement psycopg-binary==3.1.18`

**Cause**: psycopg-binary 3.1.18 tidak tersedia untuk Python 3.13. Available versions start at 3.2.2.

**Solution**: Upgrade ke psycopg[binary]==3.2.13.

### 8.4 Issue: djangorestframework-simplejwt Version
**Error**: `No matching distribution found for djangorestframework-simplejwt==5.3.2`

**Cause**: Version 5.3.2 tidak exist di PyPI (available: 5.3.0, 5.3.1, 5.4.0, 5.5.0, 5.5.1).

**Solution**: Upgrade ke 5.5.1 (latest stable).

### 8.5 Issue: Database Authentication Failed
**Error**: `password authentication failed for user "postgres"`

**Cause**: `.env` file menggunakan password placeholder `your-postgres-password-change-in-production`, sementara docker-compose menggunakan `pilah_postgres_dev`.

**Solution**: 
1. Update `.env`: `DATABASE_PASSWORD=pilah_postgres_dev`
2. Update `settings.py` untuk gunakan env var `DATABASE_*` (bukan `DB_*`)

---

## 9. Checklist Completion

- [x] Install dependencies (requirements.txt)
- [x] Create Django project structure (config/)
- [x] Create 5 apps (users, uploads, classifications, rewards, education)
- [x] Configure settings.py (database, redis, cors, rest framework)
- [x] Implement custom User model
- [x] Create and apply migrations
- [x] Test development server
- [x] Create documentation

---

## 10. Next Steps

**FASE 1 Task 2**: Implement Django models untuk semua apps:
- ✅ User model (sudah dibuat)
- Upload model
- ClassificationResult model
- Reward model
- RewardRedemption model
- PointTransaction model
- EducationMaterial model

---

## 11. Files Modified/Created

### Created
- `apps/users/models.py` - Custom User model
- `apps/users/migrations/0001_initial.py` - User migration
- `media/` - Directory for uploaded files
- `static/` - Directory for static files
- `FASE_1_Backend/01_Django_Project_Setup.md` - This documentation

### Modified
- `requirements.txt` - Updated package versions for Python 3.13
- `config/settings.py` - Complete Django configuration
- `apps/*/apps.py` - Fixed app names (5 files)
- `.env` - Updated DATABASE_PASSWORD

---

## 12. Conclusion

Django project berhasil di-setup dengan arsitektur Client-Server layered sesuai spesifikasi RPL. Backend siap untuk implementasi models (Task 2) dan API endpoints (Task 3).

**Key Achievements**:
- Django 4.2.8 + DRF 3.14.0 configured
- PostgreSQL connected and migrated
- Custom User model with email authentication
- JWT authentication configured
- CORS enabled for React frontend
- Local file storage configured (MinIO replacement)

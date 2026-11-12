# Pilah.in — Garbage Classification App

Aplikasi klasifikasi sampah untuk civitas akademik Pahlawan Cimahi / UNPAD.
Dibangun dengan arsitektur **Client-Server Layered** (RPL): Django backend, FastAPI ML service, React frontend.

> Implementasi FASE 3 — sesuai Dokumen Teknis (FR-001..FR-006 Must, API-001..API-019, TC-001..TC-053, SCR-01..SCR-13).

## Tech Stack

| Lapisan | Teknologi |
|---------|-----------|
| Frontend | React 19, TypeScript, Vite 8, Tailwind v3, Headless UI, Heroicons |
| Backend | Django 4.2 + Django REST Framework 3.15, SimpleJWT (token blacklist), drf-yasg |
| ML Service | FastAPI 0.115, Pillow (heuristik warna, placeholder CNN) |
| Database | PostgreSQL 16 |
| Cache | Redis 7 (rate-limit & access-token blacklist) |
| Storage | Local filesystem (`MEDIA_ROOT`) |

## Struktur Repo

```
Projek-RPL-26/
├── apps/                      # Django apps (backend)
│   ├── admin_panel/           # API-016..API-019 (admin monitoring)
│   ├── classifications/       # API-005..API-009 (upload, poll, history)
│   ├── education/             # API-014..API-015
│   ├── rewards/               # API-010..API-013 (reward + redeem + leaderboard)
│   ├── uploads/               # Upload model & helpers
│   ├── users/                 # API-001..API-004 (auth, profile, points)
│   └── utils/                 # auth, cache, ml_client, throttling, pagination
├── config/                    # Django settings, URLs
├── ml_service/                # FastAPI ML service (Docker)
├── FASE_0_Infrastructure/     # PostgreSQL schema, docker-compose, redis.conf
├── FASE_1_Backend/            # Dokumentasi backend
├── FASE_2_ML_Service/         # Dokumentasi ML service
├── FASE_3_Frontend/           # Dokumentasi + frontend source
│   └── pilah-frontend/        # React app (Vite)
├── tests/                     # Django test suite (TC-001..TC-053) + e2e smoke
├── IMPLEMENTASI_FASE_3.md     # Dokumentasi implementasi
├── CARA_LIHAT_DATABASE.md     # Panduan query DB
├── manage.py
├── requirements.txt
└── Makefile
```

## Setup Cepat (Development)

### Prasyarat
- Python 3.13+, Node.js 24+, Docker Desktop
- PostgreSQL 16 & Redis 7 (lewat Docker)

### 1. Infrastruktur (PostgreSQL + Redis + ML Service)
```bash
cd FASE_0_Infrastructure
docker compose up -d          # postgres, redis, ml_service
```

### 2. Backend (Django)
```bash
python -m venv .venv && .venv\Scripts\activate
pip install -r requirements.txt

# Copy env template & sesuaikan
copy .env.example .env         # Windows
#   Lalu edit SECRET_KEY, DATABASE_PASSWORD, REDIS_PASSWORD

python manage.py migrate

# Buat admin GoGreen account (akun demo)
python manage.py shell -c "from apps.users.models import User; User.objects.create_admin(npm_nip='ADM-001', name='Admin GoGreen', email='admin.gogreen@unpad.ac.id', unit_gedung='Pimpinan', password='AdminPass123!')"

python manage.py runserver 0.0.0.0:8000
```

### 3. Frontend (React + Vite)
```bash
cd FASE_3_Frontend/pilah-frontend
npm install

# Copy env template
copy .env.example .env         # Windows
#   Default: VITE_API_URL=http://localhost:8000/api/v1

npm run dev                    # http://localhost:3000
```

## Akun Demo

| Peran | Login | Password |
|---|---|---|
| Admin GoGreen | `admin.gogreen@unpad.ac.id` | `AdminPass123!` |
| Civitas | `smoke099@mail.unpad.ac.id` *atau* `140810240099` | `StrongPass123!` |

## Port Bindings

| Service | Port |
|---|---|
| Frontend dev | 3000 |
| Backend API | 8000 |
| ML service | 8001 |
| PostgreSQL | 5432 |
| Redis | 6379 |

## Testing

```bash
# Django test suite (TC-001..TC-053) — 60 tests
python manage.py test tests.test_tc_001_012_auth tests.test_tc_013_030_upload \
  tests.test_tc_031_041_classification tests.test_tc_042_053_points \
  --settings=config.settings_test --noinput

# E2E smoke API (13 langkah)
python tests/e2e_smoke.py

# Frontend TypeScript
cd FASE_3_Frontend/pilah-frontend && npx tsc --noEmit

# E2E browser (Playwright, Chrome)
cd FASE_3_Frontend/pilah-frontend && npx playwright test --reporter=list
```

## Dokumentasi

- [`IMPLEMENTASI_FASE_3.md`](IMPLEMENTASI_FASE_3.md) — detail implementasi & bug fix
- [`CARA_LIHAT_DATABASE.md`](CARA_LIHAT_DATABASE.md) — panduan query database
- `FASE_0_Infrastructure/` — schema SQL & konfigurasi infra
- `FASE_1_Backend/`, `FASE_2_ML_Service/`, `FASE_3_Frontend/` — docs per fase

## Catatan

- Model ML adalah **placeholder** heuristik warna — siap diganti model `.h5` trained.
- Storage pakai local filesystem (bukan MinIO) untuk dev lokal.
- `.env` berisi secret — **jangan commit**. Gunakan `.env.example` sebagai template.

---

_Repositori ini adalah implementasi Tugas RPL — Pahlawan Cimahi / UNPAD._

# IMPLEMENTASI FASE 3 — Pilah.in

> Garbage classification app untuk civitas akademik Pahlawan Cimahi / UNPAD.
> Arsitektur **Client-Server Layered** dengan Django backend, FastAPI ML service, React frontend.

---

## 1. Ringkasan

FASE 3 adalah rebuild lengkap backend, ML service, dan frontend agar seluruhnya
selaras dengan **Dokumen Teknis Pahlawan-Cimahi** (FR-001..FR-006 Must, API-001..API-019,
TC-001..TC-053, SCR-01..SCR-13).

- **Lapisan Backend (Django + DRF)**: Auth, Upload+Klasifikasi, Reward, Edukasi, Admin Panel.
- **Lapisan ML Service (FastAPI)**: Heuristik CNN placeholder deterministik (siap diganti model `.h5`).
- **Lapisan Frontend (React + Vite)**: Halaman auth, dashboard, upload+polling, riwayat, reward,
  leaderboard, edukasi, profil, dan admin monitoring dashboard.

### Tech Stack

| Lapisan | Teknologi |
|---------|-----------|
| Frontend | React 19, TypeScript, Vite 8, Tailwind v3, Headless UI, Heroicons |
| Backend | Django 5.1, Django REST Framework 3.15, SimpleJWT 5.5 (token blacklist), django-filter, drf-yasg |
| ML Service | FastAPI 0.115, uvicorn, Pillow, Python urllib (healthcheck) |
| Database | PostgreSQL 16 (Docker container `pilah_postgres`) |
| Cache | Redis 7 (Docker container `pilah_redis`) — untuk rate-limit & access-token blacklist |
| Storage | Local filesystem (`MEDIA_ROOT`) — MinIO di-skip untuk dev lokal |
| Test | Django test suite (60 tests), E2E smoke script Python (urllib) |

### Port Bindings

| Service | Port | Catatan |
|---------|------|---------|
| Django backend | 8000 | `python manage.py runserver` |
| ML service | 8001 | Docker container `pilah_ml_service` |
| Frontend dev | 3000 | `npm run dev` (Vite) |
| PostgreSQL | 5432 | Docker container `pilah_postgres` |
| Redis | 6379 | Docker container `pilah_redis` |

---

## 2. Arsitektur

```
+----------------------+       +----------------------+       +----------------------+
|  Frontend (React)    |       |  Backend (Django)    |       |  ML Service (FastAPI)|
|  Port 3000 (Vite)    | ----> |  Port 8000 (DRF)     | ----> |  Port 8001           |
|                      |  JWT  |                      |  HTTP |  /predict, /health    |
|  AuthContext         |       |  /api/v1/...         |       |  Heuristik kategori  |
|  api.ts (axios)      |       |  JWT auth + blacklist|       |  + confidence        |
|  Services per-domain |       |  Atomic point award  |       |                      |
+----------------------+       +----------+-----------+       +----------------------+
                                          |
                              +-----------+-----------+
                              |                       |
                       +------+-------+       +-------+------+
                       | PostgreSQL   |       | Redis        |
                       | pilah_postgres|      | pilah_redis  |
                       | (data)       |       | (cache+rate) |
                       +--------------+       +--------------+
```

### Layered Architecture (Backend)

```
apps/
├── users/             # Layer: Auth - Register/Login/Logout/Profile/Points
│   ├── models.py      # Custom User (npm_nip, role, unit_gedung, total_poin)
│   ├── serializers.py
│   ├── views.py       # Brute-force rate limit (5/6), access jti blacklist
│   └── urls.py
├── uploads/           # Layer: Upload - file storage + status polling
│   ├── models.py      # Upload (status enum, file path, file_size)
│   ├── serializers.py # MIME magic-byte validation, 5MB limit
│   └── views.py
├── classifications/   # Layer: Classification - async ML call + point award
│   ├── models.py      # ClassificationResult (kategori_sampah enum, is_valid, points_awarded)
│   ├── services.py    # process_classification_sync, 70% threshold, F() atomic increment
│   └── views.py       # CheckPointsView (idempotent)
├── rewards/           # Layer: Reward + Redemption + Leaderboard + PointTransaction
│   ├── models.py
│   ├── views.py       # RedeemRewardView (select_for_update inside atomic)
│   └── urls.py
├── education/         # Layer: Education materials (read)
│   └── ...
├── admin_panel/       # Layer: Admin monitoring (API-016..API-019)
│   └── views.py       # IsAdminOrPimpinan permission
└── utils/
    ├── auth.py        # BlacklistAwareJWTAuthentication (access jti in Redis)
    ├── ml_client.py   # MLServiceClient - HTTP call to FastAPI
    ├── pagination.py  # StandardResultsSetPagination
    ├── throttling.py  # Burst/Sustained rate throttles
    └── exception_handler.py
```

---

## 3. Database Schema

> Sesuai data dictionary dokumen teknis.

### users
| Field | Type | Catatan |
|-------|------|---------|
| id | UUID PK | |
| npm_nip | VARCHAR(30) UNIQUE | identifier login |
| name | VARCHAR(255) | |
| email | VARCHAR(255) UNIQUE | identifier login |
| role | ENUM('civitas','admin_gogreen','pimpinan') | default 'civitas' |
| unit_gedung | VARCHAR(255) | fakultas/program studi |
| total_poin | INTEGER | default 0; di-increment via F() |
| password | VARCHAR(255) | hashed (PBKDF2/Argon2) |
| is_active | BOOLEAN | |
| created_at | TIMESTAMPTZ | |

### uploads
| Field | Type | Catatan |
|-------|------|---------|
| id | UUID PK | |
| user_id | UUID FK → users.id | |
| file | VARCHAR(255) | path only, bukan BLOB |
| file_size | BIGINT | bytes |
| status | ENUM('pending','processing','completed','failed') | |
| created_at | TIMESTAMPTZ | |

### classification_results (1:1 dengan uploads)
| Field | Type | Catatan |
|-------|------|---------|
| id | UUID PK | |
| upload_id | UUID FK→uploads.id UNIQUE | |
| kategori_sampah | ENUM('organik','anorganik','residu','tidak_dikenal') | |
| confidence_score | DECIMAL(5,4) | 0.0000 - 1.0000 |
| is_valid | BOOLEAN | confidence ≥ 0.70 |
| points_awarded | INTEGER | 10 jika valid, 0 jika tidak |
| handling_instructions | TEXT | |
| waktu_proses | TIMESTAMPTZ | |

### rewards
| Field | Type | Catatan |
|-------|------|---------|
| id | UUID PK | |
| name | VARCHAR(255) | |
| description | TEXT | |
| points_required | INTEGER | |
| stock | INTEGER | |
| masa_berlaku | DATE | |
| is_active | BOOLEAN | |
| created_at | TIMESTAMPTZ | |

### reward_redemptions
| Field | Type | Catatan |
|-------|------|---------|
| id | UUID PK | |
| user_id | UUID FK | |
| reward_id | UUID FK | |
| kode_voucher | VARCHAR(20) UNIQUE | format `RWD-XXXXXX-YYYY` |
| status | ENUM('aktif','terpakai','kedaluwarsa') | default 'aktif' |
| tanggal_penukaran | TIMESTAMPTZ auto | |
| tanggal_digunakan | TIMESTAMPTZ NULL | |

### point_transactions
| Field | Type | Catatan |
|-------|------|---------|
| id | UUID PK | |
| user_id | UUID FK | |
| points | INTEGER | |
| transaction_type | ENUM('penambahan','pengurangan') | |
| description | VARCHAR(255) | |
| reference_id | UUID NULL | FK to upload/redemption |
| created_at | TIMESTAMPTZ auto | |

### education_materials
| Field | Type | Catatan |
|-------|------|---------|
| id | UUID PK | |
| judul | VARCHAR(255) | |
| kategori_sampah | ENUM('organik','anorganik','residu','umum') | 'umum' untuk materi umum |
| konten | TEXT | |
| is_published | BOOLEAN | |
| created_at | TIMESTAMPTZ auto | |
| updated_at | TIMESTAMPTZ auto | |

### outstanding_token / blacklisted_token (SimpleJWT)
Tabel bawaan `rest_framework_simplejwt.token_blacklist` untuk blacklist refresh token.

---

## 4. API Specification (API-001..API-019)

Base URL: `/api/v1/`

### Auth (apps.users)

| ID | Method | Path | Deskripsi |
|----|--------|------|-----------|
| API-001 | POST | `/auth/register` | Registrasi civitas; role di-hardcode server-side (TC-006) |
| API-002 | POST | `/auth/login` | Login via `identifier` (npm_nip OR email); brute-force 5/6 |
| API-003 | POST | `/auth/logout` | Blacklist refresh + access jti (Redis) |
| API-004 | GET | `/auth/profile` | Profile user + `total_poin` |

### Classification (apps.uploads + apps.classifications)

| ID | Method | Path | Deskripsi |
|----|--------|------|-----------|
| API-005 | POST | `/classifications/upload/` | 202 Accepted + upload_id; MIME magic-byte + 5MB check |
| API-006 | GET | `/classifications/<id>/` | Poll status (pending/processing/completed/failed) |
| API-007 | GET | `/classifications/` | History list (paginated, filter `kategori`) |
| API-008 | GET | `/classifications/<id>/points/` | Check poin (idempotent — TC-049) |

### Reward (apps.rewards)

| ID | Method | Path | Deskripsi |
|----|--------|------|-----------|
| API-009 | GET | `/points/me` | user_id, total_poin, rank |
| API-010 | POST | `/rewards/<id>/redeem` | Atomic deduct + voucher generation |
| API-011 | GET | `/rewards` | List rewards (paginated) |
| API-012 | GET | `/rewards/redemptions` | User's redemptions history |
| API-013 | GET | `/points/transactions` | Point transaction log |
| API-014 | GET | `/leaderboard?type=user\|building` | Peringkat pengguna / unit |

### Education (apps.education)

| ID | Method | Path | Deskripsi |
|----|--------|------|-----------|
| API-015 | GET | `/education/` | List materi (paginated, filter kategori_sampah) |
| API-015 | GET | `/education/<id>/` | Detail materi |

### Admin Panel (apps.admin_panel) — role: admin_gogreen / pimpinan

| ID | Method | Path | Deskripsi |
|----|--------|------|-----------|
| API-016 | GET | `/admin/dashboard/` | Stats: pengguna, upload, poin, distribusi kategori, akurasi, tren mingguan |
| API-017 | GET | `/admin/activities/` | Tabel aktivitas pengguna (filter unit_gedung, tanggal, kategori) |
| API-018 | POST/PUT/DELETE | `/admin/rewards/` `/admin/rewards/<id>/` | CRUD reward |
| API-019 | POST/PUT/DELETE | `/admin/education/` `/admin/education/<id>/` | CRUD edukasi |

### Keamanan

- **JWT Auth**: access token (1 jam) + refresh token (7 hari), rotasi refresh + blacklist
- **Access Token Blacklist** (TC-012): `BlacklistAwareJWTAuthentication` cek access jti di Redis
  - Logout menulis `jwt_blacklist:<jti>` ke Redis dengan TTL = sisa lifetime access token
  - Setiap request berikutnya dengan access token yang sama → 401
- **Brute-force rate limit** (TC-011): 5 failed → 401 (uniform error), 6th → 429 `ERR_TOO_MANY_ATTEMPTS`
- **Role-based routing**: civitas tidak bisa akses `/admin/*` → 403
- **MIME magic-byte validation** (TC-029): cek 12 byte pertama (JPEG `FFD8FF`, PNG `89504E470D0A1A0A`)
- **5 MB file limit** (TC-023/024): `DATA_UPLOAD_MAX_MEMORY_SIZE=6MB` + serializer check
- **Idempotent point award** (TC-049): `process_classification_sync` cek `is_valid` flag sebelum award

---

## 5. ML Service (FastAPI)

File: `ml_service/main.py`, `ml_service/Dockerfile`, `ml_service/requirements.txt`
Container: `pilah_ml_service` (port 8001, healthy)

### Endpoints
- `GET /health` → `{"status":"healthy"}`
- `POST /predict` → menerima file gambar, mengembalikan:

```json
{
  "kategori_sampah": "organik",
  "confidence_score": 0.94,
  "is_recyclable": false,
  "handling_instructions": "..."
}
```

### Heuristik Deterministik (Placeholder CNN)
- Menganalisis warna dominan pixel menggunakan Pillow
- **Hijau dominan** → organik (daun, sisa makanan)
- **Putih/transparan** → anorganik (plastik, kertas)
- **Coklat/abu-abu** → residu
- **Tidak terklasifikasi** → tidak_dikenal
- Threshold 0.70 diterapkan di backend (`apps.classifications.services`)
- Confidence < 0.70 → `kategori_sampah` di-downgrade ke `tidak_dikenal`, `is_valid=False`

### Test Headers (untuk TC-031..TC-036)
```
X-Test-Category: organik
X-Test-Confidence: 0.85
```
Memaksa service mengembalikan nilai spesifik — dipakai oleh Django test suite.

---

## 6. Frontend (React + Vite)

Folder: `FASE_3_Frontend/pilah-frontend/`

### Struktur
```
src/
├── App.tsx                 # Router + role-based ProtectedRoute
├── main.tsx                # Entry + AuthProvider + NotificationProvider
├── context/
│   ├── AuthContext.tsx     # user, login, register, logout, refreshUser, isAdmin
│   └── NotificationContext.tsx
├── components/
│   ├── common/             # Button, Card, Input, Select, Modal, Badge, Spinner, Alert
│   └── layout/             # Header, Sidebar, Footer, ProtectedRoute
├── pages/
│   ├── Login.tsx           # SCR-02: identifier login + role-based redirect
│   ├── Register.tsx        # SCR-01: form civitas (npm_nip, name, email, unit_gedung, password)
│   ├── Dashboard.tsx       # SCR-03: greeting, total poin, CTA upload, recent activities
│   ├── Upload.tsx          # SCR-04/05/06/07: upload→processing→result (kategori badge, poin panel)
│   ├── History.tsx         # SCR-08: filter kategori, summary cards, paginated list
│   ├── Rewards.tsx         # SCR-09: list reward, redeem modal, voucher display
│   ├── Leaderboard.tsx     # SCR-10: tabs pengguna / unit-gedung
│   ├── Education.tsx       # SCR-11 list, SCR-12 detail
│   ├── Profile.tsx         # edit name/unit_gedung, view npm_nip/peran, logout
│   └── AdminDashboard.tsx  # SCR-13: tabs Ringkasan/Aktivitas/Reward/Edukasi CRUD
├── services/
│   ├── api.ts              # axios instance, JWT interceptor, token refresh on 401
│   ├── auth.ts             # login/register/logout/profile/points
│   ├── classifications.ts  # uploadAndClassify, pollStatus, checkPoints, listHistory
│   ├── rewards.ts          # list, redeem, redemptions, transactions, leaderboard
│   ├── education.ts        # list, getById
│   └── admin.ts            # dashboard, activities, reward CRUD, education CRUD
└── types/
    └── index.ts            # semua type aligned dengan backend field names
```

### Role-Based Routing
- **civitas** → `/dashboard` (default setelah login)
- **admin_gogreen / pimpinan** → `/admin` (admin monitoring dashboard)
- `ProtectedRoute` menerima `roles?: Role[]` untuk restrict admin routes

### State Management
- `AuthContext`: `user`, `loading`, `isAuthenticated`, `isAdmin`, `login`, `register`, `logout`, `refreshUser`
- `NotificationContext`: toast notifications (success/error/info/warning)
- API interceptor: auto-refresh access token on 401, redirect ke `/login` jika refresh gagal

### Build
```bash
cd FASE_3_Frontend/pilah-frontend
npm install
npm run build   # tsc -b && vite build → dist/
npm run dev     # port 3000 (Vite)
```
Env: `VITE_API_URL` default `http://localhost:8000/api/v1`

---

## 7. Test Cases (TC-001..TC-053)

### Django Test Suite — 60 tests, ALL PASSING

```bash
cd Projek-RPL-26
python manage.py test tests.test_tc_001_012_auth tests.test_tc_013_030_upload \
  tests.test_tc_031_041_classification tests.test_tc_042_053_points \
  --settings=config.settings_test --noinput
# → Ran 60 tests in ~18s. OK.
```

| File | Coverage | Jumlah Tests |
|------|----------|--------------|
| `tests/test_tc_001_012_auth.py` | TC-001..TC-012 (Registrasi, Login, Logout, Brute-force) | 14 |
| `tests/test_tc_013_030_upload.py` | TC-013..TC-030 (Upload, MIME, Size, ML down, Storage) | 19 |
| `tests/test_tc_031_041_classification.py` | TC-031..TC-041 (Klasifikasi, Threshold BVA, Display) | 12 |
| `tests/test_tc_042_053_points.py` | TC-042..TC-053 (Poin, Idempotency, Race, Tampering) | 15 |
| `tests/helpers.py` | Shared utilities (image generators, ML mocks, user factories) | — |

### Test Settings (`config/settings_test.py`)
- `LocMemCache` (bukan DummyCache) agar rate-limit state persist dalam process
- `DEFAULT_THROTTLE_CLASSES = []` (disable throttle)
- `cache.clear()` di setUp untuk TC-009, TC-011, TC-012

### Key Test Logic
- **TC-006** (role injection): klien kirim `role=admin_gogreen` → backend ignore, role tetap `civitas`
- **TC-011** (brute-force): 5 failed → 401, 6th → 429 (logic `attempts > MAX_ATTEMPTS`)
- **TC-012** (logout blacklist): access jti di-Redis-blacklist, request berikutnya → 401
- **TC-023/024** (5MB boundary): file exactly 5MB accepted, 5MB+10 bytes rejected
- **TC-029** (MIME spoofing): text file dengan `.jpg` extension → magic byte check reject
- **TC-033/034** (threshold BVA): confidence 0.70 → valid (+10 poin), 0.69 → tidak_dikenal (0 poin)
- **TC-049** (idempotency): `process_classification_sync` dipanggil 2x → poin tetap 10
- **TC-053** (client tampering): klien kirim `jumlah_poin=9999` → backend ignore, award tetap 10

### E2E Smoke Test
```bash
python tests/e2e_smoke.py
```
13 langkah end-to-end: register → login (email+npm_nip) → profile → upload → poll →
check points → total points → leaderboard (user+building) → history → admin create reward →
admin dashboard → list rewards → redeem → point tx → logout. **Semua PASS.**

---

## 8. Cara Menjalankan

### Prasyarat
- Python 3.13+, Node.js v24+, npm 11+, Docker Desktop
- PostgreSQL & Redis via Docker: `cd FASE_0_Infrastructure && docker compose up -d`

### 1. Backend
```bash
cd Projek-RPL-26
python -m venv venv
venv\Scripts\activate          # Windows
pip install -r requirements.txt

# Setup .env (DB credentials, Redis, ML_SERVICE_URL)
python manage.py migrate
python manage.py seed_admin    # admin.gogreen@unpad.ac.id / AdminPass123!

python manage.py runserver     # port 8000
```

### 2. ML Service (Docker)
```bash
cd ml_service
docker build -t pilah-ml:v2.0 .
docker run -d --name pilah_ml_service -p 8001:8000 pilah-ml:v2.0
# Healthcheck: curl http://localhost:8001/health
```

### 3. Frontend
```bash
cd FASE_3_Frontend/pilah-frontend
npm install
npm run dev     # http://localhost:3000
```

### 4. Akun Demo
| Role | Identifier | Password |
|------|-----------|----------|
| Admin GoGreen | `admin.gogreen@unpad.ac.id` | `AdminPass123!` |
| Civitas (smoke) | `smoke099@mail.unpad.ac.id` / `140810240099` | `StrongPass123!` |

---

## 9. Functional Requirements Coverage

| FR | Deskripsi | Status | Implementasi |
|----|-----------|--------|--------------|
| FR-001 | Autentikasi & Manajemen Akun | ✅ Must | API-001..004, TC-001..012, SCR-01/02 |
| FR-002 | Unggah Foto Sampah | ✅ Must | API-005, TC-013..030, SCR-04 |
| FR-003 | Klasifikasi Otomatis | ✅ Must | API-005/006, TC-031..036, SCR-05 |
| FR-004 | Tampil Hasil Klasifikasi | ✅ Must | API-006, TC-037..041, SCR-06/07 |
| FR-005 | Cek Perolehan Poin | ✅ Must | API-008/009, TC-042..050, SCR-08 |
| FR-006 | Perolehan Poin & Reward | ✅ Must | API-010..014, TC-051..053, SCR-09/10 |
| FR-007 | Edukasi Sampah | ✅ Should | API-015, SCR-11/12 |
| FR-008 | Admin Monitoring | ✅ Should | API-016..019, SCR-13 |
| FR-009 | Leaderboard | ✅ Should | API-014, SCR-10 |
| FR-010 | Riwayat Aktivitas | ✅ Should | API-007, SCR-08 |
| FR-011 | Manajemen Reward (Admin) | ✅ Could | API-018 |

---

## 10. Catatan Implementasi

### Keputusan Desain
1. **MinIO di-skip** untuk dev lokal — pakai Django `MEDIA_ROOT` filesystem.
2. **CNN placeholder deterministik** — heuristik warna Pillow, siap diganti model `.h5` trained.
3. **Access token blacklist via Redis** — SimpleJWT hanya blacklist refresh token; kami tambahkan
   custom `BlacklistAwareJWTAuthentication` yang cek access jti di Redis untuk TC-012.
4. **`DATA_UPLOAD_MAX_MEMORY_SIZE=6MB`** — Django default 2.5MB akan block file 5MB sebelum serializer
   kami jalan; kami naikkan ke 6MB agar serializer's 5MB check bisa di-test (TC-023/024).
5. **`select_for_update` inside `transaction.atomic()`** — RedeemRewardView awalnya panggil
   `select_for_update()` di luar atomic block, menyebabkan `TransactionManagementError`. Fixed.
6. **LocMemCache (bukan DummyCache)** untuk test settings — DummyCache tidak persist state sama sekali,
   sehingga rate-limit test (TC-011) dan blacklist test (TC-012) tidak bisa diuji.

### Known Limitations
- Model ML adalah placeholder — akurasi terbatas pada heuristik warna
- Tidak ada Celery/async task queue — klasifikasi synchronous di thread request
- File storage lokal (tidak scalable untuk production)
- Tidak ada HTTPS/TLS — dev only

---

## Verifikasi Menyeluruh (End-to-End Browser Testing)

Selain Django test suite (60 tests) dan E2E smoke script API, seluruh alur pengguna
diverifikasi dengan **Playwright** menggunakan browser Chrome sungguhan (bukan cek HTTP
status) — setiap halaman di-render, console error & pageerror ditangkap, dan alur nyata
dijalankan.

**Hasil akhir: 22/22 test E2E lulus dalam ~38 detik.**

Perintah:
```bash
cd FASE_3_Frontend/pilah-frontend
npx playwright test --reporter=list
```

Cakupan test browser (`e2e/pilah.spec.ts` + `e2e/register_login.spec.ts`):
- Login civitas (email & NPM/NIP) → redirect ke `/dashboard`
- Dashboard, Riwayat, Reward, Edukasi (+detail), Peringkat (tab user & unit), Profil, Logout
- Redirect rute terproteksi saat belum login
- **Upload + klasifikasi (FR-003)**: pilih file → kirim → polling → hasil + poin
- **Tukar reward (FR-005)**: klik Tukar → konfirmasi → kode voucher `RWD-...`
- Admin: login → `/admin`, tab Ringkasan/Aktivitas/Reward/Edukasi (CRUD)
- Civitas diblokir dari `/admin`
- Register + validasi, serta **register akun baru → login → dashboard → profil**

### Bug Kritis yang Ditemukan & Diperbaiki Saat Verifikasi

Verifikasi browser menemukan **3 bug nyata** yang tidak terdeteksi oleh TypeScript
maupun test API (karena hanya muncul saat runtime di browser):

1. **`.env` API URL salah (akar masalah "login tidak redirect")**
   `VITE_API_URL=http://localhost:8000/api` kehilangan segmen `/v1`, sehingga setiap
   request menuju `/api/auth/login` → **404**. Akibatnya login gagal tanpa error jelas,
   user tetap di halaman login.
   → Diperbaiki menjadi `VITE_API_URL=http://localhost:8000/api/v1`.
   `mediaBaseURL` di `api.ts` juga dibuat robust (strip `/api` maupun `/api/v1`).

2. **Polling upload macet selamanya (React 19 StrictMode)**
   `mountedRef` di `Upload.tsx` hanya di-set `false` di cleanup `useEffect`. StrictMode
   dev me-mount → unmount → mount ulang; cleanup men-set `false` **permanen** dan tidak
   pernah di-reset, sehingga `pollLoop()` langsung `return` dan halaman tertahan di
   "Memproses Foto" tanpa pernah polling.
   → Diperbaiki dengan `mountedRef.current = true` di awal effect. Kini upload → polling
   → hasil + poin berjalan mulus.

3. **Tab Admin Dashboard kalah oleh item sidebar (ambigu selector)**
   Tab `Reward`/`Edukasi` di panel admin bertabrakan dengan menu sidebar `Reward`/`Edukasi`
   bernama sama, membuat navigasi tidak deterministik (dan menyulitkan aksesibilitas).
   → Ditambahkan `role="tablist"` + `role="tab"` + `aria-label` unik pada tiap tab admin.

Dua kegagalan test lainnya bukan bug aplikasi melainkan **asumsi test yang keliru** dan
sudah dikoreksi: (a) nilai `<input>` tidak muncul di `innerText` — diverifikasi via
`toHaveValue()`; (b) validasi "kata sandi tidak cocok" tampil sebagai error inline dan
tombol Daftar ter-disable (UX yang benar), bukan notifikasi toast.

---

_Dokumen ini mencerminkan implementasi FASE 3 Pilah.in, sesuai Dokumen Teknis Pahlawan-Cimahi._

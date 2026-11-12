# Cara Melihat Database & Menjalankan Pilah.in

> Panduan untuk cek sendiri database dan menjalankan semua service.

---

## 1. Semua Service Saat Ini Sedang Berjalan

| Service | URL | Status |
|---------|-----|--------|
| **Frontend (React)** | http://localhost:3000 | ✅ running |
| **Backend (Django)** | http://localhost:8000 | ✅ running |
| **ML Service (FastAPI)** | http://localhost:8001 | ✅ running |
| **PostgreSQL** | localhost:5432 | ✅ running (Docker) |
| **Redis** | localhost:6379 | ✅ running (Docker) |

### Akun Login (untuk testing di browser)

| Role | Email / NPM | Password |
|------|------------|----------|
| Admin GoGreen | `admin.gogreen@unpad.ac.id` | `AdminPass123!` |
| Civitas | `smoke099@mail.unpad.ac.id` atau `140810240099` | `StrongPass123!` |

Buka **http://localhost:3000** → login pakai akun di atas.

---

## 2. Cara Melihat Database

### Kredensial Database

| Field | Nilai |
|-------|-------|
| Host | `localhost` |
| Port | `5432` |
| Database | `pilah_in` |
| User | `postgres` |
| Password | `pilah_postgres_dev` |

### Opsi A — CLI via Docker (paling cepat)

**Lihat semua tabel:**
```powershell
docker exec pilah_postgres psql -U postgres -d pilah_in -c "\dt"
```

**Lihat ringkasan semua tabel sekaligus** (pake file `db_view.sql` yang sudah dibuat):
```powershell
cd "C:\Semester 5\RPL\Implementasi\Source_Code\Projek-RPL-26"
Get-Content db_view.sql | docker exec -i pilah_postgres psql -U postgres -d pilah_in
```

**Query manual (contoh: lihat semua user):**
```powershell
docker exec pilah_postgres psql -U postgres -d pilah_in -c "SELECT npm_nip, name, email, role, total_poin FROM users;"
```

**Masuk ke prompt `psql` interaktif:**
```powershell
docker exec -it pilah_postgres psql -U postgres -d pilah_in
```
Setelah masuk, Anda bisa ketik query SQL bebas, lalu `\q` untuk keluar.

### Opsi B — GUI Tools (paling nyaman)

#### DBeaver (gratis, recommended)
1. Download dari https://dbeaver.io
2. Klik **New Database Connection** → PostgreSQL
3. Isi:
   - Host: `localhost`
   - Port: `5432`
   - Database: `pilah_in`
   - Username: `postgres`
   - Password: `pilah_postgres_dev`
4. Klik **Test Connection** → Finish
5. Di sidebar kiri, expand `pilah_in` → `Schemas` → `public` → `Tables`
6. Double-click tabel mana pun untuk lihat isinya

#### pgAdmin (alternatif)
1. Download dari https://www.pgadmin.org
2. Tambah server baru dengan kredensial di atas
3. Navigate ke `Servers` → `pilah_in` → `Databases` → `pilah_in` → `Schemas` → `public` → `Tables`

---

## 3. Skema Database (Tabel Penting)

| Tabel | Deskripsi | Jumlah Data Sekarang |
|-------|-----------|----------------------|
| `users` | Akun pengguna (civitas/admin) | 2 |
| `uploads` | Foto sampah yang diunggah | 3 |
| `classification_results` | Hasil klasifikasi ML | 3 |
| `rewards` | Daftar reward tersedia | 3 |
| `reward_redemptions` | Voucher yang sudah ditukar | 2 |
| `point_transactions` | Riwayat transaksi poin | 5 |
| `education_materials` | Materi edukasi | 3 |

### Catatan: Nama Kolom FK
Tabel memakai prefix `id_` untuk foreign key (bukan `_id` suffix):
- `uploads.id_pengguna` → FK ke `users.id`
- `classification_results.id_unggahan` → FK ke `uploads.id`
- `reward_redemptions.id_reward` → FK ke `rewards.id`
- `reward_redemptions.id_pengguna` → FK ke `users.id`
- `point_transactions.id_pengguna` → FK ke `users.id`

---

## 4. Cara Menjalankan Ulang (jika service mati)

### A. Cek Docker container
```powershell
docker ps
```
Kalau `pilah_postgres`, `pilah_redis`, `pilah_ml_service` tidak ada:
```powershell
cd "C:\Semester 5\RPL\Implementasi\Source_Code\Projek-RPL-26\FASE_0_Infrastructure"
docker compose up -d
```

### B. Jalankan Backend (Django)
```powershell
cd "C:\Semester 5\RPL\Implementasi\Source_Code\Projek-RPL-26"
python manage.py runserver
```
→ tersedia di http://localhost:8000

### C. Jalankan Frontend (React)
```powershell
cd "C:\Semester 5\RPL\Implementasi\Source_Code\Projek-RPL-26\FASE_3_Frontend\pilah-frontend"
npm run dev
```
→ tersedia di http://localhost:3000

### D. Verifikasi semua sehat
```powershell
# Cek backend
Invoke-WebRequest http://localhost:8000/api/v1/education/ -UseBasicParsing

# Cek ML service
Invoke-WebRequest http://localhost:8001/health -UseBasicParsing

# Cek frontend
Invoke-WebRequest http://localhost:3000 -UseBasicParsing
```

---

## 5. Cara Reset Database (kalau perlu bersih)

```powershell
cd "C:\Semester 5\RPL\Implementasi\Source_Code\Projek-RPL-26"

# 1. Drop database lama
docker exec pilah_postgres psql -U postgres -c "DROP DATABASE IF EXISTS pilah_in;"
docker exec pilah_postgres psql -U postgres -c "CREATE DATABASE pilah_in;"

# 2. Jalankan migrasi
python manage.py migrate

# 3. Seed admin account
python manage.py shell -c "from apps.users.models import User; User.objects.create_user(npm_nip='ADM-001', name='Admin GoGreen', email='admin.gogreen@unpad.ac.id', unit_gedung='FMIPA', password='AdminPass123!', role='admin_gogreen', is_staff=True)"

# 4. Seed education materials (opsional)
python -c @"
import os, django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()
from apps.education.models import EducationMaterial
if not EducationMaterial.objects.exists():
    EducationMaterial.objects.create(judul='Memilah Sampah Organik dengan Benar', kategori_sampah='organik', konten='Sampah organik adalah sisa bahan atau objek yang berasal dari makhluk hidup...', is_published=True)
    EducationMaterial.objects.create(judul='Daur Ulang Sampah Anorganik', kategori_sampah='anorganik', konten='Sampah anorganik tidak dapat terurai secara alami...', is_published=True)
    EducationMaterial.objects.create(judul='Sampah Residu dan Penanganannya', kategori_sampah='residu', konten='Sampah residu adalah sampah yang tidak dapat didaur ulang...', is_published=True)
    print('Created 3 education materials')
"@
```

---

## 6. Query Database Penting (Copy-Paste ke psql/DBeaver)

### Cek poin user tertentu
```sql
SELECT name, total_poin, unit_gedung FROM users WHERE email = 'smoke099@mail.unpad.ac.id';
```

### Lihat semua transaksi poin user
```sql
SELECT pt.points, pt.transaction_type, pt.description, pt.created_at
FROM point_transactions pt
JOIN users u ON u.id = pt.id_pengguna
WHERE u.email = 'smoke099@mail.unpad.ac.id'
ORDER BY pt.created_at DESC;
```

### Cek hasil klasifikasi terbaru
```sql
SELECT
  u.name AS pengguna,
  cr.kategori_sampah,
  cr.confidence_score,
  cr.is_valid,
  cr.points_awarded
FROM classification_results cr
JOIN uploads up ON up.id = cr.id_unggahan
JOIN users u ON u.id = up.id_pengguna
ORDER BY cr.waktu_proses DESC;
```

### Leaderboard per pengguna
```sql
SELECT name, unit_gedung, total_poin,
       RANK() OVER (ORDER BY total_poin DESC) AS peringkat
FROM users WHERE role = 'civitas'
ORDER BY peringkat;
```

### Cek voucher yang sudah ditukar
```sql
SELECT
  u.name AS pengguna,
  r.name AS reward,
  rr.kode_voucher,
  rr.status,
  rr.tanggal_penukaran
FROM reward_redemptions rr
JOIN users u ON u.id = rr.id_pengguna
JOIN rewards r ON r.id = rr.id_reward
ORDER BY rr.tanggal_penukaran DESC;
```

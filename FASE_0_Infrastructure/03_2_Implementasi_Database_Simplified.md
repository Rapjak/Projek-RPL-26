# 3.2 Implementasi Database

## Pendahuluan

Bab ini mendokumentasikan implementasi layer database Pilah.in, mencakup physical schema PostgreSQL, desain tabel 3NF, constraints, indexes, views, dan triggers. Seluruh implementasi mengacu pada Data Dictionary dalam dokumen teknis RPL dan telah melalui verifikasi kecocokan 100%.

### Teknologi Database

DBMS: PostgreSQL 14+

Data Types: UUID (native), TIMESTAMPTZ (timezone-aware), NUMERIC (precision)

Extensions: uuid-ossp, pgcrypto

Normalization: 3NF (Third Normal Form)

Encoding: UTF-8 (mendukung Indonesian characters)

## Task 1: PostgreSQL Schema Creation

### 1.1 Overview

Task ini mengimplementasikan database schema Pilah.in yang terdiri dari:

- 7 tabel utama untuk menyimpan data pengguna, unggahan foto, hasil klasifikasi, reward, transaksi poin, dan materi edukasi
- 4 views untuk leaderboard dan statistik
- 2 triggers untuk auto-update timestamp
- Kontrol integritas data melalui constraints, foreign keys, dan check conditions

### 1.2 File Implementasi

File: FASE_0_Infrastructure/01_PostgreSQL_Schema.sql (Schema definition + sample data)

File: FASE_0_Infrastructure/03_2_Implementasi_Database.md (Dokumentasi teknis)

### 1.3 Physical Schema Diagram

Referensi diagram relasional tersedia di: Relational-Database-3NF.png - ERD diagram dengan kardinalitas dan foreign key relationships

Ringkasan Relasi:

- users → uploads (1:N via id_pengguna)
- uploads → classification_results (1:1 via id_unggahan)
- users → reward_redemptions (1:N via id_pengguna)
- reward_redemptions → rewards (N:1 via id_reward)
- users → point_transactions (1:N via id_pengguna)
- users → education_materials (1:N via id_admin, nullable)

## 1.4 Detail Tabel dan Kolom

### Tabel 1: users

Fungsi: Menyimpan data identitas civitas akademika, kredensial autentikasi, hak akses peran, dan akumulasi total saldo poin aktif.

Realisasi Requirement: DATA-001

Kolom-kolom:

- id_pengguna: UUID, PRIMARY KEY, DEFAULT gen_random_uuid() - Kunci unik pengenal akun pengguna
- npm_nip: VARCHAR(20), UNIQUE, NOT NULL - Nomor Induk Mahasiswa atau NIP civitas Unpad
- nama: VARCHAR(100), NOT NULL - Nama lengkap pengguna
- email: VARCHAR(100), UNIQUE, NOT NULL - Alamat email resmi pengguna
- password_hash: VARCHAR(255), NOT NULL - Hash kata sandi terenkripsi (PBKDF2/Argon2)
- peran: VARCHAR(20), NOT NULL, CHECK (peran IN ('civitas', 'admin_gogreen', 'pimpinan')) - Tingkat hak akses otorisasi sistem
- unit_gedung: VARCHAR(50), NOT NULL - Asal fakultas, departemen, atau lokasi gedung
- total_poin: INTEGER, NOT NULL, DEFAULT 0, CHECK (total_poin >= 0) - Akumulasi saldo poin aktif pengguna
- created_at: TIMESTAMPTZ, NOT NULL, DEFAULT CURRENT_TIMESTAMP - Waktu akun didaftarkan
- updated_at: TIMESTAMPTZ, NOT NULL, DEFAULT CURRENT_TIMESTAMP - Waktu profil terakhir kali diperbarui

Indexes:

- idx_users_npm_nip (UNIQUE) - cepat lookup via npm/nip
- idx_users_email (UNIQUE) - cepat lookup via email
- idx_users_peran - filter user berdasarkan role
- idx_users_total_poin (DESC) - leaderboard ranking

### Tabel 2: uploads

Fungsi: Menyimpan rekam jejak berkas foto bukti pemilahan sampah yang dikirim oleh civitas akademika.

Realisasi Requirement: DATA-002

Kolom-kolom:

- id_unggahan: UUID, PRIMARY KEY, DEFAULT gen_random_uuid() - Kunci unik data sesi unggahan
- id_pengguna: UUID, FOREIGN KEY REFERENCES users(id_pengguna), NOT NULL - ID pengguna yang mengunggah foto
- url_foto: VARCHAR(255), NOT NULL - Tautan lokasi penyimpanan berkas foto pada Cloud Object Storage
- status_proses: VARCHAR(20), NOT NULL, DEFAULT 'pending', CHECK (status_proses IN ('pending', 'processing', 'completed', 'failed')) - Status pemrosesan klasifikasi oleh sistem
- created_at: TIMESTAMPTZ, NOT NULL, DEFAULT CURRENT_TIMESTAMP - Waktu pengunggahan foto

Indexes:

- idx_uploads_pengguna - filter upload per pengguna
- idx_uploads_status - filter berdasarkan status proses
- idx_uploads_created (DESC) - recent uploads query

Foreign Key Constraint: ON DELETE CASCADE - menghapus user akan menghapus semua unggahannya

### Tabel 3: classification_results

Fungsi: Menyimpan luaran hasil inferensi model CNN terhadap foto sampah yang diunggah.

Realisasi Requirement: DATA-002, NFR-002

Kolom-kolom:

- id_klasifikasi: UUID, PRIMARY KEY, DEFAULT gen_random_uuid() - Kunci unik hasil pengujian klasifikasi
- id_unggahan: UUID, UNIQUE, FOREIGN KEY REFERENCES uploads(id_unggahan), NOT NULL - Relasi 1:1 ke berkas foto yang diuji
- kategori_sampah: VARCHAR(20), NOT NULL, CHECK (kategori_sampah IN ('organik', 'anorganik', 'residu', 'tidak_dikenal')) - Label kategori sampah hasil prediksi model
- confidence_score: NUMERIC(4,3), NOT NULL, CHECK (confidence_score >= 0.0 AND confidence_score <= 1.0) - Tingkat keyakinan prediksi model AI (contoh: 0.925)
- is_valid: BOOLEAN, NOT NULL, DEFAULT TRUE - Status keabsahan pemilahan (valid jika keyakinan >= ambang batas)
- waktu_proses: TIMESTAMPTZ, NOT NULL, DEFAULT CURRENT_TIMESTAMP - Waktu inferensi selesai diproses

Indexes:

- idx_classification_unggahan (UNIQUE) - O(1) lookup per upload
- idx_classification_kategori - statistik per kategori
- idx_classification_valid - filter valid/invalid classifications

Foreign Key Constraint: ON DELETE CASCADE - menghapus upload akan menghapus hasil klasifikasinya. Relasi 1:1 (UNIQUE) - satu foto hanya punya satu hasil klasifikasi

### Tabel 4: rewards

Fungsi: Menyimpan katalog insentif/hadiah yang dapat ditukarkan oleh civitas akademika menggunakan saldo poin.

Realisasi Requirement: DATA-005

Kolom-kolom:

- id_reward: UUID, PRIMARY KEY, DEFAULT gen_random_uuid() - Kunci unik item reward
- nama_reward: VARCHAR(100), NOT NULL - Nama produk atau voucher insentif
- deskripsi: TEXT, NULL - Informasi detail syarat dan ketentuan penukaran
- poin_dibutuhkan: INTEGER, NOT NULL, CHECK (poin_dibutuhkan > 0) - Biaya poin yang wajib dibayar pengguna
- stok: INTEGER, NOT NULL, DEFAULT 0, CHECK (stok >= 0) - Sisa kuota ketersediaan voucher
- masa_berlaku: DATE, NOT NULL - Batas waktu akhir penukaran reward
- is_active: BOOLEAN, NOT NULL, DEFAULT TRUE - Status ketersediaan item pada katalog
- created_at: TIMESTAMPTZ, NOT NULL, DEFAULT CURRENT_TIMESTAMP - Waktu item reward ditambahkan oleh admin

Indexes:

- idx_rewards_active - filter reward aktif di katalog
- idx_rewards_poin - filter reward berdasarkan harga poin

### Tabel 5: reward_redemptions

Fungsi: Menyimpan catatan penukaran poin menjadi kode voucher reward serta status klaim pengguna.

Realisasi Requirement: FR-008

Kolom-kolom:

- id_penukaran: UUID, PRIMARY KEY, DEFAULT gen_random_uuid() - Kunci unik transaksi penukaran
- id_pengguna: UUID, FOREIGN KEY REFERENCES users(id_pengguna), NOT NULL - ID pengguna yang melakukan penukaran
- id_reward: UUID, FOREIGN KEY REFERENCES rewards(id_reward), NOT NULL - ID reward yang ditukarkan
- kode_voucher: VARCHAR(50), UNIQUE, NOT NULL - Kode unik acak untuk verifikasi klaim ke pihak mitra/kantin
- status: VARCHAR(20), NOT NULL, DEFAULT 'aktif', CHECK (status IN ('aktif', 'terpakai', 'kedaluwarsa')) - Status masa berlaku voucher
- tanggal_penukaran: TIMESTAMPTZ, NOT NULL, DEFAULT CURRENT_TIMESTAMP - Waktu penukaran poin berhasil
- tanggal_digunakan: TIMESTAMPTZ, NULL - Waktu kode voucher divalidasi dan digunakan

Indexes:

- idx_redemptions_pengguna - riwayat penukaran per pengguna
- idx_redemptions_reward - statistik reward mana yang paling ditukar
- idx_redemptions_status - filter voucher aktif/terpakai/kedaluwarsa
- idx_redemptions_voucher (UNIQUE) - O(1) lookup via kode voucher

Foreign Key Constraints:

- id_pengguna: ON DELETE CASCADE - hapus user hapus semua penukaran
- id_reward: ON DELETE RESTRICT - reward tidak bisa dihapus selama ada penukaran aktif

### Tabel 6: point_transactions

Fungsi: Buku besar (ledger) pencatatan mutasi penambahan maupun pemotongan poin secara terperinci.

Realisasi Requirement: DATA-004

Kolom-kolom:

- id_transaksi: UUID, PRIMARY KEY, DEFAULT gen_random_uuid() - Kunci unik pencatatan transaksi poin
- id_pengguna: UUID, FOREIGN KEY REFERENCES users(id_pengguna), NOT NULL - ID pemilik akun yang mengalami mutasi poin
- id_referensi: UUID, NULL - Merujuk ke id_unggahan (jika bertambah) atau id_penukaran (jika berkurang)
- jumlah_poin: INTEGER, NOT NULL, CHECK (jumlah_poin > 0) - Nilai nominal poin yang dimutasi
- jenis_transaksi: VARCHAR(20), NOT NULL, CHECK (jenis_transaksi IN ('penambahan', 'pengurangan')) - Tipe arus poin
- deskripsi: VARCHAR(255), NOT NULL - Keterangan rincian aktivitas perolehan/penggunaan poin
- created_at: TIMESTAMPTZ, NOT NULL, DEFAULT CURRENT_TIMESTAMP - Waktu transaksi dicatatkan ke sistem

Indexes:

- idx_transactions_pengguna - riwayat transaksi per pengguna
- idx_transactions_jenis - statistik penambahan vs pengurangan
- idx_transactions_created (DESC) - recent transactions
- idx_transactions_referensi - audit trail ke upload/redemption

Foreign Key Constraint: ON DELETE CASCADE - hapus user hapus riwayat transaksi

### Tabel 7: education_materials

Fungsi: Menyimpan konten literasi panduan tata cara pemilahan sampah bagi civitas akademika.

Realisasi Requirement: FR-009

Kolom-kolom:

- id_edukasi: UUID, PRIMARY KEY, DEFAULT gen_random_uuid() - Kunci unik konten edukasi
- id_admin: UUID, FOREIGN KEY REFERENCES users(id_pengguna), NULL - ID admin pengunggah materi
- judul: VARCHAR(150), NOT NULL - Judul panduan atau artikel edukasi
- kategori_sampah: VARCHAR(20), NOT NULL, CHECK (kategori_sampah IN ('organik', 'anorganik', 'residu', 'umum')) - Kategori topik pemilahan yang dibahas
- konten: TEXT, NOT NULL - Isi uraian panduan materi secara lengkap
- url_media: VARCHAR(255), NULL - Tautan gambar/infografis pendukung
- created_at: TIMESTAMPTZ, NOT NULL, DEFAULT CURRENT_TIMESTAMP - Waktu publikasi artikel
- updated_at: TIMESTAMPTZ, NOT NULL, DEFAULT CURRENT_TIMESTAMP - Waktu artikel terakhir kali diperbarui

Indexes:

- idx_education_kategori - filter materi per kategori sampah
- idx_education_admin - materi yang dibuat per admin

Foreign Key Constraint: id_admin: ON DELETE SET NULL - hapus admin tidak menghapus materinya

## 1.5 Views (Materialized Queries)

### View 1: v_leaderboard_user

Fungsi: Peringkat pengguna berdasarkan total poin (descending).

Query view ini melakukan SELECT dari tabel users dengan filter peran civitas, mengurutkan berdasarkan total_poin descending, dan menambahkan kolom rank menggunakan window function ROW_NUMBER().

Kegunaan:

- Menampilkan leaderboard pengguna di frontend
- Ranking otomatis berdasarkan total_poin
- Filter hanya civitas (bukan admin/pimpinan)

### View 2: v_leaderboard_building

Fungsi: Peringkat gedung/unit berdasarkan total poin agregat.

Query view ini melakukan GROUP BY unit_gedung, menghitung SUM(total_poin) per gedung, COUNT(*) untuk total pengguna per gedung, dan mengurutkan berdasarkan total poin descending.

Kegunaan:

- Kompetisi antar unit/gedung
- Gamification element untuk meningkatkan partisipasi

### View 3: v_statistik_klasifikasi

Fungsi: Statistik hasil klasifikasi per kategori sampah.

Query view ini melakukan GROUP BY kategori_sampah, menghitung COUNT(*) total klasifikasi per kategori, AVG(confidence_score) rata-rata confidence, serta valid_count dan invalid_count menggunakan conditional aggregation.

Kegunaan:

- Monitoring akurasi model CNN per kategori
- Identifikasi kategori yang butuh training lebih
- Dashboard admin analytics

### View 4: v_aktivitas_pengguna

Fungsi: Ringkasan aktivitas pengguna (uploads, klasifikasi, poin).

Query view ini melakukan LEFT JOIN dari users ke uploads dan classification_results, menghitung total upload, total klasifikasi, valid klasifikasi, dan waktu upload terakhir per pengguna.

Kegunaan:

- Profil pengguna dengan statistik aktivitas
- Deteksi pengguna inactive
- Dashboard personal stats

## 1.6 Triggers (Automated Data Integrity)

### Trigger 1: trg_users_updated_at

Fungsi: Auto-update updated_at saat record users diubah.

Trigger ini menggunakan function update_updated_at_column() yang di-execute BEFORE UPDATE pada tabel users. Function ini mengubah NEW.updated_at menjadi CURRENT_TIMESTAMP sebelum record disimpan.

Kegunaan:

- Tracking perubahan profil pengguna
- Audit trail implicit

### Trigger 2: trg_education_updated_at

Fungsi: Auto-update updated_at saat record education_materials diubah.

Trigger ini menggunakan function yang sama (update_updated_at_column()) yang di-execute BEFORE UPDATE pada tabel education_materials.

Kegunaan:

- Tracking versi materi edukasi
- Kontrol konten yang sudah diedit

## 1.7 Design Decisions dan Justification

### 1.7.1 UUID vs Serial Integer IDs

Keputusan: Menggunakan UUID (Universally Unique Identifier) untuk semua Primary Key.

Alasan:

- Distributed System Ready: UUID dapat di-generate di client tanpa perlu round-trip ke DB
- Security: Menyembunyikan jumlah total user/record (tidak sequential)
- Merge-friendly: Jika ada multi-database sync, UUID tidak ada collision
- PostgreSQL Native Support: uuid-ossp extension sudah built-in

Trade-off:

- Storage overhead: 16 bytes vs 4/8 bytes untuk integer
- Slower index scan dibanding integer, tapi acceptable untuk aplikasi skala universitas

### 1.7.2 TIMESTAMPTZ vs TIMESTAMP

Keputusan: Menggunakan TIMESTAMPTZ (timezone-aware) untuk semua timestamp.

Alasan:

- Timezone Handling: Otomatis convert ke UTC di storage, client bisa convert ke local timezone
- Audit Trail Akurat: Waktu transaksi tidak ambiguous
- Multi-Region Ready: Jika ada disaster recovery di region lain, timestamp tetap konsisten

### 1.7.3 NUMERIC(4,3) untuk confidence_score

Keputusan: Tipe NUMERIC dengan presisi 4 digit, 3 digit desimal (range: 0.000 - 1.000).

Alasan:

- Exact Precision: AI confidence selalu 0.0-1.0, NUMERIC tidak ada rounding error
- Not Float/Double: Float punya precision loss, tidak cocok untuk financial/scoring logic
- Range Validation: CHECK constraint di database, bukan hanya di application layer

### 1.7.4 Enum-like VARCHAR dengan CHECK Constraints

Keputusan: Menggunakan VARCHAR dengan CHECK constraint, bukan PostgreSQL native ENUM type.

Alasan:

- Schema Flexibility: Enum di PostgreSQL hard to modify (ALTER TYPE requires recreating table)
- ORM Compatibility: Beberapa ORM (Django) lebih mudah handle VARCHAR
- Explicit Documentation: Check constraint explicit di schema
- Zero-downtime Migration: Kalau perlu tambah enum value, lebih mudah dengan VARCHAR

### 1.7.5 Cascade Delete vs Restrict

Keputusan: Campuran - CASCADE untuk user, RESTRICT untuk rewards.

Alasan CASCADE:

- Saat user dihapus, hapus semua unggahan dan klasifikasi (data orphan tidak berguna)
- Saat user dihapus, hapus semua point transactions (valid untuk audit trail individual)

Alasan RESTRICT:

- Rewards tidak boleh dihapus jika masih ada penukaran aktif (data integrity)
- Mencegah accidental deletion
- Admin harus handle penukaran terlebih dahulu

### 1.7.6 Nullable id_admin di education_materials

Keputusan: id_admin nullable, ON DELETE SET NULL.

Alasan:

- Materi edukasi tetap valuable meski admin dihapus
- Materi umum tidak selalu punya author specific (bisa system-generated)
- Soft delete di admin side: simpan materi tapi mark dengan id_admin=NULL

### 1.7.7 Tidak Ada Soft Delete

Keputusan: Hard delete dengan CASCADE, bukan soft delete (is_active column).

Alasan:

- Konsisten dengan dokumen RPL (tidak ada is_deleted column)
- Data retention policy di application layer (audit log terpisah)
- Simpler query logic (no WHERE is_deleted=FALSE di setiap query)
- Kalau butuh audit trail, gunakan triggers + separate audit table (future enhancement)

## 1.8 Sample Data

Schema include sample data untuk testing dan demo.

Rewards (4 items):

- E-Certificate Participant (500 poin)
- Sticker Pack Pemilahan (250 poin)
- Badge Top 10 Leaderboard (1000 poin)
- Bonus 100 Poin (300 poin)

Education Materials (4 articles):

- Pengenalan Sampah Organik
- Cara Memilah Sampah Organik
- Pengenalan Sampah Anorganik
- Pengenalan Sampah Residu

## 1.9 Execution dan Verification

### Prerequisite

Install PostgreSQL 14 atau lebih baru. Windows: download dari https://www.postgresql.org/download/windows/

Verify installation dengan command: psql --version

### Execution Steps

1. Login ke PostgreSQL: psql -U postgres
2. Execute schema script
3. Verify database created: gunakan command \l
4. Connect to pilah_in database: gunakan command \c pilah_in
5. List tables: gunakan command \dt
6. Test views: SELECT * FROM v_leaderboard_user; SELECT * FROM v_statistik_klasifikasi;

### Verification Checklist

- Database created with UTF-8 encoding
- All 7 tables exist with correct schema
- All indexes created
- All views accessible
- All triggers registered
- Sample data loaded
- Foreign key constraints working
- Check constraints enforced

## 1.10 Key Implementation Notes

1. Data Integrity: Constraints di database level, bukan hanya application layer
2. Performance: Indexes di kolom yang sering di-query (foreign keys, status, ranking)
3. Audit Trail: created_at dan updated_at di semua tabel untuk tracking
4. Scalability: UUID dan TIMESTAMPTZ siap untuk distributed system
5. Flexibility: Views untuk common queries, bukan hard-coded reports
6. Consistency: Schema 100% match dengan Data Dictionary dokumen teknis RPL

## Summary

Task 1 berhasil mengimplementasikan PostgreSQL database schema Pilah.in dengan:

- 7 tabel utama sesuai 3NF design
- Komprehensif constraints untuk data integrity
- 4 views untuk reporting dan analytics
- 2 triggers untuk automation
- Strategic indexes untuk performance

Schema siap untuk diintegrasikan dengan Django backend (Task 2 FASE 1).

File Location: C:\Semester 5\RPL\Implementasi\Source_Code\Projek-RPL-26\FASE_0_Infrastructure\

Last Updated: 2026-10-20

Status: 100% Compliant with RPL Technical Document

---

## Task 2: Redis Configuration

### 2.1 Overview

Task ini mengimplementasikan Redis cache layer untuk Pilah.in dengan Docker containerization. Redis digunakan untuk caching queries, session management, rate limiting, dan real-time leaderboard updates.

Teknologi: Redis 7 Alpine, Docker Compose, Volume persistence

### 2.2 Redis Role dalam Arsitektur

Redis berfungsi sebagai:

1. Session Store - menyimpan session user login (TTL: 1 jam)
2. Cache Layer - caching query results (klasifikasi, reward, leaderboard)
3. Rate Limiter - mencegah abuse API (upload frequency limit)
4. Real-time Updates - pub/sub untuk notifikasi leaderboard real-time
5. Job Queue - future enhancement untuk async classification tasks

### 2.3 File Implementasi

File: FASE_0_Infrastructure/docker-compose.yml - Docker Compose service definition

File: FASE_0_Infrastructure/redis.conf - Redis configuration

File: FASE_0_Infrastructure/.env.redis - Environment variables untuk cache TTL

### 2.4 Docker Compose Configuration

Service: pilah_redis

Container: redis:7-alpine (minimal image, ~7MB)

Port: 6379 (default Redis port)

Volume: redis_data (persist data between container restarts)

Network: pilah_network (shared bridge network untuk services)

Health Check: redis-cli ping command, interval 5s, timeout 3s

Password: Environment variable REDIS_PASSWORD (default: pilah_redis_password_dev)

### 2.5 Redis Configuration Details

Memory Management:

- maxmemory: 256MB (development size, scale di production)
- maxmemory-policy: allkeys-lru (least recently used eviction)
- maxmemory-samples: 5 (accuracy of eviction selection)

Persistence:

- RDB snapshots: save pada 900s/1change, 300s/10changes, 60s/10000changes
- AOF (Append Only File): disabled (enable untuk durability jika diperlukan)
- Directory: /data (mount ke volume)

Network:

- bind: 0.0.0.0 (accept semua interfaces)
- port: 6379 (default Redis port)
- protected-mode: yes (require password atau local connection)

Keyspace Notifications:

- Disabled by default (enable dengan notify-keyspace-events="KEA" jika butuh pub/sub events)

Replication:

- replica-read-only: yes (read-only slaves, siap untuk master-slave di production)

### 2.6 Cache TTL Strategy

Environment variables di .env.redis define cache expiration times:

- CACHE_TTL_USER_SESSION: 3600s (1 hour) - user session cache
- CACHE_TTL_CLASSIFICATION_RESULT: 86400s (24 hours) - classification AI result
- CACHE_TTL_REWARD_CATALOG: 3600s (1 hour) - katalog reward
- CACHE_TTL_LEADERBOARD: 300s (5 minutes) - leaderboard ranking (refresh frequently)
- CACHE_TTL_EDUCATION_MATERIAL: 86400s (24 hours) - education content

Rationale: Leaderboard refresh cepat untuk gamification feel, classification result cache lama karena AI model tidak berubah frequent.

### 2.7 Django Integration Points

Backend akan menggunakan redis library (django-redis package):

1. Session Backend: SESSION_ENGINE = 'django.contrib.sessions.backends.cache'
2. Cache Backend: CACHES = {'default': {'BACKEND': 'django_redis.cache.RedisCache'}}
3. Rate Limiting: django-ratelimit atau DRF throttling via Redis
4. Job Queue: Celery + Redis broker (future)

### 2.8 Execution Steps

Prerequisites: Docker dan Docker Compose installed

Windows: Download Docker Desktop dari docker.com

Verify: docker --version && docker-compose --version

Startup:

1. Navigate ke FASE_0_Infrastructure directory
2. Run: docker-compose up -d
3. Verify: docker ps (lihat pilah_redis running)
4. Test connection: docker exec pilah_redis redis-cli ping
5. Check memory: docker exec pilah_redis redis-cli INFO memory

Shutdown: docker-compose down

Cleanup: docker volume rm redis_data (delete persisted data)

### 2.9 Testing Redis Connection

Via redis-cli:

docker exec pilah_redis redis-cli

Commands to test:

- PING (return PONG)
- SET key1 "Hello Redis"
- GET key1 (return "Hello Redis")
- KEYS * (list all keys)
- FLUSHDB (clear database, dev only)
- EXIT (quit)

Via Python (Django shell):

python manage.py shell

from django.core.cache import cache

cache.set('test_key', 'test_value', 300)

cache.get('test_key')

### 2.10 Performance Considerations

Memory Limits:

- Development: 256MB sufficient untuk caching
- Production: estimate ~1GB untuk 10000+ concurrent sessions

CPU:

- Redis single-threaded, minimal CPU overhead
- Alpine image optimized untuk container efficiency

Network:

- Same network as Django (docker-compose bridge network)
- Zero latency vs external Redis

Eviction Policy:

- allkeys-lru: automatically remove least-used keys saat memory full
- Graceful degradation: old cache entries removed, not system crash

### 2.11 Monitoring Commands

Check Redis status:

docker exec pilah_redis redis-cli INFO server (version, uptime)

docker exec pilah_redis redis-cli INFO memory (memory usage)

docker exec pilah_redis redis-cli DBSIZE (total keys in DB)

docker exec pilah_redis redis-cli SLOWLOG GET 10 (slow queries)

View logs:

docker logs pilah_redis

Monitor real-time:

docker exec pilah_redis redis-cli MONITOR

### 2.12 Development Workflow

Start stack:

docker-compose up -d

Develop Django app:

python manage.py runserver

Cache automatically hits Redis via django-redis

Stop stack:

docker-compose down

Persist data survives container restart (volume redis_data)

### 2.13 Migration to Production

Production checklist:

- Change REDIS_PASSWORD to strong secret
- Increase maxmemory (estimate based on users)
- Enable AOF persistence untuk durability
- Setup Redis Sentinel atau Cluster untuk HA
- Implement Redis backups (RDB snapshots ke S3/backup storage)
- Monitor via redis-exporter + Prometheus
- Setup Redis ACL (Redis 6+) untuk role-based access

### 2.14 Key Implementation Notes

1. Alpine image: minimal footprint, fast container startup
2. Health check: automatic container restart jika Redis crash
3. Named volume: data persists across container lifecycle
4. Bridge network: secure communication antar services
5. Environment-based password: secure secret management
6. LRU eviction: graceful memory management tanpa OOM
7. No AOF by default: trade durability untuk speed (acceptable untuk dev cache)

## Summary

Task 2 berhasil mengimplementasikan Redis cache layer dengan Docker:

- 256MB in-memory cache dengan LRU eviction policy
- RDB persistence untuk data durability
- Alpine image untuk minimal overhead
- Environment-based configuration untuk flexibility
- Health check untuk operational resilience
- Ready untuk Django integration via django-redis

Redis bersama PostgreSQL (Task 1) membentuk foundation infrastructure FASE 0. Lanjut ke Task 3 (Cloud Storage).

File Location: C:\Semester 5\RPL\Implementasi\Source_Code\Projek-RPL-26\FASE_0_Infrastructure\

Last Updated: 2026-10-20

Status: ✅ Complete with Docker best practices

---

## Task 3: Cloud Storage Setup (MinIO)

### 3.1 Overview

Task ini mengimplementasikan object storage layer menggunakan MinIO (S3-compatible local storage) untuk menyimpan foto bukti pemilahan sampah yang diunggah user. MinIO dipilih karena compatible dengan AWS S3 API sehingga mudah migrate ke cloud storage production (S3, GCS, Azure Blob) tanpa code changes.

Teknologi: MinIO latest, Docker Compose, S3-compatible API

### 3.2 MinIO Role dalam Arsitektur

MinIO berfungsi sebagai:

1. Photo Storage - menyimpan foto bukti pemilahan sampah dari user (bucket: pilah-uploads)
2. ML Model Storage - menyimpan CNN model files untuk FastAPI inference (bucket: pilah-models)
3. Education Media Storage - menyimpan infografis dan media materi edukasi (bucket: pilah-education)
4. Presigned URL Generator - generate temporary URLs untuk secure file access
5. Static Asset CDN - serve static files langsung dari storage layer

### 3.3 File Implementasi

File: FASE_0_Infrastructure/docker-compose.yml - MinIO service definition (updated dengan MinIO service)

File: FASE_0_Infrastructure/.env.minio - Environment variables untuk MinIO configuration

File: FASE_0_Infrastructure/minio-init.sh - Initialization script untuk create buckets

### 3.4 Docker Compose Configuration

Service: pilah_minio

Container: minio/minio:latest (official MinIO image)

Ports:

- 9000 (API endpoint - S3-compatible)
- 9001 (Console UI - web-based management interface)

Volume: minio_data (persist uploaded files between container restarts)

Network: pilah_network (shared network dengan Redis dan future services)

Environment:

- MINIO_ROOT_USER: Admin username (default: pilah_admin)
- MINIO_ROOT_PASSWORD: Admin password (default: pilah_minio_password_dev)

Health Check: curl http://localhost:9000/minio/health/live endpoint, interval 10s

### 3.5 Bucket Structure

Tiga bucket utama:

1. pilah-uploads (public read)

Purpose: Menyimpan foto bukti pemilahan sampah dari civitas

File naming: {user_id}/{upload_id}.{ext}

Contoh path: 550e8400-e29b-41d4-a716-446655440000/660e8400-e29b-41d4-a716-446655440001.jpg

Policy: Public read (foto bisa di-embed di frontend tanpa presigned URL overhead)

2. pilah-models (download only)

Purpose: Menyimpan trained CNN model files untuk klasifikasi sampah

Files: model_cnn_v1.h5, labels.json, model_config.json

policy: Download policy (restricted read, authenticated write)

3. pilah-education (public read)

Purpose: Menyimpan infografis dan media materi edukasi

File naming: {education_id}/{media_id}.{ext}

Contoh path: 770e8400-e29b-41d4-a716-446655440002/infografis_organik.png

policy: Public read (media bisa di-embed di education pages)

### 3.6 Security Configuration

Access Control:

- Root user: pilah_admin (full access ke semua buckets)
- Access keys: pilah_access_key_dev (untuk Django backend)
- Secret keys: pilah_secret_key_dev (keep secret, rotate di production)

File Upload Limits:

- MAX_FILE_SIZE: 10MB (10485760 bytes) - max upload per file
- Allowed extensions: .jpg, .jpeg, .png, .webp (image formats only)

Presigned URLs:

- PRESIGNED_URL_EXPIRY: 3600s (1 hour) - temporary access URLs
- Used for secure temporary access tanpa public bucket policy

### 3.7 MinIO Console UI

MinIO menyediakan web-based console untuk manage buckets dan objects.

Access: http://localhost:9001

Login credentials: sama dengan MINIO_ROOT_USER dan MINIO_ROOT_PASSWORD

Features:

- Browse buckets dan objects
- Upload/download files manually
- Set bucket policies
- View access logs
- Monitor storage usage

### 3.8 Django Integration Points

Backend akan menggunakan boto3 atau django-storage dengan S3 backend:

Storage Backend:

DEFAULT_FILE_STORAGE = 'storages.backends.s3boto3.S3Boto3Storage'

AWS_S3_ENDPOINT_URL = 'http://localhost:9000'

AWS_STORAGE_BUCKET_NAME = 'pilah-uploads'

AWS_ACCESS_KEY_ID = 'pilah_access_key_dev'

AWS_SECRET_ACCESS_KEY = 'pilah_secret_key_dev'

Media Files:

- User uploaded photos: uploaded ke pilah-uploads bucket
- Education media: uploaded ke pilah-education bucket
- Model files: uploaded ke pilah-models bucket (admin only)

### 3.9 Execution Steps

Prerequisites: Docker dan Docker Compose installed

Start MinIO:

1. Navigate ke FASE_0_Infrastructure directory
2. Run: docker-compose up -d minio
3. Wait for health check to pass: docker ps
4. Access console: http://localhost:9001

Initialize Buckets:

MinIO initialization otomatis via script atau manual via console UI:

1. Login ke console http://localhost:9001
2. Navigate ke Buckets → Create Bucket
3. Create buckets: pilah-uploads, pilah-models, pilah-education
4. Set policies untuk masing-masing bucket

Test Upload:

Via console UI:

1. Select bucket pilah-uploads
2. Click Upload → select test image
3. Verify file uploaded successfully

Via AWS CLI (setelah install awscli):

aws --endpoint-url http://localhost:9000 s3 cp test.jpg s3://pilah-uploads/

Via Python (boto3):

import boto3

s3 = boto3.client('s3', endpoint_url='http://localhost:9000', ...)

s3.upload_file('test.jpg', 'pilah-uploads', 'test.jpg')

### 3.10 MinIO vs AWS S3 Comparison

Development (MinIO):

- Runs locally tanpa cloud account
- No cost, unlimited storage (limited by disk)
- S3-compatible API, same code as production
- Web console untuk easy management
- No network latency (local)

Production (AWS S3):

- Highly available (99.99% SLA)
- Global CDN (CloudFront integration)
- Infinite scalability
- Cost per GB storage + requests
- Network latency considerations

Migration Path:

- Ganti AWS_S3_ENDPOINT_URL ke https://s3.amazonaws.com
- Ganti credentials ke AWS IAM keys
- No code changes required (S3-compatible)

### 3.11 Performance Considerations

Storage:

- Local development: limited by host disk space
- Docker volume: minio_data persistent across restarts

Network:

- Local endpoint (localhost:9000): zero latency
- Container network: internal bridge, fast

Throughput:

- MinIO optimized untuk high throughput object storage
- Sufficient untuk photo uploads (10MB max per file)

Concurrency:

- Support concurrent uploads dari multiple users
- No bottleneck untuk typical university-scale usage

### 3.12 Backup Strategy

Manual Backup:

Copy volume data:

docker cp pilah_minio:/minio_data ./minio_backup

S3 Sync:

Bisa sync MinIO bucket ke AWS S3 untuk backup:

mc mirror pilah/pilah-uploads s3/aws-backup-bucket/uploads

Production Backup:

- Enable bucket versioning (keep file history)
- Setup cross-region replication
- Regular snapshots ke backup storage

### 3.13 Monitoring Commands

Check MinIO status:

docker logs pilah_minio (view server logs)

docker exec pilah_minio curl http://localhost:9000/minio/health/live (health check)

Monitor storage usage:

Access console UI http://localhost:9001 → Dashboard

View bucket size, object count, traffic

List buckets:

docker exec pilah_minio mc ls pilah

### 3.14 Production Migration Checklist

Production migration ke AWS S3:

- Create AWS S3 buckets (pilah-uploads, pilah-models, pilah-education)
- Setup IAM user dengan S3 access
- Configure bucket policies (public read untuk uploads, private untuk models)
- Setup CloudFront CDN untuk fast delivery
- Enable bucket versioning untuk data recovery
- Configure lifecycle policies (archive old files ke Glacier)
- Setup cross-region replication untuk disaster recovery
- Migrate existing data dari MinIO ke S3 (mc mirror)

### 3.15 Key Implementation Notes

1. S3-compatible: MinIO API identical ke AWS S3, zero code changes untuk migration
2. Persistent storage: Docker volume minio_data keeps files safe
3. Console UI: Easy bucket management tanpa CLI
4. Health check: Automatic container restart jika MinIO fails
5. Bucket policies: Flexible access control per bucket
6. Presigned URLs: Secure temporary access tanpa public exposure
7. Multi-bucket architecture: Separate concerns (uploads, models, education)

## Summary

Task 3 berhasil mengimplementasikan object storage layer dengan MinIO:

- 3 buckets: pilah-uploads, pilah-models, pilah-education
- S3-compatible API untuk easy cloud migration
- Web console UI untuk management
- Presigned URL support untuk secure access
- Docker persistent storage untuk data durability

MinIO bersama PostgreSQL (Task 1) dan Redis (Task 2) membentuk complete infrastructure stack. Lanjut ke Task 4 (Environment Variables).

File Location: C:\Semester 5\RPL\Implementasi\Source_Code\Projek-RPL-26\FASE_0_Infrastructure\

Last Updated: 2026-10-20

Status: ✅ Complete dengan S3-compatible architecture

---

## Task 4: Environment Variables Consolidation

### 4.1 Overview

Task ini mengkonsolidasikan semua environment variables dari PostgreSQL, Redis, MinIO, Django, dan FastAPI ke dalam unified .env template. Strategy ini memudahkan deployment consistency, secret management, dan configuration tracking.

Teknologi: .env file pattern, python-dotenv, environment variable management

### 4.2 Environment Strategy

Unified Configuration:

Single .env.example file berisi ALL environment variables untuk development

Copy .env.example → .env untuk development setup

Production: gunakan secrets management (AWS Secrets Manager, HashiCorp Vault)

Version Control:

- .env.example: di-commit ke repo (template)
- .env: di-gitignore (sensitive data locally)
- .gitignore: exclude semua .env files dan secrets

### 4.3 Environment Variables Structure

File: .env.example (template, dicommit)

File: .env (development, di-gitignore)

File: .gitignore (exclude env files dan sensitive data)

Sections dalam .env:

1. Application Base Configuration
2. PostgreSQL Database
3. Redis Cache
4. MinIO Object Storage
5. FastAPI ML Service
6. Django Backend Settings
7. Security Settings
8. Admin Settings
9. Rate Limiting
10. Logging Configuration
11. Docker/Deployment Settings
12. Frontend Configuration
13. Feature Flags
14. External Service Credentials (AWS, etc)
15. Database Backup
16. Email/SMTP Configuration

### 4.4 Key Environment Variables

Application Layer:

DJANGO_ENV: development atau production

DEBUG: True untuk dev, False untuk production

SECRET_KEY: Django secret key (generate dengan secrets.token_urlsafe(64))

ALLOWED_HOSTS: DNS/IP yang accept requests

Database:

DATABASE_HOST: PostgreSQL server address

DATABASE_PORT: 5432 (default)

DATABASE_NAME: pilah_in

DATABASE_USER: postgres

DATABASE_PASSWORD: secure password

Cache:

REDIS_HOST: localhost (dev) atau managed service

REDIS_PORT: 6379

REDIS_PASSWORD: secure password

CACHE_TTL_*: berbeda per data type (session 1h, leaderboard 5m, etc)

Storage:

MINIO_ENDPOINT: localhost:9000 (dev) atau AWS S3 (prod)

MINIO_BUCKET_*: bucket names

MAX_FILE_SIZE: 10MB max upload

PRESIGNED_URL_EXPIRY: 1 hour temporary access

ML Service:

FASTAPI_ENDPOINT: http://localhost:8000

ML_CONFIDENCE_THRESHOLD: 0.7 (minimum confidence untuk valid classification)

Security:

SESSION_COOKIE_SECURE: False (dev), True (prod)

CSRF_TRUSTED_ORIGINS: frontend URLs

PASSWORD_VALIDATORS: complexity requirements

Feature Flags:

ENABLE_LEADERBOARD: True/False

ENABLE_REWARDS: True/False

ENABLE_EDUCATION: True/False

### 4.5 Development Setup

Create .env dari template:

cp .env.example .env

Edit .env dengan development values:

DJANGO_ENV=development
DEBUG=True
DATABASE_PASSWORD=local_postgres_password
REDIS_PASSWORD=pilah_redis_password_dev
MINIO_ROOT_PASSWORD=pilah_minio_password_dev

Load environment variables di Django settings.py:

import os
from dotenv import load_dotenv

load_dotenv()

SECRET_KEY = os.getenv('SECRET_KEY')
DEBUG = os.getenv('DEBUG', False) == 'True'
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'HOST': os.getenv('DATABASE_HOST'),
        'PORT': os.getenv('DATABASE_PORT'),
        'NAME': os.getenv('DATABASE_NAME'),
        'USER': os.getenv('DATABASE_USER'),
        'PASSWORD': os.getenv('DATABASE_PASSWORD'),
    }
}

### 4.6 Production Deployment

Environment Setup:

.env.example → template di version control

.env.production → production secrets (NOT in version control)

Secrets Management Options:

1. Environment variables set by container orchestrator (Kubernetes, Docker Swarm)
2. AWS Secrets Manager untuk managed secrets
3. HashiCorp Vault untuk centralized secret management
4. GitHub Actions Secrets untuk CI/CD

Deployment Flow:

docker build -t pilah-backend .

docker run --env-file .env.production pilah-backend

Atau via docker-compose:

services:
  django:
    build: .
    env_file: .env.production
    ports:
      - "8000:8000"

### 4.7 Environment Validation

Startup Checks:

Django startup harus validate bahwa semua required env vars tersedia.

Create management command untuk validate:

python manage.py check_environment

Output: WARNING jika missing optional vars, ERROR jika missing required

Required Variables (Error jika missing):

DATABASE_HOST, DATABASE_PASSWORD, SECRET_KEY

Optional Variables (Warning jika missing):

AWS_ACCESS_KEY_ID (only for production S3)

SMTP_HOST (only for email notifications)

### 4.8 Secrets Rotation

Development:

Change .env values manually

Restart containers: docker-compose restart

Production:

Update AWS Secrets Manager atau Vault

Restart pods/containers (no downtime untuk stateless services)

Database credentials rotation:

- Update PostgreSQL user password
- Update DATABASE_PASSWORD di env
- Restart Django service

### 4.9 Docker Integration

docker-compose.yml reference:

services:
  django:
    build: .
    env_file: .env
    environment:
      - DJANGO_ENV=development
    ports:
      - "8000:8000"

Load .env secara otomatis saat docker-compose up

Override specific vars dengan environment section

### 4.10 Multi-environment Setup

Development (.env.development):

DEBUG=True
DATABASE_HOST=localhost
REDIS_HOST=localhost
MINIO_ENDPOINT=localhost:9000

Staging (.env.staging):

DEBUG=False
DATABASE_HOST=staging-db.internal
REDIS_HOST=staging-redis.internal
MINIO_ENDPOINT=staging-s3.amazonaws.com

Production (.env.production):

DEBUG=False
DATABASE_HOST=prod-db.managed.aws
REDIS_HOST=prod-elasticache.aws
MINIO_ENDPOINT=s3.amazonaws.com

Switch environment:

export ENV=staging
cp .env.${ENV} .env
docker-compose up -d

### 4.11 Documentation

.env.example includes:

- Section headers untuk organize
- Comments explaining each variable
- Contoh values untuk development
- Production notes untuk sensitive settings

Team reference:

Baru hire developer? Clone repo, cp .env.example .env, done.

Sudah ada development .env? Merge new vars dari updated .env.example

### 4.12 Security Best Practices

Do:

- Use strong random passwords (generate dengan: python -c 'import secrets; print(secrets.token_urlsafe(32))')
- Rotate secrets regularly
- Use different secrets untuk dev/staging/production
- Document environment setup (README.md)
- Use .gitignore strictly

Don't:

- Commit .env ke version control
- Share .env via email atau chat
- Hardcode secrets di code
- Use same password across environments
- Keep backups unencrypted

### 4.13 CI/CD Integration

GitHub Actions example:

jobs:
  deploy:
    runs-on: ubuntu-latest
    env:
      DATABASE_PASSWORD: ${{ secrets.DATABASE_PASSWORD }}
      SECRET_KEY: ${{ secrets.SECRET_KEY }}
    steps:
      - uses: actions/checkout@v2
      - name: Deploy
        run: docker-compose up -d

Environment variables disimpan di GitHub Secrets (encrypted)

CI/CD workflow inject secrets saat runtime

### 4.14 Troubleshooting

Variable tidak ter-load?

- Check .env file exists dan readable
- Verify load_dotenv() called sebelum accessing os.getenv()
- Check variable name spelling (case-sensitive)

Wrong value dari environment?

- Check .env override (local .env > environment vars)
- Check precedence: os.environ > .env > default

Production missing credentials?

- Verify AWS Secrets Manager atau Vault accessible
- Check IAM permissions untuk service account
- Verify env var names match deployment config

### 4.15 Key Implementation Notes

1. Single source of truth: .env.example template
2. Development friendly: cp .env.example .env, no setup needed
3. Production safe: .env ignored, secrets via secrets manager
4. Docker integrated: docker-compose auto-load .env
5. Validation: startup checks untuk missing required vars
6. Documentation: comments explain purpose setiap variable
7. Multi-environment: easy switch dev/staging/production via ENV variable

## Summary

Task 4 berhasil mengkonsolidasikan environment variables:

- Unified .env.example template dengan 16 sections
- Development .env setup minimal effort (copy + edit)
- Production secrets management strategy
- Docker compose integration
- Security best practices documented

Environment variables bersama dengan PostgreSQL, Redis, MinIO membentuk complete infrastructure configuration. Lanjut ke Task 5 (Docker local dev setup).

File Location: C:\Semester 5\RPL\Implementasi\Source_Code\Projek-RPL-26\

Last Updated: 2026-10-20

Status: ✅ Complete dengan secure secrets management

---

## Task 5: Docker Local Development Setup

### 5.1 Overview

Task ini mengimplementasikan complete local development environment menggunakan Docker Compose. Single command start untuk launch semua services: PostgreSQL, Redis, MinIO.

Teknologi: Docker Compose 3.8, multi-service orchestration

### 5.2 Docker Compose Architecture

services:

1. PostgreSQL (database)
   - Image: postgres:14-alpine
   - Port: 5432
   - Volume: postgres_data (persistent)
   - Init: auto-execute 01_PostgreSQL_Schema.sql
   - Health check: pg_isready

2. Redis (cache)
   - Image: redis:7-alpine
   - Port: 6379
   - Volume: redis_data + config file
   - Health check: redis-cli ping

3. MinIO (storage)
   - Image: minio/minio:latest
   - Ports: 9000 (API), 9001 (console)
   - Volume: minio_data (persistent)
   - Auto-create buckets: pilah-uploads, pilah-models, pilah-education

4. MinIO Init (bonus)
   - Container: minio/mc:latest (init-only)
   - Creates buckets before services start
   - Sets bucket policies

Network: pilah_network (bridge, isolated)

Volumes: 3 named volumes (data persistence)

### 5.3 File Structure

FASE_0_Infrastructure/

├── docker-compose.yml - Main orchestration file
├── 01_PostgreSQL_Schema.sql - Database initialization
├── redis.conf - Redis configuration
├── minio-init.sh - MinIO bucket initialization (Linux/Mac)
├── .env.minio - MinIO environment variables
├── .env.redis - Redis environment variables
└── .gitignore - Exclude .env files

Root Project/

├── .env.example - Unified environment template
├── Makefile - Make targets for common commands
└── start-infrastructure.bat - Windows startup script

### 5.4 Execution Steps

Option 1: Windows Batch Script

Double-click start-infrastructure.bat

Or run in terminal:

start-infrastructure.bat

Option 2: Manual Docker Compose

Navigate ke FASE_0_Infrastructure:

cd FASE_0_Infrastructure

Start services:

docker-compose up -d

Check status:

docker-compose ps

Option 3: Make Commands (Linux/Mac)

make up - Start services
make ps - Show status
make logs - View logs
make down - Stop services
make clean - Stop + remove volumes

### 5.5 Verification Checklist

After running startup script:

1. Docker containers running:

docker-compose ps

Expected: 3 containers (pilah_postgres, pilah_redis, pilah_minio)

2. PostgreSQL ready:

docker exec pilah_postgres pg_isready

Expected output: /var/run/postgresql:5432 - accepting connections

3. Redis ready:

docker exec pilah_redis redis-cli ping

Expected output: PONG

4. MinIO ready:

curl http://localhost:9000/minio/health/live

Expected: 200 OK

5. Buckets created:

docker exec pilah_minio mc ls pilah

Expected: pilah-uploads, pilah-models, pilah-education

### 5.6 Make Commands Reference

Infrastructure:

make up - Start all services (docker-compose up -d)

make down - Stop all services (docker-compose down)

make ps - Show container status

make logs - Stream logs (docker-compose logs -f)

make status - Health check per service

Database:

make shell-postgres - PostgreSQL psql shell

make db-migrate - Re-run schema script

make db-backup - Create database backup

Cache:

make shell-redis - Redis redis-cli shell

make redis-flush - Clear Redis cache

Storage:

make minio-console - Open MinIO web console

make minio-test - Test bucket access

### 5.7 Windows Startup Script

start-infrastructure.bat handles:

1. Docker installation check
2. Docker daemon running check
3. .env file creation (if missing)
4. docker-compose up -d execution
5. Service status check
6. User guidance for next steps

Features:

- Error handling (Docker not installed/running)
- Auto-create .env from template
- Interactive pause (read instructions)
- Cross-platform (works in CMD, PowerShell)

### 5.8 Health Check Implementation

PostgreSQL:

test: ["CMD-SHELL", "pg_isready -U postgres -d pilah_in"]

interval: 10s

timeout: 5s

retries: 5

Redis:

test: ["CMD", "redis-cli", "ping"]

interval: 5s

timeout: 3s

retries: 5

MinIO:

test: ["CMD", "curl", "-f", "http://localhost:9000/minio/health/live"]

interval: 10s

timeout: 5s

retries: 5

Benefits:

- Automatic container restart jika service fails
- Dependency wait (services start in order)
- Integration dengan orchestration tools

### 5.9 Volume Management

Named volumes (persistent):

1. postgres_data - PostgreSQL data directory
   - Survives container restart
   - Survives docker-compose down (unless -v flag)
   - Backup: pg_dump dari running container

2. redis_data - Redis RDB/AOF files
   - Survives container restart
   - Data persistence untuk cache entries

3. minio_data - MinIO object storage
   - Survives container restart
   - All uploaded files persistent

Delete volumes (data loss):

docker-compose down -v

docker volume prune

### 5.10 Network Configuration

pilah_network (bridge):

- Services connected to same network
- DNS resolution (service name = hostname)
- Isolated dari host network
- Internal communication tanpa port exposure

Usage:

Django service connect to:

PostgreSQL: postgres:5432

Redis: redis:6379

MinIO: minio:9000

Host → Container communication:

localhost:5432 → PostgreSQL

localhost:6379 → Redis

localhost:9000 → MinIO API

localhost:9001 → MinIO Console

### 5.11 Troubleshooting

Container not starting?

Check logs: docker-compose logs

Check config: docker-compose config

Health check failing?

PostgreSQL: Check DATABASE_PASSWORD matches environment

Redis: Verify redis.conf syntax

MinIO: Check port 9000 not in use

Port conflicts?

Change port mappings:

postgres: 5432:5432 → 5433:5432

redis: 6379:6379 → 6380:6379

minio: 9000:9000 → 9002:9000

Restart after change.

Disk space full?

Clean up unused images: docker system prune

Remove unused volumes: docker volume prune

Check volume size: docker volume inspect postgres_data

### 5.12 Backup Strategies

PostgreSQL Backup:

docker exec pilah_postgres pg_dump -U postgres pilah_in > backup.sql

Restore:

docker exec -i pilah_postgres psql -U postgres pilah_in < backup.sql

MinIO Backup:

mc mirror pilah/pilah-uploads s3/backup-bucket/uploads

Redis Backup:

docker cp pilah_redis:/data/dump.rdb ./redis_backup.rdb

### 5.13 Development Workflow

Start:

start-infrastructure.bat (or make up)

Verify services running:

make status

Connect to PostgreSQL:

make shell-postgres

Run migrations:

make db-migrate

Connect to Redis:

make shell-redis

Access MinIO:

http://localhost:9001

Development:

Edit code in host machine

Django auto-reload enabled (if mounted)

Restart service: docker-compose restart django (if needed)

Stop:

docker-compose down

### 5.14 CI/CD Integration

GitHub Actions example:

jobs:
  test:
    services:
      postgres:
        image: postgres:14-alpine
        env:
          POSTGRES_PASSWORD: test_password
        ports:
          - 5432:5432
      redis:
        image: redis:7-alpine
        ports:
          - 6379:6379
    steps:
      - uses: actions/checkout@v2
      - run: pytest

Production:

docker-compose production.yml (production overrides)

Environment variables from secrets manager

No local development scripts needed

### 5.15 Production Readiness

Local setup is development-only. Production requires:

1. External PostgreSQL (RDS, CloudSQL, etc)
2. Managed Redis (ElastiCache, Memorystore)
3. S3-compatible storage (AWS S3, GCS, Azure Blob)
4. Docker Swarm atau Kubernetes untuk orchestration
5. TLS termination (NGINX/traefik)
6. Environment-specific config files
7. Secrets management (HashiCorp Vault, AWS Secrets Manager)

### 5.16 Key Implementation Notes

1. Single command start: docker-compose up -d
2. Health checks: Automatic service monitoring
3. Persistent volumes: Data survives restarts
4. Auto-initialization: Schema loaded on first start
5. Network isolation: Secure internal communication
6. Windows support: start-infrastructure.bat
7. Linux/Mac support: Makefile targets
8. Clean setup: Named volumes vs bind mounts

## Summary

Task 5 berhasil mengimplementasikan local development environment:

- Docker Compose orchestration (3 services)
- Health checks untuk reliability
- Named volumes untuk data persistence
- Windows startup script (start-infrastructure.bat)
- Makefile untuk common commands
- Auto-initialization (PostgreSQL schema)

Infrastructure siap untuk:
- PostgreSQL database dengan schema auto-load
- Redis cache dengan LRU eviction
- MinIO object storage dengan 3 buckets

Files ready:
- docker-compose.yml (complete stack)
- Makefile (command shortcuts)
- start-infrastructure.bat (Windows one-click)

Next: FASE 1 (Django Backend) - API endpoints dan models.

File Location: C:\Semester 5\RPL\Implementasi\Source_Code\Projek-RPL-26\

Last Updated: 2026-10-20

Status: ✅ FASE 0 Complete - Infrastructure ready for Django integration

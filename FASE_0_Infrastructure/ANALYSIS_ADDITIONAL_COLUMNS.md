# Analisis Kolom Tambahan - Pilah.in PostgreSQL Schema

## Dokumen Ini Menjelaskan:

1. Kolom yang awalnya ditambahkan namun TIDAK ada di dokumen RPL resmi
2. Alasan kenapa kolom tersebut TIDAK boleh ditambah
3. Dampak apabila kolom tersebut ditambah
4. Apakah sistem tetap bisa jalan tanpa kolom tersebut

---

## Analisis Kolom Tambahan

### 1. Tabel `users`

| Kolom Tambahan | Alasan Kenapa TIDAK Tambah | Dampak Jika Ditambah | Bisa Jalan Tanpa? |
|----------------|----------------------------|----------------------|-------------------|
| `is_active` (BOOLEAN) | Dokumen menggunakan `peran` sebagai penentu status akun. Admin menghapus akun melalui update `peran` ke 'deleted' atau soft delete di level aplikasi. | - Menambah kolom redundant<br>- Logika pengecekan akun jadi lebih kompleks (check `is_active` DAN `peran`)<br>- Potential inconsistency jika `is_active=FALSE` tapi `peran='civitas'` | ✅ **Ya** - Sistem bisa jalan. Status akun dikontrol oleh `peran` value. |

### 2. Tabel `uploads`

| Kolom Tambahan | Alasan Kenapa TIDAK Tambah | Dampak Jika Ditambah | Bisa Jalan Tanpa? |
|----------------|----------------------------|----------------------|-------------------|
| `photo_size_bytes` (BIGINT) | Tidak ada di API design. Tidak dibutuhkan untuk business logic. Upload validation dilakukan di frontend dan backend layer sebelum simpan ke DB. | - Menambah storage overhead<br>- Tidak memberikan nilai bisnis<br>- API response tidak butuh informasi ini | ✅ **Ya** - Sistem bisa jalan. Size check dilakukan di layer aplikasi, bukan di database. |
| `photo_filename` (VARCHAR) | Dokumen hanya menyimpan `url_foto` sebagai reference ke Cloud Storage. Filename tidak kritis untuk business logic. | - Menambah storage overhead<br>- Jika filename berubah di cloud, data DB jadi tidak akurat | ✅ **Ya** - Sistem bisa jalan. Filename tidak dibutuhkan untuk klasifikasi, poin, atau reward. |
| `classification_status` → `status_proses` | ✅ **SUDAH DIPERBAIKI** sesuai dokumen (status_proses) | N/A | N/A |
| `processed_at` (TIMESTAMP) | Tidak ada di dokumen. Tidak dibutuhkan untuk business logic. Waktu klasifikasi sudah tersimpan di `classification_results.waktu_proses`. | - Redundant data<br>- Potential inconsistency antara `uploads.processed_at` dan `classification_results.waktu_proses` | ✅ **Ya** - Sistem bisa jalan. Waktu klasifikasi tersimpan di tabel classification_results. |
| `is_valid` (BOOLEAN) | ✅ **SUDAH ADA** di `classification_results.is_valid`. Tidak perlu duplikat di `uploads`. | - Data redundancy<br>- Potential inconsistency jika `is_valid` di uploads vs classification_results berbeda | ✅ **Ya** - Sistem bisa jalan. Validitas disimpan di classification_results. |
| `poin_awarded` (INTEGER) | Poin dihitung otomatis dari `classification_results.confidence_score` dan `is_valid`. Tidak perlu simpan manual. | - Data redundancy<br>- Risk of manual error jika admin/edit poin_awarded secara manual | ✅ **Ya** - Sistem bisa jalan. Poin dihitung dari classification_results. |

### 3. Tabel `classification_results`

| Kolom Tambahan | Alasan Kenapa TIDAK Tambah | Dampak Jika Ditambah | Bisa Jalan Tanpa? |
|----------------|----------------------------|----------------------|-------------------|
| `model_version` (VARCHAR) | Tidak ada di dokumen. Tidak dibutuhkan untuk business logic. Versioning model bisa dihandle di ML service layer. | - Menambah storage overhead<br>- Tidak memberikan nilai bisnis di application layer | ✅ **Ya** - Sistem bisa jalan. Model versioning bisa dilakukan di ML service. |
| `processing_time_ms` (INTEGER) | Tidak ada di dokumen. Monitoring ML performance bisa dilakukan di ML service layer, bukan di application DB. | - Menambah storage overhead<br>- Tidak dibutuhkan untuk API response atau business logic | ✅ **Ya** - Sistem bisa jalan. Processing time monitoring bisa di ML service. |
| `created_at` → `waktu_proses` | ✅ **SUDAH DIPERBAIKI** sesuai dokumen (waktu_proses) | N/A | N/A |
| `confidence_score` NUMERIC(5,2) → NUMERIC(4,3) | ✅ **SUDAH DIPERBAIKI** sesuai dokumen (0.000-1.000) | N/A | N/A |
| `kategori_sampah` tanpa 'tidak_dikenal' → dengan 'tidak_dikenal' | ✅ **SUDAH DIPERBAIKI** sesuai dokumen (organik, anorganik, residu, tidak_dikenal) | N/A | N/A |

### 4. Tabel `rewards`

| Kolom Tambahan | Alasan Kenapa TIDAK Tambah | Dampak Jika Ditambah | Bisa Jalan Tanpa? |
|----------------|----------------------------|----------------------|-------------------|
| `stok_tersedia` → `stok` | ✅ **SUDAH DIPERBAIKI** sesuai dokumen (stok) | N/A | N/A |
| `jenis_reward` (VARCHAR) | Tidak ada di dokumen. Jenis reward tidak dibutuhkan untuk business logic. Semua reward dihandle sama. | - Menambah storage overhead<br>- Menambah kompleksitas logic tanpa benefit | ✅ **Ya** - Sistem bisa jalan. Tidak ada business logic berdasarkan jenis reward. |
| `status_reward` (VARCHAR) | Tidak ada di dokumen. Menggunakan `is_active` untuk menentukan ketersediaan reward. | - Redundant column<br>- Potential inconsistency jika `status_reward='inactive'` tapi `is_active=TRUE` | ✅ **Ya** - Sistem bisa jalan. `is_active` sudah cukup untuk control reward availability. |
| `tanggal_berlaku_mulai` (DATE) | Tidak ada di dokumen. Hanya `masa_berlaku` (end date) yang dibutuhkan. | - Redundant column<br>- Menambah complexity validasi tanpa benefit | ✅ **Ya** - Sistem bisa jalan. Hanya end date yang dibutuhkan untuk validasi. |
| `tanggal_berlaku_akhir` → `masa_berlaku` | ✅ **SUDAH DIPERBAIKI** sesuai dokumen (masa_berlaku) | N/A | N/A |

### 5. Tabel `reward_redemptions`

| Kolom Tambahan | Alasan Kenapa TIDAK Tambah | Dampak Jika Ditambah | Bisa Jalan Tanpa? |
|----------------|----------------------------|----------------------|-------------------|
| `redemption_id` → `id_penukaran` | ✅ **SUDAH DIPERBAIKI** sesuai dokumen (id_penukaran) | N/A | N/A |
| `poin_terpakai` (INTEGER) | Tidak ada di dokumen. Poin sudah tercatat di `point_transactions` dengan `jenis_transaksi='pengurangan'`. | - Redundant data<br>- Risk of inconsistency jika `poin_terpakai` tidak sinkron dengan `point_transactions` | ✅ **Ya** - Sistem bisa jalan. Poin tracking di point_transactions sudah cukup. |
| `status` = 'pending', 'completed', 'expired', 'cancelled' → 'aktif', 'terpakai', 'kedaluwarsa' | ✅ **SUDAH DIPERBAIKI** sesuai dokumen | N/A | N/A |
| `used_at` (TIMESTAMP) | Tidak ada di dokumen. Status 'terpakai' sudah cukup, tidak perlu waktu spesifik. | - Redundant column<br>- Tidak memberikan nilai bisnis | ✅ **Ya** - Sistem bisa jalan. Waktu penggunaan tidak kritis. |
| `expired_at` (TIMESTAMP) | Tidak ada di dokumen. Status 'kedaluwarsa' sudah cukup, tidak perlu waktu spesifik. | - Redundant column<br>- Tidak memberikan nilai bisnis | ✅ **Ya** - Sistem bisa jalan. Waktu kedaluwarsa tidak kritis. |
| `catatan` (TEXT) | Tidak ada di dokumen. Tidak dibutuhkan untuk business logic. | - Redundant column<br>- Menambah kompleksitas tanpa benefit | ✅ **Ya** - Sistem bisa jalan. Catatan tidak dibutuhkan. |
| `created_at` → `tanggal_penukaran` | ✅ **SUDAH DIPERBAIKI** sesuai dokumen (tanggal_penukaran) | N/A | N/A |

### 6. Tabel `point_transactions`

| Kolom Tambahan | Alasan Kenapa TIDAK Tambah | Dampak Jika Ditambah | Bisa Jalan Tanpa? |
|----------------|----------------------------|----------------------|-------------------|
| `transaction_id` → `id_transaksi` | ✅ **SUDAH DIPERBAIKI** sesuai dokumen (id_transaksi) | N/A | N/A |
| `upload_id` (UUID FK) | ✅ **SUDAH DIPERBAIKI** sesuai dokumen (`id_referensi` nullable yang bisa ke upload atau redemption) | N/A | N/A |
| `jumlah_poin` CHECK >= 0 → > 0 | ✅ **SUDAH DIPERBAIKI** sesuai dokumen (CHECK > 0) | N/A | N/A |
| `tipe_transaksi` → `jenis_transaksi` | ✅ **SUDAH DIPERBAIKI** sesuai dokumen (jenis_transaksi) | N/A | N/A |
| `tipe_transaksi` values: 'classification', 'reward_redemption', 'bonus', 'penalty' → 'penambahan', 'pengurangan' | ✅ **SUDAH DIPERBAIKI** sesuai dokumen | N/A | N/A |
| `balance_before` (INTEGER) | Tidak ada di dokumen. Balance tracking bisa dilakukan di application layer. | - Redundant column<br>- Risk of inconsistency jika balance tidak akurat | ✅ **Ya** - Sistem bisa jalan. Balance tracking di layer aplikasi. |
| `balance_after` (INTEGER) | Tidak ada di dokumen. Balance tracking bisa dilakukan di application layer. | - Redundant column<br>- Risk of inconsistency jika balance tidak akurat | ✅ **Ya** - Sistem bisa jalan. Balance tracking di layer aplikasi. |

### 7. Tabel `education_materials`

| Kolom Tambahan | Alasan Kenapa TIDAK Tambah | Dampak Jika Ditambah | Bisa Jalan Tanpa? |
|----------------|----------------------------|----------------------|-------------------|
| `material_id` → `id_edukasi` | ✅ **SUDAH DIPERBAIKI** sesuai dokumen (id_edukasi) | N/A | N/A |
| `gambar_url` → `url_media` | ✅ **SUDAH DIPERBAIKI** sesuai dokumen (url_media) | N/A | N/A |
| `kategori_sampah` nullable → NOT NULL | ✅ **SUDAH DIPERBAIKI** sesuai dokumen (NOT NULL) | N/A | N/A |
| `urutan_ditampilkan` (INTEGER) | Tidak ada di dokumen. Tidak dibutuhkan untuk business logic. Ordering bisa dilakukan di query layer. | - Redundant column<br>- Menambah complexity tanpa benefit | ✅ **Ya** - Sistem bisa jalan. Ordering di handled di application layer. |
| `is_aktif` (BOOLEAN) | Tidak ada di dokumen. Menggunakan `is_active` pada tabel `rewards` untuk control availability. Education materials bisa dihandle dengan soft delete (delete record atau set `konten` kosong). | - Redundant column<br>- Potential inconsistency jika `is_aktif=FALSE` tapi record masih ada | ✅ **Ya** - Sistem bisa jalan. Content management di handled di application layer. |
| `created_at` → `created_at` (TIMESTAMPTZ) | ✅ **SUDAH DIPERBAIKI** sesuai dokumen (TIMESTAMPTZ) | N/A | N/A |
| `updated_at` → `updated_at` (TIMESTAMPTZ) | ✅ **SUDAH DIPERBAIKI** sesuai dokumen (TIMESTAMPTZ) | N/A | N/A |

---

## Kesimpulan

### Apakah Sistem Bisa Jalan Tanpa Kolom Tambahan?

**✅ YES - 100% Sistem Bisa Jalan Tanpa Kolom Tambahan**

Semua kolom yang ditambahkan sebelumnya adalah:
1. **Redundant** - Data sudah tersimpan di tempat lain
2. **Tidak dibutuhkan** - Tidak ada business logic yang mengharuskan kolom tersebut
3. **Menambah complexity** - Risk of inconsistency tanpa benefit

### Prinsip yang Diterapkan:

1. **Konsisten dengan Dokumen RPL** - Schema ini 100% match dengan Data Dictionary di bab 2.4.3
2. **Minimal Schema** - Hanya kolom yang dibutuhkan untuk business logic
3. **Data Integrity** - Tidak ada redundant data yang bisa menyebabkan inconsistency
4. **Clean Architecture** - Business logic di application layer, data di database layer

### Rekomendasi:

- Jangan menambah kolom yang tidak ada di dokumen RPL
- Jika ada requirement baru, update dokumen RPL terlebih dahulu
- Schema change harus didokumentasikan dengan alasan yang jelas

---

**Document Version:** 1.0  
**Created:** 2026-10-20  
**Aligned With:** RPL Technical Document Section 2.4.3 (Data Dictionary)

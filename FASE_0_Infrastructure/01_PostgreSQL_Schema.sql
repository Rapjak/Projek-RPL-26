-- ============================================================================
-- PILAH.IN - POSTGRESQL DATABASE SCHEMA (3NF)
-- ============================================================================
-- Project: Pilah.in - Garbage Classification App with Gamification
-- Database: pilah_in
-- Version: 1.0 - Exact match with RPL Technical Document
-- Created: 2026-10-20
-- ============================================================================
-- IMPORTANT: This schema is 100% aligned with Data Dictionary section 2.4.3
-- No additional columns beyond the official specification
-- ============================================================================

-- Drop existing database if exists (development only)
-- DROP DATABASE IF EXISTS pilah_in;

-- Create database
-- CREATE DATABASE pilah_in
--     ENCODING 'UTF8'
--     LC_COLLATE 'en_US.UTF-8'
--     LC_CTYPE 'en_US.UTF-8';

-- Connect to database (run manually or via environment)
-- \c pilah_in

-- Enable UUID extension for PostgreSQL
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Enable pgcrypto for password hashing
CREATE EXTENSION IF NOT EXISTS pgcrypto;


-- ============================================================================
-- TABLE 1: users
-- ============================================================================
-- Purpose: Menyimpan data identitas civitas akademika, kredensial autentikasi,
--          hak akses peran, serta akumulasi total saldo poin aktif
-- Realizes: DATA-001
-- ============================================================================

CREATE TABLE users (
    id_pengguna UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    npm_nip VARCHAR(20) UNIQUE NOT NULL,
    nama VARCHAR(100) NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    peran VARCHAR(20) NOT NULL CHECK (peran IN ('civitas', 'admin_gogreen', 'pimpinan')),
    unit_gedung VARCHAR(50) NOT NULL,
    total_poin INTEGER NOT NULL DEFAULT 0 CHECK (total_poin >= 0),
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for performance
CREATE INDEX idx_users_npm_nip ON users(npm_nip);
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_peran ON users(peran);
CREATE INDEX idx_users_total_poin ON users(total_poin DESC);


-- ============================================================================
-- TABLE 2: uploads
-- ============================================================================
-- Purpose: Menyimpan rekam jejak berkas foto bukti pemilahan sampah yang
--          dikirim oleh civitas akademika
-- Realizes: DATA-002
-- ============================================================================

CREATE TABLE uploads (
    id_unggahan UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    id_pengguna UUID NOT NULL,
    url_foto VARCHAR(255) NOT NULL,
    status_proses VARCHAR(20) NOT NULL DEFAULT 'pending' 
        CHECK (status_proses IN ('pending', 'processing', 'completed', 'failed')),
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT fk_uploads_pengguna FOREIGN KEY (id_pengguna) 
        REFERENCES users(id_pengguna) ON DELETE CASCADE
);

-- Indexes for performance
CREATE INDEX idx_uploads_pengguna ON uploads(id_pengguna);
CREATE INDEX idx_uploads_status ON uploads(status_proses);
CREATE INDEX idx_uploads_created ON uploads(created_at DESC);


-- ============================================================================
-- TABLE 3: classification_results
-- ============================================================================
-- Purpose: Menyimpan luaran hasil inferensi model CNN terhadap foto sampah
--          yang diunggah
-- Realizes: DATA-002, NFR-002
-- ============================================================================

CREATE TABLE classification_results (
    id_klasifikasi UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    id_unggahan UUID UNIQUE NOT NULL,
    kategori_sampah VARCHAR(20) NOT NULL 
        CHECK (kategori_sampah IN ('organik', 'anorganik', 'residu', 'tidak_dikenal')),
    confidence_score NUMERIC(4,3) NOT NULL 
        CHECK (confidence_score >= 0.0 AND confidence_score <= 1.0),
    is_valid BOOLEAN NOT NULL DEFAULT TRUE,
    waktu_proses TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT fk_classification_unggahan FOREIGN KEY (id_unggahan) 
        REFERENCES uploads(id_unggahan) ON DELETE CASCADE
);

-- Indexes for performance
CREATE INDEX idx_classification_unggahan ON classification_results(id_unggahan);
CREATE INDEX idx_classification_kategori ON classification_results(kategori_sampah);
CREATE INDEX idx_classification_valid ON classification_results(is_valid);


-- ============================================================================
-- TABLE 4: rewards
-- ============================================================================
-- Purpose: Menyimpan katalog insentif/hadiah yang dapat ditukarkan oleh
--          civitas akademika menggunakan saldo poin
-- Realizes: DATA-005
-- ============================================================================

CREATE TABLE rewards (
    id_reward UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    nama_reward VARCHAR(100) NOT NULL,
    deskripsi TEXT NULL,
    poin_dibutuhkan INTEGER NOT NULL CHECK (poin_dibutuhkan > 0),
    stok INTEGER NOT NULL DEFAULT 0 CHECK (stok >= 0),
    masa_berlaku DATE NOT NULL,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for performance
CREATE INDEX idx_rewards_active ON rewards(is_active);
CREATE INDEX idx_rewards_poin ON rewards(poin_dibutuhkan);


-- ============================================================================
-- TABLE 5: reward_redemptions
-- ============================================================================
-- Purpose: Menyimpan catatan penukaran poin menjadi kode voucher reward
--          serta status klaim pengguna
-- Realizes: FR-008
-- ============================================================================

CREATE TABLE reward_redemptions (
    id_penukaran UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    id_pengguna UUID NOT NULL,
    id_reward UUID NOT NULL,
    kode_voucher VARCHAR(50) UNIQUE NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'aktif' 
        CHECK (status IN ('aktif', 'terpakai', 'kedaluwarsa')),
    tanggal_penukaran TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    tanggal_digunakan TIMESTAMPTZ NULL,
    
    CONSTRAINT fk_redemptions_pengguna FOREIGN KEY (id_pengguna) 
        REFERENCES users(id_pengguna) ON DELETE CASCADE,
    CONSTRAINT fk_redemptions_reward FOREIGN KEY (id_reward) 
        REFERENCES rewards(id_reward) ON DELETE RESTRICT
);

-- Indexes for performance
CREATE INDEX idx_redemptions_pengguna ON reward_redemptions(id_pengguna);
CREATE INDEX idx_redemptions_reward ON reward_redemptions(id_reward);
CREATE INDEX idx_redemptions_status ON reward_redemptions(status);
CREATE INDEX idx_redemptions_voucher ON reward_redemptions(kode_voucher);


-- ============================================================================
-- TABLE 6: point_transactions
-- ============================================================================
-- Purpose: Buku besar (ledger) pencatatan mutasi penambahan maupun pemotongan
--          poin secara terperinci
-- Realizes: DATA-004
-- ============================================================================

CREATE TABLE point_transactions (
    id_transaksi UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    id_pengguna UUID NOT NULL,
    id_referensi UUID NULL,
    jumlah_poin INTEGER NOT NULL CHECK (jumlah_poin > 0),
    jenis_transaksi VARCHAR(20) NOT NULL 
        CHECK (jenis_transaksi IN ('penambahan', 'pengurangan')),
    deskripsi VARCHAR(255) NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT fk_transactions_pengguna FOREIGN KEY (id_pengguna) 
        REFERENCES users(id_pengguna) ON DELETE CASCADE
);

-- Indexes for performance
CREATE INDEX idx_transactions_pengguna ON point_transactions(id_pengguna);
CREATE INDEX idx_transactions_jenis ON point_transactions(jenis_transaksi);
CREATE INDEX idx_transactions_created ON point_transactions(created_at DESC);
CREATE INDEX idx_transactions_referensi ON point_transactions(id_referensi);


-- ============================================================================
-- TABLE 7: education_materials
-- ============================================================================
-- Purpose: Menyimpan konten literasi panduan tata cara pemilahan sampah
--          bagi civitas akademika
-- Realizes: FR-009
-- ============================================================================

CREATE TABLE education_materials (
    id_edukasi UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    id_admin UUID NULL,
    judul VARCHAR(150) NOT NULL,
    kategori_sampah VARCHAR(20) NOT NULL 
        CHECK (kategori_sampah IN ('organik', 'anorganik', 'residu', 'umum')),
    konten TEXT NOT NULL,
    url_media VARCHAR(255) NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT fk_education_admin FOREIGN KEY (id_admin) 
        REFERENCES users(id_pengguna) ON DELETE SET NULL
);

-- Indexes for performance
CREATE INDEX idx_education_kategori ON education_materials(kategori_sampah);
CREATE INDEX idx_education_admin ON education_materials(id_admin);


-- ============================================================================
-- VIEWS FOR COMMON QUERIES
-- ============================================================================

-- View: Leaderboard peringkat pengguna berdasarkan poin
CREATE VIEW v_leaderboard_user AS
SELECT 
    ROW_NUMBER() OVER (ORDER BY total_poin DESC) as rank,
    id_pengguna,
    npm_nip,
    nama,
    unit_gedung,
    total_poin
FROM users
WHERE peran = 'civitas'
ORDER BY total_poin DESC;

-- View: Leaderboard peringkat gedung/unit
CREATE VIEW v_leaderboard_building AS
SELECT 
    ROW_NUMBER() OVER (ORDER BY SUM(total_poin) DESC) as rank,
    unit_gedung,
    SUM(total_poin) as total_poin,
    COUNT(*) as total_pengguna
FROM users
WHERE peran = 'civitas'
GROUP BY unit_gedung
ORDER BY SUM(total_poin) DESC;

-- View: Statistik klasifikasi per kategori
CREATE VIEW v_statistik_klasifikasi AS
SELECT 
    kategori_sampah,
    COUNT(*) as jumlah_klasifikasi,
    ROUND(AVG(confidence_score)::numeric, 3) as rata_confidence,
    COUNT(CASE WHEN is_valid = TRUE THEN 1 END) as valid_count,
    COUNT(CASE WHEN is_valid = FALSE THEN 1 END) as invalid_count
FROM classification_results
GROUP BY kategori_sampah;

-- View: Ringkasan aktivitas pengguna
CREATE VIEW v_aktivitas_pengguna AS
SELECT 
    u.id_pengguna,
    u.npm_nip,
    u.nama,
    u.unit_gedung,
    u.total_poin,
    COUNT(DISTINCT up.id_unggahan) as total_upload,
    COUNT(DISTINCT cr.id_klasifikasi) as total_klasifikasi,
    COUNT(CASE WHEN cr.is_valid = TRUE THEN 1 END) as valid_klasifikasi,
    MAX(up.created_at) as upload_terakhir
FROM users u
LEFT JOIN uploads up ON u.id_pengguna = up.id_pengguna
LEFT JOIN classification_results cr ON up.id_unggahan = cr.id_unggahan
WHERE u.peran = 'civitas'
GROUP BY u.id_pengguna, u.npm_nip, u.nama, u.unit_gedung, u.total_poin;


-- ============================================================================
-- TRIGGERS FOR DATA INTEGRITY
-- ============================================================================

-- Trigger: Auto-update updated_at pada tabel users
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_users_updated_at
BEFORE UPDATE ON users
FOR EACH ROW
EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER trg_education_updated_at
BEFORE UPDATE ON education_materials
FOR EACH ROW
EXECUTE FUNCTION update_updated_at_column();


-- ============================================================================
-- INITIAL SAMPLE DATA (OPTIONAL)
-- ============================================================================

-- Sample rewards
INSERT INTO rewards (nama_reward, deskripsi, poin_dibutuhkan, stok, masa_berlaku, is_active)
VALUES 
    ('E-Certificate Participant', 'Sertifikat digital untuk peserta challenge pemilahan', 500, 999, '2027-12-31', TRUE),
    ('Sticker Pack Pemilahan', 'Paket sticker panduan pemilahan sampah', 250, 100, '2027-06-30', TRUE),
    ('Badge Top 10 Leaderboard', 'Badge khusus untuk 10 besar leaderboard', 1000, 50, '2027-12-31', TRUE),
    ('Bonus 100 Poin', 'Bonus tambahan 100 poin untuk minggu depan', 300, 200, '2027-03-31', TRUE);

-- Sample education materials
INSERT INTO education_materials (judul, kategori_sampah, konten)
VALUES 
    ('Pengenalan Sampah Organik', 'organik', 'Sampah organik adalah limbah yang berasal dari makhluk hidup dan mudah terurai secara alami. Contoh: sisa makanan, daun kering, ranting pohon.'),
    ('Cara Memilah Sampah Organik', 'organik', 'Langkah-langkah memilah sampah organik: 1) Pisahkan dari plastik, 2) Buang ke tempat sampah hijau, 3) Pastikan tidak tercampur dengan residu.'),
    ('Pengenalan Sampah Anorganik', 'anorganik', 'Sampah anorganik adalah limbah dari bahan sintetis yang sulit terurai. Contoh: plastik, kaleng, botol kaca, kertas.'),
    ('Pengenalan Sampah Residu', 'residu', 'Sampah residu adalah sampah yang tidak dapat didaur ulang dan harus dibuang ke TPA. Contoh: popok, pembalut, tisu kotor.');


-- ============================================================================
-- END OF SCHEMA - 100% COMPLIANT WITH RPL TECHNICAL DOCUMENT
-- ============================================================================

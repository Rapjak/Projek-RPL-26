-- ============================================================
-- Pilah.in — Database Viewer Queries
-- Jalankan via:
--   docker exec -it pilah_postgres psql -U postgres -d pilah_in -f /dev/stdin < db_view.sql
-- atau salin-tempel ke pgAdmin / DBeaver.
-- ============================================================

\echo '==================== RINGKASAN JUMLAH BARIS ===================='
SELECT 'users'                  AS tabel, COUNT(*) AS jumlah FROM users
UNION ALL SELECT 'uploads',              COUNT(*) FROM uploads
UNION ALL SELECT 'classification_results', COUNT(*) FROM classification_results
UNION ALL SELECT 'rewards',              COUNT(*) FROM rewards
UNION ALL SELECT 'reward_redemptions',   COUNT(*) FROM reward_redemptions
UNION ALL SELECT 'point_transactions',   COUNT(*) FROM point_transactions
UNION ALL SELECT 'education_materials',  COUNT(*) FROM education_materials
UNION ALL SELECT 'token_blacklist_outstandingtoken', COUNT(*) FROM token_blacklist_outstandingtoken
ORDER BY tabel;

\echo ''
\echo '==================== USERS ===================='
SELECT id, npm_nip, name, email, role, unit_gedung, total_poin, is_active, created_at
FROM users ORDER BY created_at DESC LIMIT 20;

\echo ''
\echo '==================== UPLOADS (foto yang diunggah) ===================='
SELECT u.id, us.name AS pengguna, u.file, u.file_size, u.status, u.created_at
FROM uploads u JOIN users us ON us.id = u.id_pengguna
ORDER BY u.created_at DESC LIMIT 20;

\echo ''
\echo '==================== CLASSIFICATION_RESULTS ===================='
SELECT
  cr.id,
  us.name AS pengguna,
  cr.kategori_sampah,
  cr.confidence_score,
  cr.is_valid,
  cr.points_awarded,
  cr.waktu_proses
FROM classification_results cr
JOIN uploads u ON u.id = cr.id_unggahan
JOIN users us ON us.id = u.id_pengguna
ORDER BY cr.waktu_proses DESC LIMIT 20;

\echo ''
\echo '==================== REWARDS ===================='
SELECT id, name, points_required, stock, masa_berlaku, is_active, created_at
FROM rewards ORDER BY created_at DESC LIMIT 20;

\echo ''
\echo '==================== REWARD_REDEMPTIONS (penukaran) ===================='
SELECT
  rr.id,
  us.name AS pengguna,
  r.name AS reward_name,
  rr.kode_voucher,
  rr.status,
  rr.tanggal_penukaran,
  rr.tanggal_digunakan
FROM reward_redemptions rr
JOIN rewards r ON r.id = rr.id_reward
JOIN users us ON us.id = rr.id_pengguna
ORDER BY rr.tanggal_penukaran DESC LIMIT 20;

\echo ''
\echo '==================== POINT_TRANSACTIONS ===================='
SELECT
  pt.id,
  us.name AS pengguna,
  pt.points,
  pt.transaction_type,
  pt.description,
  pt.reference_id,
  pt.created_at
FROM point_transactions pt
JOIN users us ON us.id = pt.id_pengguna
ORDER BY pt.created_at DESC LIMIT 30;

\echo ''
\echo '==================== EDUCATION_MATERIALS ===================='
SELECT id, judul, kategori_sampah, is_published, created_at
FROM education_materials ORDER BY created_at DESC LIMIT 20;

\echo ''
\echo '==================== LEADERBOARD (per pengguna) ===================='
SELECT name, unit_gedung, total_poin,
       RANK() OVER (ORDER BY total_poin DESC) AS peringkat
FROM users WHERE role='civitas' ORDER BY peringkat LIMIT 10;

\echo ''
\echo '==================== LEADERBOARD (per unit/gedung) ===================='
SELECT unit_gedung, SUM(total_poin) AS total_poin_unit,
       RANK() OVER (ORDER BY SUM(total_poin) DESC) AS peringkat
FROM users WHERE role='civitas'
GROUP BY unit_gedung ORDER BY peringkat LIMIT 10;

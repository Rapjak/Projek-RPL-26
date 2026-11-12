// ============================================================================
// Pilah.in Frontend Types - aligned with backend API-001..API-019
// ============================================================================

export type Role = 'civitas' | 'admin_gogreen' | 'pimpinan';

export type KategoriSampah = 'organik' | 'anorganik' | 'residu' | 'tidak_dikenal';

export type UploadStatus = 'pending' | 'processing' | 'completed' | 'failed';

// ---------------------------------------------------------------------------
// Auth & User
// ---------------------------------------------------------------------------
export interface User {
  user_id: string;
  npm_nip: string;
  name: string;
  email: string;
  peran: Role;
  unit_gedung: string;
  total_poin: number;
}

export interface RegisterRequest {
  npm_nip: string;
  name: string;
  email: string;
  unit_gedung: string;
  password: string;
}

export interface RegisterResponse {
  message: string;
  user_id: string;
  peran: Role;
  user: UserProfile;
}

export interface UserProfile {
  id: string;
  npm_nip: string;
  name: string;
  email: string;
  role: Role;
  unit_gedung: string;
  total_poin: number;
  created_at: string;
  is_active: boolean;
}

export interface LoginRequest {
  identifier: string;
  password: string;
}

export interface LoginResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
  user: User;
}

export interface UserPoints {
  user_id: string;
  total_poin: number;
  rank: number;
}

// ---------------------------------------------------------------------------
// Classifications (Upload + Result)
// ---------------------------------------------------------------------------
export interface UploadAccepted {
  message: string;
  upload_id: string;
  status: UploadStatus;
  url_foto: string;
}

export interface ClassificationPollResponse {
  upload_id: string;
  status: UploadStatus;
  waktu_upload: string;
  kategori?: KategoriSampah;
  confidence?: number;
  is_valid?: boolean;
  deskripsi?: string;
  poin_diperoleh?: number;
  error?: string;
}

export interface ClassificationResult {
  id: string;
  upload: string;
  kategori_sampah: KategoriSampah;
  confidence_score: string;
  is_valid: boolean;
  points_awarded: number;
  handling_instructions: string;
  waktu_proses: string;
}

export interface HistoryItem {
  id: string;
  url_foto: string;
  status: UploadStatus;
  file_size: number;
  created_at: string;
  classification: ClassificationResult | null;
}

export interface HistoryResponse {
  data: HistoryItem[];
  total_unggahan: number;
  total_poin_diperoleh: number;
  total: number;
  page: number;
}

export interface CheckPointsResponse {
  upload_id: string;
  memenuhi_syarat: boolean;
  jumlah_poin: number;
  alasan: string;
}

// ---------------------------------------------------------------------------
// Rewards
// ---------------------------------------------------------------------------
export interface Reward {
  id: string;
  name: string;
  description: string;
  points_required: number;
  ketersediaan: boolean;
  stock: number;
  masa_berlaku: string;
  is_active: boolean;
  image: string | null;
}

export interface RedeemResponse {
  message: string;
  sisa_poin: number;
  kode_reward: string;
  nama_reward: string;
  redemption_id: string;
}

export interface Redemption {
  id: string;
  reward: string;
  nama_reward: string;
  kode_voucher: string;
  status: 'aktif' | 'terpakai' | 'kedaluwarsa';
  tanggal_penukaran: string;
  tanggal_digunakan: string | null;
}

// ---------------------------------------------------------------------------
// Point transactions
// ---------------------------------------------------------------------------
export interface PointTransaction {
  id: string;
  points: number;
  transaction_type: 'penambahan' | 'pengurangan';
  description: string;
  referensi_upload: string | null;
  created_at: string;
}

export interface PointTransactionsResponse {
  data: PointTransaction[];
  total: number;
}

// ---------------------------------------------------------------------------
// Leaderboard
// ---------------------------------------------------------------------------
export interface LeaderboardUserEntry {
  id: string;
  name: string;
  unit_gedung: string;
  total_poin: number;
  rank: number;
}

export interface LeaderboardUserResponse {
  type: 'user';
  data: LeaderboardUserEntry[];
  user_rank: number | null;
  user_poin: number;
  total_peserta: number;
  page: number;
}

export interface LeaderboardBuildingEntry {
  rank: number;
  unit_gedung: string;
  total_poin: number;
}

export interface LeaderboardBuildingResponse {
  type: 'building';
  data: LeaderboardBuildingEntry[];
  user_building_rank: number | null;
  user_building: string;
  page: number;
}

export type LeaderboardResponse = LeaderboardUserResponse | LeaderboardBuildingResponse;

// ---------------------------------------------------------------------------
// Education
// ---------------------------------------------------------------------------
export interface EducationMaterialList {
  id: string;
  judul: string;
  kategori_sampah: 'organik' | 'anorganik' | 'residu' | 'umum';
  ringkasan: string;
  image: string | null;
  created_at: string;
}

export interface EducationMaterial {
  id: string;
  judul: string;
  kategori_sampah: 'organik' | 'anorganik' | 'residu' | 'umum';
  konten: string;
  url_media: string | null;
  image: string | null;
  is_published: boolean;
  created_at: string;
  updated_at: string;
}

// ---------------------------------------------------------------------------
// Admin
// ---------------------------------------------------------------------------
export interface AdminDashboard {
  total_pengguna: number;
  total_upload: number;
  total_upload_hari_ini: number;
  total_poin_terdistribusi: number;
  akurasi_rata_rata: number;
  distribusi_kategori: Record<string, number>;
  tren_mingguan: Array<{ tanggal: string; jumlah: number }>;
}

export interface AdminActivity {
  user_id: string;
  npm_nip: string;
  nama: string;
  unit_gedung: string;
  waktu_upload: string;
  kategori: KategoriSampah | null;
  confidence: number | null;
  poin_diperoleh: number;
}

export interface AdminActivitiesResponse {
  data: AdminActivity[];
  total: number;
  page: number;
}

// ---------------------------------------------------------------------------
// Notifications (frontend)
// ---------------------------------------------------------------------------
export interface Notification {
  id: string;
  type: 'success' | 'error' | 'info' | 'warning';
  message: string;
}

// ---------------------------------------------------------------------------
// API error shape
// ---------------------------------------------------------------------------
export interface ApiErrorBody {
  error?: { code: string; message: string };
  detail?: string;
  [key: string]: unknown;
}

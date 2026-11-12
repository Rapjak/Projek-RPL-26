import { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import { useNotification } from '../context/NotificationContext';
import { Card } from '../components/common/Card';
import { Badge } from '../components/common/Badge';
import { Button } from '../components/common/Button';
import { Spinner } from '../components/common/Spinner';
import { Modal } from '../components/common/Modal';
import { Input } from '../components/common/Input';
import { Select } from '../components/common/Select';
import { adminService } from '../services/admin';
import { rewardService } from '../services/rewards';
import { educationService } from '../services/education';
import type {
  AdminDashboard as DashboardStats,
  AdminActivitiesResponse,
  Reward,
  EducationMaterialList,
} from '../types';

type Tab = 'overview' | 'activities' | 'rewards' | 'education';

interface Paginated<T> {
  count: number;
  next: string | null;
  previous: string | null;
  results: T[];
}

const KATEGORI_BADGE: Record<string, 'success' | 'info' | 'warning' | 'default'> = {
  organik: 'success',
  anorganik: 'info',
  residu: 'warning',
  tidak_dikenal: 'default',
};

export function AdminDashboard() {
  const { user } = useAuth();
  const { addNotification } = useNotification();
  const [tab, setTab] = useState<Tab>('overview');

  // Overview state
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [statsLoading, setStatsLoading] = useState(true);

  // Activities state
  const [activities, setActivities] = useState<AdminActivitiesResponse | null>(null);
  const [activitiesLoading, setActivitiesLoading] = useState(true);

  // Rewards state
  const [rewards, setRewards] = useState<Paginated<Reward> | null>(null);
  const [rewardsLoading, setRewardsLoading] = useState(true);
  const [rewardModal, setRewardModal] = useState<Partial<Reward> | null>(null);
  const [savingReward, setSavingReward] = useState(false);

  // Education state
  const [eduList, setEduList] = useState<Paginated<EducationMaterialList> | null>(null);
  const [eduLoading, setEduLoading] = useState(true);

  useEffect(() => {
    if (tab === 'overview' && !stats) fetchStats();
    if (tab === 'activities' && !activities) fetchActivities();
    if (tab === 'rewards' && !rewards) fetchRewards();
    if (tab === 'education' && !eduList) fetchEducation();
  }, [tab]);

  const fetchStats = async () => {
    setStatsLoading(true);
    try {
      const data = await adminService.getDashboard();
      setStats(data);
    } catch {
      addNotification('error', 'Gagal memuat statistik dashboard');
    } finally {
      setStatsLoading(false);
    }
  };

  const fetchActivities = async () => {
    setActivitiesLoading(true);
    try {
      const data = await adminService.getActivities({ page: 1 });
      setActivities(data);
    } catch {
      addNotification('error', 'Gagal memuat aktivitas');
    } finally {
      setActivitiesLoading(false);
    }
  };

  const fetchRewards = async () => {
    setRewardsLoading(true);
    try {
      const data = await rewardService.list({ page: 1 });
      setRewards(data);
    } catch {
      addNotification('error', 'Gagal memuat reward');
    } finally {
      setRewardsLoading(false);
    }
  };

  const fetchEducation = async () => {
    setEduLoading(true);
    try {
      const data = await educationService.list({ page: 1 });
      setEduList(data);
    } catch {
      addNotification('error', 'Gagal memuat materi edukasi');
    } finally {
      setEduLoading(false);
    }
  };

  // Reward CRUD handlers
  const handleSaveReward = async () => {
    if (!rewardModal) return;
    setSavingReward(true);
    try {
      if (rewardModal.id) {
        await adminService.updateReward(rewardModal.id, rewardModal);
        addNotification('success', 'Reward berhasil diperbarui');
      } else {
        await adminService.createReward(rewardModal);
        addNotification('success', 'Reward berhasil dibuat');
      }
      setRewardModal(null);
      fetchRewards();
    } catch (err: any) {
      addNotification('error', err.response?.data?.error?.message || 'Gagal menyimpan reward');
    } finally {
      setSavingReward(false);
    }
  };

  const handleDeleteReward = async (id: string) => {
    if (!confirm('Hapus reward ini?')) return;
    try {
      await adminService.deleteReward(id);
      addNotification('success', 'Reward dihapus');
      fetchRewards();
    } catch {
      addNotification('error', 'Gagal menghapus reward');
    }
  };

  // Education CRUD
  const handleDeleteEdu = async (id: string) => {
    if (!confirm('Hapus materi edukasi ini?')) return;
    try {
      await adminService.deleteEducation(id);
      addNotification('success', 'Materi dihapus');
      fetchEducation();
    } catch {
      addNotification('error', 'Gagal menghapus materi');
    }
  };

  const TABS: Array<{ key: Tab; label: string }> = [
    { key: 'overview', label: 'Ringkasan' },
    { key: 'activities', label: 'Aktivitas' },
    { key: 'rewards', label: 'Reward' },
    { key: 'education', label: 'Edukasi' },
  ];

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Admin Dashboard</h1>
          <p className="text-gray-600 mt-1">Monitoring & manajemen Pilah.in</p>
        </div>
        <Badge variant="info">Admin: {user?.name}</Badge>
      </div>

      {/* Tabs */}
      <div className="flex gap-2 border-b border-gray-200 overflow-x-auto" role="tablist" aria-label="Admin sections">
        {TABS.map(t => (
          <button
            key={t.key}
            role="tab"
            aria-selected={tab === t.key}
            aria-label={`Admin tab: ${t.label}`}
            onClick={() => setTab(t.key)}
            className={`px-4 py-3 font-medium border-b-2 whitespace-nowrap transition-colors ${
              tab === t.key
                ? 'border-emerald-600 text-emerald-600'
                : 'border-transparent text-gray-600 hover:text-gray-900'
            }`}
          >
            {t.label}
          </button>
        ))}
      </div>

      {/* Overview tab */}
      {tab === 'overview' && (
        statsLoading ? (
          <div className="flex justify-center py-12"><Spinner size="lg" /></div>
        ) : stats ? (
          <div className="space-y-6">
            <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
              <Card className="p-4">
                <p className="text-sm text-gray-500">Total Pengguna</p>
                <p className="text-2xl font-bold text-gray-900">{stats.total_pengguna}</p>
              </Card>
              <Card className="p-4">
                <p className="text-sm text-gray-500">Total Upload</p>
                <p className="text-2xl font-bold text-gray-900">{stats.total_upload}</p>
              </Card>
              <Card className="p-4">
                <p className="text-sm text-gray-500">Upload Hari Ini</p>
                <p className="text-2xl font-bold text-emerald-600">{stats.total_upload_hari_ini}</p>
              </Card>
              <Card className="p-4">
                <p className="text-sm text-gray-500">Poin Terdistribusi</p>
                <p className="text-2xl font-bold text-emerald-600">{stats.total_poin_terdistribusi}</p>
              </Card>
            </div>

            <Card className="p-6">
              <h3 className="font-semibold text-gray-900 mb-4">Distribusi Kategori Sampah</h3>
              {Object.keys(stats.distribusi_kategori).length > 0 ? (
                <div className="space-y-3">
                  {Object.entries(stats.distribusi_kategori).map(([kat, count]) => (
                    <div key={kat} className="flex items-center gap-3">
                      <Badge variant={KATEGORI_BADGE[kat] || 'default'}>{kat}</Badge>
                      <div className="flex-1 bg-gray-100 rounded-full h-2 overflow-hidden">
                        <div
                          className="bg-emerald-500 h-full rounded-full"
                          style={{ width: `${Math.min(100, (count / Math.max(stats.total_upload, 1)) * 100)}%` }}
                        />
                      </div>
                      <span className="text-sm text-gray-700 w-8 text-right">{count}</span>
                    </div>
                  ))}
                </div>
              ) : (
                <p className="text-gray-500 text-sm">Belum ada data klasifikasi.</p>
              )}
            </Card>

            <Card className="p-6">
              <h3 className="font-semibold text-gray-900 mb-2">Akurasi Rata-rata Model</h3>
              <p className="text-3xl font-bold text-emerald-600">
                {(stats.akurasi_rata_rata * 100).toFixed(1)}%
              </p>
            </Card>
          </div>
        ) : (
          <Card className="text-center py-12">
            <p className="text-gray-500">Gagal memuat statistik</p>
          </Card>
        )
      )}

      {/* Activities tab */}
      {tab === 'activities' && (
        activitiesLoading ? (
          <div className="flex justify-center py-12"><Spinner size="lg" /></div>
        ) : activities && activities.data.length > 0 ? (
          <Card className="overflow-hidden">
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Nama</th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">NPM/NIP</th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Unit</th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Kategori</th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Confidence</th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Poin</th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Waktu</th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {activities.data.map((a, i) => (
                    <tr key={i} className="hover:bg-gray-50">
                      <td className="px-4 py-3 text-sm text-gray-900">{a.nama}</td>
                      <td className="px-4 py-3 text-sm text-gray-600">{a.npm_nip}</td>
                      <td className="px-4 py-3 text-sm text-gray-600">{a.unit_gedung}</td>
                      <td className="px-4 py-3">
                        {a.kategori ? (
                          <Badge variant={KATEGORI_BADGE[a.kategori] || 'default'}>{a.kategori}</Badge>
                        ) : <span className="text-gray-400">-</span>}
                      </td>
                      <td className="px-4 py-3 text-sm text-gray-600">
                        {a.confidence != null ? `${(a.confidence * 100).toFixed(0)}%` : '-'}
                      </td>
                      <td className="px-4 py-3 text-sm font-medium text-emerald-600">{a.poin_diperoleh}</td>
                      <td className="px-4 py-3 text-sm text-gray-500">
                        {new Date(a.waktu_upload).toLocaleString('id-ID', { dateStyle: 'short', timeStyle: 'short' })}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </Card>
        ) : (
          <Card className="text-center py-12">
            <p className="text-gray-500">Belum ada aktivitas</p>
          </Card>
        )
      )}

      {/* Rewards tab */}
      {tab === 'rewards' && (
        <>
          <div className="flex justify-end">
            <Button
              onClick={() => setRewardModal({
                name: '', description: '', points_required: 10, stock: 10,
                masa_berlaku: new Date(Date.now() + 30 * 86400000).toISOString().split('T')[0],
                is_active: true,
              })}
              className="bg-emerald-600 hover:bg-emerald-700"
            >
              + Tambah Reward
            </Button>
          </div>

          {rewardsLoading ? (
            <div className="flex justify-center py-12"><Spinner size="lg" /></div>
          ) : rewards && rewards.results.length > 0 ? (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {rewards.results.map(r => (
                <Card key={r.id} className="p-4">
                  <div className="flex justify-between">
                    <div>
                      <h4 className="font-semibold text-gray-900">{r.name}</h4>
                      <p className="text-xs text-gray-600 mt-1">{r.description}</p>
                      <p className="text-sm text-emerald-600 font-bold mt-2">{r.points_required} poin</p>
                      <p className="text-xs text-gray-500">Stok: {r.stock} · Berlaku: {r.masa_berlaku}</p>
                    </div>
                    <div className="flex flex-col gap-2">
                      <Button size="sm" variant="outline" onClick={() => setRewardModal(r)}>Edit</Button>
                      <Button size="sm" variant="outline" className="border-red-300 text-red-600" onClick={() => handleDeleteReward(r.id)}>Hapus</Button>
                    </div>
                  </div>
                </Card>
              ))}
            </div>
          ) : (
            <Card className="text-center py-12">
              <p className="text-gray-500">Belum ada reward</p>
            </Card>
          )}
        </>
      )}

      {/* Education tab */}
      {tab === 'education' && (
        <>
          <div className="flex justify-end">
            <Button
              onClick={() => addNotification('info', 'Gunakan form admin Django /admin/ untuk membuat materi baru')}
              className="bg-emerald-600 hover:bg-emerald-700"
            >
              + Tambah Materi
            </Button>
          </div>

          {eduLoading ? (
            <div className="flex justify-center py-12"><Spinner size="lg" /></div>
          ) : eduList && eduList.results.length > 0 ? (
            <div className="space-y-3">
              {eduList.results.map(m => (
                <Card key={m.id} className="p-4">
                  <div className="flex justify-between">
                    <div>
                      <h4 className="font-semibold text-gray-900">{m.judul}</h4>
                      <p className="text-sm text-gray-600 mt-1">{m.ringkasan}</p>
                      <Badge variant={KATEGORI_BADGE[m.kategori_sampah] || 'default'} className="mt-2">
                        {m.kategori_sampah}
                      </Badge>
                    </div>
                    <Button size="sm" variant="outline" className="border-red-300 text-red-600" onClick={() => handleDeleteEdu(m.id)}>
                      Hapus
                    </Button>
                  </div>
                </Card>
              ))}
            </div>
          ) : (
            <Card className="text-center py-12">
              <p className="text-gray-500">Belum ada materi edukasi</p>
            </Card>
          )}
        </>
      )}

      {/* Reward create/edit modal */}
      {rewardModal && (
        <Modal
          isOpen={true}
          onClose={() => setRewardModal(null)}
          title={rewardModal.id ? 'Edit Reward' : 'Tambah Reward'}
          size="lg"
        >
          <div className="space-y-4">
            <Input
              label="Nama Reward"
              value={rewardModal.name || ''}
              onChange={(e) => setRewardModal({ ...rewardModal, name: e.target.value })}
            />
            <Input
              label="Deskripsi"
              value={rewardModal.description || ''}
              onChange={(e) => setRewardModal({ ...rewardModal, description: e.target.value })}
            />
            <div className="grid grid-cols-2 gap-4">
              <Input
                label="Poin Dibutuhkan"
                type="number"
                value={String(rewardModal.points_required ?? 0)}
                onChange={(e) => setRewardModal({ ...rewardModal, points_required: parseInt(e.target.value) || 0 })}
              />
              <Input
                label="Stok"
                type="number"
                value={String(rewardModal.stock ?? 0)}
                onChange={(e) => setRewardModal({ ...rewardModal, stock: parseInt(e.target.value) || 0 })}
              />
            </div>
            <Input
              label="Masa Berlaku"
              type="date"
              value={rewardModal.masa_berlaku?.split('T')[0] || ''}
              onChange={(e) => setRewardModal({ ...rewardModal, masa_berlaku: e.target.value })}
            />
            <Select
              label="Status"
              value={rewardModal.is_active ? 'true' : 'false'}
              onChange={(e) => setRewardModal({ ...rewardModal, is_active: e.target.value === 'true' })}
            >
              <option value="true">Aktif</option>
              <option value="false">Nonaktif</option>
            </Select>
            <div className="flex gap-3 pt-4">
              <Button variant="outline" className="flex-1 border-gray-300" onClick={() => setRewardModal(null)}>
                Batal
              </Button>
              <Button className="flex-1 bg-emerald-600 hover:bg-emerald-700" loading={savingReward} onClick={handleSaveReward}>
                Simpan
              </Button>
            </div>
          </div>
        </Modal>
      )}
    </div>
  );
}

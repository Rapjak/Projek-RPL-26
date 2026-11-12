import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { Card } from '../components/common/Card';
import { Badge } from '../components/common/Badge';
import { Button } from '../components/common/Button';
import { useNotification } from '../context/NotificationContext';
import { Spinner } from '../components/common/Spinner';
import { classificationService } from '../services/classifications';
import { authService } from '../services/auth';
import { mediaBaseURL } from '../services/api';
import type { HistoryItem, UserPoints } from '../types';

const STATUS_BADGE: Record<string, 'success' | 'warning' | 'error' | 'default'> = {
  completed: 'success',
  processing: 'warning',
  pending: 'warning',
  failed: 'error',
};
const STATUS_LABEL: Record<string, string> = {
  completed: 'Selesai',
  processing: 'Diproses',
  pending: 'Menunggu',
  failed: 'Gagal',
};
const KATEGORI_LABEL: Record<string, string> = {
  organik: 'Organik',
  anorganik: 'Anorganik',
  residu: 'Residu',
  tidak_dikenal: 'Tidak Dikenal',
};

export function Dashboard() {
  const { user } = useAuth();
  const { addNotification } = useNotification();
  const navigate = useNavigate();
  const [recent, setRecent] = useState<HistoryItem[]>([]);
  const [points, setPoints] = useState<UserPoints | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchDashboardData();
  }, []);

  const fetchDashboardData = async () => {
    try {
      const [historyResp, pointsResp] = await Promise.all([
        classificationService.listHistory({ page: 1 }),
        authService.getPoints().catch(() => null),
      ]);
      setRecent((historyResp.data || []).slice(0, 3));
      if (pointsResp) setPoints(pointsResp);
    } catch (err: any) {
      addNotification('error', 'Gagal memuat data dashboard');
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <Spinner size="lg" />
      </div>
    );
  }

  const totalPoin = points?.total_poin ?? user?.total_poin ?? 0;

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-gray-900">Halo, {user?.name}!</h1>
        <p className="text-gray-600 mt-1">Kelola sampah Anda dan kumpulkan poin</p>
      </div>

      <Card className="bg-gradient-to-br from-emerald-50 to-emerald-100 border-emerald-200 p-6">
        <div className="text-center">
          <p className="text-sm text-emerald-700 font-medium">Total Poin</p>
          <p className="text-4xl font-bold text-emerald-600 mt-2">
            {totalPoin.toLocaleString('id-ID')}
          </p>
          {points && (
            <p className="text-xs text-emerald-600 mt-2">Peringkat #{points.rank} di antara civitas</p>
          )}
        </div>
      </Card>

      <Button
        onClick={() => navigate('/upload')}
        className="w-full bg-emerald-600 hover:bg-emerald-700 text-white font-semibold py-3 rounded-lg"
      >
        Unggah Foto Sampah
      </Button>

      <div>
        <div className="flex justify-between items-center mb-4">
          <h2 className="text-lg font-semibold text-gray-900">Aktivitas Terkini</h2>
          <button
            onClick={() => navigate('/history')}
            className="text-sm text-emerald-600 hover:text-emerald-700 font-medium"
          >
            Lihat semua
          </button>
        </div>

        {recent.length === 0 ? (
          <Card className="text-center py-8">
            <p className="text-gray-500">Belum ada aktivitas. Mulai dengan mengunggah foto!</p>
          </Card>
        ) : (
          <div className="space-y-3">
            {recent.map((activity) => (
              <Card key={activity.id} className="p-4">
                <div className="flex items-center gap-4">
                  {activity.url_foto && (
                    <div className="w-16 h-16 bg-gray-200 rounded-lg flex-shrink-0 overflow-hidden">
                      <img
                        src={`${mediaBaseURL}${activity.url_foto}`}
                        alt="upload"
                        className="w-full h-full object-cover"
                      />
                    </div>
                  )}
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center justify-between">
                      <p className="font-medium text-gray-900 truncate">
                        {activity.classification
                          ? KATEGORI_LABEL[activity.classification.kategori_sampah] || 'Sampah'
                          : 'Foto Sampah'}
                      </p>
                      <Badge variant={STATUS_BADGE[activity.status] || 'default'}>
                        {STATUS_LABEL[activity.status] || activity.status}
                      </Badge>
                    </div>
                    <p className="text-xs text-gray-500 mt-1">
                      {new Date(activity.created_at).toLocaleDateString('id-ID', {
                        weekday: 'short',
                        year: 'numeric',
                        month: 'short',
                        day: 'numeric',
                        hour: '2-digit',
                        minute: '2-digit',
                      })}
                    </p>
                  </div>
                </div>
              </Card>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

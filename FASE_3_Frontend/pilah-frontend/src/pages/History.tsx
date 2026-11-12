import { useState, useEffect } from 'react';
import { useNotification } from '../context/NotificationContext';
import { Card } from '../components/common/Card';
import { Badge } from '../components/common/Badge';
import { Spinner } from '../components/common/Spinner';
import { classificationService } from '../services/classifications';
import { mediaBaseURL } from '../services/api';
import type { HistoryResponse } from '../types';

const KATEGORI_BADGE: Record<string, 'success' | 'info' | 'warning' | 'default'> = {
  organik: 'success',
  anorganik: 'info',
  residu: 'warning',
  tidak_dikenal: 'default',
};
const KATEGORI_LABEL: Record<string, string> = {
  organik: 'Organik',
  anorganik: 'Anorganik',
  residu: 'Residu',
  tidak_dikenal: 'Tidak Dikenal',
};

export function History() {
  const { addNotification } = useNotification();
  const [data, setData] = useState<HistoryResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [activeFilter, setActiveFilter] = useState<string>('semua');
  const [page, setPage] = useState(1);

  useEffect(() => {
    fetchHistory();
  }, [page, activeFilter]);

  const fetchHistory = async () => {
    setLoading(true);
    try {
      const resp = await classificationService.listHistory({
        page,
        kategori: activeFilter !== 'semua' ? activeFilter : undefined,
      });
      setData(resp);
    } catch (err) {
      addNotification('error', 'Gagal memuat riwayat');
    } finally {
      setLoading(false);
    }
  };

  if (loading && !data) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <Spinner size="lg" />
      </div>
    );
  }

  const items = data?.data || [];
  const total = data?.total || 0;

  return (
    <div className="space-y-6">
      <h2 className="text-2xl font-bold text-gray-900">Riwayat Aktivitas</h2>

      {data && (
        <div className="grid grid-cols-2 gap-3">
          <Card className="p-4 bg-emerald-50 border-emerald-200">
            <p className="text-xs text-emerald-700">Total Unggahan</p>
            <p className="text-2xl font-bold text-emerald-700">{data.total_unggahan}</p>
          </Card>
          <Card className="p-4 bg-emerald-50 border-emerald-200">
            <p className="text-xs text-emerald-700">Total Poin Diperoleh</p>
            <p className="text-2xl font-bold text-emerald-700">{data.total_poin_diperoleh}</p>
          </Card>
        </div>
      )}

      <div className="flex gap-2 overflow-x-auto pb-2">
        {['semua', 'organik', 'anorganik', 'residu'].map((filter) => (
          <button
            key={filter}
            onClick={() => { setActiveFilter(filter); setPage(1); }}
            className={`px-4 py-2 rounded-full text-sm font-medium whitespace-nowrap transition-colors ${
              activeFilter === filter
                ? 'bg-emerald-600 text-white'
                : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
            }`}
          >
            {filter.charAt(0).toUpperCase() + filter.slice(1)}
          </button>
        ))}
      </div>

      {items.length > 0 ? (
        <>
          <div className="space-y-3">
            {items.map((item) => {
              const kategori = item.classification?.kategori_sampah || 'tidak_dikenal';
              const poin = item.classification?.points_awarded || 0;
              return (
                <Card key={item.id} className="p-4">
                  <div className="flex items-center gap-4">
                    <div className="w-16 h-16 bg-gray-100 rounded-lg flex-shrink-0 overflow-hidden">
                      {item.url_foto && (
                        <img
                          src={`${mediaBaseURL}${item.url_foto}`}
                          alt="upload"
                          className="w-full h-full object-cover"
                        />
                      )}
                    </div>
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center justify-between gap-2">
                        <p className="font-medium text-gray-900 truncate">
                          {KATEGORI_LABEL[kategori]}
                        </p>
                        <Badge variant={KATEGORI_BADGE[kategori]}>
                          {KATEGORI_LABEL[kategori]}
                        </Badge>
                      </div>
                      <p className="text-xs text-gray-500 mt-1">
                        {new Date(item.created_at).toLocaleDateString('id-ID', {
                          weekday: 'short',
                          year: 'numeric',
                          month: 'short',
                          day: 'numeric',
                          hour: '2-digit',
                          minute: '2-digit',
                        })}
                      </p>
                      {poin > 0 && <p className="text-xs text-emerald-600 mt-1">+{poin} poin</p>}
                    </div>
                  </div>
                </Card>
              );
            })}
          </div>

          {total > 10 && (
            <div className="flex justify-center gap-2">
              <button
                onClick={() => setPage(p => Math.max(1, p - 1))}
                disabled={page === 1}
                className="px-4 py-2 bg-white border border-gray-300 rounded-lg disabled:opacity-50 text-sm"
              >
                Sebelumnya
              </button>
              <span className="px-4 py-2 text-sm text-gray-700">
                Hal {page} dari {Math.ceil(total / 10)}
              </span>
              <button
                onClick={() => setPage(p => p + 1)}
                disabled={page * 10 >= total}
                className="px-4 py-2 bg-white border border-gray-300 rounded-lg disabled:opacity-50 text-sm"
              >
                Selanjutnya
              </button>
            </div>
          )}
        </>
      ) : (
        <Card className="text-center py-12">
          <p className="text-gray-500">Belum ada riwayat aktivitas.</p>
        </Card>
      )}
    </div>
  );
}

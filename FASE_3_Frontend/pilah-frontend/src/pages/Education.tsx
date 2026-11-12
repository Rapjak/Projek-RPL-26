import { useState, useEffect } from 'react';
import { useNotification } from '../context/NotificationContext';
import { Card } from '../components/common/Card';
import { Badge } from '../components/common/Badge';
import { Spinner } from '../components/common/Spinner';
import { educationService } from '../services/education';
import { mediaBaseURL } from '../services/api';
import type { EducationMaterial, EducationMaterialList } from '../types';

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
  umum: 'default',
};
const KATEGORI_LABEL: Record<string, string> = {
  organik: 'Organik',
  anorganik: 'Anorganik',
  residu: 'Residu',
  umum: 'Umum',
};

export function Education() {
  const { addNotification } = useNotification();
  const [materials, setMaterials] = useState<Paginated<EducationMaterialList> | null>(null);
  const [loading, setLoading] = useState(true);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [detail, setDetail] = useState<EducationMaterial | null>(null);
  const [detailLoading, setDetailLoading] = useState(false);
  const [activeCategory, setActiveCategory] = useState<string>('semua');

  useEffect(() => {
    fetchMaterials();
  }, []);

  const fetchMaterials = async () => {
    try {
      const data = await educationService.list({ page: 1 });
      setMaterials(data);
    } catch (error) {
      addNotification('error', 'Gagal memuat materi edukasi');
    } finally {
      setLoading(false);
    }
  };

  const openDetail = async (id: string) => {
    setSelectedId(id);
    setDetailLoading(true);
    try {
      const m = await educationService.getById(id);
      setDetail(m);
    } catch {
      addNotification('error', 'Gagal memuat detail materi');
      setSelectedId(null);
    } finally {
      setDetailLoading(false);
    }
  };

  const filteredMaterials = materials?.results.filter((m) => {
    if (activeCategory === 'semua') return true;
    return m.kategori_sampah === activeCategory;
  });

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <Spinner size="lg" />
      </div>
    );
  }

  // Detail view (SCR-12)
  if (selectedId) {
    if (detailLoading) {
      return (
        <div className="flex items-center justify-center min-h-screen">
          <Spinner size="lg" />
        </div>
      );
    }
    if (!detail) return null;

    return (
      <div className="space-y-6">
        <button
          onClick={() => { setSelectedId(null); setDetail(null); }}
          className="text-emerald-600 hover:text-emerald-700 font-medium flex items-center gap-1"
        >
          ← Kembali
        </button>

        <Card className="p-6 space-y-6">
          {detail.image && (
            <img
              src={`${mediaBaseURL}${detail.image}`}
              alt={detail.judul}
              className="w-full h-48 object-cover rounded-lg"
            />
          )}

          <div>
            <h1 className="text-2xl font-bold text-gray-900">{detail.judul}</h1>
            <Badge variant={KATEGORI_BADGE[detail.kategori_sampah] || 'default'} className="mt-2">
              {KATEGORI_LABEL[detail.kategori_sampah] || detail.kategori_sampah}
            </Badge>
          </div>

          <div className="space-y-4">
            <h3 className="font-semibold text-gray-900">Ringkasan</h3>
            <p className="text-gray-700">{detail.konten}</p>
          </div>

          <div className="bg-emerald-50 rounded-lg p-4">
            <h4 className="font-medium text-gray-900 mb-2">Tips</h4>
            <p className="text-sm text-gray-700">
              Pisahkan sampah berdasarkan kategori untuk memudahkan proses daur ulang dan pengolahan.
            </p>
          </div>
        </Card>
      </div>
    );
  }

  // List view (SCR-11)
  return (
    <div className="space-y-6">
      <h2 className="text-2xl font-bold text-gray-900">Edukasi</h2>

      <div className="flex gap-2 overflow-x-auto pb-2">
        {['semua', 'organik', 'anorganik', 'residu', 'umum'].map((category) => (
          <button
            key={category}
            onClick={() => setActiveCategory(category)}
            className={`px-4 py-2 rounded-full text-sm font-medium whitespace-nowrap transition-colors ${
              activeCategory === category
                ? 'bg-emerald-600 text-white'
                : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
            }`}
          >
            {category.charAt(0).toUpperCase() + category.slice(1)}
          </button>
        ))}
      </div>

      {filteredMaterials && filteredMaterials.length > 0 ? (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {filteredMaterials.map((material) => (
            <Card
              key={material.id}
              className="cursor-pointer hover:shadow-md transition-shadow p-4"
              onClick={() => openDetail(material.id)}
            >
              <div className="flex gap-4">
                {material.image && (
                  <div className="w-20 h-20 bg-gray-200 rounded-lg flex-shrink-0 overflow-hidden">
                    <img
                      src={`${mediaBaseURL}${material.image}`}
                      alt={material.judul}
                      className="w-full h-full object-cover"
                    />
                  </div>
                )}
                <div className="flex-1">
                  <h3 className="font-semibold text-gray-900">{material.judul}</h3>
                  <p className="text-sm text-gray-600 mt-1 line-clamp-2">{material.ringkasan}</p>
                  <Badge variant={KATEGORI_BADGE[material.kategori_sampah] || 'default'} className="mt-3">
                    {KATEGORI_LABEL[material.kategori_sampah] || material.kategori_sampah}
                  </Badge>
                </div>
              </div>
            </Card>
          ))}
        </div>
      ) : (
        <Card className="text-center py-12">
          <p className="text-gray-500">Belum ada materi edukasi.</p>
        </Card>
      )}
    </div>
  );
}

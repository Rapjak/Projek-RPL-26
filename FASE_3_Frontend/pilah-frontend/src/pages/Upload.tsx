import { useState, useRef, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { useNotification } from '../context/NotificationContext';
import { Button } from '../components/common/Button';
import { Card } from '../components/common/Card';
import { Spinner } from '../components/common/Spinner';
import { classificationService } from '../services/classifications';
import type { ClassificationPollResponse } from '../types';

type ViewState = 'upload' | 'processing' | 'result';

const KATEGORI_LABEL: Record<string, string> = {
  organik: 'Organik',
  anorganik: 'Anorganik',
  residu: 'Residu',
  tidak_dikenal: 'Tidak Dikenal',
};

const KATEGORI_COLOR: Record<string, string> = {
  organik: 'text-green-600 bg-green-50 border-green-200',
  anorganik: 'text-blue-600 bg-blue-50 border-blue-200',
  residu: 'text-gray-700 bg-gray-100 border-gray-200',
  tidak_dikenal: 'text-orange-600 bg-orange-50 border-orange-200',
};

const MAX_SIZE = 5 * 1024 * 1024;

export function UploadPage() {
  const { refreshUser } = useAuth();
  const { addNotification } = useNotification();
  const navigate = useNavigate();
  const fileInputRef = useRef<HTMLInputElement>(null);
  // Track whether component is still mounted so async polling loop
  // can bail out instead of calling setState on an unmounted component.
  const mountedRef = useRef(true);

  useEffect(() => {
    // Reset on mount (React 19 StrictMode mounts → unmounts → remounts in dev,
    // so the cleanup below would otherwise leave this stuck at false).
    mountedRef.current = true;
    return () => { mountedRef.current = false; };
  }, []);

  const [viewState, setViewState] = useState<ViewState>('upload');
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const [result, setResult] = useState<ClassificationPollResponse | null>(null);

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    // Client-side pre-validation (TC-015, TC-016, TC-026)
    const isJpegPng = file.type === 'image/jpeg' || file.type === 'image/png';
    if (!isJpegPng) {
      addNotification('error', 'Format file tidak didukung. Gunakan JPEG atau PNG.');
      return;
    }
    if (file.size === 0) {
      addNotification('error', 'Berkas kosong atau rusak. Silakan pilih foto lain.');
      return;
    }
    if (file.size > MAX_SIZE) {
      addNotification('error', 'Ukuran file melebihi batas maksimal 5 MB.');
      return;
    }

    setSelectedFile(file);
    setPreviewUrl(URL.createObjectURL(file));
  };

  const handleUpload = async () => {
    if (!selectedFile) return;
    setViewState('processing');

    try {
      // API-005: upload + auto-trigger classification
      const accepted = await classificationService.uploadAndClassify(selectedFile);

      // Poll API-006 until status is completed/failed
      const pollLoop = async () => {
        const maxAttempts = 40;
        for (let i = 0; i < maxAttempts; i++) {
          await new Promise(r => setTimeout(r, 800));
          if (!mountedRef.current) return; // component unmounted, abort
          try {
            const status = await classificationService.pollStatus(accepted.upload_id);
            if (!mountedRef.current) return;
            if (status.status === 'completed' || status.status === 'failed') {
              setResult(status);
              setViewState('result');
              // Refresh user points in AuthContext
              if (status.poin_diperoleh && status.poin_diperoleh > 0) {
                await refreshUser();
              }
              return;
            }
          } catch (err) {
            // Continue polling on transient errors
          }
        }
        if (!mountedRef.current) return;
        addNotification('error', 'Proses klasifikasi memakan waktu terlalu lama. Coba lagi.');
        setViewState('upload');
      };
      pollLoop();
    } catch (error: any) {
      const msg = error.response?.data?.file?.[0]
        || error.response?.data?.error?.message
        || error.response?.data?.detail
        || 'Upload gagal. Silakan coba lagi.';
      addNotification('error', msg);
      setViewState('upload');
    }
  };

  const handleReset = () => {
    setViewState('upload');
    setSelectedFile(null);
    setPreviewUrl(null);
    setResult(null);
    if (fileInputRef.current) fileInputRef.current.value = '';
  };

  // SCR-04: Upload view
  if (viewState === 'upload') {
    return (
      <div className="max-w-2xl mx-auto space-y-6">
        <h2 className="text-2xl font-bold text-gray-900">Unggah Foto Sampah</h2>

        <Card className="p-6 space-y-6">
          <div className="bg-gray-100 rounded-lg aspect-video flex items-center justify-center overflow-hidden">
            {previewUrl ? (
              <img src={previewUrl} alt="preview" className="w-full h-full object-cover" />
            ) : (
              <p className="text-gray-500 text-sm">Pratinjau foto akan tampil di sini</p>
            )}
          </div>

          <div className="grid grid-cols-2 gap-3">
            <Button onClick={() => fileInputRef.current?.click()} className="bg-emerald-600 hover:bg-emerald-700">
              Ambil Foto
            </Button>
            <Button
              onClick={() => fileInputRef.current?.click()}
              variant="outline"
              className="border-gray-300"
            >
              Pilih dari Galeri
            </Button>
          </div>

          <input
            ref={fileInputRef}
            type="file"
            accept="image/jpeg,image/jpg,image/png"
            onChange={handleFileSelect}
            className="hidden"
          />

          <div className="bg-emerald-50 border border-emerald-200 rounded-lg p-4">
            <p className="font-medium text-gray-900 mb-2">Tips foto yang baik:</p>
            <ul className="text-sm text-gray-700 space-y-1 list-disc list-inside">
              <li>Satu jenis sampah per foto (objek tunggal)</li>
              <li>Cahaya cukup, foto tidak buram</li>
              <li>Objek terlihat jelas dan utuh di frame</li>
              <li>Latar belakang kontras dengan objek sampah</li>
            </ul>
          </div>

          <p className="text-xs text-gray-500 text-center">
            Format JPG / PNG - Maksimal 5 MB
          </p>

          <Button
            onClick={handleUpload}
            disabled={!selectedFile}
            className="w-full bg-gray-400 hover:bg-gray-500 disabled:bg-gray-300"
          >
            Kirim Foto
          </Button>
        </Card>
      </div>
    );
  }

  // SCR-05: Processing view
  if (viewState === 'processing') {
    return (
      <div className="max-w-2xl mx-auto">
        <Card className="p-8">
          <div className="text-center space-y-6">
            <Spinner size="lg" />
            <h3 className="text-lg font-semibold text-gray-900">Memproses Foto</h3>
            <p className="text-gray-600">Foto sedang dianalisis oleh model AI...</p>

            <div className="space-y-3 text-left max-w-sm mx-auto">
              <div className="flex items-center gap-3">
                <div className="w-5 h-5 rounded-full bg-emerald-500 flex items-center justify-center flex-shrink-0">
                  <svg className="w-3 h-3 text-white" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                  </svg>
                </div>
                <span className="text-sm text-gray-700">Foto diterima</span>
              </div>
              <div className="flex items-center gap-3">
                <div className="w-5 h-5 rounded-full border-2 border-emerald-500 flex items-center justify-center flex-shrink-0">
                  <div className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse"></div>
                </div>
                <span className="text-sm text-gray-700">Mengklasifikasi jenis sampah</span>
              </div>
              <div className="flex items-center gap-3">
                <div className="w-5 h-5 rounded-full border-2 border-gray-300 flex-shrink-0"></div>
                <span className="text-sm text-gray-500">Menentukan hasil & poin</span>
              </div>
            </div>

            <p className="text-sm text-gray-500">Mohon tunggu, jangan tutup halaman ini</p>
          </div>
        </Card>
      </div>
    );
  }

  // SCR-06 / SCR-07: Result view
  if (viewState === 'result' && result) {
    const kategori = result.kategori || 'tidak_dikenal';
    const isInvalid = kategori === 'tidak_dikenal' || !result.is_valid;
    const label = KATEGORI_LABEL[kategori] || 'Tidak Dikenal';
    const colorClass = KATEGORI_COLOR[kategori] || KATEGORI_COLOR.tidak_dikenal;
    const confidence = result.confidence ? (result.confidence * 100).toFixed(0) : '0';

    return (
      <div className="max-w-2xl mx-auto space-y-6">
        <h2 className="text-2xl font-bold text-gray-900">Hasil Klasifikasi</h2>

        <Card className="p-6 space-y-6">
          <div className="flex justify-center">
            <div className="w-32 h-32 bg-gray-200 rounded-lg overflow-hidden">
              {previewUrl && <img src={previewUrl} alt="hasil" className="w-full h-full object-cover" />}
            </div>
          </div>

          <div className={`text-center rounded-lg border p-4 ${colorClass}`}>
            <p className="text-sm opacity-80 mb-1">Kategori sampah</p>
            <p className="text-2xl font-bold">{label}</p>
            {!isInvalid && (
              <p className="text-sm opacity-80 mt-1">Tingkat keyakinan model: {confidence}%</p>
            )}
          </div>

          {result.status === 'failed' ? (
            <div className="bg-red-50 border border-red-200 rounded-lg p-4">
              <p className="font-medium text-red-800 mb-1">Klasifikasi Gagal</p>
              <p className="text-sm text-red-700">
                Layanan klasifikasi sedang tidak tersedia. Silakan coba beberapa saat lagi.
              </p>
            </div>
          ) : isInvalid ? (
            <div className="bg-orange-50 border border-orange-200 rounded-lg p-4">
              <p className="font-medium text-orange-800 mb-2">Foto belum dapat dikenali</p>
              <p className="text-sm text-orange-700 mb-3">
                Tingkat keyakinan model di bawah 70%. Tidak ada poin yang diberikan.
              </p>
              <p className="text-sm text-orange-700 mb-1">Tips pengambilan foto:</p>
              <ul className="text-xs text-orange-700 space-y-1 list-disc list-inside">
                <li>Pastikan objek sampah terlihat jelas</li>
                <li>Ambil foto dari jarak dekat</li>
                <li>Hindari foto blur atau gelap</li>
                <li>Pastikan hanya satu jenis sampah dalam foto</li>
              </ul>
            </div>
          ) : (
            <>
              <div className="bg-gray-50 rounded-lg p-4">
                <p className="font-medium text-gray-900 mb-2">Arahan pembuangan</p>
                <p className="text-sm text-gray-700">{result.deskripsi || ''}</p>
              </div>

              <div className="bg-emerald-50 border border-emerald-200 rounded-lg p-4">
                <p className="font-medium text-gray-900 mb-2">Perolehan Poin</p>
                <div className="flex items-center gap-2 mb-1">
                  <svg className="w-4 h-4 text-emerald-600" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                  </svg>
                  <span className="text-sm text-gray-700">Aktivitas memenuhi ketentuan pemilahan</span>
                </div>
                <p className="text-2xl font-bold text-emerald-600">+{result.poin_diperoleh} poin</p>
              </div>
            </>
          )}

          <div className="space-y-3">
            <Button onClick={handleReset} className="w-full bg-emerald-600 hover:bg-emerald-700">
              Unggah Lagi
            </Button>
            <Button
              onClick={() => navigate('/dashboard')}
              variant="outline"
              className="w-full border-emerald-600 text-emerald-600 hover:bg-emerald-50"
            >
              Ke Beranda
            </Button>
          </div>
        </Card>
      </div>
    );
  }

  return null;
}

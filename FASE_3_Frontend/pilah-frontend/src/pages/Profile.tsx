import { useState } from 'react';
import { useAuth } from '../context/AuthContext';
import { useNotification } from '../context/NotificationContext';
import { Card, CardHeader, CardBody } from '../components/common/Card';
import { Button } from '../components/common/Button';
import { Input } from '../components/common/Input';
import { authService } from '../services/auth';

const PERAN_LABEL: Record<string, string> = {
  civitas: 'Civitas Akademika',
  admin_gogreen: 'Admin GoGreen',
  pimpinan: 'Pimpinan',
};

export function Profile() {
  const { user, refreshUser, logout } = useAuth();
  const { addNotification } = useNotification();
  const [editing, setEditing] = useState(false);
  const [saving, setSaving] = useState(false);
  const [formData, setFormData] = useState({
    name: user?.name || '',
    unit_gedung: user?.unit_gedung || '',
  });

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setFormData({ ...formData, [e.target.name]: e.target.value });
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSaving(true);
    try {
      await authService.updateProfile(formData);
      await refreshUser();
      addNotification('success', 'Profil berhasil diperbarui');
      setEditing(false);
    } catch (error: any) {
      const msg =
        error.response?.data?.error?.message ||
        error.response?.data?.detail ||
        'Gagal memperbarui profil';
      addNotification('error', msg);
    } finally {
      setSaving(false);
    }
  };

  const handleLogout = async () => {
    await logout();
  };

  return (
    <div className="max-w-2xl mx-auto space-y-6">
      <h2 className="text-2xl font-bold text-gray-900">Profil</h2>

      {/* Stats */}
      <div className="grid grid-cols-2 gap-4">
        <Card>
          <CardBody className="text-center">
            <p className="text-sm text-gray-500">Total Poin</p>
            <p className="text-2xl font-bold text-emerald-600">{user?.total_poin || 0}</p>
          </CardBody>
        </Card>
        <Card>
          <CardBody className="text-center">
            <p className="text-sm text-gray-500">Peran</p>
            <p className="text-lg font-bold text-gray-900">
              {PERAN_LABEL[user?.peran || 'civitas']}
            </p>
          </CardBody>
        </Card>
      </div>

      {/* Profile Info */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <h3 className="text-lg font-semibold">Informasi Pribadi</h3>
            {!editing && (
              <Button variant="ghost" size="sm" onClick={() => setEditing(true)}>
                Ubah
              </Button>
            )}
          </div>
        </CardHeader>
        <CardBody>
          <form onSubmit={handleSubmit} className="space-y-4">
            <Input
              type="text"
              label="NPM/NIP"
              value={user?.npm_nip || ''}
              disabled
            />

            <Input
              type="email"
              label="Email"
              value={user?.email || ''}
              disabled
            />

            <Input
              type="text"
              name="name"
              label="Nama Lengkap"
              value={editing ? formData.name : user?.name || ''}
              onChange={handleChange}
              disabled={!editing}
            />

            <Input
              type="text"
              name="unit_gedung"
              label="Unit/Gedung"
              value={editing ? formData.unit_gedung : user?.unit_gedung || ''}
              onChange={handleChange}
              disabled={!editing}
              placeholder={editing ? 'Contoh: FMIPA - Teknik Informatika' : '-'}
            />

            {editing && (
              <div className="flex gap-3 pt-4">
                <Button type="submit" loading={saving}>
                  Simpan Perubahan
                </Button>
                <Button
                  variant="secondary"
                  type="button"
                  onClick={() => {
                    setEditing(false);
                    setFormData({ name: user?.name || '', unit_gedung: user?.unit_gedung || '' });
                  }}
                >
                  Batal
                </Button>
              </div>
            )}
          </form>
        </CardBody>
      </Card>

      <Button
        onClick={handleLogout}
        variant="outline"
        className="w-full border-red-300 text-red-600 hover:bg-red-50"
      >
        Keluar
      </Button>
    </div>
  );
}

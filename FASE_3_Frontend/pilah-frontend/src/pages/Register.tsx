import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { useNotification } from '../context/NotificationContext';
import { Button } from '../components/common/Button';
import { Input } from '../components/common/Input';
import { Select } from '../components/common/Select';

const UNIT_OPTIONS = [
  'FMIPA - Teknik Informatika',
  'FMIPA - Matematika',
  'FMIPA - Fisika',
  'FMIPA - Kimia',
  'FMIPA - Biologi',
  'FMIPA - Ilmu Lingkungan',
  'FEB - Akuntansi',
  'FEB - Manajemen',
  'FH - Ilmu Hukum',
  'FISIP - Ilmu Komunikasi',
  'FKIP - Pendidikan Biologi',
  'FIB - Sastra Indonesia',
];

export function Register() {
  const [form, setForm] = useState({
    npm_nip: '',
    name: '',
    email: '',
    unit_gedung: '',
    password: '',
    password2: '',
  });
  const [loading, setLoading] = useState(false);
  const { register } = useAuth();
  const { addNotification } = useNotification();
  const navigate = useNavigate();

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
    setForm({ ...form, [e.target.name]: e.target.value });
  };

  const passwordMatch = form.password === form.password2;
  const passwordLong = form.password.length >= 8;
  const canSubmit = form.npm_nip && form.name && form.email && form.unit_gedung && passwordMatch && passwordLong;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!passwordMatch) {
      addNotification('error', 'Kata sandi tidak cocok');
      return;
    }
    if (!passwordLong) {
      addNotification('error', 'Kata sandi minimal 8 karakter');
      return;
    }
    if (!form.email.includes('@')) {
      addNotification('error', 'Format email tidak valid');
      return;
    }

    setLoading(true);
    try {
      // Send to backend - role is hardcoded to civitas server-side (TC-006)
      const { password2, ...payload } = form;
      await register(payload);
      addNotification('success', 'Registrasi berhasil! Silakan login.');
      navigate('/login');
    } catch (error: any) {
      const data = error.response?.data;
      let msg = 'Registrasi gagal';
      if (data) {
        if (Array.isArray(data.email)) msg = data.email[0];
        else if (Array.isArray(data.npm_nip)) msg = data.npm_nip[0];
        else if (Array.isArray(data.password)) msg = data.password[0];
        else if (data.error?.message) msg = data.error.message;
        else if (typeof data.detail === 'string') msg = data.detail;
      }
      addNotification('error', msg);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-emerald-50 to-gray-50 px-4 py-12">
      <div className="max-w-md w-full">
        <div className="text-center mb-8">
          <div className="inline-flex w-16 h-16 bg-emerald-600 rounded-2xl items-center justify-center mb-4 shadow-lg">
            <span className="text-white font-bold text-2xl">P</span>
          </div>
          <h2 className="text-3xl font-bold text-gray-900">Buat Akun</h2>
          <p className="text-gray-600 mt-2">Bergabung dengan Pilah.in hari ini</p>
        </div>

        <div className="bg-white p-8 rounded-2xl shadow-sm border border-gray-200">
          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1.5">NPM/NIP</label>
              <Input
                type="text"
                name="npm_nip"
                placeholder="Contoh: 140810240015"
                value={form.npm_nip}
                onChange={handleChange}
                required
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1.5">Nama Lengkap</label>
              <Input
                type="text"
                name="name"
                placeholder="Masukkan nama lengkap"
                value={form.name}
                onChange={handleChange}
                required
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1.5">Email</label>
              <Input
                type="email"
                name="email"
                placeholder="nama@mail.unpad.ac.id"
                value={form.email}
                onChange={handleChange}
                required
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1.5">Unit/Gedung</label>
              <Select
                name="unit_gedung"
                value={form.unit_gedung}
                onChange={handleChange}
                required
              >
                <option value="">Pilih Unit/Fakultas</option>
                {UNIT_OPTIONS.map(u => <option key={u} value={u}>{u}</option>)}
              </Select>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1.5">Kata Sandi</label>
              <Input
                type="password"
                name="password"
                placeholder="Minimal 8 karakter"
                value={form.password}
                onChange={handleChange}
                required
              />
              {form.password && !passwordLong && (
                <p className="mt-1 text-xs text-red-600">Kata sandi minimal 8 karakter</p>
              )}
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1.5">Konfirmasi Kata Sandi</label>
              <Input
                type="password"
                name="password2"
                placeholder="••••••••"
                value={form.password2}
                onChange={handleChange}
                required
              />
              {form.password2 && !passwordMatch && (
                <p className="mt-1 text-xs text-red-600">Kata sandi tidak cocok</p>
              )}
            </div>

            <Button
              type="submit"
              className="w-full bg-emerald-600 hover:bg-emerald-700"
              loading={loading}
              disabled={!canSubmit}
            >
              Daftar
            </Button>
          </form>

          <div className="mt-6 text-center">
            <p className="text-sm text-gray-600">
              Sudah punya akun?{' '}
              <Link to="/login" className="text-emerald-600 hover:text-emerald-700 font-medium">
                Masuk
              </Link>
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}

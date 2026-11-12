import React, { useState, useEffect } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { useNotification } from '../context/NotificationContext';
import { Button } from '../components/common/Button';
import { Input } from '../components/common/Input';

export function Login() {
  const [identifier, setIdentifier] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [justLoggedIn, setJustLoggedIn] = useState(false);
  const { login, user } = useAuth();
  const { addNotification } = useNotification();
  const navigate = useNavigate();

  const canSubmit = identifier.trim().length > 0 && password.length > 0;

  // Navigate AFTER the auth user state has been committed by React.
  // This avoids a race where ProtectedRoute renders before `user` is set,
  // which would redirect back to /login (symptom: "login responds but no redirect").
  useEffect(() => {
    if (justLoggedIn && user) {
      if (user.peran === 'admin_gogreen' || user.peran === 'pimpinan') {
        navigate('/admin', { replace: true });
      } else {
        navigate('/dashboard', { replace: true });
      }
    }
  }, [justLoggedIn, user, navigate]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!canSubmit) return;
    setLoading(true);

    try {
      const loggedUser = await login(identifier.trim(), password);
      addNotification('success', `Selamat datang, ${loggedUser.name}`);
      // Trigger redirect via effect (runs after state commit)
      setJustLoggedIn(true);
    } catch (error: any) {
      const msg =
        error.response?.data?.error?.message ||
        error.response?.data?.detail ||
        'Login gagal. Periksa kredensial Anda.';
      addNotification('error', msg);
      setPassword('');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-emerald-50 to-gray-50 px-4">
      <div className="max-w-md w-full">
        <div className="text-center mb-8">
          <div className="inline-flex w-16 h-16 bg-emerald-600 rounded-2xl items-center justify-center mb-4 shadow-lg">
            <span className="text-white font-bold text-2xl">P</span>
          </div>
          <h2 className="text-3xl font-bold text-gray-900">Pilah.in</h2>
          <p className="text-gray-600 mt-2">Masuk ke akun Anda</p>
        </div>

        <div className="bg-white p-8 rounded-2xl shadow-sm border border-gray-200">
          <form onSubmit={handleSubmit} className="space-y-5">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1.5">
                NPM/NIP atau Email
              </label>
              <Input
                type="text"
                placeholder="140810240015 atau email@unpad.ac.id"
                value={identifier}
                onChange={(e) => setIdentifier(e.target.value)}
                required
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1.5">
                Kata Sandi
              </label>
              <Input
                type="password"
                placeholder="••••••••"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
              />
            </div>

            <Button
              type="submit"
              className="w-full bg-emerald-600 hover:bg-emerald-700"
              loading={loading}
              disabled={!canSubmit}
            >
              Masuk
            </Button>
          </form>

          <div className="mt-6 text-center">
            <p className="text-sm text-gray-600">
              Belum punya akun?{' '}
              <Link to="/register" className="text-emerald-600 hover:text-emerald-700 font-medium">
                Daftar
              </Link>
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}

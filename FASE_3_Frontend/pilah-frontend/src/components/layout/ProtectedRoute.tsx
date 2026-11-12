import React from 'react';
import { Navigate } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import { Spinner } from '../common/Spinner';

interface ProtectedRouteProps {
  children: React.ReactNode;
  /** Restrict access to specific roles (e.g. admin routes). */
  roles?: Array<'civitas' | 'admin_gogreen' | 'pimpinan'>;
}

export function ProtectedRoute({ children, roles }: ProtectedRouteProps) {
  const { isAuthenticated, loading, user } = useAuth();

  // While the auth state is initialising, or a token exists but the profile
  // hasn't been hydrated into `user` yet, show a spinner instead of bouncing
  // to /login (prevents the post-login redirect race).
  const hasToken = !!localStorage.getItem('access_token');
  if (loading || (hasToken && !user)) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <Spinner size="lg" />
      </div>
    );
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }

  // Role-based authorization (SCR-13: admin dashboard only for admin/pimpinan)
  if (roles && user && !roles.includes(user.peran)) {
    return <Navigate to="/dashboard" replace />;
  }

  return <>{children}</>;
}

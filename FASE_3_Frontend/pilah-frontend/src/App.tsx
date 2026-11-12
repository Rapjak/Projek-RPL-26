import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider } from './context/AuthContext';
import { NotificationProvider } from './context/NotificationContext';
import { Header } from './components/layout/Header';
import { Footer } from './components/layout/Footer';
import { ProtectedRoute } from './components/layout/ProtectedRoute';
import { Sidebar } from './components/layout/Sidebar';
import { Login } from './pages/Login';
import { Register } from './pages/Register';
import { Dashboard } from './pages/Dashboard';
import { UploadPage } from './pages/Upload';
import { History } from './pages/History';
import { Rewards } from './pages/Rewards';
import { Education } from './pages/Education';
import { Profile } from './pages/Profile';
import { Leaderboard } from './pages/Leaderboard';
import { AdminDashboard } from './pages/AdminDashboard';

function Layout({ children }: { children: React.ReactNode }) {
  const [sidebarOpen, setSidebarOpen] = React.useState(false);

  return (
    <div className="min-h-screen bg-gray-50">
      <Header onMenuToggle={() => setSidebarOpen(!sidebarOpen)} />

      <div className="flex pt-16">
        <Sidebar isOpen={sidebarOpen} onClose={() => setSidebarOpen(false)} />

        <main className="flex-1 p-4 sm:p-6 lg:p-8 overflow-x-hidden">
          <div className="max-w-7xl mx-auto">{children}</div>
        </main>
      </div>

      <Footer />
    </div>
  );
}

function App() {
  return (
    <AuthProvider>
      <NotificationProvider>
        <Router>
          <Routes>
            <Route path="/login" element={<Login />} />
            <Route path="/register" element={<Register />} />

            <Route
              path="/"
              element={
                <ProtectedRoute>
                  <Layout>
                    <Dashboard />
                  </Layout>
                </ProtectedRoute>
              }
            />

            <Route
              path="/dashboard"
              element={
                <ProtectedRoute>
                  <Layout>
                    <Dashboard />
                  </Layout>
                </ProtectedRoute>
              }
            />

            <Route
              path="/upload"
              element={
                <ProtectedRoute>
                  <Layout>
                    <UploadPage />
                  </Layout>
                </ProtectedRoute>
              }
            />

            <Route
              path="/history"
              element={
                <ProtectedRoute>
                  <Layout>
                    <History />
                  </Layout>
                </ProtectedRoute>
              }
            />

            <Route
              path="/rewards"
              element={
                <ProtectedRoute>
                  <Layout>
                    <Rewards />
                  </Layout>
                </ProtectedRoute>
              }
            />

            <Route
              path="/education"
              element={
                <ProtectedRoute>
                  <Layout>
                    <Education />
                  </Layout>
                </ProtectedRoute>
              }
            />

            <Route
              path="/leaderboard"
              element={
                <ProtectedRoute>
                  <Layout>
                    <Leaderboard />
                  </Layout>
                </ProtectedRoute>
              }
            />

            <Route
              path="/profile"
              element={
                <ProtectedRoute>
                  <Layout>
                    <Profile />
                  </Layout>
                </ProtectedRoute>
              }
            />

            {/* SCR-13: Admin Dashboard - restricted to admin_gogreen & pimpinan */}
            <Route
              path="/admin"
              element={
                <ProtectedRoute roles={['admin_gogreen', 'pimpinan']}>
                  <Layout>
                    <AdminDashboard />
                  </Layout>
                </ProtectedRoute>
              }
            />

            <Route path="*" element={<Navigate to="/dashboard" replace />} />
          </Routes>
        </Router>
      </NotificationProvider>
    </AuthProvider>
  );
}

export default App;

import { useNavigate, useLocation } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import {
  HomeIcon,
  ArrowUpTrayIcon,
  GiftIcon,
  AcademicCapIcon,
  TrophyIcon,
  UserCircleIcon,
  XMarkIcon,
  ShieldCheckIcon
} from '@heroicons/react/24/outline';

interface SidebarProps {
  isOpen?: boolean;
  onClose?: () => void;
}

const civitasNavItems = [
  { path: '/dashboard', label: 'Beranda', icon: HomeIcon },
  { path: '/education', label: 'Edukasi', icon: AcademicCapIcon },
  { path: '/upload', label: 'Unggah Foto', icon: ArrowUpTrayIcon },
  { path: '/leaderboard', label: 'Peringkat', icon: TrophyIcon },
  { path: '/rewards', label: 'Reward', icon: GiftIcon },
  { path: '/profile', label: 'Profil', icon: UserCircleIcon }
];

const adminExtraItems = [
  { path: '/admin', label: 'Admin Dashboard', icon: ShieldCheckIcon }
];

export function Sidebar({ isOpen = true, onClose }: SidebarProps) {
  const navigate = useNavigate();
  const location = useLocation();
  const { isAuthenticated, isAdmin } = useAuth();

  if (!isAuthenticated) return null;

  const navItems = isAdmin ? [...adminExtraItems, ...civitasNavItems] : civitasNavItems;

  return (
    <>
      {/* Mobile backdrop */}
      {isOpen && (
        <div
          className="fixed inset-0 z-30 bg-black bg-opacity-50 sm:hidden"
          onClick={onClose}
        />
      )}

      {/* Sidebar */}
      <aside
        className={`fixed top-16 left-0 z-40 w-64 h-[calc(100vh-64px)] bg-white border-r border-gray-200 transform transition-transform sm:relative sm:top-0 sm:translate-x-0 ${
          isOpen ? 'translate-x-0' : '-translate-x-full'
        }`}
      >
        <div className="flex flex-col h-full">
          {/* Close button on mobile */}
          <button
            onClick={onClose}
            className="sm:hidden absolute top-4 right-4 p-1 hover:bg-gray-100 rounded-lg"
          >
            <XMarkIcon className="h-6 w-6 text-gray-600" />
          </button>

          {/* Navigation */}
          <nav className="flex-1 px-4 py-8 space-y-1">
            {navItems.map(({ path, label, icon: Icon }) => {
              const isActive = location.pathname === path;
              return (
                <button
                  key={path}
                  onClick={() => {
                    navigate(path);
                    onClose?.();
                  }}
                  className={`w-full flex items-center gap-3 px-4 py-3 rounded-lg transition-colors ${
                    isActive
                      ? 'bg-emerald-50 text-emerald-600'
                      : 'text-gray-600 hover:bg-gray-50'
                  }`}
                >
                  <Icon className="h-5 w-5" />
                  <span className="font-medium">{label}</span>
                </button>
              );
            })}
          </nav>

          {/* Footer */}
          <div className="p-4 border-t border-gray-200">
            <p className="text-xs text-gray-500 text-center">Pilah.in v1.0</p>
          </div>
        </div>
      </aside>
    </>
  );
}

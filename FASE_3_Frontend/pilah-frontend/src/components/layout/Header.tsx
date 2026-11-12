import { useNavigate } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import { Menu, Transition } from '@headlessui/react';
import { UserCircleIcon, ArrowRightOnRectangleIcon, Bars3Icon } from '@heroicons/react/24/outline';

interface HeaderProps {
  onMenuToggle?: () => void;
}

export function Header({ onMenuToggle }: HeaderProps) {
  const { user, isAdmin, logout } = useAuth();
  const navigate = useNavigate();

  const handleLogout = async () => {
    await logout();
    navigate('/login');
  };

  return (
    <header className="sticky top-0 z-40 w-full bg-white border-b border-gray-200 shadow-sm">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          <div className="flex items-center gap-8">
            <div className="flex items-center gap-2">
              <div className="w-8 h-8 bg-emerald-600 rounded-lg flex items-center justify-center">
                <span className="text-white font-bold">P</span>
              </div>
              <span className="font-bold text-lg text-gray-900">Pilah.in</span>
            </div>
          </div>

          <div className="flex items-center gap-4">
            {user && (
              <>
                <div className="hidden sm:flex items-center gap-2 px-3 py-1.5 bg-emerald-50 rounded-lg">
                  <span className="text-sm text-emerald-700 font-medium">{user.total_poin}</span>
                  <span className="text-xs text-emerald-600">poin</span>
                </div>

                <Menu as="div" className="relative">
                  <Menu.Button className="flex items-center gap-2 hover:opacity-70 transition-opacity">
                    <UserCircleIcon className="h-8 w-8 text-gray-600" />
                    <span className="text-sm text-gray-700">{user.name}</span>
                  </Menu.Button>

                  <Transition
                    enter="transition ease-out duration-100"
                    enterFrom="transform opacity-0 scale-95"
                    enterTo="transform opacity-100 scale-100"
                    leave="transition ease-in duration-75"
                    leaveFrom="transform opacity-100 scale-100"
                    leaveTo="transform opacity-0 scale-95"
                  >
                    <Menu.Items className="absolute right-0 mt-2 w-48 bg-white rounded-lg shadow-lg border border-gray-200 py-1">
                      {isAdmin && (
                        <Menu.Item>
                          {({ active }) => (
                            <button
                              onClick={() => navigate('/admin')}
                              className={`w-full text-left px-4 py-2 text-sm ${active ? 'bg-gray-50' : ''}`}
                            >
                              Admin Dashboard
                            </button>
                          )}
                        </Menu.Item>
                      )}
                      <Menu.Item>
                        {({ active }) => (
                          <button
                            onClick={() => navigate('/profile')}
                            className={`w-full text-left px-4 py-2 text-sm ${active ? 'bg-gray-50' : ''}`}
                          >
                            Profil
                          </button>
                        )}
                      </Menu.Item>
                      <Menu.Item>
                        {({ active }) => (
                          <button
                            onClick={handleLogout}
                            className={`w-full text-left px-4 py-2 text-sm text-red-600 flex items-center gap-2 ${active ? 'bg-gray-50' : ''}`}
                          >
                            <ArrowRightOnRectangleIcon className="h-4 w-4" />
                            Keluar
                          </button>
                        )}
                      </Menu.Item>
                    </Menu.Items>
                  </Transition>
                </Menu>
              </>
            )}
            {onMenuToggle && (
              <button
                onClick={onMenuToggle}
                className="sm:hidden p-2 hover:bg-gray-100 rounded-lg"
              >
                <Bars3Icon className="h-6 w-6 text-gray-600" />
              </button>
            )}
          </div>
        </div>
      </div>
    </header>
  );
}

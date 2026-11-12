import { createContext, useContext, useState, useCallback } from 'react';
import type { ReactNode } from 'react';
import type { Notification } from '../types';

interface NotificationContextType {
  notifications: Notification[];
  addNotification: (type: 'success' | 'error' | 'info' | 'warning', message: string, duration?: number) => void;
  removeNotification: (id: string) => void;
}

const NotificationContext = createContext<NotificationContextType | undefined>(undefined);

export function NotificationProvider({ children }: { children: ReactNode }) {
  const [notifications, setNotifications] = useState<Notification[]>([]);

  const addNotification = useCallback(
    (type: 'success' | 'error' | 'info' | 'warning', message: string, duration = 5000) => {
      const id = Math.random().toString(36).substr(2, 9);
      const notification: Notification = { id, type, message };
      setNotifications((prev) => [...prev, notification]);

      if (duration > 0) {
        setTimeout(() => removeNotification(id), duration);
      }
    },
    []
  );

  const removeNotification = useCallback((id: string) => {
    setNotifications((prev) => prev.filter((n) => n.id !== id));
  }, []);

  return (
    <NotificationContext.Provider value={{ notifications, addNotification, removeNotification }}>
      {children}
    </NotificationContext.Provider>
  );
}

export function useNotification() {
  const context = useContext(NotificationContext);
  if (!context) {
    throw new Error('useNotification must be used within NotificationProvider');
  }
  return context;
}

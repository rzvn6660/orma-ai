import { useState, useEffect, useCallback } from 'react';
import { notificationApi } from '../services/api';
import { useWebSocket } from '../hooks/useWebSocket';
import { Bell, Check, AlertTriangle, AlertOctagon, Heart, Pill } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';

export default function NotificationCenter({ user }) {
  const [notifications, setNotifications] = useState([]);
  const [isOpen, setIsOpen] = useState(false);
  const [unreadCount, setUnreadCount] = useState(0);

  const fetchNotifications = async () => {
    try {
      const data = await notificationApi.getNotifications();
      setNotifications(data);
      setUnreadCount(data.filter(n => !n.is_read).length);
    } catch (err) {
      console.error(err);
    }
  };

  useEffect(() => {
    if (user) fetchNotifications();
  }, [user]);

  // Handle incoming real-time notifications
  const handleNewNotification = useCallback((data) => {
    if (data.type === 'notification') {
      setNotifications(prev => [data, ...prev]);
      setUnreadCount(prev => prev + 1);
    }
  }, []);

  useWebSocket(user?.id, handleNewNotification);

  const handleMarkRead = async (id) => {
    try {
      await notificationApi.markRead(id);
      setNotifications(prev => prev.map(n => n.id === id ? { ...n, is_read: true } : n));
      setUnreadCount(prev => Math.max(0, prev - 1));
    } catch (err) {
      console.error(err);
    }
  };

  const getIcon = (priority) => {
    if (priority === 'high') return <AlertOctagon className="w-5 h-5 text-red-400" />;
    if (priority === 'medium') return <AlertTriangle className="w-5 h-5 text-amber-400" />;
    return <Heart className="w-5 h-5 text-blue-400" />;
  };

  return (
    <div className="relative">
      <button 
        onClick={() => setIsOpen(!isOpen)}
        className="relative p-2 bg-slate-800/80 hover:bg-slate-700/80 rounded-full transition-colors focus:outline-none"
      >
        <Bell className="w-6 h-6 text-slate-300" />
        {unreadCount > 0 && (
          <span className="absolute top-0 right-0 w-5 h-5 bg-red-500 text-white text-xs font-bold rounded-full flex items-center justify-center animate-bounce shadow-[0_0_10px_rgba(239,68,68,0.5)]">
            {unreadCount}
          </span>
        )}
      </button>

      <AnimatePresence>
        {isOpen && (
          <motion.div
            initial={{ opacity: 0, y: 10, scale: 0.95 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: 10, scale: 0.95 }}
            className="absolute right-0 mt-2 w-80 max-h-96 overflow-y-auto bg-slate-900 border border-slate-700 shadow-2xl rounded-2xl z-50 p-2"
          >
            <div className="p-3 border-b border-slate-800 mb-2 flex justify-between items-center sticky top-0 bg-slate-900/95 backdrop-blur z-10">
              <h3 className="text-white font-bold">Alerts & Notifications</h3>
              <span className="text-xs text-slate-400">{unreadCount} unread</span>
            </div>

            <div className="space-y-1">
              {notifications.length === 0 ? (
                <div className="p-4 text-center text-slate-500 text-sm">
                  No notifications yet.
                </div>
              ) : (
                notifications.map(n => (
                  <div key={n.id} className={`p-3 rounded-xl flex gap-3 transition-colors ${!n.is_read ? 'bg-slate-800/80' : 'bg-transparent hover:bg-slate-800/40'}`}>
                    <div className="shrink-0 mt-1">{getIcon(n.priority)}</div>
                    <div className="flex-1">
                      <h4 className={`text-sm ${!n.is_read ? 'text-white font-bold' : 'text-slate-300 font-medium'}`}>{n.title}</h4>
                      <p className="text-xs text-slate-400 mt-0.5 line-clamp-2">{n.message}</p>
                      <span className="text-[10px] text-slate-500 mt-1 block">
                        {new Date(n.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                      </span>
                    </div>
                    {!n.is_read && (
                      <button onClick={() => handleMarkRead(n.id)} className="shrink-0 p-1 hover:bg-slate-700 rounded-full h-fit text-blue-400">
                        <Check className="w-4 h-4" />
                      </button>
                    )}
                  </div>
                ))
              )}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}

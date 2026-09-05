import { useState, useEffect, useCallback } from 'react';
import { notificationApi } from '../services/api';
import { useWebSocket } from '../hooks/useWebSocket';
import { Bell, Check, AlertTriangle, AlertOctagon, Heart, Pill } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import { formatEmergencyTimestamp } from '../utils/timeUtils';
import { 
  syncReadNotifications, 
  reconcileWithReadStorage, 
  markNotificationReadInStorage 
} from '../utils/notificationStorage';

export default function NotificationCenter({ user, onViewChange }) {
  const [notifications, setNotifications] = useState([]);
  const [isOpen, setIsOpen] = useState(false);
  const [unreadCount, setUnreadCount] = useState(0);

  const fetchNotifications = useCallback(async () => {
    try {
      const data = await notificationApi.getNotifications();
      const uniqueNotifications = Array.isArray(data) 
        ? Array.from(new Map(data.map(item => [item.id, item])).values()) 
        : [];
      syncReadNotifications(uniqueNotifications);
      const reconciled = reconcileWithReadStorage(uniqueNotifications);
      setNotifications(reconciled);
      setUnreadCount(reconciled.filter(n => !n.is_read).length);
    } catch (err) {
      console.error(err);
    }
  }, []);

  useEffect(() => {
    if (user) fetchNotifications();
    const handleUpdate = () => fetchNotifications();
    window.addEventListener('orma:remindersUpdated', handleUpdate);
    window.addEventListener('orma:notification', handleUpdate);
    return () => {
      window.removeEventListener('orma:remindersUpdated', handleUpdate);
      window.removeEventListener('orma:notification', handleUpdate);
    };
  }, [user, fetchNotifications]);

  // Handle incoming real-time notifications
  const handleNewNotification = useCallback((data) => {
    if (
      data.type === 'notification' || 
      data.type === 'medicine_missed' ||
      data.type === 'emergency_alert' || 
      data.type === 'emergency_acknowledged' || 
      data.type === 'emergency_resolved'
    ) {
      fetchNotifications();
    }
  }, [fetchNotifications]);

  useWebSocket(user?.id, handleNewNotification);

  const handleMarkRead = async (id, e) => {
    e?.stopPropagation();
    try {
      markNotificationReadInStorage(id);
      await notificationApi.markRead(id);
      setNotifications(prev => prev.map(n => n.id === id ? { ...n, is_read: true } : n));
      setUnreadCount(prev => Math.max(0, prev - 1));
    } catch (err) {
      console.error(err);
    }
  };

  const handleMarkAllRead = async () => {
    try {
      const unreadList = notifications.filter(n => !n.is_read);
      unreadList.forEach(n => markNotificationReadInStorage(n.id));
      await Promise.allSettled(unreadList.map(n => notificationApi.markRead(n.id)));
      setNotifications(prev => prev.map(n => ({ ...n, is_read: true })));
      setUnreadCount(0);
    } catch (err) {
      console.error(err);
    }
  };

  const handleClickItem = (n) => {
    if (!n.is_read) {
      handleMarkRead(n.id);
    }
    if (n.priority === 'high' || n.title?.includes('Emergency')) {
      if (onViewChange) {
        onViewChange('emergency');
      } else {
        window.dispatchEvent(new CustomEvent('orma_navigate', { detail: 'emergency' }));
      }
      setIsOpen(false);
    }
  };

  const getCategoryMeta = (n) => {
    const title = (n.title || '').toLowerCase();
    const msg = (n.message || '').toLowerCase();
    
    if (n.priority === 'high' || title.includes('emergency') || title.includes('sos')) {
      return {
        category: 'Emergency',
        icon: <AlertOctagon className="w-5 h-5 text-red-400 shrink-0" />,
        badgeClass: 'bg-red-500/20 text-red-300 border-red-500/40',
        cardClass: 'bg-red-950/40 hover:bg-red-950/60 border border-red-500/30'
      };
    }
    
    if (title.includes('missed') || msg.includes('missed') || msg.includes('has not confirmed')) {
      return {
        category: 'Medication Missed',
        icon: <AlertTriangle className="w-5 h-5 text-amber-400 shrink-0" />,
        badgeClass: 'bg-amber-500/20 text-amber-300 border-amber-500/40',
        cardClass: !n.is_read ? 'bg-amber-950/20 border border-amber-500/20' : 'bg-transparent hover:bg-slate-800/40'
      };
    }

    if (title.includes('adherence') || msg.includes('adherence') || title.includes('summary')) {
      return {
        category: 'Medication Adherence',
        icon: <Pill className="w-5 h-5 text-emerald-400 shrink-0" />,
        badgeClass: 'bg-emerald-500/20 text-emerald-300 border-emerald-500/40',
        cardClass: !n.is_read ? 'bg-emerald-950/20 border border-emerald-500/20' : 'bg-transparent hover:bg-slate-800/40'
      };
    }

    if (title.includes('reminder') || title.includes('medicine') || title.includes('medication')) {
      return {
        category: 'Medication Reminder',
        icon: <Pill className="w-5 h-5 text-cyan-400 shrink-0" />,
        badgeClass: 'bg-cyan-500/20 text-cyan-300 border-cyan-500/40',
        cardClass: !n.is_read ? 'bg-slate-800/80 hover:bg-slate-800 border border-slate-700/50' : 'bg-transparent hover:bg-slate-800/40'
      };
    }

    return {
      category: 'System',
      icon: <Bell className="w-5 h-5 text-blue-400 shrink-0" />,
      badgeClass: 'bg-blue-500/20 text-blue-300 border-blue-500/40',
      cardClass: !n.is_read ? 'bg-slate-800/80 hover:bg-slate-800' : 'bg-transparent hover:bg-slate-800/40'
    };
  };

  return (
    <div className="relative">
      <button 
        type="button"
        onClick={() => setIsOpen(!isOpen)}
        aria-label={`Notifications (${unreadCount} unread)`}
        className="relative p-2.5 bg-slate-900/60 hover:bg-slate-800/80 text-slate-300 hover:text-white rounded-full transition-all border border-white/10 hover:border-white/20 shadow-md backdrop-blur-xl focus:outline-none focus:ring-2 focus:ring-blue-400/50 cursor-pointer"
      >
        <Bell className="w-5 h-5" />
        {unreadCount > 0 && (
          <span className="absolute -top-0.5 -right-0.5 min-w-[20px] h-5 px-1.5 bg-red-600 text-white text-[11px] font-extrabold rounded-full flex items-center justify-center shadow-[0_0_10px_rgba(239,68,68,0.5)] border-2 border-slate-900">
            {unreadCount}
          </span>
        )}
      </button>

      <AnimatePresence>
        {isOpen && (
          <motion.div
            initial={{ opacity: 0, y: 8, scale: 0.96 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: 8, scale: 0.96 }}
            className="absolute right-0 mt-2 w-84 max-h-96 overflow-y-auto bg-slate-900/95 border border-white/10 shadow-2xl backdrop-blur-2xl rounded-2xl z-50 p-2"
          >
            <div className="p-3 border-b border-white/10 mb-2 flex justify-between items-center sticky top-0 bg-slate-950/80 backdrop-blur-md z-10 rounded-xl">
              <h3 className="text-white font-bold text-sm">Alerts & Notifications</h3>
              <div className="flex items-center gap-2">
                <span className="text-xs text-slate-400 font-semibold">{unreadCount} unread</span>
                {unreadCount > 0 && (
                  <button
                    type="button"
                    onClick={handleMarkAllRead}
                    className="text-[11px] text-blue-400 hover:text-blue-300 font-semibold hover:underline cursor-pointer"
                  >
                    Mark all as read
                  </button>
                )}
              </div>
            </div>

            <div className="space-y-1">
              {notifications.length === 0 ? (
                <div className="p-4 text-center text-slate-500 text-sm">
                  No notifications yet.
                </div>
              ) : (
                notifications.map(n => {
                  const meta = getCategoryMeta(n);
                  return (
                    <div 
                      key={n.id} 
                      onClick={() => handleClickItem(n)}
                      className={`p-3 rounded-xl flex gap-3 transition-colors cursor-pointer ${meta.cardClass}`}
                    >
                      <div className="shrink-0 mt-1">{meta.icon}</div>
                      <div className="flex-1">
                        <div className="flex items-center justify-between gap-2 mb-0.5">
                          <span className={`px-2 py-0.5 rounded-md text-[10px] font-extrabold uppercase border ${meta.badgeClass}`}>
                            {meta.category}
                          </span>
                          <span className="text-[10px] text-slate-400 font-medium shrink-0">
                            {formatEmergencyTimestamp(n.created_at, user?.timezone)}
                          </span>
                        </div>
                        <h4 className={`text-sm ${!n.is_read ? 'text-white font-bold' : 'text-slate-300 font-medium'}`}>{n.title}</h4>
                        <p className="text-xs text-slate-400 mt-0.5 line-clamp-2">{n.message}</p>
                      </div>
                      {!n.is_read ? (
                        <button 
                          type="button"
                          onClick={(e) => handleMarkRead(n.id, e)} 
                          className="shrink-0 px-2 py-1 bg-blue-500/15 hover:bg-blue-500/25 text-blue-300 hover:text-blue-200 border border-blue-500/30 rounded-lg text-[10px] font-semibold flex items-center gap-1 cursor-pointer transition-colors self-center"
                          title="Mark as read"
                          aria-label={`Mark notification ${n.title} as read`}
                        >
                          <Check className="w-3 h-3 text-blue-400" />
                          <span>Mark as read</span>
                        </button>
                      ) : (
                        <span 
                          className="shrink-0 px-1.5 py-0.5 text-slate-500 text-[10px] font-medium flex items-center gap-1 self-center" 
                          title="Read"
                        >
                          <Check className="w-3 h-3 text-slate-500" />
                          <span>Read</span>
                        </span>
                      )}
                    </div>
                  );
                })
              )}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}

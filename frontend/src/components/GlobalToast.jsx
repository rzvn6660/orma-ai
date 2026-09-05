import React, { useState, useEffect, useRef } from 'react';
import { AnimatePresence, motion } from 'framer-motion';
import { CheckCircle2, AlertCircle, AlertTriangle, Info, X } from 'lucide-react';
import { isNotificationReadInStorage } from '../utils/notificationStorage';

export default function GlobalToast() {
  const [toasts, setToasts] = useState([]);
  const recentToastsRef = useRef(new Map());

  useEffect(() => {
    const handleToast = (e) => {
      const { type = 'info', message, id: incomingId, notification_id, is_read } = e.detail || {};
      if (!message) return;

      // Suppress toast if notification is already read
      if (is_read === true) return;
      if (incomingId && isNotificationReadInStorage(incomingId)) return;
      if (notification_id && isNotificationReadInStorage(notification_id)) return;

      const now = Date.now();
      const dedupKey = incomingId || `${type}_${message.trim()}`;

      // Deduplication:
      // If incomingId is provided, enforce a 10-minute window.
      // If inferred from message, enforce an 8-second window.
      const windowMs = incomingId ? 10 * 60 * 1000 : 8000;
      const lastTime = recentToastsRef.current.get(dedupKey);
      if (lastTime && (now - lastTime) < windowMs) {
        return;
      }
      recentToastsRef.current.set(dedupKey, now);

      // Prevent identical message already visible on screen
      setToasts(prev => {
        if (prev.some(t => t.message === message)) {
          return prev;
        }
        const toastId = incomingId || `${now}-${Math.random().toString(36).substr(2, 9)}`;
        return [...prev.slice(-3), { id: toastId, type, message }];
      });

      const autoDismissId = incomingId || dedupKey;
      setTimeout(() => {
        setToasts(prev => prev.filter(t => t.id !== autoDismissId && t.id !== incomingId));
      }, 4500);

      // Periodically prune stale entries from recentToastsRef (> 15 minutes)
      if (recentToastsRef.current.size > 50) {
        for (const [key, timestamp] of recentToastsRef.current.entries()) {
          if (now - timestamp > 15 * 60 * 1000) {
            recentToastsRef.current.delete(key);
          }
        }
      }
    };

    window.addEventListener('orma:toast', handleToast);
    return () => window.removeEventListener('orma:toast', handleToast);
  }, []);

  const removeToast = (id) => {
    setToasts(prev => prev.filter(t => t.id !== id));
  };

  const variantStyles = {
    success: {
      border: 'border-emerald-500/30',
      iconColor: 'text-emerald-400',
      bgGlow: 'from-emerald-500/10 to-transparent',
      Icon: CheckCircle2
    },
    error: {
      border: 'border-red-500/30',
      iconColor: 'text-red-400',
      bgGlow: 'from-red-500/10 to-transparent',
      Icon: AlertCircle
    },
    warning: {
      border: 'border-amber-500/30',
      iconColor: 'text-amber-400',
      bgGlow: 'from-amber-500/10 to-transparent',
      Icon: AlertTriangle
    },
    info: {
      border: 'border-blue-500/30',
      iconColor: 'text-blue-400',
      bgGlow: 'from-blue-500/10 to-transparent',
      Icon: Info
    }
  };

  return (
    <aside 
      aria-label="Notifications" 
      aria-live="polite"
      className="fixed bottom-6 right-6 z-[100] flex flex-col items-end gap-2.5 max-w-sm sm:max-w-md w-full px-4 sm:px-0 pointer-events-none"
    >
      <AnimatePresence>
        {toasts.map((toast) => {
          const config = variantStyles[toast.type] || variantStyles.info;
          const Icon = config.Icon;

          return (
            <motion.div
              key={toast.id}
              initial={{ opacity: 0, y: 15, scale: 0.95 }}
              animate={{ opacity: 1, y: 0, scale: 1 }}
              exit={{ opacity: 0, y: 10, scale: 0.95 }}
              transition={{ duration: 0.2 }}
              role="status"
              className={`relative flex items-center justify-between gap-3 p-4 rounded-2xl bg-[#060B1E]/95 backdrop-blur-2xl border ${config.border} bg-gradient-to-r ${config.bgGlow} shadow-[0_20px_50px_rgba(0,0,0,0.8),0_0_20px_rgba(59,130,246,0.15)] w-full pointer-events-auto overflow-hidden`}
            >
              <div className="flex items-center gap-3 min-w-0">
                <div className={`shrink-0 ${config.iconColor}`}>
                  <Icon className="w-5 h-5" />
                </div>
                <p className="text-xs sm:text-sm font-bold text-white tracking-tight leading-snug break-words">
                  {toast.message}
                </p>
              </div>

              <button
                type="button"
                onClick={() => removeToast(toast.id)}
                className="p-1 rounded-lg text-slate-400 hover:text-white hover:bg-white/10 transition-colors shrink-0 cursor-pointer"
                aria-label="Dismiss notification"
              >
                <X className="w-4 h-4" />
              </button>
            </motion.div>
          );
        })}
      </AnimatePresence>
    </aside>
  );
}

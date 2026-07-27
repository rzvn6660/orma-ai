import { useState, useEffect } from 'react';
import { AnimatePresence, motion } from 'framer-motion';
import { CheckCircle2, AlertCircle, Info } from 'lucide-react';

export default function GlobalToast() {
  const [toasts, setToasts] = useState([]);

  useEffect(() => {
    const handleToast = (e) => {
      const { type, message } = e.detail;
      const id = Date.now().toString() + Math.random().toString();
      setToasts(prev => [...prev, { id, type, message }]);

      setTimeout(() => {
        setToasts(prev => prev.filter(t => t.id !== id));
      }, 4000);
    };

    window.addEventListener('orma:toast', handleToast);
    return () => window.removeEventListener('orma:toast', handleToast);
  }, []);

  return (
    <div className="fixed bottom-6 left-1/2 -translate-x-1/2 z-[100] flex flex-col items-center gap-3 w-full max-w-sm px-4 pointer-events-none">
      <AnimatePresence>
        {toasts.map((toast) => {
          const isError = toast.type === 'error';
          const isSuccess = toast.type === 'success';

          return (
            <motion.div
              key={toast.id}
              initial={{ opacity: 0, y: 20, scale: 0.95 }}
              animate={{ opacity: 1, y: 0, scale: 1 }}
              exit={{ opacity: 0, y: -20, scale: 0.95 }}
              className={`flex items-center gap-3 px-5 py-4 rounded-2xl shadow-2xl border backdrop-blur-md w-full pointer-events-auto ${
                isError 
                  ? 'bg-red-500/10 border-red-500/20 text-red-400'
                  : isSuccess 
                    ? 'bg-emerald-500/10 border-emerald-500/20 text-emerald-400'
                    : 'bg-slate-800/80 border-slate-700 text-slate-200'
              }`}
            >
              {isError ? (
                <AlertCircle className="w-5 h-5 shrink-0" />
              ) : isSuccess ? (
                <CheckCircle2 className="w-5 h-5 shrink-0" />
              ) : (
                <Info className="w-5 h-5 shrink-0" />
              )}
              <span className="font-semibold text-sm">{toast.message}</span>
            </motion.div>
          );
        })}
      </AnimatePresence>
    </div>
  );
}

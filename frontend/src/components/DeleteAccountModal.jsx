import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { AlertTriangle, X, Trash2, ShieldAlert, RefreshCw } from 'lucide-react';
import { authApi } from '../services/api';

export default function DeleteAccountModal({ isOpen, onClose, user, onAccountDeleted }) {
  const [confirmText, setConfirmText] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  if (!isOpen) return null;

  const isConfirmed = confirmText.trim().toUpperCase() === 'DELETE';

  const handleDelete = async (e) => {
    e?.preventDefault();
    if (!isConfirmed || loading) return;

    setError('');
    setLoading(true);
    try {
      await authApi.deleteAccount();
      // Account deleted successfully from backend
      if (onAccountDeleted) {
        onAccountDeleted();
      } else {
        localStorage.removeItem('orma_token');
        window.location.href = '/';
      }
    } catch (err) {
      console.error('Failed to delete account:', err);
      setError(err.response?.data?.detail || err.message || 'Failed to delete account. Please try again.');
      setLoading(false);
    }
  };

  return (
    <AnimatePresence>
      <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-md">
        <motion.div
          initial={{ opacity: 0, scale: 0.95, y: 10 }}
          animate={{ opacity: 1, scale: 1, y: 0 }}
          exit={{ opacity: 0, scale: 0.95, y: 10 }}
          className="w-full max-w-lg bg-slate-900 border border-red-500/30 rounded-3xl p-6 sm:p-8 shadow-2xl relative overflow-hidden"
          role="dialog"
          aria-labelledby="delete-account-title"
        >
          {/* Subtle Ambient Red Glow */}
          <div className="absolute top-0 right-0 w-48 h-48 bg-red-600/10 rounded-full blur-3xl pointer-events-none" />

          {/* Close button */}
          <button
            type="button"
            onClick={onClose}
            disabled={loading}
            className="absolute top-5 right-5 p-2 rounded-xl text-slate-400 hover:text-white hover:bg-slate-800/80 transition-colors cursor-pointer"
            aria-label="Close modal"
          >
            <X className="w-5 h-5" />
          </button>

          {/* Header */}
          <div className="flex items-center gap-3.5 mb-5">
            <div className="w-12 h-12 rounded-2xl bg-red-600/20 border border-red-500/30 text-red-400 flex items-center justify-center shrink-0">
              <AlertTriangle className="w-6 h-6" />
            </div>
            <div>
              <h2 id="delete-account-title" className="text-xl font-extrabold text-white tracking-tight">
                Delete Account
              </h2>
              <p className="text-xs text-red-400/90 font-semibold mt-0.5">
                Permanent and irreversible action
              </p>
            </div>
          </div>

          {/* Warning summary */}
          <div className="p-4 rounded-2xl bg-red-950/25 border border-red-500/20 space-y-2 mb-5 text-xs text-slate-300">
            <p className="font-bold text-red-300">This will permanently erase your ORMA AI account for:</p>
            <p className="font-mono text-white text-xs bg-black/40 px-2.5 py-1.5 rounded-lg border border-red-500/20">
              {user?.email}
            </p>
            <ul className="list-disc pl-4 space-y-1 text-[11px] text-slate-400 pt-1">
              <li>All medication schedules and adherence history will be deleted.</li>
              <li>All uploaded health records and medical documents will be purged.</li>
              <li>All voice memory events and AI conversation history will be erased.</li>
              <li>Family caregiver connections and link codes will be revoked.</li>
            </ul>
          </div>

          {error && (
            <div className="mb-4 p-3 rounded-2xl bg-red-500/15 border border-red-500/30 text-red-300 text-xs font-semibold flex items-center gap-2">
              <ShieldAlert className="w-4 h-4 shrink-0" />
              <span>{error}</span>
            </div>
          )}

          {/* Confirmation Form */}
          <form onSubmit={handleDelete} className="space-y-4">
            <div>
              <label htmlFor="confirm-delete-input" className="block text-xs font-bold text-slate-300 mb-1.5">
                To confirm, type <span className="font-mono text-red-400 font-extrabold">DELETE</span> in capital letters:
              </label>
              <input
                id="confirm-delete-input"
                type="text"
                value={confirmText}
                onChange={(e) => setConfirmText(e.target.value)}
                placeholder="DELETE"
                autoComplete="off"
                className="w-full h-12 bg-slate-950/80 border border-slate-700 focus:border-red-500 rounded-xl px-4 font-mono text-sm text-white placeholder-slate-600 outline-none transition-colors"
              />
            </div>

            <div className="pt-2 flex gap-3">
              <button
                type="button"
                onClick={onClose}
                disabled={loading}
                className="flex-1 h-12 rounded-2xl bg-slate-800 hover:bg-slate-700/80 text-slate-300 text-sm font-bold transition-colors cursor-pointer"
              >
                Cancel
              </button>
              <button
                type="submit"
                disabled={!isConfirmed || loading}
                className="flex-1 h-12 rounded-2xl bg-red-600 hover:bg-red-500 disabled:bg-slate-800/80 text-white disabled:text-slate-600 text-sm font-extrabold shadow-lg shadow-red-600/20 transition-all cursor-pointer disabled:cursor-not-allowed flex items-center justify-center gap-2"
              >
                {loading ? (
                  <>
                    <RefreshCw className="w-4 h-4 animate-spin" />
                    <span>Deleting...</span>
                  </>
                ) : (
                  <>
                    <Trash2 className="w-4 h-4" />
                    <span>Delete Account</span>
                  </>
                )}
              </button>
            </div>
          </form>
        </motion.div>
      </div>
    </AnimatePresence>
  );
}

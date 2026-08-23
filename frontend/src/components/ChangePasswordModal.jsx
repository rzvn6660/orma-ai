import { useState, useEffect, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Lock, Eye, EyeOff, X, Check, AlertCircle, Loader2 } from 'lucide-react';
import { authApi } from '../services/api';

export default function ChangePasswordModal({ isOpen, onClose }) {
  const [currentPassword, setCurrentPassword] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');

  const [showCurrent, setShowCurrent] = useState(false);
  const [showNew, setShowNew] = useState(false);
  const [showConfirm, setShowConfirm] = useState(false);

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState(false);

  const currentInputRef = useRef(null);

  // Reset form states when modal opens/closes
  useEffect(() => {
    if (isOpen) {
      setCurrentPassword('');
      setNewPassword('');
      setConfirmPassword('');
      setShowCurrent(false);
      setShowNew(false);
      setShowConfirm(false);
      setError('');
      setSuccess(false);
      setLoading(false);

      // Focus first input
      setTimeout(() => {
        currentInputRef.current?.focus();
      }, 50);
    }
  }, [isOpen]);

  // Handle ESC key to close
  useEffect(() => {
    const handleKeyDown = (e) => {
      if (e.key === 'Escape' && isOpen && !loading) {
        onClose();
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [isOpen, loading, onClose]);

  // Real-time password requirement checklist (matches backend validate_password)
  const reqLength = newPassword.length >= 8;
  const reqLower = /[a-z]/.test(newPassword);
  const reqUpper = /[A-Z]/.test(newPassword);
  const reqNum = /\d/.test(newPassword);
  const reqSpecial = /[@$!%*?&]/.test(newPassword);
  const reqMatch = newPassword.length > 0 && newPassword === confirmPassword;

  const isFormValid =
    currentPassword.trim().length > 0 &&
    reqLength &&
    reqLower &&
    reqUpper &&
    reqNum &&
    reqSpecial &&
    reqMatch;

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (loading) return;

    setError('');

    // Pre-submission validation
    if (!currentPassword) {
      setError('Please enter your current password.');
      return;
    }

    if (!newPassword) {
      setError('Please enter a new password.');
      return;
    }

    if (newPassword !== confirmPassword) {
      setError('Passwords do not match.');
      return;
    }

    if (!reqLength) {
      setError('Password must be at least 8 characters long.');
      return;
    }
    if (!reqLower) {
      setError('Password must contain at least one lowercase letter.');
      return;
    }
    if (!reqUpper) {
      setError('Password must contain at least one uppercase letter.');
      return;
    }
    if (!reqNum) {
      setError('Password must contain at least one number.');
      return;
    }
    if (!reqSpecial) {
      setError('Password must contain at least one special character (@$!%*?&).');
      return;
    }

    setLoading(true);

    try {
      await authApi.changePassword(currentPassword, newPassword);
      setSuccess(true);
      setTimeout(() => {
        onClose();
      }, 1500);
    } catch (err) {
      const detail =
        err.response?.data?.detail ||
        (err.response?.status === 401
          ? 'Session expired. Please sign in again.'
          : 'Failed to change password. Please try again.');
      setError(detail);
    } finally {
      setLoading(false);
    }
  };

  return (
    <AnimatePresence>
      {isOpen && (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-sm"
          role="dialog"
          aria-modal="true"
          aria-labelledby="change-password-title"
          aria-describedby="change-password-desc"
          onClick={(e) => {
            if (e.target === e.currentTarget && !loading) {
              onClose();
            }
          }}
        >
          <motion.div
            initial={{ opacity: 0, scale: 0.95, y: 10 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.95, y: 10 }}
            transition={{ duration: 0.18, ease: 'easeOut' }}
            className="w-full max-w-md bg-slate-900 border border-slate-800 rounded-3xl p-6 sm:p-7 shadow-2xl relative text-slate-100 flex flex-col gap-5 max-h-[90vh] overflow-y-auto"
            onClick={(e) => e.stopPropagation()}
          >
            {/* Header */}
            <div className="flex items-start justify-between gap-4">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-2xl bg-blue-500/10 border border-blue-500/20 flex items-center justify-center text-blue-400 shrink-0">
                  <Lock className="w-5 h-5" />
                </div>
                <div>
                  <h2 id="change-password-title" className="text-xl font-bold text-white tracking-tight">
                    Change Password
                  </h2>
                  <p id="change-password-desc" className="text-xs text-slate-400 mt-0.5">
                    Update your password to keep your ORMA AI account secure.
                  </p>
                </div>
              </div>

              <button
                type="button"
                onClick={onClose}
                disabled={loading}
                className="text-slate-400 hover:text-white p-1.5 rounded-xl hover:bg-slate-800 transition-colors cursor-pointer disabled:opacity-50"
                aria-label="Close dialog"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            {/* Error message */}
            {error && (
              <div className="p-3.5 bg-red-500/10 border border-red-500/20 rounded-2xl text-red-400 text-xs font-semibold flex items-center gap-2.5">
                <AlertCircle className="w-4 h-4 shrink-0" />
                <span>{error}</span>
              </div>
            )}

            {/* Success message */}
            {success ? (
              <div className="py-8 flex flex-col items-center justify-center text-center gap-3">
                <div className="w-14 h-14 rounded-full bg-emerald-500/10 border border-emerald-500/30 flex items-center justify-center text-emerald-400">
                  <Check className="w-7 h-7" />
                </div>
                <h3 className="text-lg font-bold text-white">Password Changed Successfully</h3>
                <p className="text-xs text-slate-400">Your ORMA account security credentials have been updated.</p>
              </div>
            ) : (
              <form onSubmit={handleSubmit} className="space-y-4">
                {/* Current Password */}
                <div>
                  <label
                    htmlFor="current-password-input"
                    className="block text-xs font-bold text-slate-300 uppercase tracking-wider mb-1.5 ml-0.5"
                  >
                    Current Password
                  </label>
                  <div className="relative flex items-center">
                    <input
                      ref={currentInputRef}
                      id="current-password-input"
                      required
                      type={showCurrent ? 'text' : 'password'}
                      value={currentPassword}
                      onChange={(e) => setCurrentPassword(e.target.value)}
                      placeholder="••••••••"
                      autoComplete="current-password"
                      className="w-full h-12 bg-slate-800/80 border border-slate-700 rounded-xl px-3.5 pr-11 text-white text-sm font-medium placeholder:text-slate-500 focus:outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-500/20 transition-all"
                    />
                    <button
                      type="button"
                      onClick={() => setShowCurrent(!showCurrent)}
                      className="absolute right-2 p-1.5 rounded-lg text-slate-400 hover:text-slate-200 transition-colors cursor-pointer"
                      aria-label={showCurrent ? 'Hide current password' : 'Show current password'}
                    >
                      {showCurrent ? <EyeOff className="w-4 h-4 text-blue-400" /> : <Eye className="w-4 h-4" />}
                    </button>
                  </div>
                </div>

                {/* New Password */}
                <div>
                  <label
                    htmlFor="new-password-input"
                    className="block text-xs font-bold text-slate-300 uppercase tracking-wider mb-1.5 ml-0.5"
                  >
                    New Password
                  </label>
                  <div className="relative flex items-center">
                    <input
                      id="new-password-input"
                      required
                      type={showNew ? 'text' : 'password'}
                      value={newPassword}
                      onChange={(e) => setNewPassword(e.target.value)}
                      placeholder="••••••••"
                      autoComplete="new-password"
                      className="w-full h-12 bg-slate-800/80 border border-slate-700 rounded-xl px-3.5 pr-11 text-white text-sm font-medium placeholder:text-slate-500 focus:outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-500/20 transition-all"
                    />
                    <button
                      type="button"
                      onClick={() => setShowNew(!showNew)}
                      className="absolute right-2 p-1.5 rounded-lg text-slate-400 hover:text-slate-200 transition-colors cursor-pointer"
                      aria-label={showNew ? 'Hide new password' : 'Show new password'}
                    >
                      {showNew ? <EyeOff className="w-4 h-4 text-blue-400" /> : <Eye className="w-4 h-4" />}
                    </button>
                  </div>
                </div>

                {/* Confirm New Password */}
                <div>
                  <label
                    htmlFor="confirm-password-input"
                    className="block text-xs font-bold text-slate-300 uppercase tracking-wider mb-1.5 ml-0.5"
                  >
                    Confirm New Password
                  </label>
                  <div className="relative flex items-center">
                    <input
                      id="confirm-password-input"
                      required
                      type={showConfirm ? 'text' : 'password'}
                      value={confirmPassword}
                      onChange={(e) => setConfirmPassword(e.target.value)}
                      placeholder="••••••••"
                      autoComplete="new-password"
                      className="w-full h-12 bg-slate-800/80 border border-slate-700 rounded-xl px-3.5 pr-11 text-white text-sm font-medium placeholder:text-slate-500 focus:outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-500/20 transition-all"
                    />
                    <button
                      type="button"
                      onClick={() => setShowConfirm(!showConfirm)}
                      className="absolute right-2 p-1.5 rounded-lg text-slate-400 hover:text-slate-200 transition-colors cursor-pointer"
                      aria-label={showConfirm ? 'Hide confirmation password' : 'Show confirmation password'}
                    >
                      {showConfirm ? <EyeOff className="w-4 h-4 text-blue-400" /> : <Eye className="w-4 h-4" />}
                    </button>
                  </div>
                </div>

                {/* Requirements Checklist */}
                {newPassword.length > 0 && (
                  <div className="p-3.5 bg-slate-800/40 border border-slate-700/60 rounded-2xl space-y-1.5 text-[11px] font-semibold text-slate-400">
                    <p className="text-[10px] uppercase font-bold text-slate-500 tracking-wider mb-1">
                      Password Requirements
                    </p>
                    <div className={`flex items-center gap-1.5 ${reqLength ? 'text-emerald-400' : 'text-slate-400'}`}>
                      <Check className={`w-3.5 h-3.5 ${reqLength ? 'text-emerald-400' : 'text-slate-500'}`} />
                      <span>At least 8 characters</span>
                    </div>
                    <div className={`flex items-center gap-1.5 ${reqLower ? 'text-emerald-400' : 'text-slate-400'}`}>
                      <Check className={`w-3.5 h-3.5 ${reqLower ? 'text-emerald-400' : 'text-slate-500'}`} />
                      <span>At least one lowercase letter</span>
                    </div>
                    <div className={`flex items-center gap-1.5 ${reqUpper ? 'text-emerald-400' : 'text-slate-400'}`}>
                      <Check className={`w-3.5 h-3.5 ${reqUpper ? 'text-emerald-400' : 'text-slate-500'}`} />
                      <span>At least one uppercase letter</span>
                    </div>
                    <div className={`flex items-center gap-1.5 ${reqNum ? 'text-emerald-400' : 'text-slate-400'}`}>
                      <Check className={`w-3.5 h-3.5 ${reqNum ? 'text-emerald-400' : 'text-slate-500'}`} />
                      <span>At least one number</span>
                    </div>
                    <div className={`flex items-center gap-1.5 ${reqSpecial ? 'text-emerald-400' : 'text-slate-400'}`}>
                      <Check className={`w-3.5 h-3.5 ${reqSpecial ? 'text-emerald-400' : 'text-slate-500'}`} />
                      <span>At least one special character (@$!%*?&)</span>
                    </div>
                    {confirmPassword.length > 0 && (
                      <div className={`flex items-center gap-1.5 ${reqMatch ? 'text-emerald-400' : 'text-red-400'}`}>
                        <Check className={`w-3.5 h-3.5 ${reqMatch ? 'text-emerald-400' : 'text-red-400'}`} />
                        <span>{reqMatch ? 'Passwords match' : 'Passwords do not match'}</span>
                      </div>
                    )}
                  </div>
                )}

                {/* Action Buttons */}
                <div className="pt-2 flex items-center justify-end gap-3">
                  <button
                    type="button"
                    onClick={onClose}
                    disabled={loading}
                    className="px-4 py-2.5 rounded-xl border border-slate-700 bg-slate-800 hover:bg-slate-700 text-slate-300 hover:text-white font-semibold text-xs transition-colors cursor-pointer disabled:opacity-50"
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    disabled={loading || !isFormValid}
                    className="px-5 py-2.5 rounded-xl bg-blue-600 hover:bg-blue-500 text-white font-bold text-xs shadow-lg shadow-blue-500/20 transition-all flex items-center justify-center gap-2 cursor-pointer disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    {loading ? (
                      <>
                        <Loader2 className="w-3.5 h-3.5 animate-spin" />
                        <span>Changing password...</span>
                      </>
                    ) : (
                      'Change Password'
                    )}
                  </button>
                </div>
              </form>
            )}
          </motion.div>
        </div>
      )}
    </AnimatePresence>
  );
}

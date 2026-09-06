import { useState, useEffect, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Mail, CheckCircle2, AlertCircle, X, RefreshCw, ShieldCheck } from 'lucide-react';
import { authApi } from '../services/api';

export default function VerifyEmailModal({ isOpen, onClose, user, onVerified }) {
  const [otp, setOtp] = useState('');
  const [loading, setLoading] = useState(false);
  const [resending, setResending] = useState(false);
  const [cooldown, setCooldown] = useState(0);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState(false);
  const inputRef = useRef(null);

  const email = user?.email || '';

  // Focus input on open
  useEffect(() => {
    if (isOpen) {
      setOtp('');
      setError('');
      setSuccess(false);
      setTimeout(() => inputRef.current?.focus(), 100);
    }
  }, [isOpen]);

  // Cooldown countdown timer
  useEffect(() => {
    if (cooldown <= 0) return;
    const timer = setInterval(() => {
      setCooldown((prev) => (prev > 0 ? prev - 1 : 0));
    }, 1000);
    return () => clearInterval(timer);
  }, [cooldown]);

  if (!isOpen) return null;

  const handleResend = async () => {
    if (cooldown > 0 || resending || !email) return;
    setError('');
    setResending(true);
    try {
      await authApi.resendVerificationOtp(email);
      setCooldown(60);
    } catch (err) {
      const msg = err.response?.data?.detail || err.message || 'Failed to send verification code.';
      setError(msg);
      // If backend returned wait time in 429, extract seconds
      const match = typeof msg === 'string' && msg.match(/wait (\d+) seconds/i);
      if (match && match[1]) {
        setCooldown(parseInt(match[1], 10));
      }
    } finally {
      setResending(false);
    }
  };

  const handleVerify = async (e) => {
    e?.preventDefault();
    const cleanOtp = otp.trim();
    if (cleanOtp.length !== 6) {
      setError('Please enter the complete 6-digit verification code.');
      return;
    }
    setError('');
    setLoading(true);
    try {
      const res = await authApi.verifyEmailOtp(email, cleanOtp);
      setSuccess(true);
      const updatedUser = { ...(user || {}), email_verified: true, ...(res.user || {}) };
      window.dispatchEvent(new CustomEvent('orma_user_updated', { detail: { email_verified: true } }));
      if (onVerified) onVerified(updatedUser);
      setTimeout(() => {
        onClose();
      }, 1400);
    } catch (err) {
      const msg = err.response?.data?.detail || err.message || 'Verification failed. Please check the code.';
      setError(msg);
    } finally {
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
          className="w-full max-w-md bg-slate-900 border border-slate-800 rounded-3xl p-6 sm:p-8 shadow-2xl relative overflow-hidden"
          role="dialog"
          aria-labelledby="verify-email-title"
        >
          {/* Subtle Ambient Glow */}
          <div className="absolute top-0 right-0 w-48 h-48 bg-blue-600/10 rounded-full blur-3xl pointer-events-none" />

          {/* Close button */}
          <button
            type="button"
            onClick={onClose}
            className="absolute top-5 right-5 p-2 rounded-xl text-slate-400 hover:text-white hover:bg-slate-800/80 transition-colors cursor-pointer"
            aria-label="Close modal"
          >
            <X className="w-5 h-5" />
          </button>

          {/* Header */}
          <div className="flex items-center gap-3.5 mb-6">
            <div className="w-12 h-12 rounded-2xl bg-blue-600/20 border border-blue-500/30 text-blue-400 flex items-center justify-center shrink-0">
              <Mail className="w-6 h-6" />
            </div>
            <div>
              <h2 id="verify-email-title" className="text-xl font-bold text-white tracking-tight">
                Verify Your Email
              </h2>
              <p className="text-xs text-slate-400 mt-0.5">
                Confirm ownership of your ORMA AI account
              </p>
            </div>
          </div>

          {/* Body */}
          {success ? (
            <motion.div
              initial={{ opacity: 0, scale: 0.9 }}
              animate={{ opacity: 1, scale: 1 }}
              className="py-8 text-center space-y-3"
            >
              <div className="w-16 h-16 rounded-full bg-emerald-500/20 border border-emerald-500/30 text-emerald-400 mx-auto flex items-center justify-center">
                <CheckCircle2 className="w-8 h-8" />
              </div>
              <h3 className="text-lg font-extrabold text-white">Email Verified!</h3>
              <p className="text-sm text-slate-400">
                Your email <span className="text-white font-semibold">{email}</span> is now verified.
              </p>
            </motion.div>
          ) : (
            <form onSubmit={handleVerify} className="space-y-5">
              <div className="p-3.5 rounded-2xl bg-slate-950/60 border border-slate-800 flex items-center justify-between gap-3">
                <div className="min-w-0 flex-1">
                  <p className="text-[11px] font-bold text-slate-400 uppercase tracking-wider">Recipient Address</p>
                  <p className="text-sm font-semibold text-white truncate mt-0.5">{email}</p>
                </div>
                <button
                  type="button"
                  onClick={handleResend}
                  disabled={cooldown > 0 || resending}
                  className="px-3 py-1.5 rounded-xl bg-blue-600/20 hover:bg-blue-600/30 text-blue-400 disabled:text-slate-500 disabled:bg-slate-800/40 border border-blue-500/30 disabled:border-transparent text-xs font-bold transition-colors cursor-pointer disabled:cursor-not-allowed flex items-center gap-1.5 shrink-0"
                >
                  <RefreshCw className={`w-3.5 h-3.5 ${resending ? 'animate-spin' : ''}`} />
                  <span>{cooldown > 0 ? `${cooldown}s` : 'Send Code'}</span>
                </button>
              </div>

              {/* Error Alert */}
              {error && (
                <div className="p-3 rounded-2xl bg-red-500/10 border border-red-500/25 text-red-400 text-xs font-semibold flex items-start gap-2.5">
                  <AlertCircle className="w-4 h-4 shrink-0 mt-0.5" />
                  <span>{error}</span>
                </div>
              )}

              {/* OTP Input */}
              <div className="space-y-1.5">
                <label htmlFor="email-otp-input" className="block text-xs font-bold text-slate-300 uppercase tracking-wider">
                  Enter 6-Digit Code
                </label>
                <input
                  id="email-otp-input"
                  ref={inputRef}
                  type="text"
                  inputMode="numeric"
                  maxLength={6}
                  value={otp}
                  onChange={(e) => setOtp(e.target.value.replace(/\D/g, ''))}
                  placeholder="123456"
                  className="w-full h-14 bg-slate-950/80 border border-slate-700 focus:border-blue-500 rounded-2xl px-4 text-center font-mono text-2xl font-bold tracking-[0.4em] text-white outline-none transition-colors"
                />
                <p className="text-[11px] text-slate-500 text-center mt-1">
                  Check your inbox for the code from ORMA AI.
                </p>
              </div>

              {/* Submit Button */}
              <div className="pt-2 flex gap-3">
                <button
                  type="button"
                  onClick={onClose}
                  className="flex-1 h-12 rounded-2xl bg-slate-800 hover:bg-slate-700/80 text-slate-300 text-sm font-bold transition-colors cursor-pointer"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={loading || otp.trim().length !== 6}
                  className="flex-1 h-12 rounded-2xl bg-blue-600 hover:bg-blue-500 disabled:bg-slate-800 text-white disabled:text-slate-500 text-sm font-extrabold shadow-lg shadow-blue-600/20 transition-all cursor-pointer disabled:cursor-not-allowed flex items-center justify-center gap-2"
                >
                  {loading ? (
                    <>
                      <RefreshCw className="w-4 h-4 animate-spin" />
                      <span>Verifying...</span>
                    </>
                  ) : (
                    <>
                      <ShieldCheck className="w-4 h-4" />
                      <span>Verify Code</span>
                    </>
                  )}
                </button>
              </div>
            </form>
          )}
        </motion.div>
      </div>
    </AnimatePresence>
  );
}

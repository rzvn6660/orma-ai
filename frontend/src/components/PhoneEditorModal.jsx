import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Phone, X, Check, AlertCircle, RefreshCw, Globe, ShieldCheck, Trash2 } from 'lucide-react';
import { authApi, caregiverApi } from '../services/api';

const COUNTRIES = [
  { code: '+91', name: 'India', flag: '🇮🇳', sample: '9876543210' },
  { code: '+971', name: 'UAE', flag: '🇦🇪', sample: '501234567' },
  { code: '+1', name: 'US / Canada', flag: '🇺🇸', sample: '2025550199' },
  { code: '+44', name: 'UK', flag: '🇬🇧', sample: '7911123456' },
  { code: '+65', name: 'Singapore', flag: '🇸🇬', sample: '81234567' },
  { code: '+61', name: 'Australia', flag: '🇦🇺', sample: '412345678' },
  { code: '+49', name: 'Germany', flag: '🇩🇪', sample: '15123456789' },
  { code: '+966', name: 'Saudi Arabia', flag: '🇸🇦', sample: '512345678' },
  { code: '+974', name: 'Qatar', flag: '🇶🇦', sample: '33123456' },
  { code: '+965', name: 'Kuwait', flag: '🇰🇼', sample: '51234567' },
];

/**
 * PhoneEditorModal
 * Accessible dialog for managing international emergency contact numbers.
 * Normalizes numbers to E.164 standard (e.g. +919876543210).
 */
export default function PhoneEditorModal({
  isOpen,
  onClose,
  initialPhone = '',
  onPhoneSaved
}) {
  const parseInitial = () => {
    if (!initialPhone) return { countryCode: '+91', localNumber: '' };
    const matched = COUNTRIES.find(c => initialPhone.startsWith(c.code));
    if (matched) {
      return {
        countryCode: matched.code,
        localNumber: initialPhone.slice(matched.code.length).trim()
      };
    }
    return { countryCode: '+91', localNumber: initialPhone.replace(/^\+/, '') };
  };

  const [selectedCountry, setSelectedCountry] = useState(parseInitial().countryCode);
  const [localNumber, setLocalNumber] = useState(parseInitial().localNumber);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  // Synchronize when initialPhone changes
  useEffect(() => {
    const init = parseInitial();
    setSelectedCountry(init.countryCode);
    setLocalNumber(init.localNumber);
    setError('');
  }, [initialPhone, isOpen]);

  if (!isOpen) return null;

  // Clean and normalize number
  const cleanDigits = localNumber.replace(/\D/g, '');
  const normalizedNumber = cleanDigits ? `${selectedCountry}${cleanDigits}` : '';

  const handleSave = async (e) => {
    e.preventDefault();
    setError('');

    if (!cleanDigits) {
      setError('Please enter a phone number.');
      return;
    }

    if (cleanDigits.length < 7 || cleanDigits.length > 15) {
      setError('Please enter a valid phone number (7 to 15 digits).');
      return;
    }

    setLoading(true);
    try {
      // 1. Persist to backend database via authApi
      const updatedUser = await authApi.updateMe({ phone: normalizedNumber });
      
      // 2. Also ensure caregiver profile is synced if caregiverApi is available
      try {
        await caregiverApi.updatePhone(normalizedNumber);
      } catch (cgErr) {
        // Non-fatal if role is not caregiver
      }

      // 3. Query authoritative profile directly from database
      const freshUser = await authApi.getMe();
      const authoritativeUser = freshUser || updatedUser;

      // 4. Update local storage user if present
      const storedUser = localStorage.getItem('orma_user');
      if (storedUser) {
        try {
          const parsed = JSON.parse(storedUser);
          parsed.phone = normalizedNumber;
          localStorage.setItem('orma_user', JSON.stringify(parsed));
        } catch {}
      }

      // 5. Broadcast to all application components
      window.dispatchEvent(new CustomEvent('orma_user_updated', {
        detail: authoritativeUser
      }));

      window.dispatchEvent(new CustomEvent('orma:toast', { 
        detail: { type: 'success', message: 'Phone number saved successfully.' } 
      }));

      if (onPhoneSaved) {
        onPhoneSaved(normalizedNumber, authoritativeUser);
      }
      onClose();
    } catch (err) {
      console.error('Failed to save phone number:', err);
      setError("Couldn't save your phone number. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  const handleRemove = async () => {
    setError('');
    setLoading(true);
    try {
      const updatedUser = await authApi.updateMe({ phone: '' });
      try {
        await caregiverApi.updatePhone('');
      } catch (cgErr) {}

      const freshUser = await authApi.getMe();
      const authoritativeUser = freshUser || updatedUser;
      
      const storedUser = localStorage.getItem('orma_user');
      if (storedUser) {
        try {
          const parsed = JSON.parse(storedUser);
          parsed.phone = null;
          localStorage.setItem('orma_user', JSON.stringify(parsed));
        } catch {}
      }

      window.dispatchEvent(new CustomEvent('orma_user_updated', {
        detail: authoritativeUser
      }));

      window.dispatchEvent(new CustomEvent('orma:toast', { 
        detail: { type: 'info', message: 'Phone number removed.' } 
      }));

      if (onPhoneSaved) {
        onPhoneSaved(null, authoritativeUser);
      }
      onClose();
    } catch (err) {
      console.error('Failed to remove phone number:', err);
      setError("Couldn't remove your phone number. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <AnimatePresence>
      <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
        {/* Backdrop */}
        <motion.div 
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          onClick={onClose}
          className="absolute inset-0 bg-slate-950/80 backdrop-blur-md"
          aria-hidden="true"
        />

        {/* Dialog Container */}
        <motion.div 
          initial={{ opacity: 0, scale: 0.95, y: 15 }}
          animate={{ opacity: 1, scale: 1, y: 0 }}
          exit={{ opacity: 0, scale: 0.95, y: 15 }}
          transition={{ duration: 0.15 }}
          role="dialog"
          aria-modal="true"
          aria-labelledby="phone-dialog-title"
          className="relative bg-slate-900 border border-white/15 rounded-3xl p-6 sm:p-8 max-w-md w-full shadow-2xl z-10 space-y-6"
        >
          {/* Dialog Header */}
          <div className="flex items-start justify-between">
            <div className="flex items-center gap-3">
              <div className="w-12 h-12 rounded-2xl bg-blue-600/20 border border-blue-500/30 flex items-center justify-center text-blue-400 shrink-0">
                <Phone className="w-6 h-6" />
              </div>
              <div>
                <h3 id="phone-dialog-title" className="text-xl font-extrabold text-white tracking-tight">
                  Emergency Contact Phone
                </h3>
                <p className="text-xs text-slate-400 mt-0.5">
                  Direct one-tap call for your linked family member.
                </p>
              </div>
            </div>
            <button
              type="button"
              onClick={onClose}
              className="p-2 text-slate-400 hover:text-white rounded-xl bg-slate-800/50 hover:bg-slate-800 transition-colors"
              aria-label="Close dialog"
            >
              <X className="w-5 h-5" />
            </button>
          </div>

          {/* Form */}
          <form onSubmit={handleSave} className="space-y-4">
            <div>
              <label className="block text-xs font-bold uppercase tracking-wider text-slate-300 mb-2">
                Country & Phone Number
              </label>

              <div className="flex items-center gap-2">
                {/* Country Code Selector */}
                <div className="relative w-36 shrink-0">
                  <select
                    value={selectedCountry}
                    onChange={(e) => setSelectedCountry(e.target.value)}
                    className="w-full bg-slate-950 border border-white/10 rounded-xl px-3 py-3 text-xs font-bold text-white focus:outline-none focus:border-blue-500 appearance-none cursor-pointer"
                    aria-label="Country Code"
                  >
                    {COUNTRIES.map((c) => (
                      <option key={c.code} value={c.code} className="bg-slate-900 text-white">
                        {c.flag} {c.code} ({c.name})
                      </option>
                    ))}
                  </select>
                </div>

                {/* Local Number Input */}
                <div className="flex-1">
                  <input
                    type="tel"
                    value={localNumber}
                    onChange={(e) => setLocalNumber(e.target.value)}
                    placeholder="98765 43210"
                    autoFocus
                    className="w-full bg-slate-950 border border-white/10 rounded-xl px-4 py-3 text-sm font-bold text-white placeholder-slate-600 focus:outline-none focus:border-blue-500"
                    aria-label="Phone Number"
                  />
                </div>
              </div>

              {/* Normalized Format Preview */}
              {cleanDigits.length >= 4 && (
                <p className="text-[11px] text-slate-400 mt-2 font-mono flex items-center gap-1">
                  <ShieldCheck className="w-3 h-3 text-blue-400" />
                  <span>Callable format: <strong className="text-cyan-300">{normalizedNumber}</strong></span>
                </p>
              )}
            </div>

            {/* Error Feedback */}
            {error && (
              <div className="p-3 bg-red-500/10 border border-red-500/30 rounded-xl flex items-center gap-2 text-red-300 text-xs font-semibold">
                <AlertCircle className="w-4 h-4 shrink-0" />
                <span>{error}</span>
              </div>
            )}

            {/* Action Buttons */}
            <div className="space-y-2 pt-3 border-t border-white/10">
              <div className="flex items-center gap-3">
                <button
                  type="button"
                  onClick={onClose}
                  disabled={loading}
                  className="w-1/2 py-3 px-4 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-300 font-bold text-xs transition-colors min-h-[48px] cursor-pointer"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={loading}
                  className="w-1/2 py-3 px-4 rounded-xl bg-blue-600 hover:bg-blue-500 text-white font-extrabold text-xs shadow-md shadow-blue-600/30 transition-all min-h-[48px] cursor-pointer flex items-center justify-center gap-2"
                >
                  {loading ? (
                    <>
                      <RefreshCw className="w-4 h-4 animate-spin" />
                      <span>Saving...</span>
                    </>
                  ) : (
                    <>
                      <Check className="w-4 h-4" />
                      <span>Save Phone</span>
                    </>
                  )}
                </button>
              </div>

              {/* Remove Option if initial phone exists */}
              {initialPhone && (
                <button
                  type="button"
                  onClick={handleRemove}
                  disabled={loading}
                  className="w-full py-2.5 px-4 rounded-xl text-red-400 hover:text-red-300 hover:bg-red-500/10 text-xs font-bold transition-colors flex items-center justify-center gap-1.5 cursor-pointer"
                >
                  <Trash2 className="w-3.5 h-3.5" />
                  <span>Remove Phone Number</span>
                </button>
              )}
            </div>
          </form>
        </motion.div>
      </div>
    </AnimatePresence>
  );
}

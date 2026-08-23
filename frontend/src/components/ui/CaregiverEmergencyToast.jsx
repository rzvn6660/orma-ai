import React from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { AlertOctagon, PhoneCall, Check, Volume2, X, ChevronRight, ShieldAlert } from 'lucide-react';
import { unlockAudioContext } from '../../utils/emergencyAudio';
import { formatEmergencyTimestamp } from '../../utils/timeUtils';

/**
 * CaregiverEmergencyToast
 * Accessible 21st.dev-inspired Toast Notification for Incoming Real-Time Emergency Alerts.
 * Displays high-priority alert details, direct emergency navigation, and sound controls.
 */
export default function CaregiverEmergencyToast({
  alert,
  onViewEmergency,
  onAcknowledge,
  onDismiss,
  audioBlocked = false,
  userTimezone
}) {
  if (!alert) return null;

  const elderName = alert.elder_name || 'Your linked family member';
  const alertTime = formatEmergencyTimestamp(alert.created_at, userTimezone);

  return (
    <AnimatePresence>
      <div 
        className="fixed top-6 right-4 sm:right-8 z-50 max-w-md w-full pointer-events-auto"
        role="alert"
        aria-live="assertive"
      >
        <motion.div
          initial={{ opacity: 0, y: -20, scale: 0.95 }}
          animate={{ opacity: 1, y: 0, scale: 1 }}
          exit={{ opacity: 0, y: -20, scale: 0.95 }}
          transition={{ duration: 0.2, ease: "easeOut" }}
          className="bg-slate-900/95 border-2 border-red-500 rounded-3xl p-5 shadow-[0_10px_40px_rgba(239,68,68,0.35)] backdrop-blur-2xl text-white space-y-4 relative overflow-hidden"
        >
          {/* Subtle Top Red Accent Light */}
          <div className="absolute top-0 left-0 right-0 h-1 bg-gradient-to-r from-red-600 via-rose-500 to-red-600 animate-pulse" />

          {/* Top Bar: Icon + Header + Close */}
          <div className="flex items-start justify-between gap-3">
            <div className="flex items-center gap-3">
              <div className="w-11 h-11 rounded-2xl bg-red-500/20 border border-red-500/40 flex items-center justify-center text-red-400 shrink-0 shadow-lg shadow-red-500/20 animate-pulse">
                <AlertOctagon className="w-6 h-6" />
              </div>
              <div>
                <div className="flex items-center gap-2">
                  <span className="text-xs font-black uppercase tracking-wider text-red-400 bg-red-500/10 px-2 py-0.5 rounded-full border border-red-500/30">
                    Emergency Alert
                  </span>
                  <span className="text-[11px] text-slate-400 font-medium">
                    {alertTime}
                  </span>
                </div>
                <h3 className="text-base font-extrabold text-white tracking-tight mt-1">
                  {elderName}
                </h3>
              </div>
            </div>

            <button
              type="button"
              onClick={onDismiss}
              className="p-1.5 text-slate-400 hover:text-white rounded-xl bg-slate-800/60 hover:bg-slate-800 transition-colors cursor-pointer"
              aria-label="Dismiss alert toast"
            >
              <X className="w-4 h-4" />
            </button>
          </div>

          {/* Body Message */}
          <p className="text-xs sm:text-sm text-slate-200 leading-relaxed font-medium">
            {alert.message || `${elderName} may need immediate assistance.`}
          </p>

          {/* Audio Autoplay Unblock Fallback Banner */}
          {audioBlocked && (
            <button
              type="button"
              onClick={() => unlockAudioContext()}
              className="w-full py-2 px-3 rounded-xl bg-amber-500/20 hover:bg-amber-500/30 border border-amber-500/40 text-amber-300 text-xs font-bold flex items-center justify-center gap-2 cursor-pointer transition-colors"
            >
              <Volume2 className="w-4 h-4 animate-bounce" />
              <span>Audio is paused by browser. Tap to enable alert sound</span>
            </button>
          )}

          {/* Action Buttons */}
          <div className="flex items-center gap-2.5 pt-1">
            <button
              type="button"
              onClick={onViewEmergency}
              className="flex-1 py-3 px-4 rounded-2xl bg-red-600 hover:bg-red-500 text-white font-extrabold text-xs sm:text-sm shadow-md shadow-red-600/30 transition-all flex items-center justify-center gap-1.5 min-h-[48px] cursor-pointer"
            >
              <span>View Emergency</span>
              <ChevronRight className="w-4 h-4" />
            </button>

            {onAcknowledge && (
              <button
                type="button"
                onClick={onAcknowledge}
                className="py-3 px-4 rounded-2xl bg-slate-800 hover:bg-slate-700 text-slate-200 border border-white/10 hover:border-white/20 font-bold text-xs sm:text-sm transition-colors flex items-center justify-center gap-1.5 min-h-[48px] cursor-pointer"
              >
                <Check className="w-4 h-4 text-emerald-400" />
                <span>Acknowledge</span>
              </button>
            )}
          </div>
        </motion.div>
      </div>
    </AnimatePresence>
  );
}

import React, { useEffect, useRef } from 'react';
import { motion, AnimatePresence, useReducedMotion } from 'framer-motion';
import { 
  AlertOctagon, 
  Phone, 
  Check, 
  Volume2, 
  X, 
  ChevronRight, 
  ShieldAlert, 
  Clock, 
  ExternalLink 
} from 'lucide-react';
import { unlockAudioContext } from '../../utils/emergencyAudio';
import { formatLocalTime, formatRelativeTime } from '../../utils/timeUtils';

/**
 * CaregiverEmergencyOverlay
 * Central high-priority healthcare interruption modal overlay for Caregivers.
 * Displays immediate who, what, when, status, direct phone dialing, acknowledgement, and details.
 */
export default function CaregiverEmergencyOverlay({
  alert,
  userTimezone,
  audioBlocked = false,
  onAcknowledge,
  onViewDetails,
  onDismiss,
  totalActiveCount = 1
}) {
  const shouldReduceMotion = useReducedMotion();
  const acknowledgeBtnRef = useRef(null);

  // Auto-focus the primary acknowledge action for accessibility
  useEffect(() => {
    if (alert && acknowledgeBtnRef.current) {
      acknowledgeBtnRef.current.focus();
    }
  }, [alert]);

  // Handle ESC key to dismiss (temporary hide, does NOT resolve or acknowledge)
  useEffect(() => {
    const handleKeyDown = (e) => {
      if (e.key === 'Escape' && onDismiss) {
        onDismiss();
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [onDismiss]);

  if (!alert || alert.status === 'resolved') return null;

  const elderName = alert.elder_name || 'Your linked family member';
  const timeFormatted = formatLocalTime(alert.created_at, userTimezone);
  const relativeStr = formatRelativeTime(alert.created_at);
  const isAcknowledged = alert.status === 'acknowledged';

  return (
    <AnimatePresence>
      <div 
        className="fixed inset-0 z-50 flex items-center justify-center p-4 sm:p-6 overflow-y-auto"
        role="alertdialog"
        aria-modal="true"
        aria-labelledby="emergency-overlay-title"
        aria-describedby="emergency-overlay-desc"
      >
        {/* Subtle Dark Backdrop */}
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          className="fixed inset-0 bg-slate-950/85 backdrop-blur-md"
          aria-hidden="true"
          onClick={onDismiss}
        />

        {/* Central Modal Card */}
        <motion.div
          initial={shouldReduceMotion ? { opacity: 0 } : { opacity: 0, scale: 0.94, y: 15 }}
          animate={shouldReduceMotion ? { opacity: 1 } : { opacity: 1, scale: 1, y: 0 }}
          exit={shouldReduceMotion ? { opacity: 0 } : { opacity: 0, scale: 0.94, y: 15 }}
          transition={{ duration: 0.2, ease: "easeOut" }}
          className="relative w-full max-w-lg bg-[#0B132B] border-2 border-red-500/70 rounded-3xl p-6 sm:p-8 shadow-[0_20px_60px_rgba(239,68,68,0.3)] z-10 text-white space-y-6 overflow-hidden"
        >
          {/* Top Decorative Ambient Glow */}
          <div className="absolute top-0 right-0 w-64 h-32 bg-red-600/15 rounded-full blur-3xl pointer-events-none" />
          <div className="absolute -top-1 left-0 right-0 h-1.5 bg-gradient-to-r from-red-600 via-rose-500 to-red-600" />

          {/* Header Row: Urgent Badge + Close (Dismiss for now) */}
          <div className="flex items-start justify-between gap-4">
            <div className="flex items-center gap-3.5">
              <div className="w-14 h-14 rounded-2xl bg-red-500/20 border-2 border-red-500/50 flex items-center justify-center text-red-400 shrink-0 shadow-lg shadow-red-500/25">
                <AlertOctagon className="w-8 h-8 animate-pulse" />
              </div>
              <div>
                <div className="flex items-center gap-2 flex-wrap">
                  <span className="text-[11px] font-black uppercase tracking-wider px-2.5 py-0.5 rounded-full bg-red-500/20 text-red-300 border border-red-500/40">
                    Emergency Alert
                  </span>
                  {totalActiveCount > 1 && (
                    <span className="text-[11px] font-bold px-2 py-0.5 rounded-full bg-slate-800 text-amber-300 border border-amber-500/30">
                      {totalActiveCount} Active Alerts
                    </span>
                  )}
                </div>
                <h2 id="emergency-overlay-title" className="text-xl sm:text-2xl font-black text-white tracking-tight mt-1">
                  {elderName}
                </h2>
              </div>
            </div>

            {onDismiss && (
              <button
                type="button"
                onClick={onDismiss}
                className="p-2 text-slate-400 hover:text-white rounded-xl bg-slate-800/60 hover:bg-slate-800 border border-white/10 transition-colors cursor-pointer"
                title="Dismiss overlay (emergency remains active)"
                aria-label="Dismiss overlay for now"
              >
                <X className="w-5 h-5" />
              </button>
            )}
          </div>

          {/* Incident Message & Who/What/When Context */}
          <div className="space-y-3">
            <div className="p-4 rounded-2xl bg-slate-950/70 border border-white/10 space-y-2">
              <p id="emergency-overlay-desc" className="text-sm sm:text-base font-semibold text-slate-100 leading-snug">
                {alert.message || `${elderName} may need immediate assistance.`}
              </p>
              <p className="text-xs text-slate-400 leading-relaxed">
                Emergency assistance was requested by your linked family member.
              </p>
            </div>

            {/* When + Status Metadata Grid */}
            <div className="grid grid-cols-2 gap-3 text-xs">
              <div className="p-3 rounded-xl bg-slate-900/80 border border-white/5 space-y-1">
                <span className="text-slate-400 font-medium flex items-center gap-1">
                  <Clock className="w-3.5 h-3.5 text-blue-400" /> Triggered
                </span>
                <p className="font-bold text-white text-sm">
                  {timeFormatted}
                </p>
                <span className="text-[10px] text-slate-400 block">{relativeStr}</span>
              </div>

              <div className="p-3 rounded-xl bg-slate-900/80 border border-white/5 space-y-1">
                <span className="text-slate-400 font-medium flex items-center gap-1">
                  <ShieldAlert className="w-3.5 h-3.5 text-red-400" /> Status
                </span>
                <p className="font-bold text-red-300 flex items-center gap-1.5 text-xs sm:text-sm">
                  <span className="w-2 h-2 rounded-full bg-red-400 animate-pulse" />
                  {isAcknowledged ? 'Acknowledged' : 'Active — Response Needed'}
                </p>
                <span className="text-[10px] text-slate-400 block">
                  {isAcknowledged ? 'Response underway' : 'Awaiting caregiver action'}
                </span>
              </div>
            </div>
          </div>

          {/* Autoplay Audio Unblock Banner (if restricted by browser) */}
          {audioBlocked && (
            <button
              type="button"
              onClick={() => unlockAudioContext()}
              className="w-full py-2.5 px-4 rounded-2xl bg-amber-500/20 hover:bg-amber-500/30 border border-amber-500/40 text-amber-300 text-xs font-bold flex items-center justify-center gap-2 cursor-pointer transition-colors shadow-sm"
            >
              <Volume2 className="w-4 h-4 animate-bounce" />
              <span>Audio is paused by browser. Tap to enable alert sound</span>
            </button>
          )}

          {/* Primary Action Buttons */}
          <div className="space-y-3 pt-1">
            <div className="flex flex-col sm:flex-row gap-3">
              {/* Action 1: Call Elder */}
              {alert.elder_phone ? (
                <a
                  href={`tel:${alert.elder_phone}`}
                  className="w-full sm:w-1/2 py-3.5 px-4 rounded-2xl bg-blue-600 hover:bg-blue-500 text-white font-extrabold text-sm shadow-lg shadow-blue-600/30 transition-all flex items-center justify-center gap-2 min-h-[48px] cursor-pointer"
                >
                  <Phone className="w-4 h-4" />
                  <span>Call {elderName}</span>
                </a>
              ) : (
                <div 
                  className="w-full sm:w-1/2 py-3.5 px-4 rounded-2xl bg-slate-900 border border-white/10 text-slate-400 font-bold text-xs flex items-center justify-center text-center min-h-[48px]"
                  title="No emergency phone number recorded for this elder"
                >
                  Phone not available
                </div>
              )}

              {/* Action 2: Acknowledge Alert */}
              <button
                ref={acknowledgeBtnRef}
                type="button"
                onClick={onAcknowledge}
                className="w-full sm:w-1/2 py-3.5 px-4 rounded-2xl bg-red-600 hover:bg-red-500 text-white font-black text-sm shadow-lg shadow-red-600/40 transition-all flex items-center justify-center gap-2 min-h-[48px] cursor-pointer"
              >
                <Check className="w-5 h-5 text-white" />
                <span>Acknowledge Alert</span>
              </button>
            </div>

            {/* Secondary Action: View Emergency Details */}
            {onViewDetails && (
              <button
                type="button"
                onClick={onViewDetails}
                className="w-full py-3 px-4 rounded-2xl bg-slate-800/80 hover:bg-slate-800 text-slate-300 hover:text-white font-bold text-xs border border-white/10 transition-colors flex items-center justify-center gap-1.5 cursor-pointer min-h-[44px]"
              >
                <span>View Emergency Details in Response Center</span>
                <ChevronRight className="w-4 h-4 text-slate-400" />
              </button>
            )}
          </div>
        </motion.div>
      </div>
    </AnimatePresence>
  );
}

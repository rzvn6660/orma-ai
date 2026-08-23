import React from 'react';
import { AlertOctagon, Phone, ChevronRight, Check } from 'lucide-react';
import { formatEmergencyTimestamp } from '../../utils/timeUtils';

export default function CaregiverEmergencyBanner({
  alert,
  onViewEmergency,
  onAcknowledge,
  userTimezone,
  className = ''
}) {
  if (!alert || alert.status === 'resolved') return null;

  const elderName = alert.elder_name || 'Your linked family member';
  const alertTime = formatEmergencyTimestamp(alert.created_at, userTimezone);
  const isAcknowledged = alert.status === 'acknowledged';

  return (
    <div 
      className={`w-full p-4 sm:p-5 rounded-3xl bg-red-950/40 border-2 ${
        isAcknowledged ? 'border-amber-500/40' : 'border-red-500/60 shadow-[0_0_30px_rgba(239,68,68,0.2)]'
      } backdrop-blur-xl flex flex-col md:flex-row md:items-center justify-between gap-4 relative overflow-hidden ${className}`}
      role="alert"
    >
      {/* Specular Ambient Glow */}
      <div className="absolute top-0 right-0 w-64 h-32 bg-red-600/10 rounded-full blur-2xl pointer-events-none" />

      {/* Left: Info */}
      <div className="flex items-center gap-3.5 relative z-10">
        <div className={`w-11 h-11 rounded-2xl ${
          isAcknowledged ? 'bg-amber-500/20 text-amber-400 border border-amber-500/30' : 'bg-red-500/20 text-red-400 border border-red-500/40 animate-pulse'
        } flex items-center justify-center shrink-0`}>
          <AlertOctagon className="w-6 h-6" />
        </div>

        <div>
          <div className="flex items-center gap-2 flex-wrap">
            <span className={`text-[11px] font-black uppercase tracking-wider px-2 py-0.5 rounded-full border ${
              isAcknowledged 
                ? 'bg-amber-500/15 text-amber-300 border-amber-500/30' 
                : 'bg-red-500/20 text-red-300 border-red-500/40'
            }`}>
              {isAcknowledged ? 'Emergency Acknowledged' : 'Active Emergency'}
            </span>
            <span className="text-xs text-slate-400 font-medium">
              Received {alertTime}
            </span>
          </div>

          <h3 className="text-base font-extrabold text-white tracking-tight mt-0.5">
            {elderName} {isAcknowledged ? '— Acknowledged, response underway' : 'may need immediate assistance'}
          </h3>
        </div>
      </div>

      {/* Right: Quick Actions */}
      <div className="flex items-center gap-2.5 flex-wrap relative z-10">
        {alert.elder_phone && (
          <a
            href={`tel:${alert.elder_phone}`}
            className="px-4 py-2.5 rounded-xl bg-slate-900/80 hover:bg-slate-800 text-white text-xs font-bold border border-white/10 flex items-center gap-1.5 min-h-[44px] cursor-pointer transition-colors"
          >
            <Phone className="w-3.5 h-3.5 text-blue-400" />
            <span>Call {elderName}</span>
          </a>
        )}

        {!isAcknowledged && onAcknowledge && (
          <button
            type="button"
            onClick={onAcknowledge}
            className="px-4 py-2.5 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-bold border border-white/10 flex items-center gap-1.5 min-h-[44px] cursor-pointer transition-colors"
          >
            <Check className="w-3.5 h-3.5 text-emerald-400" />
            <span>Acknowledge</span>
          </button>
        )}

        <button
          type="button"
          onClick={onViewEmergency}
          className="px-5 py-2.5 rounded-xl bg-red-600 hover:bg-red-500 text-white text-xs font-extrabold shadow-md shadow-red-600/30 flex items-center gap-1.5 min-h-[44px] cursor-pointer transition-all"
        >
          <span>View Emergency</span>
          <ChevronRight className="w-4 h-4" />
        </button>
      </div>
    </div>
  );
}

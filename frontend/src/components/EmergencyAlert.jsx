import { motion } from 'framer-motion';
import { ShieldAlert, AlertTriangle } from 'lucide-react';

export default function EmergencyAlert({ isActive = false, severity = 'low', onViewChange }) {
  return (
    <div
      className={`orma-card transition-all duration-300 ${
        isActive 
          ? '!border-red-500/50 !bg-red-950/30 shadow-[0_0_30px_rgba(239,68,68,0.15)]' 
          : ''
      }`}
    >
      <div className="flex justify-between items-center mb-3 relative z-10">
        <div className="flex items-center gap-2.5">
          <div className="w-8 h-8 rounded-xl bg-red-500/10 border border-red-500/20 flex items-center justify-center text-red-400">
            <ShieldAlert className="w-4 h-4" />
          </div>
          <div>
            <h3 className={`text-base font-bold tracking-tight ${isActive ? 'text-red-400' : 'text-white'}`}>
              {isActive ? `Emergency (${severity.toUpperCase()})` : 'Emergency Help'}
            </h3>
            <p className="text-[11px] text-slate-400">Immediate family & care assistance</p>
          </div>
        </div>
      </div>

      <p className="text-xs text-slate-300 mb-4 leading-relaxed relative z-10">
        Need immediate assistance? Press below to trigger your emergency response circle.
      </p>

      <button 
        type="button"
        onClick={() => onViewChange && onViewChange('emergency')}
        className={`w-full py-3.5 px-4 rounded-2xl font-bold text-sm transition-all flex justify-center items-center gap-2 cursor-pointer relative z-10 ${
          isActive
            ? 'bg-red-600 hover:bg-red-500 text-white shadow-[0_0_20px_rgba(239,68,68,0.4)]'
            : 'bg-red-500/10 hover:bg-red-500/20 text-red-400 border border-red-500/30 hover:border-red-500/50'
        }`}
      >
        <AlertTriangle className="w-4 h-4" />
        <span>SOS / Emergency Help</span>
      </button>
    </div>
  );
}


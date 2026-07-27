import { motion } from 'framer-motion';
import { ShieldAlert, AlertTriangle } from 'lucide-react';

export default function EmergencyAlert({ isActive = false, severity = 'low', onViewChange }) {
  return (
    <motion.div 
      initial={{ opacity: 0, x: 20 }}
      animate={{ opacity: 1, x: 0 }}
      transition={{ duration: 0.6, delay: 0.4 }}
      className={`orma-card p-6 border transition-all duration-300 rounded-[2rem] shadow-xl ${
        isActive 
          ? 'border-red-500 bg-red-900/20 shadow-[0_0_40px_rgba(239,68,68,0.3)] animate-pulse' 
          : 'border-slate-700/50 bg-slate-800/40'
      }`}
    >
      <div className="flex justify-between items-center mb-4 pb-3 border-b border-slate-700/50">
        <h3 className={`text-[17px] font-medium tracking-wide ${isActive ? 'text-red-400' : 'text-white'}`}>
          {isActive ? `Emergency (${severity.toUpperCase()})` : 'Emergency Help'}
        </h3>
        <ShieldAlert className={`w-5 h-5 ${isActive ? 'text-red-500 animate-bounce' : 'text-slate-400'}`} />
      </div>

      <div className="flex flex-col gap-3">
        <button 
          onClick={() => onViewChange && onViewChange('emergency')}
          className={`w-full py-3 rounded-xl font-medium text-[15px] transition-all flex justify-center items-center gap-2 shadow-lg active:scale-[0.98] ${
            isActive
              ? 'bg-red-600 hover:bg-red-500 text-white shadow-[0_0_20px_rgba(239,68,68,0.4)]'
              : 'bg-red-500/10 hover:bg-red-500/20 text-red-400 border border-red-500/20 hover:border-red-500/40'
          }`}
        >
          <AlertTriangle className={`w-4 h-4 ${isActive ? 'fill-current' : ''}`} />
          SOS Alert
        </button>
      </div>
    </motion.div>
  );
}

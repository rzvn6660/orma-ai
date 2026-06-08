import React from 'react';
import { motion } from 'framer-motion';
import { Heart, Activity, AlertTriangle, ShieldAlert } from 'lucide-react';

export default function EmergencyAlert({ isActive = false, severity = 'low' }) {
  return (
    <motion.div 
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.6, delay: 0.5 }}
      className={`glass-card overflow-hidden relative group border ${isActive ? 'border-red-500 shadow-[0_0_30px_rgba(239,68,68,0.4)] animate-pulse' : 'border-transparent'}`}
    >
      <div className={`absolute inset-0 bg-gradient-to-br transition-all duration-500 ${isActive ? 'from-red-600/30 to-orange-600/20' : 'from-red-500/10 to-orange-500/5 group-hover:from-red-500/20'}`} />
      
      <div className="p-6 relative z-10 flex flex-col items-center justify-center text-center">
        <div className={`w-16 h-16 rounded-full flex items-center justify-center mb-4 relative ${isActive ? 'bg-red-500/40' : 'bg-red-500/20'}`}>
          <div className={`absolute inset-0 rounded-full opacity-75 ${isActive ? 'bg-red-500/60 animate-ping' : 'bg-red-500/30 animate-ping'}`} />
          <ShieldAlert className={`w-8 h-8 ${isActive ? 'text-red-200' : 'text-red-400'}`} />
        </div>
        
        <h3 className={`text-xl font-bold mb-2 ${isActive ? 'text-red-400' : 'text-white'}`}>
          {isActive ? `Emergency Detected (${severity.toUpperCase()})` : 'Emergency Help'}
        </h3>
        <p className={`text-sm mb-6 ${isActive ? 'text-red-200' : 'text-slate-400'}`}>
          {isActive ? 'Alerting your emergency contacts immediately.' : 'Press and hold for 3 seconds to alert family and emergency services.'}
        </p>
        
        <button className="w-full bg-gradient-to-r from-red-600 to-red-500 hover:from-red-500 hover:to-red-400 text-white font-bold py-4 rounded-xl shadow-[0_0_20px_rgba(239,68,68,0.3)] transition-all active:scale-95 flex justify-center items-center gap-2">
          <AlertTriangle className="w-5 h-5" />
          SOS Alert
        </button>
      </div>
    </motion.div>
  );
}

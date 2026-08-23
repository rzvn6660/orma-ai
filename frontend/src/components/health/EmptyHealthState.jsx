import React from 'react';
import { motion } from 'framer-motion';
import { 
  FileText, 
  Plus, 
  Heart, 
  Activity, 
  ShieldCheck, 
  TrendingUp, 
  Droplets, 
  Thermometer, 
  Clock 
} from 'lucide-react';

/**
 * EmptyHealthState
 * Clean, trustworthy empty state for ORMA Health Records inspired by 21st.dev / shadcn empty state patterns.
 * Focuses on actual clinical record management and patient guidance.
 */
export default function EmptyHealthState({ onAddReading }) {
  const supportedVitals = [
    { label: 'Blood Pressure', icon: Heart, desc: 'Systolic & diastolic monitoring', color: 'text-rose-400 bg-rose-500/10 border-rose-500/20' },
    { label: 'Heart Rate', icon: Activity, desc: 'Pulse resting & active measurements', color: 'text-blue-400 bg-blue-500/10 border-blue-500/20' },
    { label: 'Blood Sugar', icon: Droplets, desc: 'Fasting & post-meal glucose logs', color: 'text-amber-400 bg-amber-500/10 border-amber-500/20' },
    { label: 'Oxygen Saturation', icon: Activity, desc: 'SpO2 pulse oximetry readings', color: 'text-cyan-400 bg-cyan-500/10 border-cyan-500/20' },
    { label: 'Body Temperature', icon: Thermometer, desc: 'Fever & health checks', color: 'text-emerald-400 bg-emerald-500/10 border-emerald-500/20' },
    { label: 'Sleep & Rest', icon: Clock, desc: 'Nightly sleep duration and quality', color: 'text-indigo-400 bg-indigo-500/10 border-indigo-500/20' },
  ];

  return (
    <motion.div 
      initial={{ opacity: 0, y: 15 }}
      animate={{ opacity: 1, y: 0 }}
      className="max-w-4xl mx-auto space-y-6 pb-8"
    >
      {/* 1. Main Empty State Hero Card */}
      <div className="orma-card text-center p-8 sm:p-12 relative overflow-hidden border-white/10 shadow-2xl">
        <div className="absolute inset-0 bg-gradient-to-b from-blue-500/5 via-transparent to-transparent pointer-events-none" />

        <div className="w-16 h-16 rounded-3xl bg-blue-600/15 border border-blue-500/30 flex items-center justify-center mx-auto mb-4 text-blue-400 shadow-lg">
          <FileText className="w-8 h-8" />
        </div>

        <h3 className="text-xl sm:text-2xl font-extrabold text-white tracking-tight mb-2">
          No Health Records Yet
        </h3>

        <p className="text-slate-400 text-xs sm:text-sm max-w-lg mx-auto leading-relaxed mb-6">
          Record your blood pressure, heart rate, blood sugar, and other clinical vitals to keep your medical history organized and accessible to your family caregivers.
        </p>

        <div className="flex items-center justify-center gap-3 flex-wrap">
          <button
            type="button"
            onClick={onAddReading}
            className="px-6 py-3 rounded-2xl bg-blue-600 hover:bg-blue-500 text-white font-bold text-sm shadow-lg shadow-blue-600/25 transition-all hover:scale-[1.02] flex items-center gap-2 cursor-pointer"
          >
            <Plus className="w-4 h-4" />
            <span>Add First Health Reading</span>
          </button>
        </div>
      </div>

      {/* 2. Supported Health Measurements Grid */}
      <div className="orma-card p-6 sm:p-8">
        <div className="flex items-center justify-between mb-5 pb-3 border-b border-white/10">
          <div>
            <h4 className="text-base font-bold text-white tracking-tight flex items-center gap-2">
              <TrendingUp className="w-4 h-4 text-blue-400" />
              <span>Supported Clinical Measurements</span>
            </h4>
            <p className="text-xs text-slate-400 mt-0.5">
              Select any measurement type to record your readings
            </p>
          </div>
          <span className="text-xs font-bold text-emerald-400 bg-emerald-500/10 border border-emerald-500/20 px-3 py-1 rounded-full flex items-center gap-1.5">
            <ShieldCheck className="w-3.5 h-3.5" /> Private & Secure
          </span>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3.5">
          {supportedVitals.map((vital, idx) => {
            const Icon = vital.icon;
            return (
              <div
                key={idx}
                onClick={onAddReading}
                className="p-4 rounded-2xl bg-slate-950/50 border border-white/5 hover:border-white/15 transition-all cursor-pointer flex items-start gap-3 group"
              >
                <div className={`w-9 h-9 rounded-xl border flex items-center justify-center shrink-0 ${vital.color} group-hover:scale-105 transition-transform`}>
                  <Icon className="w-4 h-4" />
                </div>
                <div>
                  <h5 className="text-sm font-bold text-white group-hover:text-blue-300 transition-colors">
                    {vital.label}
                  </h5>
                  <p className="text-xs text-slate-400 mt-0.5 leading-snug">
                    {vital.desc}
                  </p>
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </motion.div>
  );
}

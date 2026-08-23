import { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { Activity, Heart, Droplets, ArrowRight } from 'lucide-react';
import { healthRecordApi } from '../services/api';

export default function HealthSnapshot({ onViewChange }) {
  const [latestRecords, setLatestRecords] = useState({
    blood_pressure: null,
    heart_rate: null,
    spo2: null
  });

  useEffect(() => {
    const fetchLatest = async () => {
      try {
        const records = await healthRecordApi.getRecords();
        const latestBP = records.find(r => r.vital_type === 'blood_pressure');
        const latestHR = records.find(r => r.vital_type === 'heart_rate');
        const latestSpO2 = records.find(r => r.vital_type === 'spo2');
        setLatestRecords({
          blood_pressure: latestBP,
          heart_rate: latestHR,
          spo2: latestSpO2
        });
      } catch (e) {
        console.error("Failed to fetch recent health records", e);
      }
    };
    fetchLatest();
  }, []);

  const timeAgo = (dateStr, timeStr) => {
    if (!dateStr || !timeStr) return '';
    try {
      const recordDate = new Date(`${dateStr}T${timeStr}`);
      const diffMs = new Date() - recordDate;
      const diffHrs = Math.floor(diffMs / (1000 * 60 * 60));
      if (diffHrs < 1) return 'Just now';
      if (diffHrs < 24) return `${diffHrs} hours ago`;
      return `${Math.floor(diffHrs/24)} days ago`;
    } catch {
      return '';
    }
  };

  // Find most recent timestamp
  const getMostRecentTime = () => {
    const records = Object.values(latestRecords).filter(Boolean);
    if (records.length === 0) return 'No data yet';
    // Just grab the first one since it's already sorted by ID desc in API (latest first)
    const mostRecent = records.sort((a,b) => b.id - a.id)[0];
    return timeAgo(mostRecent.date, mostRecent.time);
  };

  return (
    <motion.div 
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      className="orma-card p-5 border-white/10 hover:border-blue-500/30 transition-all cursor-pointer group"
      onClick={() => onViewChange('records')}
    >
      <div className="flex justify-between items-start mb-4 relative z-10">
        <div>
          <h3 className="text-base font-bold text-white flex items-center gap-2 tracking-tight">
            <Activity className="w-5 h-5 text-blue-400" /> Today's Health
          </h3>
          <p className="text-xs text-slate-400 mt-1">Last Updated: {getMostRecentTime()}</p>
        </div>
        <div className="p-2 bg-blue-500/10 rounded-full text-blue-400 opacity-0 group-hover:opacity-100 transition-opacity">
          <ArrowRight className="w-4 h-4" />
        </div>
      </div>

      <div className="space-y-3 relative z-10">
        <div className="flex justify-between items-center p-3.5 bg-slate-950/50 rounded-2xl border border-white/5">
          <div className="flex items-center gap-2.5">
            <div className="w-8 h-8 rounded-xl bg-rose-500/10 border border-rose-500/20 flex items-center justify-center text-rose-400 shrink-0">
              <Heart className="w-4 h-4" />
            </div>
            <div>
              <span className="text-slate-300 text-xs font-bold uppercase tracking-wider">Blood Pressure</span>
              <p className="text-[11px] text-slate-400">Systolic / Diastolic</p>
            </div>
          </div>
          <span className="font-bold text-white text-sm">
            {latestRecords.blood_pressure ? `${latestRecords.blood_pressure.value} mmHg` : <span className="text-slate-400 text-xs font-medium">No reading yet</span>}
          </span>
        </div>
        
        <div className="grid grid-cols-2 gap-3">
          <div className="flex flex-col p-3.5 bg-slate-950/50 rounded-2xl border border-white/5">
            <div className="flex items-center gap-2 mb-1.5">
              <div className="w-6 h-6 rounded-lg bg-rose-400/10 border border-rose-400/20 flex items-center justify-center text-rose-400 shrink-0">
                <Activity className="w-3.5 h-3.5" />
              </div>
              <span className="text-slate-400 text-[11px] font-bold uppercase tracking-wider">Heart Rate</span>
            </div>
            <span className="font-bold text-white text-sm mt-0.5">
              {latestRecords.heart_rate ? `${latestRecords.heart_rate.value} bpm` : <span className="text-slate-400 text-xs font-medium">No reading yet</span>}
            </span>
          </div>
          <div className="flex flex-col p-3.5 bg-slate-950/50 rounded-2xl border border-white/5">
            <div className="flex items-center gap-2 mb-1.5">
              <div className="w-6 h-6 rounded-lg bg-cyan-500/10 border border-cyan-500/20 flex items-center justify-center text-cyan-400 shrink-0">
                <Droplets className="w-3.5 h-3.5" />
              </div>
              <span className="text-slate-400 text-[11px] font-bold uppercase tracking-wider">SpO₂</span>
            </div>
            <span className="font-bold text-white text-sm mt-0.5">
              {latestRecords.spo2 ? `${latestRecords.spo2.value}%` : <span className="text-slate-400 text-xs font-medium">No reading yet</span>}
            </span>
          </div>
        </div>
      </div>
    </motion.div>
  );
}

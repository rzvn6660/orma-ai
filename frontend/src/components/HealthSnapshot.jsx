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
      className="orma-card p-5 border-blue-500/30 bg-slate-900/50 hover:bg-slate-800/80 transition-colors cursor-pointer group relative overflow-hidden"
      onClick={() => onViewChange('records')}
    >
      <div className="flex justify-between items-start mb-4">
        <div>
          <h3 className="text-lg font-bold text-white flex items-center gap-2">
            <Activity className="w-5 h-5 text-blue-400" /> Today's Health
          </h3>
          <p className="text-xs text-slate-400 mt-1">Last Updated: {getMostRecentTime()}</p>
        </div>
        <div className="p-2 bg-blue-500/10 rounded-full text-blue-400 opacity-0 group-hover:opacity-100 transition-opacity">
          <ArrowRight className="w-4 h-4" />
        </div>
      </div>

      <div className="space-y-4">
        <div className="flex justify-between items-center p-3 bg-slate-800/50 rounded-xl border border-slate-700/50">
          <div className="flex items-center gap-2">
            <Heart className="w-4 h-4 text-rose-500" />
            <span className="text-slate-300 text-sm font-medium">Blood Pressure</span>
          </div>
          <span className="font-bold text-white">
            {latestRecords.blood_pressure ? `${latestRecords.blood_pressure.value}` : <span className="text-slate-500 text-xs">No reading</span>}
          </span>
        </div>
        
        <div className="grid grid-cols-2 gap-3">
          <div className="flex flex-col p-3 bg-slate-800/50 rounded-xl border border-slate-700/50">
            <div className="flex items-center gap-2 mb-1">
              <Activity className="w-4 h-4 text-rose-400" />
              <span className="text-slate-400 text-xs font-medium uppercase tracking-wider">Heart</span>
            </div>
            <span className="font-bold text-white">
              {latestRecords.heart_rate ? `${latestRecords.heart_rate.value} bpm` : <span className="text-slate-500 text-xs">--</span>}
            </span>
          </div>
          <div className="flex flex-col p-3 bg-slate-800/50 rounded-xl border border-slate-700/50">
            <div className="flex items-center gap-2 mb-1">
              <Droplets className="w-4 h-4 text-cyan-500" />
              <span className="text-slate-400 text-xs font-medium uppercase tracking-wider">SpO₂</span>
            </div>
            <span className="font-bold text-white">
              {latestRecords.spo2 ? `${latestRecords.spo2.value}%` : <span className="text-slate-500 text-xs">--</span>}
            </span>
          </div>
        </div>
      </div>
    </motion.div>
  );
}

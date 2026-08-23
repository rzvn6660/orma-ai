import React from 'react';
import { motion } from 'framer-motion';
import { 
  CheckCircle2, 
  Clock, 
  AlertTriangle, 
  RotateCcw, 
  PieChart as PieIcon,
  ShieldCheck 
} from 'lucide-react';

export default function MedicationStatusBreakdown({
  medicines = [],
  summaryData,
  className = ''
}) {
  // Compute counts truthfully from medicines list or summaryData
  const total = medicines.length > 0 ? medicines.length : (summaryData?.medicines_taken || 0) + (summaryData?.pending_medicines || 0) + (summaryData?.missed_medicines || 0);

  const takenCount = medicines.length > 0 
    ? medicines.filter(m => m.taken_status).length 
    : (summaryData?.medicines_taken || 0);

  const missedCount = medicines.length > 0 
    ? medicines.filter(m => !m.taken_status && m.adherence_pattern_flags === 'missed').length 
    : (summaryData?.missed_medicines || 0);

  const snoozedCount = medicines.length > 0 
    ? medicines.filter(m => !m.taken_status && (m.snoozed || m.is_snoozed)).length 
    : 0;

  const pendingCount = medicines.length > 0 
    ? medicines.filter(m => !m.taken_status && m.adherence_pattern_flags !== 'missed' && !m.snoozed && !m.is_snoozed).length 
    : (summaryData?.pending_medicines || 0);

  const getPercent = (count) => (total > 0 ? Math.round((count / total) * 100) : 0);

  const items = [
    {
      label: 'Taken Doses',
      count: takenCount,
      percent: getPercent(takenCount),
      icon: CheckCircle2,
      color: 'emerald',
      barColor: 'bg-emerald-400',
      textColor: 'text-emerald-400',
      bgColor: 'bg-emerald-500/10',
      borderColor: 'border-emerald-500/20'
    },
    {
      label: 'Pending / Upcoming',
      count: pendingCount,
      percent: getPercent(pendingCount),
      icon: Clock,
      color: 'amber',
      barColor: 'bg-amber-400',
      textColor: 'text-amber-400',
      bgColor: 'bg-amber-500/10',
      borderColor: 'border-amber-500/20'
    },
    {
      label: 'Missed Doses',
      count: missedCount,
      percent: getPercent(missedCount),
      icon: AlertTriangle,
      color: 'red',
      barColor: 'bg-red-400',
      textColor: 'text-red-400',
      bgColor: 'bg-red-500/10',
      borderColor: 'border-red-500/20'
    },
    {
      label: 'Snoozed',
      count: snoozedCount,
      percent: getPercent(snoozedCount),
      icon: RotateCcw,
      color: 'purple',
      barColor: 'bg-purple-400',
      textColor: 'text-purple-400',
      bgColor: 'bg-purple-500/10',
      borderColor: 'border-purple-500/20'
    }
  ];

  return (
    <div className={`orma-card flex flex-col justify-between ${className}`} aria-label="Medication Status Breakdown">
      <div className="relative z-10">
        <div className="flex items-center justify-between mb-5">
          <div className="flex items-center gap-2.5">
            <div className="w-8 h-8 rounded-xl bg-purple-500/10 border border-purple-500/20 flex items-center justify-center text-purple-400 shrink-0">
              <PieIcon className="w-4 h-4" />
            </div>
            <div>
              <h3 className="text-base font-bold text-white tracking-tight">Medication Status</h3>
              <p className="text-[11px] text-slate-400">Daily dose distribution breakdown</p>
            </div>
          </div>
          <span className="text-xs font-bold text-slate-300 bg-slate-950/60 px-2.5 py-1 rounded-xl border border-white/10">
            {total} Total Doses
          </span>
        </div>

        {/* Stacked Progress Bar */}
        {total > 0 && (
          <div className="w-full h-3.5 bg-slate-950/70 rounded-full overflow-hidden p-0.5 border border-white/10 flex gap-0.5 mb-5 shadow-inner">
            {items.map((item, idx) => {
              if (item.percent === 0) return null;
              return (
                <div
                  key={idx}
                  style={{ width: `${item.percent}%` }}
                  className={`h-full ${item.barColor} first:rounded-l-full last:rounded-r-full transition-all`}
                  title={`${item.label}: ${item.count} (${item.percent}%)`}
                />
              );
            })}
          </div>
        )}

        {/* Breakdown Items */}
        <div className="space-y-2.5">
          {items.map((item, idx) => {
            const Icon = item.icon;
            return (
              <div 
                key={idx} 
                className="bg-slate-950/50 p-3 rounded-2xl border border-white/5 flex items-center justify-between transition-colors hover:border-white/10"
              >
                <div className="flex items-center gap-2.5">
                  <div className={`w-7 h-7 rounded-lg ${item.bgColor} border ${item.borderColor} flex items-center justify-center ${item.textColor} shrink-0`}>
                    <Icon className="w-3.5 h-3.5" />
                  </div>
                  <div>
                    <span className="text-xs font-bold text-slate-200">{item.label}</span>
                    <p className="text-[10px] text-slate-400">{item.percent}% of total</p>
                  </div>
                </div>

                <div className="text-right">
                  <span className={`text-sm font-extrabold ${item.textColor}`}>
                    {item.count}
                  </span>
                  <span className="text-[10px] text-slate-500 ml-1">doses</span>
                </div>
              </div>
            );
          })}
        </div>
      </div>

      <p className="text-[10px] text-slate-500 mt-4 text-center relative z-10">
        Status computed live from scheduled daily medication records.
      </p>
    </div>
  );
}

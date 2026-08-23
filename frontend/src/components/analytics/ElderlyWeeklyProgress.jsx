import React from 'react';
import { Check, Clock, Sparkles } from 'lucide-react';

export default function ElderlyWeeklyProgress({
  adherenceRate = 90,
  className = ''
}) {
  // Determine current day of week to highlight
  const days = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'];
  const todayIndex = (new Date().getDay() + 6) % 7; // Convert Sun=0 to Mon=0..Sun=6

  const weekProgress = days.map((day, idx) => {
    const isPast = idx < todayIndex;
    const isToday = idx === todayIndex;
    const isFuture = idx > todayIndex;

    return {
      day,
      isPast,
      isToday,
      isFuture,
      status: isPast ? 'completed' : isToday ? 'active' : 'upcoming'
    };
  });

  return (
    <div className={`orma-card p-5 sm:p-6 ${className}`} aria-label="Your Weekly Schedule Overview">
      <div className="flex items-center justify-between mb-4 relative z-10">
        <div className="flex items-center gap-2.5">
          <div className="w-8 h-8 rounded-xl bg-emerald-500/15 border border-emerald-500/30 flex items-center justify-center text-emerald-400 shrink-0">
            <Sparkles className="w-4 h-4" />
          </div>
          <div>
            <h3 className="text-base sm:text-lg font-extrabold text-white tracking-tight">Your Week</h3>
            <p className="text-xs text-slate-300">Daily medicine routine progress</p>
          </div>
        </div>
        <span className="text-xs font-extrabold text-emerald-400 bg-emerald-500/10 px-3 py-1 rounded-full border border-emerald-500/25">
          On Track
        </span>
      </div>

      {/* 7-Day Pill Strip */}
      <div className="grid grid-cols-7 gap-1.5 sm:gap-2.5 my-3 relative z-10">
        {weekProgress.map((item, idx) => {
          return (
            <div
              key={idx}
              className={`flex flex-col items-center justify-center py-2 sm:py-3 rounded-2xl border transition-all text-center ${
                item.status === 'completed'
                  ? 'bg-emerald-500/15 border-emerald-500/30 text-emerald-400'
                  : item.status === 'active'
                  ? 'bg-blue-600/25 border-blue-400 text-cyan-300 shadow-[0_0_15px_rgba(59,130,246,0.25)]'
                  : 'bg-slate-950/40 border-white/5 text-slate-500'
              }`}
            >
              <span className="text-[11px] sm:text-xs font-bold uppercase tracking-wider mb-1">
                {item.day}
              </span>
              <div className="w-5 h-5 sm:w-6 sm:h-6 rounded-full flex items-center justify-center">
                {item.status === 'completed' && <Check className="w-3.5 h-3.5 sm:w-4 sm:h-4 stroke-[2.5]" />}
                {item.status === 'active' && <div className="w-2.5 h-2.5 rounded-full bg-cyan-400 animate-pulse" />}
                {item.status === 'upcoming' && <div className="w-1.5 h-1.5 rounded-full bg-slate-700" />}
              </div>
            </div>
          );
        })}
      </div>

      {/* Reassuring Feedback Statement */}
      <p className="text-xs sm:text-sm text-slate-300 mt-3 text-center font-medium relative z-10">
        You're doing well keeping up with your schedule this week.
      </p>
    </div>
  );
}

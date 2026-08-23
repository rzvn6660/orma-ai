import React from 'react';
import { motion } from 'framer-motion';
import { 
  Check, 
  Pill, 
  Calendar, 
  Activity, 
  AlertOctagon, 
  Heart, 
  Clock, 
  ShieldCheck 
} from 'lucide-react';

/**
 * Formats a Date/ISO string to friendly 12h time string (e.g., "04:05 PM")
 */
function formatEventTime(isoStr, userTimezone) {
  if (!isoStr) return '--:--';
  try {
    const d = new Date(isoStr.endsWith('Z') ? isoStr : `${isoStr}Z`);
    if (isNaN(d.getTime())) {
      // Fallback for plain time strings like "9:00 AM"
      return isoStr;
    }
    return d.toLocaleTimeString('en-US', {
      hour: '2-digit',
      minute: '2-digit',
      timeZone: userTimezone || Intl.DateTimeFormat().resolvedOptions().timeZone
    });
  } catch {
    return isoStr;
  }
}

/**
 * Returns date group heading (e.g., "TODAY", "YESTERDAY", "AUG 15")
 */
function getDateHeading(isoStr, userTimezone) {
  if (!isoStr) return 'TODAY';
  try {
    const d = new Date(isoStr.endsWith('Z') ? isoStr : `${isoStr}Z`);
    if (isNaN(d.getTime())) return 'TODAY';

    const now = new Date();
    const isToday = d.toDateString() === now.toDateString();
    if (isToday) return 'TODAY';

    const yesterday = new Date();
    yesterday.setDate(now.getDate() - 1);
    const isYesterday = d.toDateString() === yesterday.toDateString();
    if (isYesterday) return 'YESTERDAY';

    return d.toLocaleDateString('en-US', { month: 'short', day: 'numeric' }).toUpperCase();
  } catch {
    return 'RECENT';
  }
}

export default function HealthActivityTimeline({
  events = [],
  emergencies = [],
  userTimezone,
  className = ''
}) {
  // Combine completed events and emergency triggers into a unified audit feed
  const combinedList = [];

  // 1. Add completed health planner / medication events
  if (Array.isArray(events)) {
    events
      .filter(e => e.status)
      .forEach(e => {
        combinedList.push({
          id: `evt-${e.id}`,
          rawDate: e.completed_at || e.date || new Date().toISOString(),
          title: e.title || 'Completed Health Event',
          category: e.event_type || 'Medicine',
          status: 'completed',
          statusLabel: 'Completed',
          details: e.description || 'Recorded in care log'
        });
      });
  }

  // 2. Add emergency alerts & triggers
  if (Array.isArray(emergencies)) {
    emergencies.forEach(em => {
      combinedList.push({
        id: `em-${em.id}`,
        rawDate: em.time || new Date().toISOString(),
        title: em.type || 'Safety Alert Trigger',
        category: 'emergency',
        status: em.resolved ? 'resolved' : 'action_needed',
        statusLabel: em.resolved ? 'Resolved' : 'Action Needed',
        details: em.severity ? `Severity: ${em.severity.toUpperCase()}` : 'Safety trigger'
      });
    });
  }

  // Group by date heading
  const grouped = {};
  combinedList.forEach(item => {
    const heading = getDateHeading(item.rawDate, userTimezone);
    if (!grouped[heading]) grouped[heading] = [];
    grouped[heading].push(item);
  });

  const headings = Object.keys(grouped);

  if (combinedList.length === 0) {
    return (
      <div className={`p-8 text-center border border-dashed border-white/10 rounded-2xl bg-slate-950/30 ${className}`}>
        <Activity className="w-8 h-8 text-slate-500 mx-auto mb-2" />
        <p className="text-sm font-bold text-white mb-1">No Activity Logged Yet</p>
        <p className="text-xs text-slate-400">Completed care tasks and health events will appear here in chronological order.</p>
      </div>
    );
  }

  return (
    <div className={`space-y-6 ${className}`} aria-label="Recent Health Events Activity Timeline">
      {headings.map((heading) => (
        <div key={heading} className="space-y-3">
          {/* Section Date Header */}
          <div className="flex items-center gap-3">
            <span className="text-[11px] font-extrabold tracking-wider text-blue-400 uppercase bg-blue-500/10 border border-blue-500/20 px-2.5 py-0.5 rounded-md">
              {heading}
            </span>
            <div className="flex-1 h-[1px] bg-slate-800/80" />
          </div>

          {/* Timeline Nodes */}
          <div className="relative space-y-3">
            {/* Vertical Connecting Line — Centered exactly at 16px (center of w-8 marker column) */}
            <div 
              className="absolute left-4 -translate-x-1/2 top-3 bottom-3 w-[2px] bg-slate-800 pointer-events-none" 
              aria-hidden="true" 
            />

            {grouped[heading].map((item, idx) => {
              const displayTime = formatEventTime(item.rawDate, userTimezone);
              const isAlert = item.category === 'emergency';
              const isResolved = item.status === 'resolved';
              const isActionNeeded = item.status === 'action_needed';

              let nodeBg = 'bg-slate-900 border-slate-700 text-blue-400';
              let nodeIcon = <Activity className="w-3.5 h-3.5" />;
              let statusBadge = (
                <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-[11px] font-bold bg-emerald-500/10 text-emerald-400 border border-emerald-500/25">
                  <Check className="w-3 h-3" /> Completed
                </span>
              );

              if (item.category.toLowerCase().includes('medicine')) {
                nodeIcon = <Pill className="w-3.5 h-3.5" />;
              } else if (item.category.toLowerCase().includes('appointment') || item.category.toLowerCase().includes('planner')) {
                nodeIcon = <Calendar className="w-3.5 h-3.5 text-emerald-400" />;
              } else if (isAlert) {
                if (isActionNeeded) {
                  nodeBg = 'bg-red-500/20 border-red-500/50 text-red-400 shadow-[0_0_12px_rgba(239,68,68,0.3)]';
                  nodeIcon = <AlertOctagon className="w-3.5 h-3.5" />;
                  statusBadge = (
                    <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-[11px] font-extrabold bg-red-500/20 text-red-400 border border-red-500/30">
                      Action Needed
                    </span>
                  );
                } else {
                  nodeBg = 'bg-amber-500/20 border-amber-500/50 text-amber-400';
                  nodeIcon = <AlertOctagon className="w-3.5 h-3.5" />;
                  statusBadge = (
                    <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-[11px] font-bold bg-emerald-500/10 text-emerald-400 border border-emerald-500/25">
                      Resolved
                    </span>
                  );
                }
              }

              return (
                <motion.div 
                  key={item.id || idx}
                  initial={{ opacity: 0, x: -6 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ duration: 0.15 }}
                  className="relative flex items-start gap-3.5 sm:gap-4 group"
                >
                  {/* Status Node Column — Fixed 32px (w-8) width guaranteeing mathematical alignment with the 16px rail */}
                  <div className="w-8 flex items-center justify-center shrink-0 pt-0.5">
                    <div className={`relative z-10 w-7 h-7 sm:w-8 sm:h-8 rounded-full border-2 flex items-center justify-center shrink-0 shadow-sm ${nodeBg}`}>
                      {nodeIcon}
                    </div>
                  </div>

                  {/* Activity Details Card */}
                  <div className="flex-1 min-w-0 rounded-2xl bg-slate-950/50 border border-white/5 p-3 sm:p-3.5 backdrop-blur-xl transition-colors hover:border-white/15 flex flex-col sm:flex-row sm:items-center justify-between gap-2">
                    <div>
                      <div className="flex items-center gap-2 flex-wrap mb-0.5">
                        <span className="text-[11px] font-mono font-bold text-slate-300 bg-slate-900 px-2 py-0.5 rounded-md border border-white/5">
                          {displayTime}
                        </span>
                        <h4 className="text-xs sm:text-sm font-bold text-white tracking-tight">
                          {item.title}
                        </h4>
                      </div>
                      <p className="text-[11px] text-slate-400 font-medium">
                        {item.details} {item.category && `· ${item.category}`}
                      </p>
                    </div>

                    <div className="shrink-0 self-start sm:self-center">
                      {statusBadge}
                    </div>
                  </div>
                </motion.div>
              );
            })}
          </div>
        </div>
      ))}
    </div>
  );
}

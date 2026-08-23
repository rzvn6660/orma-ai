import React from 'react';
import { motion } from 'framer-motion';
import { 
  Check, 
  Clock, 
  AlertTriangle, 
  Pill, 
  Sparkles, 
  Volume2, 
  CheckCircle2, 
  HelpCircle,
  Plus
} from 'lucide-react';

/**
 * Parses time strings like "08:00", "8:00 AM", "16:30", "4:30 PM" into total minutes from midnight for accurate chronological sorting.
 */
function parseTimeToMinutes(timeStr) {
  if (!timeStr) return 9999;
  const str = String(timeStr).trim();
  
  // Format: "8:00 AM" or "08:00 PM"
  const ampmMatch = str.match(/(\d+):(\d+)\s*(AM|PM)?/i);
  if (ampmMatch) {
    let hours = parseInt(ampmMatch[1], 10);
    const minutes = parseInt(ampmMatch[2], 10);
    const modifier = ampmMatch[3]?.toUpperCase();

    if (modifier === 'PM' && hours < 12) hours += 12;
    if (modifier === 'AM' && hours === 12) hours = 0;
    return hours * 60 + minutes;
  }

  // Format: "14:00"
  const parts = str.split(':');
  if (parts.length >= 2) {
    return parseInt(parts[0], 10) * 60 + parseInt(parts[1], 10);
  }
  return 9999;
}

/**
 * Formats time string to user-friendly "8:00 AM" format.
 */
function formatDisplayTime(timeStr) {
  if (!timeStr) return '--:--';
  const str = String(timeStr).trim();
  if (str.toUpperCase().includes('AM') || str.toUpperCase().includes('PM')) {
    return str;
  }
  const parts = str.split(':');
  if (parts.length >= 2) {
    let hour = parseInt(parts[0], 10);
    const minute = parts[1].padStart(2, '0');
    const ampm = hour >= 12 ? 'PM' : 'AM';
    hour = hour % 12 || 12;
    return `${hour}:${minute} ${ampm}`;
  }
  return str;
}

export default function MedicationTimeline({
  medicines = [],
  mode = 'caregiver', // 'caregiver' | 'elderly'
  onTakeMedicine,
  onAddMedicine,
  className = ''
}) {
  // Sort medicines chronologically by reminder_time
  const sortedMedicines = [...medicines].sort((a, b) => {
    return parseTimeToMinutes(a.reminder_time) - parseTimeToMinutes(b.reminder_time);
  });

  // Determine the next upcoming / due medicine index
  const now = new Date();
  const currentMinutes = now.getHours() * 60 + now.getMinutes();

  let nextUpcomingId = null;
  const pendingMedicines = sortedMedicines.filter(m => !m.taken_status);
  
  if (pendingMedicines.length > 0) {
    // Look for the first pending medicine whose scheduled time is closest to now or in future
    const futurePending = pendingMedicines.find(m => parseTimeToMinutes(m.reminder_time) >= currentMinutes - 30);
    nextUpcomingId = futurePending ? futurePending.id : pendingMedicines[0].id;
  }

  if (sortedMedicines.length === 0) {
    return (
      <div className={`p-8 text-center border border-dashed border-white/10 rounded-2xl bg-slate-950/30 ${className}`}>
        <div className="w-12 h-12 rounded-2xl bg-blue-500/10 border border-blue-500/20 flex items-center justify-center text-blue-400 mx-auto mb-3">
          <Pill className="w-6 h-6" />
        </div>
        <h4 className="text-base font-bold text-white mb-1">No Medicines Scheduled Today</h4>
        <p className="text-xs text-slate-400 max-w-sm mx-auto mb-4 leading-relaxed">
          There are no scheduled medication reminders active for today.
        </p>
        {onAddMedicine && (
          <button
            type="button"
            onClick={onAddMedicine}
            className="px-4 py-2 rounded-xl bg-blue-600 hover:bg-blue-500 text-white text-xs font-bold transition-all shadow-md inline-flex items-center gap-1.5 cursor-pointer"
          >
            <Plus className="w-3.5 h-3.5" />
            <span>Add Medicine</span>
          </button>
        )}
      </div>
    );
  }

  return (
    <div className={`relative ${className}`} aria-label="Today's Medication Timeline">
      {/* Continuous Vertical Timeline Track — Centered exactly at 16px (center of w-8 marker column) */}
      <div 
        className="absolute left-4 -translate-x-1/2 top-4 bottom-4 w-[2px] bg-gradient-to-b from-blue-500/40 via-slate-700/60 to-slate-800/20 pointer-events-none" 
        aria-hidden="true"
      />

      <div className="space-y-4 sm:space-y-5">
        {sortedMedicines.map((med, index) => {
          const isTaken = Boolean(med.taken_status);
          const isMissed = !isTaken && med.adherence_pattern_flags === 'missed';
          const isSnoozed = !isTaken && (med.snoozed || med.is_snoozed);
          const isNextUpcoming = med.id === nextUpcomingId && !isTaken;
          const displayTime = formatDisplayTime(med.reminder_time);

          // Status Node Styling
          let nodeBg = 'bg-slate-900 border-slate-700 text-slate-400';
          let nodeIcon = <Clock className="w-3.5 h-3.5" />;
          let cardBorder = 'border-white/5 hover:border-white/15';
          let statusBadge = null;

          if (isTaken) {
            nodeBg = 'bg-emerald-500/20 border-emerald-500/50 text-emerald-400 shadow-[0_0_12px_rgba(16,185,129,0.25)]';
            nodeIcon = <Check className="w-3.5 h-3.5 stroke-[2.5]" />;
            statusBadge = (
              <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-[11px] font-bold bg-emerald-500/10 text-emerald-400 border border-emerald-500/25">
                <Check className="w-3 h-3" /> Taken
              </span>
            );
          } else if (isMissed) {
            nodeBg = 'bg-red-500/20 border-red-500/50 text-red-400 shadow-[0_0_12px_rgba(239,68,68,0.25)]';
            nodeIcon = <AlertTriangle className="w-3.5 h-3.5 stroke-[2.5]" />;
            cardBorder = 'border-red-500/30 bg-red-950/15';
            statusBadge = (
              <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-[11px] font-bold bg-red-500/20 text-red-400 border border-red-500/30">
                <AlertTriangle className="w-3 h-3" /> Missed
              </span>
            );
          } else if (isSnoozed) {
            nodeBg = 'bg-purple-500/20 border-purple-500/50 text-purple-400 shadow-[0_0_12px_rgba(168,85,247,0.25)]';
            nodeIcon = <Clock className="w-3.5 h-3.5 stroke-[2.5]" />;
            cardBorder = 'border-purple-500/30 bg-purple-950/10';
            statusBadge = (
              <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-[11px] font-bold bg-purple-500/15 text-purple-300 border border-purple-500/30">
                Snoozed
              </span>
            );
          } else if (isNextUpcoming) {
            nodeBg = 'bg-cyan-500/20 border-cyan-400 text-cyan-300 shadow-[0_0_14px_rgba(34,211,238,0.35)]';
            nodeIcon = <Sparkles className="w-3.5 h-3.5" />;
            cardBorder = 'border-cyan-500/35 bg-slate-900/80 shadow-[0_0_20px_rgba(6,182,212,0.06)]';
            statusBadge = (
              <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-[11px] font-bold bg-cyan-500/15 text-cyan-300 border border-cyan-500/30">
                <span className="w-1.5 h-1.5 rounded-full bg-cyan-400 animate-pulse" /> Due Next
              </span>
            );
          } else {
            // General upcoming
            nodeBg = 'bg-slate-900 border-slate-700 text-slate-400';
            nodeIcon = <Clock className="w-3.5 h-3.5" />;
            statusBadge = (
              <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-[11px] font-semibold bg-slate-800 text-slate-400 border border-slate-700">
                Upcoming
              </span>
            );
          }

          return (
            <motion.div 
              key={med.id || index}
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.2, delay: index * 0.04 }}
              className="relative flex items-start gap-3.5 sm:gap-4 group"
            >
              {/* Timeline Status Node Column — Fixed 32px (w-8) width guaranteeing mathematical alignment with the 16px rail */}
              <div className="w-8 flex items-center justify-center shrink-0 pt-0.5">
                <div 
                  className={`relative z-10 w-7 h-7 sm:w-8 sm:h-8 rounded-full border-2 flex items-center justify-center shrink-0 transition-transform group-hover:scale-105 ${nodeBg}`}
                  title={`Scheduled: ${displayTime}`}
                >
                  {nodeIcon}
                </div>
              </div>

              {/* Medicine Item Card */}
              <div className={`flex-1 min-w-0 rounded-2xl bg-slate-950/60 border p-3.5 sm:p-4 backdrop-blur-xl transition-all shadow-md ${cardBorder}`}>
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2.5">
                  
                  {/* Left Side: Time, Name, Dosage, Details */}
                  <div className="flex-1">
                    <div className="flex items-center gap-2 flex-wrap mb-1">
                      <span className="text-xs font-mono font-bold text-slate-300 bg-slate-900/80 px-2 py-0.5 rounded-md border border-white/5">
                        {displayTime}
                      </span>
                      <h4 className={`text-sm sm:text-base font-bold tracking-tight ${isTaken ? 'text-slate-300' : 'text-white'}`}>
                        {med.medicine_name}
                      </h4>
                      {med.dosage && (
                        <span className="text-xs text-slate-400 font-medium">({med.dosage})</span>
                      )}
                    </div>

                    {/* Caregiver Detailed Info / Metadata */}
                    {mode === 'caregiver' && (
                      <div className="text-[11px] text-slate-400 flex flex-wrap items-center gap-x-2 gap-y-0.5 mt-1 font-medium">
                        {isTaken && (
                          <span className="text-emerald-400 flex items-center gap-1 font-semibold">
                            {med.confirmation_method === 'voice' ? (
                              <>
                                <Volume2 className="w-3 h-3 text-emerald-400" />
                                <span>Voice confirmed</span>
                              </>
                            ) : (
                              <>
                                <Check className="w-3 h-3 text-emerald-400" />
                                <span>Manually confirmed</span>
                              </>
                            )}
                          </span>
                        )}

                        {isMissed && (
                          <span className="text-red-400 font-bold">
                            Missed dose · Caregiver alert logged
                          </span>
                        )}

                        {isSnoozed && (
                          <span className="text-purple-300 font-medium">
                            Snoozed · Reminder pending
                          </span>
                        )}

                        {!isTaken && !isMissed && !isSnoozed && (
                          <span className="text-slate-400">
                            {isNextUpcoming ? 'Active upcoming reminder' : 'Scheduled daily dose'}
                          </span>
                        )}

                        {med.purpose && (
                          <>
                            <span className="text-slate-600">•</span>
                            <span className="text-slate-400">{med.purpose}</span>
                          </>
                        )}
                      </div>
                    )}

                    {/* Elderly Simplified Subtitle */}
                    {mode === 'elderly' && (
                      <p className="text-xs text-slate-400 mt-0.5">
                        {isTaken 
                          ? 'Dose completed for today' 
                          : isNextUpcoming 
                          ? 'Ready to take now' 
                          : 'Scheduled for later today'}
                      </p>
                    )}
                  </div>

                  {/* Right Side: Status Badge or Elderly Action Button */}
                  <div className="flex items-center gap-2 shrink-0 self-start sm:self-center">
                    {statusBadge}

                    {/* Action Button for Elderly User */}
                    {mode === 'elderly' && !isTaken && onTakeMedicine && (
                      <button
                        type="button"
                        onClick={(e) => onTakeMedicine(med.id, e)}
                        className={`px-3.5 py-1.5 rounded-xl font-bold text-xs shadow-md transition-all flex items-center gap-1.5 cursor-pointer ${
                          isNextUpcoming
                            ? 'bg-emerald-600 hover:bg-emerald-500 text-white shadow-emerald-600/20'
                            : 'bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700'
                        }`}
                      >
                        <Check className="w-3.5 h-3.5" />
                        <span>Take</span>
                      </button>
                    )}
                  </div>

                </div>
              </div>
            </motion.div>
          );
        })}
      </div>
    </div>
  );
}

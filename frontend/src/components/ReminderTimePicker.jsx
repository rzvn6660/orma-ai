import { useState, useEffect } from 'react';
import { Sun, Moon, Sunset, Coffee, Clock, Plus, Trash2, ChevronDown, AlertTriangle } from 'lucide-react';

/**
 * Robustly parses a time string into { hour: "08", minute: "00", period: "AM" }
 * Handles formats like: "08:00 AM", "8:00 AM", "20:30", "0:00", etc.
 */
export function parseTimeString(timeStr) {
  if (!timeStr || typeof timeStr !== 'string') {
    return { hour: '08', minute: '00', period: 'AM' };
  }

  const str = timeStr.trim();
  
  // Check for AM/PM format
  const ampmMatch = str.match(/^(\d{1,2}):(\d{2})\s*(AM|PM|am|pm)$/i);
  if (ampmMatch) {
    let h = parseInt(ampmMatch[1], 10);
    const m = parseInt(ampmMatch[2], 10);
    const period = ampmMatch[3].toUpperCase();
    if (h < 1) h = 12;
    if (h > 12) h = 12;
    const hStr = String(h).padStart(2, '0');
    const mStr = String(m < 0 || m > 59 ? 0 : m).padStart(2, '0');
    return { hour: hStr, minute: mStr, period };
  }

  // Check for 24-hour format e.g. "20:30" or "8:15"
  const h24Match = str.match(/^(\d{1,2}):(\d{2})$/);
  if (h24Match) {
    let h = parseInt(h24Match[1], 10);
    const m = parseInt(h24Match[2], 10);
    const period = h >= 12 ? 'PM' : 'AM';
    let h12 = h % 12;
    if (h12 === 0) h12 = 12;
    const hStr = String(h12).padStart(2, '0');
    const mStr = String(m < 0 || m > 59 ? 0 : m).padStart(2, '0');
    return { hour: hStr, minute: mStr, period };
  }

  // Default fallback
  return { hour: '08', minute: '00', period: 'AM' };
}

/**
 * Formats hour, minute, and period into standardized string e.g. "08:00 AM"
 */
export function formatTimeParts(hour, minute, period) {
  const h = String(hour).padStart(2, '0');
  const m = String(minute).padStart(2, '0');
  const p = (period || 'AM').toUpperCase();
  return `${h}:${m} ${p}`;
}

const HOURS = Array.from({ length: 12 }, (_, i) => String(i + 1).padStart(2, '0'));
const MINUTES = Array.from({ length: 60 }, (_, i) => String(i).padStart(2, '0'));

const COMMON_MINUTES = ['00', '15', '30', '45'];

const QUICK_PRESETS = [
  { label: 'Morning', time: '08:00 AM', icon: Sun },
  { label: 'Afternoon', time: '01:00 PM', icon: Coffee },
  { label: 'Evening', time: '06:00 PM', icon: Sunset },
  { label: 'Bedtime', time: '09:00 PM', icon: Moon },
];

/**
 * Single Time Control Row Component for Elderly Users
 */
export function SingleTimePickerRow({ value, onChange, label = "Dose Time", onDelete = null, showPresets = false }) {
  const { hour, minute, period } = parseTimeString(value);

  const handleHourChange = (e) => {
    const newH = e.target.value;
    onChange(formatTimeParts(newH, minute, period));
  };

  const handleMinuteChange = (e) => {
    const newM = e.target.value;
    onChange(formatTimeParts(hour, newM, period));
  };

  const handlePeriodChange = (newPeriod) => {
    onChange(formatTimeParts(hour, minute, newPeriod));
  };

  const handlePresetSelect = (presetTime) => {
    onChange(presetTime);
  };

  return (
    <div className="flex flex-col gap-3 p-4 sm:p-5 bg-slate-950/90 border-2 border-slate-700/80 rounded-2xl shadow-xl transition-all hover:border-slate-600">
      <div className="flex items-center justify-between">
        <span className="text-base font-extrabold text-slate-200 tracking-wide flex items-center gap-2">
          <Clock className="w-5 h-5 text-blue-400 shrink-0" />
          {label}
        </span>
        {onDelete && (
          <button
            type="button"
            onClick={onDelete}
            className="p-2 text-slate-400 hover:text-red-400 hover:bg-red-500/10 rounded-xl transition-colors cursor-pointer"
            title="Remove dose time"
            aria-label={`Remove ${label}`}
          >
            <Trash2 className="w-5 h-5" />
          </button>
        )}
      </div>

      {/* Quick Time Presets */}
      {showPresets && (
        <div className="flex flex-wrap gap-2 py-1">
          {QUICK_PRESETS.map((p) => {
            const Icon = p.icon;
            const isSelected = value === p.time;
            return (
              <button
                key={p.label}
                type="button"
                onClick={() => handlePresetSelect(p.time)}
                className={`flex items-center gap-2 px-3.5 py-2 rounded-xl text-sm font-bold transition-all cursor-pointer border-2 ${
                  isSelected
                    ? 'bg-blue-600/30 border-blue-400 text-blue-300 shadow-md scale-[1.02]'
                    : 'bg-slate-900 border-slate-700/80 text-slate-300 hover:bg-slate-800 hover:text-white hover:border-slate-600'
                }`}
              >
                <Icon className="w-4 h-4 text-blue-400" />
                <span>{p.label}</span>
                <span className="opacity-75 text-xs font-semibold">({p.time})</span>
              </button>
            );
          })}
        </div>
      )}

      {/* Main Senior-Friendly Control Row: [ 08 ▼ ] : [ 00 ▼ ]  [ AM | PM ] */}
      <div className="flex items-center gap-3 sm:gap-4 flex-wrap pt-1">
        
        {/* Hour Select with explicit dropdown arrow */}
        <div className="flex flex-col">
          <span className="text-xs font-black text-slate-300 uppercase tracking-wider mb-1.5 ml-1">Hour</span>
          <div className="relative flex items-center">
            <select
              value={hour}
              onChange={handleHourChange}
              aria-label="Select Hour"
              className="h-14 min-w-[104px] bg-slate-900 border-2 border-slate-600 hover:border-blue-400 focus:border-blue-400 focus:ring-4 focus:ring-blue-400/30 rounded-2xl pl-4 pr-10 text-2xl font-black text-white text-center cursor-pointer outline-none transition-all appearance-none shadow-inner"
            >
              {HOURS.map((h) => (
                <option key={h} value={h} className="bg-slate-900 text-white font-bold py-2 text-lg">
                  {h}
                </option>
              ))}
            </select>
            <ChevronDown className="w-5 h-5 text-blue-400 absolute right-3 pointer-events-none" />
          </div>
        </div>

        {/* Colon Separator */}
        <span className="text-3xl font-black text-slate-300 pt-5 font-mono select-none">:</span>

        {/* Minute Select with explicit dropdown arrow */}
        <div className="flex flex-col">
          <span className="text-xs font-black text-slate-300 uppercase tracking-wider mb-1.5 ml-1">Minute</span>
          <div className="relative flex items-center">
            <select
              value={minute}
              onChange={handleMinuteChange}
              aria-label="Select Minute"
              className="h-14 min-w-[104px] bg-slate-900 border-2 border-slate-600 hover:border-blue-400 focus:border-blue-400 focus:ring-4 focus:ring-blue-400/30 rounded-2xl pl-4 pr-10 text-2xl font-black text-white text-center cursor-pointer outline-none transition-all appearance-none shadow-inner"
            >
              <optgroup label="Common Times">
                {COMMON_MINUTES.map((m) => (
                  <option key={`common_${m}`} value={m} className="bg-slate-900 text-white font-bold py-2 text-lg">
                    {m}
                  </option>
                ))}
              </optgroup>
              <optgroup label="All Minutes">
                {MINUTES.map((m) => (
                  <option key={`all_${m}`} value={m} className="bg-slate-900 text-white font-medium py-1">
                    {m}
                  </option>
                ))}
              </optgroup>
            </select>
            <ChevronDown className="w-5 h-5 text-blue-400 absolute right-3 pointer-events-none" />
          </div>
        </div>

        {/* AM / PM Large Segmented Toggle */}
        <div className="flex flex-col ml-auto sm:ml-2">
          <span className="text-xs font-black text-slate-300 uppercase tracking-wider mb-1.5 ml-1">AM or PM</span>
          <div className="flex items-center h-14 bg-slate-900 p-1.5 rounded-2xl border-2 border-slate-600 gap-1.5 shadow-inner" role="radiogroup" aria-label="AM or PM selection">
            <button
              type="button"
              onClick={() => handlePeriodChange('AM')}
              aria-label="Select AM"
              aria-pressed={period === 'AM'}
              className={`h-full px-5 rounded-xl font-black text-lg transition-all cursor-pointer flex items-center justify-center min-w-[68px] ${
                period === 'AM'
                  ? 'bg-blue-600 text-white shadow-lg shadow-blue-600/40 border-2 border-blue-400 scale-[1.02]'
                  : 'text-slate-300 hover:text-white hover:bg-slate-800'
              }`}
            >
              AM
            </button>
            <button
              type="button"
              onClick={() => handlePeriodChange('PM')}
              aria-label="Select PM"
              aria-pressed={period === 'PM'}
              className={`h-full px-5 rounded-xl font-black text-lg transition-all cursor-pointer flex items-center justify-center min-w-[68px] ${
                period === 'PM'
                  ? 'bg-blue-600 text-white shadow-lg shadow-blue-600/40 border-2 border-blue-400 scale-[1.02]'
                  : 'text-slate-300 hover:text-white hover:bg-slate-800'
              }`}
            >
              PM
            </button>
          </div>
        </div>

      </div>
    </div>
  );
}

/**
 * Main ReminderTimePicker supporting single or multiple dose schedules based on frequency.
 */
export default function ReminderTimePicker({
  timings = [],
  onChange,
  frequency = "Once Daily",
  isCustom = false
}) {
  // Ensure timings is an array of strings
  const timeList = Array.isArray(timings) && timings.length > 0 ? timings : ['08:00 AM'];

  // Check for duplicates
  const hasDuplicates = new Set(timeList).size !== timeList.length;

  const handleTimeChange = (index, newTimeStr) => {
    const updated = [...timeList];
    updated[index] = newTimeStr;
    onChange(updated);
  };

  const handleAddTime = () => {
    const lastTime = timeList[timeList.length - 1] || '08:00 AM';
    const parsed = parseTimeString(lastTime);
    // Add 1 hour default
    let h = parseInt(parsed.hour, 10) + 1;
    let period = parsed.period;
    if (h > 12) {
      h = 1;
      period = period === 'AM' ? 'PM' : 'AM';
    }
    const newTime = formatTimeParts(h, parsed.minute, period);
    onChange([...timeList, newTime]);
  };

  const handleRemoveTime = (index) => {
    if (timeList.length <= 1) return;
    const updated = timeList.filter((_, i) => i !== index);
    onChange(updated);
  };

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <label className="text-lg font-extrabold text-slate-200 tracking-wide block">
          Reminder Times <span className="text-red-400">*</span>
        </label>
        <span className="text-sm font-bold text-slate-300 bg-slate-800/80 px-3.5 py-1.5 rounded-full border border-slate-700">
          {timeList.length} {timeList.length === 1 ? 'Dose per day' : 'Doses per day'}
        </span>
      </div>

      {hasDuplicates && (
        <div className="p-4 bg-amber-500/15 border-2 border-amber-500/40 rounded-2xl text-amber-200 text-sm font-bold flex items-center gap-3 shadow-lg">
          <AlertTriangle className="w-6 h-6 text-amber-400 shrink-0" />
          <span>Duplicate reminder times detected. Please select a unique time for each dose.</span>
        </div>
      )}

      <div className="space-y-4">
        {timeList.map((t, idx) => {
          let doseLabel = `Dose ${idx + 1}`;
          if (timeList.length === 1) doseLabel = "Reminder Time";
          else if (timeList.length === 2) doseLabel = idx === 0 ? "Dose 1 (Morning/Day)" : "Dose 2 (Evening/Night)";
          else if (timeList.length === 3) doseLabel = idx === 0 ? "Dose 1 (Morning)" : idx === 1 ? "Dose 2 (Afternoon)" : "Dose 3 (Evening)";

          return (
            <SingleTimePickerRow
              key={idx}
              value={t}
              onChange={(newVal) => handleTimeChange(idx, newVal)}
              label={doseLabel}
              onDelete={(isCustom || frequency === 'Custom') && timeList.length > 1 ? () => handleRemoveTime(idx) : null}
              showPresets={timeList.length === 1}
            />
          );
        })}
      </div>

      {(isCustom || frequency === 'Custom') && (
        <button
          type="button"
          onClick={handleAddTime}
          className="w-full py-3.5 border-2 border-dashed border-blue-500/50 hover:border-blue-400 text-blue-300 hover:bg-blue-500/10 rounded-2xl font-bold transition-all text-base flex items-center justify-center gap-2 cursor-pointer mt-2"
        >
          <Plus className="w-5 h-5" /> Add Additional Reminder Time
        </button>
      )}
    </div>
  );
}

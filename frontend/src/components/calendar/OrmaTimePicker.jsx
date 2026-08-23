import React, { useState, useEffect, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Clock, ChevronDown } from 'lucide-react';

const COMMON_PRESETS = [
  '08:00 AM',
  '09:30 AM',
  '10:30 AM',
  '12:00 PM',
  '02:00 PM',
  '04:30 PM',
  '06:00 PM',
  '08:00 PM'
];

export default function OrmaTimePicker({
  value, // e.g. "10:30 AM" or "14:00"
  onChange,
  label = 'Time',
  disabled = false,
  className = ''
}) {
  const [isOpen, setIsOpen] = useState(false);
  const containerRef = useRef(null);

  // Parse time components
  const parseTime = (timeStr) => {
    if (!timeStr) return { hour: '10', minute: '30', ampm: 'AM' };
    const str = String(timeStr).trim();
    const match = str.match(/(\d+):(\d+)\s*(AM|PM)?/i);
    if (match) {
      let h = parseInt(match[1], 10);
      const m = match[2].padStart(2, '0');
      let period = match[3] ? match[3].toUpperCase() : 'AM';

      if (!match[3]) {
        // 24-hour format conversion
        period = h >= 12 ? 'PM' : 'AM';
        h = h % 12 || 12;
      }
      return { hour: String(h).padStart(2, '0'), minute: m, ampm: period };
    }
    return { hour: '10', minute: '30', ampm: 'AM' };
  };

  const [timeState, setTimeState] = useState(parseTime(value));

  useEffect(() => {
    if (value) {
      setTimeState(parseTime(value));
    }
  }, [value]);

  // Close on outside click
  useEffect(() => {
    const handleClickOutside = (e) => {
      if (containerRef.current && !containerRef.current.contains(e.target)) {
        setIsOpen(false);
      }
    };
    if (isOpen) {
      document.addEventListener('mousedown', handleClickOutside);
    }
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, [isOpen]);

  const updateTime = (h, m, p) => {
    const formatted = `${String(h).padStart(2, '0')}:${String(m).padStart(2, '0')} ${p}`;
    setTimeState({ hour: String(h).padStart(2, '0'), minute: String(m).padStart(2, '0'), ampm: p });
    onChange(formatted);
  };

  const hours = Array.from({ length: 12 }, (_, i) => String(i + 1).padStart(2, '0'));
  const minutes = ['00', '15', '30', '45'];

  return (
    <div className={`relative ${className}`} ref={containerRef}>
      {label && (
        <label className="block text-xs font-bold text-slate-300 uppercase tracking-wider mb-1.5">
          {label}
        </label>
      )}

      {/* Trigger Button */}
      <button
        type="button"
        disabled={disabled}
        onClick={() => setIsOpen(!isOpen)}
        className={`w-full flex items-center justify-between px-4 py-2.5 rounded-2xl bg-slate-900/80 border text-sm font-medium transition-all cursor-pointer ${
          isOpen
            ? 'border-blue-500 shadow-[0_0_15px_rgba(59,130,246,0.2)] text-white'
            : 'border-white/10 hover:border-white/20 text-slate-200'
        } ${disabled ? 'opacity-50 cursor-not-allowed' : ''}`}
      >
        <div className="flex items-center gap-2.5">
          <Clock className="w-4 h-4 text-blue-400" />
          <span className="font-mono font-bold tracking-wider">{value || 'Select Time'}</span>
        </div>
        <ChevronDown className={`w-4 h-4 text-slate-400 transition-transform ${isOpen ? 'rotate-180' : ''}`} />
      </button>

      {/* Popover */}
      <AnimatePresence>
        {isOpen && (
          <motion.div
            initial={{ opacity: 0, y: 6, scale: 0.98 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: 4, scale: 0.98 }}
            transition={{ duration: 0.15 }}
            className="absolute left-0 top-full mt-2 z-50 w-72 p-4 rounded-3xl bg-slate-900/95 backdrop-blur-2xl border border-white/15 shadow-2xl"
          >
            {/* Quick Presets */}
            <div className="mb-3.5">
              <span className="text-[10px] uppercase font-bold text-slate-400 tracking-wider mb-1.5 block">
                Quick Presets
              </span>
              <div className="grid grid-cols-2 gap-1.5">
                {COMMON_PRESETS.map((preset) => (
                  <button
                    key={preset}
                    type="button"
                    onClick={() => {
                      onChange(preset);
                      setIsOpen(false);
                    }}
                    className={`py-1.5 px-2.5 rounded-xl text-xs font-mono font-bold transition-colors cursor-pointer text-left ${
                      value === preset
                        ? 'bg-blue-600 text-white shadow-sm'
                        : 'bg-slate-950/60 text-slate-300 hover:bg-white/10 hover:text-white border border-white/5'
                    }`}
                  >
                    {preset}
                  </button>
                ))}
              </div>
            </div>

            {/* Custom Time Spinners */}
            <div className="pt-3 border-t border-white/10">
              <span className="text-[10px] uppercase font-bold text-slate-400 tracking-wider mb-2 block">
                Custom Selection
              </span>
              
              <div className="flex items-center justify-center gap-2">
                {/* Hours */}
                <select
                  value={timeState.hour}
                  onChange={(e) => updateTime(e.target.value, timeState.minute, timeState.ampm)}
                  className="bg-slate-950 border border-white/15 rounded-xl px-2.5 py-1.5 text-sm font-mono font-bold text-white focus:border-blue-500 focus:outline-none cursor-pointer"
                >
                  {hours.map((h) => (
                    <option key={h} value={h} className="bg-slate-900 text-white">{h}</option>
                  ))}
                </select>

                <span className="text-white font-bold font-mono">:</span>

                {/* Minutes */}
                <select
                  value={timeState.minute}
                  onChange={(e) => updateTime(timeState.hour, e.target.value, timeState.ampm)}
                  className="bg-slate-950 border border-white/15 rounded-xl px-2.5 py-1.5 text-sm font-mono font-bold text-white focus:border-blue-500 focus:outline-none cursor-pointer"
                >
                  {minutes.map((m) => (
                    <option key={m} value={m} className="bg-slate-900 text-white">{m}</option>
                  ))}
                </select>

                {/* AM / PM Toggle */}
                <div className="flex rounded-xl bg-slate-950 border border-white/15 p-0.5">
                  {['AM', 'PM'].map((period) => (
                    <button
                      key={period}
                      type="button"
                      onClick={() => updateTime(timeState.hour, timeState.minute, period)}
                      className={`px-2.5 py-1 text-xs font-bold rounded-lg transition-colors cursor-pointer ${
                        timeState.ampm === period
                          ? 'bg-blue-600 text-white shadow-sm'
                          : 'text-slate-400 hover:text-white'
                      }`}
                    >
                      {period}
                    </button>
                  ))}
                </div>
              </div>
            </div>

            {/* Confirm Button */}
            <div className="mt-4 pt-2 border-t border-white/5">
              <button
                type="button"
                onClick={() => setIsOpen(false)}
                className="w-full py-1.5 bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-bold rounded-xl transition-colors cursor-pointer"
              >
                Done
              </button>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}

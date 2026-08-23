import React from 'react';
import { Minus, Plus } from 'lucide-react';

export default function OrmaSlider({
  label,
  value = 50,
  min = 0,
  max = 100,
  step = 5,
  unit = '%',
  onChange,
  showSteppers = true,
  disabled = false,
  className = ''
}) {
  const handleDecrement = () => {
    if (!disabled && onChange) {
      onChange(Math.max(min, value - step));
    }
  };

  const handleIncrement = () => {
    if (!disabled && onChange) {
      onChange(Math.min(max, value + step));
    }
  };

  const percentage = ((value - min) / (max - min)) * 100;

  return (
    <div className={`w-full ${className}`}>
      <div className="flex items-center justify-between mb-2">
        {label && (
          <label className="text-xs sm:text-sm font-bold text-white tracking-tight">
            {label}
          </label>
        )}
        <span className="text-xs sm:text-sm font-bold text-blue-400 font-mono bg-blue-500/10 border border-blue-500/20 px-2.5 py-0.5 rounded-full">
          {value}{unit}
        </span>
      </div>

      <div className="flex items-center gap-3">
        {showSteppers && (
          <button
            type="button"
            disabled={disabled || value <= min}
            onClick={handleDecrement}
            className="w-8 h-8 rounded-xl bg-slate-900 border border-white/10 hover:border-white/20 text-slate-300 hover:text-white flex items-center justify-center transition-colors disabled:opacity-40 cursor-pointer"
            aria-label="Decrease value"
          >
            <Minus className="w-4 h-4" />
          </button>
        )}

        <div className="relative flex-1 flex items-center">
          <input
            type="range"
            min={min}
            max={max}
            step={step}
            value={value}
            disabled={disabled}
            onChange={(e) => onChange && onChange(Number(e.target.value))}
            className="w-full h-2.5 bg-slate-800 rounded-full appearance-none cursor-pointer accent-blue-500 focus:outline-none"
            style={{
              background: `linear-gradient(to right, #3b82f6 ${percentage}%, #1e293b ${percentage}%)`
            }}
          />
        </div>

        {showSteppers && (
          <button
            type="button"
            disabled={disabled || value >= max}
            onClick={handleIncrement}
            className="w-8 h-8 rounded-xl bg-slate-900 border border-white/10 hover:border-white/20 text-slate-300 hover:text-white flex items-center justify-center transition-colors disabled:opacity-40 cursor-pointer"
            aria-label="Increase value"
          >
            <Plus className="w-4 h-4" />
          </button>
        )}
      </div>
    </div>
  );
}

import React from 'react';
import { motion } from 'framer-motion';

export default function OrmaToggle({
  label,
  description,
  checked = false,
  onChange,
  disabled = false,
  size = 'default', // 'default' | 'large'
  showStatusLabel = true,
  className = '',
  id
}) {
  const isLarge = size === 'large';
  const toggleId = id || (label ? label.toLowerCase().replace(/\s+/g, '-') : undefined);

  const handleToggle = () => {
    if (!disabled && onChange) {
      onChange(!checked);
    }
  };

  return (
    <div className={`flex items-center justify-between gap-4 ${className}`}>
      {(label || description) && (
        <div className="flex-1 min-w-0">
          {label && (
            <label
              htmlFor={toggleId}
              onClick={handleToggle}
              className={`block font-bold text-white tracking-tight cursor-pointer ${
                isLarge ? 'text-base sm:text-lg' : 'text-sm sm:text-base'
              } ${disabled ? 'opacity-50' : ''}`}
            >
              {label}
            </label>
          )}
          {description && (
            <p className={`text-slate-400 mt-0.5 leading-relaxed ${isLarge ? 'text-xs sm:text-sm' : 'text-xs'}`}>
              {description}
            </p>
          )}
        </div>
      )}

      <div className="flex items-center gap-2.5 shrink-0">
        {showStatusLabel && (
          <span className={`text-[11px] font-extrabold uppercase px-2 py-0.5 rounded-full border transition-colors ${
            checked 
              ? 'bg-blue-500/15 text-blue-400 border-blue-500/30' 
              : 'bg-slate-800 text-slate-400 border-slate-700'
          }`}>
            {checked ? 'ON' : 'OFF'}
          </span>
        )}

        <button
          id={toggleId}
          type="button"
          role="switch"
          aria-checked={checked}
          disabled={disabled}
          onClick={handleToggle}
          className={`relative rounded-full transition-colors cursor-pointer focus:outline-none focus:ring-2 focus:ring-blue-500/50 p-1 border ${
            isLarge ? 'w-16 h-9' : 'w-14 h-8'
          } ${
            checked
              ? 'bg-blue-600 border-blue-400/50 shadow-[0_0_15px_rgba(59,130,246,0.35)]'
              : 'bg-slate-900 border-white/15 hover:border-white/25'
          } ${disabled ? 'opacity-50 cursor-not-allowed' : ''}`}
        >
          <motion.div
            layout
            transition={{ type: 'spring', stiffness: 500, damping: 30 }}
            className={`rounded-full bg-white shadow-md ${
              isLarge ? 'w-7 h-7' : 'w-6 h-6'
            }`}
            style={{
              marginLeft: checked ? 'auto' : '0'
            }}
          />
        </button>
      </div>
    </div>
  );
}

import React from 'react';
import { motion } from 'framer-motion';

export function OrmaRadialProgress({
  percentage = 0,
  size = 120,
  strokeWidth = 10,
  label = 'Adherence',
  sublabel = 'This week',
  color = '#3b82f6', // blue
  trackColor = 'rgba(255, 255, 255, 0.08)',
  className = ''
}) {
  const radius = (size - strokeWidth) / 2;
  const circumference = 2 * Math.PI * radius;
  const safePercentage = Math.max(0, Math.min(100, isNaN(percentage) ? 0 : percentage));
  const strokeDashoffset = circumference - (safePercentage / 100) * circumference;

  return (
    <div className={`flex flex-col items-center justify-center ${className}`}>
      <div className="relative flex items-center justify-center" style={{ width: size, height: size }}>
        <svg width={size} height={size} className="rotate-[-90deg]">
          {/* Background Track */}
          <circle
            cx={size / 2}
            cy={size / 2}
            r={radius}
            stroke={trackColor}
            strokeWidth={strokeWidth}
            fill="transparent"
          />
          {/* Animated Value Arc */}
          <circle
            cx={size / 2}
            cy={size / 2}
            r={radius}
            stroke={color}
            strokeWidth={strokeWidth}
            strokeDasharray={circumference}
            strokeDashoffset={strokeDashoffset}
            strokeLinecap="round"
            fill="transparent"
            className="transition-all duration-700 ease-out"
          />
        </svg>

        {/* Center Percentage Display */}
        <div className="absolute inset-0 flex flex-col items-center justify-center text-center">
          <span className="text-2xl sm:text-3xl font-black text-white tracking-tight">
            {Math.round(safePercentage)}%
          </span>
          {label && (
            <span className="text-[10px] sm:text-xs font-bold text-slate-400 uppercase tracking-wider">
              {label}
            </span>
          )}
        </div>
      </div>

      {sublabel && (
        <p className="text-xs text-slate-400 font-medium mt-2.5 text-center">
          {sublabel}
        </p>
      )}
    </div>
  );
}

export function OrmaLinearProgress({
  value = 0,
  max = 100,
  label,
  valueLabel,
  helperText,
  colorVariant = 'blue', // 'blue' | 'emerald' | 'amber' | 'purple'
  className = ''
}) {
  const percentage = Math.max(0, Math.min(100, (value / max) * 100));

  const variantColors = {
    blue: 'bg-blue-500',
    emerald: 'bg-emerald-500',
    amber: 'bg-amber-500',
    purple: 'bg-purple-500'
  };

  return (
    <div className={`w-full ${className}`}>
      {(label || valueLabel) && (
        <div className="flex items-center justify-between text-xs font-bold mb-1.5">
          {label && <span className="text-slate-300">{label}</span>}
          <span className="text-white font-mono">{valueLabel || `${Math.round(percentage)}%`}</span>
        </div>
      )}

      <div className="w-full h-2.5 bg-slate-800/80 rounded-full overflow-hidden border border-white/5">
        <motion.div
          initial={{ width: 0 }}
          animate={{ width: `${percentage}%` }}
          transition={{ duration: 0.5, ease: 'easeOut' }}
          className={`h-full rounded-full ${variantColors[colorVariant] || variantColors.blue}`}
        />
      </div>

      {helperText && (
        <p className="text-[11px] text-slate-400 mt-1">
          {helperText}
        </p>
      )}
    </div>
  );
}

export default OrmaRadialProgress;

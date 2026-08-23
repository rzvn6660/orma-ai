import React from 'react';
import { motion } from 'framer-motion';
import { Check } from 'lucide-react';

export default function OrmaRadioGroup({
  label,
  options = [], // [{ value, label, description, icon: Icon }]
  value,
  onChange,
  className = '',
  orientation = 'vertical' // 'vertical' | 'horizontal'
}) {
  return (
    <div className={`w-full ${className}`} role="radiogroup" aria-label={label}>
      {label && (
        <label className="block text-xs font-bold text-slate-300 uppercase tracking-wider mb-2.5">
          {label}
        </label>
      )}

      <div className={`grid gap-2.5 ${
        orientation === 'horizontal' ? 'grid-cols-1 sm:grid-cols-2 md:grid-cols-3' : 'grid-cols-1'
      }`}>
        {options.map((option) => {
          const isSelected = value === option.value;
          const Icon = option.icon;

          return (
            <button
              key={option.value}
              type="button"
              role="radio"
              aria-checked={isSelected}
              onClick={() => onChange(option.value)}
              className={`p-4 rounded-2xl border text-left transition-all flex items-start gap-3.5 relative cursor-pointer ${
                isSelected
                  ? 'bg-blue-600/15 border-blue-500 shadow-md shadow-blue-500/10 ring-1 ring-blue-500/50'
                  : 'bg-slate-950/50 border-white/10 hover:border-white/20 hover:bg-slate-900/50'
              }`}
            >
              {/* Radio Indicator */}
              <div className={`w-5 h-5 rounded-full border flex items-center justify-center mt-0.5 shrink-0 transition-colors ${
                isSelected ? 'border-blue-400 bg-blue-500 text-white' : 'border-slate-600 bg-slate-900'
              }`}>
                {isSelected && <div className="w-2 h-2 rounded-full bg-white" />}
              </div>

              {/* Icon if provided */}
              {Icon && (
                <div className={`w-8 h-8 rounded-xl flex items-center justify-center shrink-0 ${
                  isSelected ? 'bg-blue-500/20 text-blue-400' : 'bg-slate-800 text-slate-400'
                }`}>
                  <Icon className="w-4 h-4" />
                </div>
              )}

              {/* Text */}
              <div className="flex-1 min-w-0">
                <p className={`text-sm font-bold tracking-tight ${isSelected ? 'text-white' : 'text-slate-200'}`}>
                  {option.label}
                </p>
                {option.description && (
                  <p className="text-xs text-slate-400 mt-0.5 leading-relaxed">
                    {option.description}
                  </p>
                )}
              </div>
            </button>
          );
        })}
      </div>
    </div>
  );
}

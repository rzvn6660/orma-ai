import React from 'react';
import { X, AlertCircle } from 'lucide-react';

export default function OrmaInput({
  label,
  error,
  helperText,
  icon: Icon,
  size = 'default', // 'default' | 'large'
  clearable = false,
  value,
  onChange,
  onClear,
  className = '',
  id,
  type = 'text',
  disabled = false,
  required = false,
  placeholder,
  ...props
}) {
  const inputId = id || (label ? label.toLowerCase().replace(/\s+/g, '-') : undefined);
  const isLarge = size === 'large';

  return (
    <div className={`w-full ${className}`}>
      {label && (
        <label 
          htmlFor={inputId}
          className={`block font-bold text-slate-300 uppercase tracking-wider mb-1.5 ${
            isLarge ? 'text-xs sm:text-sm' : 'text-xs'
          }`}
        >
          {label} {required && <span className="text-red-400">*</span>}
        </label>
      )}

      <div className="relative flex items-center">
        {Icon && (
          <div className="absolute left-3.5 text-slate-400 pointer-events-none flex items-center justify-center">
            <Icon className={isLarge ? 'w-5 h-5' : 'w-4 h-4'} />
          </div>
        )}

        <input
          id={inputId}
          type={type}
          value={value}
          onChange={onChange}
          disabled={disabled}
          required={required}
          placeholder={placeholder}
          className={`w-full rounded-2xl bg-slate-950/70 border transition-all text-white placeholder-slate-500 outline-none ${
            Icon ? (isLarge ? 'pl-11' : 'pl-10') : 'px-4'
          } ${clearable && value ? 'pr-10' : 'pr-4'} ${
            isLarge ? 'py-3.5 text-base sm:text-lg min-h-[52px]' : 'py-2.5 text-sm min-h-[42px]'
          } ${
            error 
              ? 'border-red-500/50 focus:border-red-400 bg-red-950/10' 
              : 'border-white/10 hover:border-white/20 focus:border-blue-500 focus:bg-slate-900 shadow-sm'
          } ${disabled ? 'opacity-50 cursor-not-allowed' : ''}`}
          {...props}
        />

        {clearable && value && !disabled && (
          <button
            type="button"
            onClick={onClear || (() => onChange && onChange({ target: { value: '' } }))}
            className="absolute right-3 p-1 rounded-lg text-slate-400 hover:text-white hover:bg-white/10 transition-colors cursor-pointer"
            aria-label="Clear input"
          >
            <X className="w-4 h-4" />
          </button>
        )}
      </div>

      {error ? (
        <p className="mt-1.5 text-xs text-red-400 font-semibold flex items-center gap-1">
          <AlertCircle className="w-3.5 h-3.5 shrink-0" />
          <span>{error}</span>
        </p>
      ) : helperText ? (
        <p className="mt-1 text-[11px] text-slate-400 font-medium">
          {helperText}
        </p>
      ) : null}
    </div>
  );
}

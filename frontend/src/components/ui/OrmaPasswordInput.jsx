import React, { useState } from 'react';
import { Lock, Eye, EyeOff, Check, AlertCircle } from 'lucide-react';

export default function OrmaPasswordInput({
  label = 'Password',
  value = '',
  onChange,
  error,
  helperText,
  showStrengthMeter = false,
  size = 'default',
  required = false,
  placeholder = '••••••••',
  id,
  className = '',
  ...props
}) {
  const [showPassword, setShowPassword] = useState(false);
  const inputId = id || 'password-input';
  const isLarge = size === 'large';

  // Password requirements calculation
  const passLength = value.length >= 8;
  const passLower = /[a-z]/.test(value);
  const passUpper = /[A-Z]/.test(value);
  const passNum = /\d/.test(value);
  const passSpecial = /[@$!%*?&#^()]/.test(value);

  const passedCount = [passLength, passLower, passUpper, passNum, passSpecial].filter(Boolean).length;
  const strengthPercentage = (passedCount / 5) * 100;

  let strengthLabel = 'Weak';
  let strengthColor = 'bg-red-500';
  let strengthTextColor = 'text-red-400';

  if (passedCount >= 4) {
    strengthLabel = 'Strong';
    strengthColor = 'bg-emerald-500';
    strengthTextColor = 'text-emerald-400';
  } else if (passedCount >= 2) {
    strengthLabel = 'Moderate';
    strengthColor = 'bg-amber-500';
    strengthTextColor = 'text-amber-400';
  }

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
        <div className="absolute left-3.5 text-slate-400 pointer-events-none flex items-center justify-center">
          <Lock className={isLarge ? 'w-5 h-5' : 'w-4 h-4'} />
        </div>

        <input
          id={inputId}
          type={showPassword ? 'text' : 'password'}
          value={value}
          onChange={onChange}
          required={required}
          placeholder={placeholder}
          className={`w-full rounded-2xl bg-slate-950/70 border transition-all text-white placeholder-slate-500 outline-none pl-10 pr-11 ${
            isLarge ? 'py-3.5 text-base sm:text-lg min-h-[52px]' : 'py-2.5 text-sm min-h-[42px]'
          } ${
            error 
              ? 'border-red-500/50 focus:border-red-400 bg-red-950/10' 
              : 'border-white/10 hover:border-white/20 focus:border-blue-500 focus:bg-slate-900 shadow-sm'
          }`}
          {...props}
        />

        <button
          type="button"
          onClick={() => setShowPassword(!showPassword)}
          className="absolute right-3 p-1.5 rounded-xl text-slate-400 hover:text-white hover:bg-white/10 transition-colors cursor-pointer"
          aria-label={showPassword ? 'Hide password' : 'Show password'}
        >
          {showPassword ? (
            <EyeOff className={isLarge ? 'w-5 h-5 text-blue-400' : 'w-4 h-4 text-blue-400'} />
          ) : (
            <Eye className={isLarge ? 'w-5 h-5' : 'w-4 h-4'} />
          )}
        </button>
      </div>

      {/* Password Strength Progress Bar & Checklist */}
      {showStrengthMeter && value.length > 0 && (
        <div className="mt-3 p-3 bg-slate-950/60 border border-white/10 rounded-2xl space-y-2">
          <div className="flex items-center justify-between text-xs">
            <span className="text-slate-400 font-medium">Password Strength:</span>
            <span className={`font-bold ${strengthTextColor}`}>{strengthLabel}</span>
          </div>

          <div className="w-full h-1.5 bg-slate-800 rounded-full overflow-hidden">
            <div 
              style={{ width: `${strengthPercentage}%` }} 
              className={`h-full ${strengthColor} transition-all duration-300 rounded-full`} 
            />
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-1 pt-1 text-[11px] font-medium">
            <div className={`flex items-center gap-1.5 ${passLength ? 'text-emerald-400' : 'text-slate-500'}`}>
              <Check className="w-3.5 h-3.5" /> 8+ characters
            </div>
            <div className={`flex items-center gap-1.5 ${passUpper && passLower ? 'text-emerald-400' : 'text-slate-500'}`}>
              <Check className="w-3.5 h-3.5" /> Uppercase & lowercase
            </div>
            <div className={`flex items-center gap-1.5 ${passNum ? 'text-emerald-400' : 'text-slate-500'}`}>
              <Check className="w-3.5 h-3.5" /> At least one number
            </div>
            <div className={`flex items-center gap-1.5 ${passSpecial ? 'text-emerald-400' : 'text-slate-500'}`}>
              <Check className="w-3.5 h-3.5" /> Special character (@$!%*?)
            </div>
          </div>
        </div>
      )}

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

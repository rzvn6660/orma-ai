import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';

export function OrmaSpinner({
  size = 'md', // 'sm' | 'md' | 'lg' | 'xl'
  variant = 'blue', // 'blue' | 'emerald' | 'purple' | 'white'
  className = ''
}) {
  const [isReducedMotion, setIsReducedMotion] = useState(false);

  useEffect(() => {
    if (typeof window !== 'undefined') {
      const media = window.matchMedia('(prefers-reduced-motion: reduce)');
      setIsReducedMotion(media.matches);
      const listener = (e) => setIsReducedMotion(e.matches);
      media.addEventListener('change', listener);
      return () => media.removeEventListener('change', listener);
    }
  }, []);

  const sizeDimensions = {
    sm: 16,
    md: 24,
    lg: 36,
    xl: 48
  };

  const strokeWidths = {
    sm: 2.5,
    md: 3,
    lg: 3.5,
    xl: 4
  };

  const colors = {
    blue: '#3b82f6',
    emerald: '#10b981',
    purple: '#a855f7',
    white: '#ffffff'
  };

  const d = sizeDimensions[size] || 24;
  const sw = strokeWidths[size] || 3;
  const strokeColor = colors[variant] || colors.blue;
  const radius = (d - sw) / 2;
  const circumference = 2 * Math.PI * radius;

  return (
    <div 
      className={`inline-flex items-center justify-center ${className}`}
      role="status"
      aria-label="Loading"
    >
      <svg
        width={d}
        height={d}
        viewBox={`0 0 ${d} ${d}`}
        className={isReducedMotion ? 'opacity-80' : 'animate-spin'}
        style={isReducedMotion ? {} : { animationDuration: '1s' }}
      >
        <circle
          cx={d / 2}
          cy={d / 2}
          r={radius}
          stroke="rgba(255, 255, 255, 0.12)"
          strokeWidth={sw}
          fill="none"
        />
        <circle
          cx={d / 2}
          cy={d / 2}
          r={radius}
          stroke={strokeColor}
          strokeWidth={sw}
          strokeLinecap="round"
          strokeDasharray={circumference}
          strokeDashoffset={circumference * 0.7}
          fill="none"
        />
      </svg>
    </div>
  );
}

export function OrmaLoadingState({
  title = 'Loading...',
  description,
  variant = 'blue',
  size = 'lg',
  className = ''
}) {
  return (
    <div className={`flex flex-col items-center justify-center p-8 sm:p-12 text-center ${className}`}>
      <div className="p-4 rounded-3xl bg-slate-900/80 border border-white/10 shadow-xl mb-4 backdrop-blur-xl">
        <OrmaSpinner size={size} variant={variant} />
      </div>
      <h4 className="text-base sm:text-lg font-bold text-white tracking-tight mb-1">
        {title}
      </h4>
      {description && (
        <p className="text-xs sm:text-sm text-slate-400 max-w-sm leading-relaxed">
          {description}
        </p>
      )}
    </div>
  );
}

export default OrmaSpinner;

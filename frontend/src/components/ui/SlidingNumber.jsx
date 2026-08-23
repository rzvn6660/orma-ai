import React from 'react';
import { motion, useReducedMotion } from 'framer-motion';

/**
 * SlidingDigit Component
 * Smoothly shifts between digits (0-9) using Framer Motion vertical translation.
 * Respects prefers-reduced-motion for elderly accessibility.
 */
export function SlidingDigit({ digit, className = '' }) {
  const shouldReduceMotion = useReducedMotion();
  const num = parseInt(digit, 10);
  const isNumber = !isNaN(num);

  if (!isNumber) {
    return <span className={`inline-block select-none ${className}`}>{digit}</span>;
  }

  if (shouldReduceMotion) {
    return <span className={`inline-block tabular-nums select-none ${className}`}>{digit}</span>;
  }

  return (
    <span 
      className={`inline-block overflow-hidden relative tabular-nums select-none ${className}`}
      style={{ height: '1.05em', verticalAlign: 'middle' }}
    >
      <motion.span
        className="flex flex-col items-center"
        initial={false}
        animate={{ y: `-${num * 10}%` }}
        transition={{
          type: 'spring',
          stiffness: 260,
          damping: 28,
          mass: 0.8
        }}
        style={{ height: '1000%' }}
      >
        {[0, 1, 2, 3, 4, 5, 6, 7, 8, 9].map((n) => (
          <span 
            key={n} 
            className="flex items-center justify-center"
            style={{ height: '10%' }}
          >
            {n}
          </span>
        ))}
      </motion.span>
    </span>
  );
}

/**
 * SlidingTimeDisplay Component
 * Renders 12-hour formatted time (HH:MM AM/PM) with smooth sliding digits.
 */
export function SlidingTimeDisplay({ 
  hours, 
  minutes, 
  period, 
  className = '', 
  digitClassName = '', 
  periodClassName = '',
  colonClassName = ''
}) {
  const hourDigits = hours.split('');
  const minuteDigits = minutes.split('');

  return (
    <div 
      className={`inline-flex items-center font-black tracking-tight ${className}`} 
      aria-label={`${hours}:${minutes} ${period}`}
    >
      {/* Hours Digits */}
      <span className="inline-flex items-center">
        {hourDigits.map((d, i) => (
          <SlidingDigit key={`h-${i}`} digit={d} className={digitClassName} />
        ))}
      </span>

      {/* Colon Separator */}
      <span className={`inline-block mx-0.5 sm:mx-1 opacity-70 ${colonClassName || digitClassName}`}>
        :
      </span>

      {/* Minutes Digits */}
      <span className="inline-flex items-center">
        {minuteDigits.map((d, i) => (
          <SlidingDigit key={`m-${i}`} digit={d} className={digitClassName} />
        ))}
      </span>

      {/* Period (AM/PM) */}
      {period && (
        <span className={`ml-2 sm:ml-3 ${periodClassName}`}>
          {period}
        </span>
      )}
    </div>
  );
}

export default SlidingTimeDisplay;

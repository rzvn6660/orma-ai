import React, { useRef, useEffect } from 'react';

export default function OtpInput({
  length = 6,
  value = '',
  onChange,
  disabled = false,
  error = false,
  className = ''
}) {
  const inputRefs = useRef([]);

  // Ensure refs array is initialized
  useEffect(() => {
    inputRefs.current = inputRefs.current.slice(0, length);
  }, [length]);

  const digits = (value || '').padEnd(length, ' ').slice(0, length).split('');

  const handleChange = (index, e) => {
    const char = e.target.value.slice(-1);
    if (!/^[0-9]$/.test(char) && char !== '') return;

    const newDigits = [...digits];
    newDigits[index] = char || ' ';
    const newValue = newDigits.join('').trimEnd();
    onChange(newValue);

    // Focus next input if digit entered
    if (char && index < length - 1) {
      inputRefs.current[index + 1]?.focus();
    }
  };

  const handleKeyDown = (index, e) => {
    if (e.key === 'Backspace') {
      if (!digits[index] || digits[index] === ' ') {
        if (index > 0) {
          inputRefs.current[index - 1]?.focus();
          const newDigits = [...digits];
          newDigits[index - 1] = ' ';
          onChange(newDigits.join('').trimEnd());
        }
      } else {
        const newDigits = [...digits];
        newDigits[index] = ' ';
        onChange(newDigits.join('').trimEnd());
      }
    } else if (e.key === 'ArrowLeft' && index > 0) {
      inputRefs.current[index - 1]?.focus();
    } else if (e.key === 'ArrowRight' && index < length - 1) {
      inputRefs.current[index + 1]?.focus();
    }
  };

  const handlePaste = (e) => {
    e.preventDefault();
    const pasteData = e.clipboardData.getData('text').trim();
    if (!/^[0-9]+$/.test(pasteData)) return;

    const pastedDigits = pasteData.slice(0, length);
    onChange(pastedDigits);

    const nextFocusIndex = Math.min(pastedDigits.length, length - 1);
    inputRefs.current[nextFocusIndex]?.focus();
  };

  return (
    <div className={`flex items-center justify-center gap-2 sm:gap-3 ${className}`} onPaste={handlePaste}>
      {Array.from({ length }, (_, i) => {
        const digit = digits[i] !== ' ' ? digits[i] : '';
        const isFilled = Boolean(digit);

        return (
          <input
            key={i}
            ref={(el) => (inputRefs.current[i] = el)}
            type="text"
            inputMode="numeric"
            pattern="[0-9]*"
            maxLength={1}
            value={digit}
            disabled={disabled}
            onChange={(e) => handleChange(i, e)}
            onKeyDown={(e) => handleKeyDown(i, e)}
            className={`w-11 h-14 sm:w-12 sm:h-16 text-center text-xl sm:text-2xl font-mono font-extrabold rounded-2xl border-2 transition-all outline-none ${
              error
                ? 'border-red-500/50 bg-red-500/10 text-red-300 focus:border-red-400'
                : isFilled
                ? 'border-blue-500 bg-slate-900 text-white shadow-md shadow-blue-500/20'
                : 'border-white/15 bg-slate-950/80 text-slate-300 hover:border-white/25 focus:border-blue-500 focus:bg-slate-900'
            } ${disabled ? 'opacity-50 cursor-not-allowed' : ''}`}
            aria-label={`Digit ${i + 1}`}
          />
        );
      })}
    </div>
  );
}

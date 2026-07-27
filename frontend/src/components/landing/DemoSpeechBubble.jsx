import React from 'react';
import { motion } from 'framer-motion';

export default function DemoSpeechBubble({ text, subtitle, variant = 'question', className = '' }) {
  const isQuestion = variant === 'question';

  return (
    <motion.div
      initial={{ opacity: 0, y: 8, scale: 0.95 }}
      animate={{ opacity: 1, y: 0, scale: 1 }}
      exit={{ opacity: 0, y: -6, scale: 0.95 }}
      transition={{ duration: 0.25, ease: 'easeOut' }}
      className={`relative p-3 sm:p-3.5 rounded-2xl backdrop-blur-md shadow-xl border select-none ${
        isQuestion 
          ? 'bg-slate-900/95 border-blue-500/40 text-white shadow-blue-950/40' 
          : 'bg-slate-900/95 border-cyan-500/40 text-white shadow-cyan-950/40'
      } ${className}`}
    >
      {/* Little tail on speech bubble */}
      <div 
        className={`absolute w-3 h-3 rotate-45 border-b border-r bg-slate-900/95 ${
          isQuestion 
            ? 'border-blue-500/40 -bottom-1.5 left-6' 
            : 'border-cyan-500/40 -bottom-1.5 right-6'
        }`}
        aria-hidden="true"
      />
      <div className="relative z-10">
        <p className="text-xs sm:text-sm font-semibold tracking-tight leading-snug">
          {text}
        </p>
        {subtitle && (
          <p className="text-[11px] text-slate-400 mt-1 font-normal">
            {subtitle}
          </p>
        )}
      </div>
    </motion.div>
  );
}

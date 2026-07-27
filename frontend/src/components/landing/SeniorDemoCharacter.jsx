import React from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Play } from 'lucide-react';
import DemoSpeechBubble from './DemoSpeechBubble';

export default function SeniorDemoCharacter({ 
  step, 
  onStartDemo, 
  targetOffset = { x: 0, y: 0 }, 
  isMobile = false,
  reducedMotion = false 
}) {
  const isIdle = step === 'idle';
  const isWalking = step === 'walking';
  const isTurning = step === 'turning' || step === 'asking';
  const isAsking = step === 'asking' || step === 'listening';
  const isAcknowledging = step === 'acknowledging';

  // Compute horizontal-only position based on step (Grounded Baseline Y = 0)
  const getXPosition = () => {
    if (reducedMotion || isMobile) return 0;
    if (isIdle) return 0;
    return targetOffset.x;
  };

  return (
    <div className="relative inline-block select-none z-20">
      
      {/* CTA Callout Bubble beside character at Idle */}
      {isIdle && (
        <motion.div
          initial={{ opacity: 0, y: 6, scale: 0.95 }}
          animate={{ opacity: 1, y: 0, scale: 1 }}
          exit={{ opacity: 0, scale: 0.9 }}
          transition={{ duration: 0.25 }}
          className="absolute -top-12 left-0 z-30 whitespace-nowrap"
        >
          <button
            onClick={onStartDemo}
            type="button"
            aria-label="Play ORMA medication reminder demonstration"
            className="group flex items-center gap-2 px-3.5 py-1.5 rounded-full bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-500 hover:to-indigo-500 text-white text-xs font-bold shadow-[0_4px_16px_rgba(37,99,235,0.4)] border border-blue-400/30 transition-all hover:scale-105 active:scale-95 cursor-pointer focus:outline-none focus:ring-2 focus:ring-blue-400"
          >
            <span className="tracking-wide">See ORMA in action</span>
            <span className="flex items-center justify-center w-4 h-4 rounded-full bg-white/20 group-hover:bg-white/30 transition-colors">
              <Play className="w-2.5 h-2.5 fill-white text-white translate-x-0.5" aria-hidden="true" />
            </span>
          </button>
        </motion.div>
      )}

      {/* Main Character Moving Container: Speech bubbles are encapsulated inside so they translate WITH the character */}
      <motion.div
        animate={{
          x: getXPosition(),
          y: 0, // Always grounded on baseline
        }}
        transition={{
          duration: isWalking ? 2.2 : 0.4,
          ease: [0.25, 1, 0.5, 1]
        }}
        className="relative cursor-pointer group"
        onClick={isIdle ? onStartDemo : undefined}
      >
        {/* CHARACTER-OWNED SPEECH BUBBLES: Always move with the character */}
        <AnimatePresence>
          {isAsking && (
            <DemoSpeechBubble 
              key="asking-bubble"
              text="ORMA, when is my next medicine?"
              variant="question"
              className="absolute -top-16 left-1/2 -translate-x-1/2 whitespace-nowrap z-30 shadow-2xl"
            />
          )}
          {isAcknowledging && (
            <DemoSpeechBubble 
              key="acknowledging-bubble"
              text="Thank you, ORMA!"
              variant="question"
              className="absolute -top-14 left-1/2 -translate-x-1/2 whitespace-nowrap z-30 shadow-2xl"
            />
          )}
        </AnimatePresence>

        {/* 2.5D Senior Grandfather Vector Articulation */}
        <div className="relative w-28 h-40 sm:w-32 sm:h-44 md:w-36 md:h-48 flex items-center justify-center">
          
          {/* Dynamic Ground Shadow */}
          <motion.div 
            animate={
              isWalking && !reducedMotion 
                ? { scaleX: [1, 0.8, 1, 0.8, 1], opacity: [0.6, 0.35, 0.6, 0.35, 0.6] }
                : { scaleX: 1, opacity: 0.5 }
            }
            transition={{ duration: 0.8, repeat: isWalking ? Infinity : 0 }}
            className="absolute bottom-1 left-1/2 -translate-x-1/2 w-18 h-3.5 bg-black/60 blur-[3px] rounded-full pointer-events-none" 
            aria-hidden="true" 
          />

          {/* SVG Character Articulation Layer */}
          <motion.svg
            viewBox="0 0 100 140"
            className="w-full h-full overflow-visible drop-shadow-[0_8px_14px_rgba(0,0,0,0.65)]"
            animate={
              isIdle && !reducedMotion
                ? { y: [0, -2, 0] }
                : isWalking && !reducedMotion
                ? { y: [0, -4, 0, -4, 0], rotate: [0, 1, -1, 1, 0] }
                : isAcknowledging
                ? { y: [0, -3, 0] }
                : { y: 0 }
            }
            transition={
              isIdle
                ? { duration: 3.2, repeat: Infinity, ease: 'easeInOut' }
                : isWalking
                ? { duration: 0.8, repeat: Infinity, ease: 'easeInOut' }
                : isAcknowledging
                ? { duration: 0.6 }
                : {}
            }
          >
            <defs>
              <linearGradient id="shirtGrad" x1="0%" y1="0%" x2="100%" y2="100%">
                <stop offset="0%" stopColor="#e8dfd1" />
                <stop offset="100%" stopColor="#c5b7a1" />
              </linearGradient>
              <linearGradient id="pantGrad" x1="0%" y1="0%" x2="100%" y2="100%">
                <stop offset="0%" stopColor="#334155" />
                <stop offset="100%" stopColor="#1e293b" />
              </linearGradient>
              <linearGradient id="skinGrad" x1="0%" y1="0%" x2="100%" y2="100%">
                <stop offset="0%" stopColor="#f5c7a9" />
                <stop offset="100%" stopColor="#e0a580" />
              </linearGradient>
              <linearGradient id="caneGrad" x1="0%" y1="0%" x2="0%" y2="100%">
                <stop offset="0%" stopColor="#a16207" />
                <stop offset="100%" stopColor="#713f12" />
              </linearGradient>
            </defs>

            {/* BACK LEG */}
            <motion.g
              animate={
                isWalking && !reducedMotion
                  ? { rotate: [-18, 18, -18], y: [0, -2, 0] }
                  : { rotate: 0 }
              }
              transition={{ duration: 0.8, repeat: isWalking ? Infinity : 0, ease: 'easeInOut' }}
              style={{ transformOrigin: '42px 85px' }}
            >
              <rect x="38" y="85" width="10" height="32" rx="4" fill="url(#pantGrad)" />
              <path d="M 36 115 L 48 115 C 51 115 52 119 50 121 L 34 121 Z" fill="#0f172a" />
            </motion.g>

            {/* FRONT LEG */}
            <motion.g
              animate={
                isWalking && !reducedMotion
                  ? { rotate: [18, -18, 18], y: [0, -2, 0] }
                  : { rotate: 0 }
              }
              transition={{ duration: 0.8, repeat: isWalking ? Infinity : 0, ease: 'easeInOut' }}
              style={{ transformOrigin: '56px 85px' }}
            >
              <rect x="52" y="85" width="11" height="33" rx="4" fill="url(#pantGrad)" />
              <path d="M 50 116 L 64 116 C 67 116 68 120 66 122 L 48 122 Z" fill="#1e293b" />
            </motion.g>

            {/* TORSO & SHIRT */}
            <g id="torso">
              <path d="M 32 45 Q 50 42 68 45 L 65 88 Q 50 90 35 88 Z" fill="url(#shirtGrad)" />
              <path d="M 32 45 L 46 87 L 35 88 Z" fill="#b09f87" />
              <path d="M 68 45 L 54 87 L 65 88 Z" fill="#b09f87" />
              <circle cx="50" cy="56" r="1.5" fill="#786c5c" />
              <circle cx="50" cy="67" r="1.5" fill="#786c5c" />
              <circle cx="50" cy="78" r="1.5" fill="#786c5c" />
              <path d="M 40 44 L 50 52 L 44 44 Z" fill="#ffffff" />
              <path d="M 60 44 L 50 52 L 56 44 Z" fill="#ffffff" />
            </g>

            {/* LEFT ARM (Background Arm) */}
            <motion.g
              animate={
                isWalking && !reducedMotion
                  ? { rotate: [15, -15, 15] }
                  : { rotate: 0 }
              }
              transition={{ duration: 0.8, repeat: isWalking ? Infinity : 0, ease: 'easeInOut' }}
              style={{ transformOrigin: '34px 48px' }}
            >
              <rect x="28" y="48" width="8" height="26" rx="3" fill="#b09f87" />
              <circle cx="32" cy="76" r="4" fill="url(#skinGrad)" />
            </motion.g>

            {/* RIGHT ARM & WALKING STICK */}
            <motion.g
              animate={
                isWalking && !reducedMotion
                  ? { rotate: [-15, 15, -15], x: [0, 2, 0] }
                  : { rotate: 0 }
              }
              transition={{ duration: 0.8, repeat: isWalking ? Infinity : 0, ease: 'easeInOut' }}
              style={{ transformOrigin: '64px 48px' }}
            >
              <rect x="62" y="48" width="9" height="28" rx="3.5" fill="#c5b7a1" />
              <circle cx="66.5" cy="78" r="4.5" fill="url(#skinGrad)" />
              <path d="M 66 70 C 66 64 74 64 74 70 L 74 122" fill="none" stroke="url(#caneGrad)" strokeWidth="3.5" strokeLinecap="round" />
              <circle cx="70" cy="65" r="2.5" fill="#eab308" />
              <rect x="72.5" y="120" width="3" height="3" rx="1" fill="#0f172a" />
            </motion.g>

            {/* HEAD & FACE */}
            <motion.g
              animate={
                isAcknowledging
                  ? { rotate: [0, 10, -5, 0] }
                  : isTurning
                  ? { rotate: 4 }
                  : { rotate: 0 }
              }
              transition={{ duration: 0.5 }}
              style={{ transformOrigin: '50px 40px' }}
            >
              <rect x="45" y="38" width="10" height="8" rx="2" fill="url(#skinGrad)" />
              <ellipse cx="50" cy="28" rx="15" ry="17" fill="url(#skinGrad)" />
              <path d="M 35 25 C 33 12 67 12 65 25 C 67 18 33 18 35 25 Z" fill="#f8fafc" />
              <path d="M 34 22 C 32 28 34 32 36 34 L 37 26 Z" fill="#e2e8f0" />
              <path d="M 66 22 C 68 28 66 32 64 34 L 63 26 Z" fill="#e2e8f0" />
              <circle cx="34" cy="29" r="3.5" fill="url(#skinGrad)" />
              <circle cx="66" cy="29" r="3.5" fill="url(#skinGrad)" />
              <rect x="39" y="24" width="9" height="7" rx="2" fill="none" stroke="#3b82f6" strokeWidth="1.5" />
              <rect x="52" y="24" width="9" height="7" rx="2" fill="none" stroke="#3b82f6" strokeWidth="1.5" />
              <line x1="48" y1="27" x2="52" y2="27" stroke="#3b82f6" strokeWidth="1.5" />
              <circle cx="43.5" cy="27.5" r="1.5" fill="#1e293b" />
              <circle cx="56.5" cy="27.5" r="1.5" fill="#1e293b" />
              <path d="M 40 21 Q 44 19 47 21" fill="none" stroke="#ffffff" strokeWidth="1.5" strokeLinecap="round" />
              <path d="M 53 21 Q 56 19 60 21" fill="none" stroke="#ffffff" strokeWidth="1.5" strokeLinecap="round" />
              <path d="M 43 33 Q 50 31 57 33 Q 50 37 43 33 Z" fill="#f1f5f9" />
              <path d="M 44 36 Q 50 40 56 36" fill="none" stroke="#9a3412" strokeWidth="1.5" strokeLinecap="round" />
            </motion.g>

          </motion.svg>
        </div>
      </motion.div>

    </div>
  );
}

import React from 'react';
import { motion, useReducedMotion } from 'framer-motion';

/**
 * BrandLogo — ORMA AI logo component.
 *
 * Props:
 *   animated (bool) — When true, plays a one-time premium entrance animation
 *                     on mount. Defaults to false so every other usage
 *                     (Auth, Sidebar, Dashboard) is completely unaffected.
 *
 * Reduced-motion: when prefers-reduced-motion is set, only an opacity fade
 * is used; all scale, translate, and filter motion is disabled.
 */
export default function BrandLogo({
  className = 'h-10',
  textClassName = 'text-xl',
  showText = true,
  tagline = null,
  layout = 'horizontal',
  textColor = 'text-slate-800',
  accentColor = 'text-blue-600',
  textOverride = null,
  animated = false,
}) {
  // useReducedMotion must be called unconditionally (Rules of Hooks).
  const prefersReducedMotion = useReducedMotion();

  // ── Non-animated path (all existing usages) ──────────────────────────────
  if (!animated) {
    if (layout === 'vertical') {
      return (
        <div className="flex flex-col items-center justify-center gap-3">
          <img
            src="/logo-transparent.png"
            alt="ORMA AI Logo"
            className={`${className} w-auto object-contain`}
            style={{ border: 'none', outline: 'none', boxShadow: 'none', background: 'transparent' }}
          />
          {showText && (
            <div className="flex flex-col items-center">
              <span
                className={`font-bold tracking-tight ${textColor} ${textClassName}`}
                style={{ border: 'none', outline: 'none', boxShadow: 'none', background: 'transparent' }}
              >
                {textOverride || <>Orma<span className={accentColor}>AI</span></>}
              </span>
              {tagline && (
                <span className="text-[10px] font-medium tracking-wider text-slate-400 uppercase -mt-0.5">
                  {tagline}
                </span>
              )}
            </div>
          )}
        </div>
      );
    }

    return (
      <div
        className="flex items-center gap-3.5"
        style={{ border: 'none', outline: 'none', boxShadow: 'none', background: 'transparent' }}
      >
        <img
          src="/logo-transparent.png"
          alt="ORMA AI Logo"
          className={`${className} w-auto object-contain`}
          style={{ border: 'none', outline: 'none', boxShadow: 'none', background: 'transparent' }}
        />
        {showText && (
          <div className="flex flex-col">
            <span
              className={`font-bold tracking-tight ${textColor} ${textClassName}`}
              style={{ border: 'none', outline: 'none', boxShadow: 'none', background: 'transparent' }}
            >
              {textOverride || <>Orma<span className={accentColor}>AI</span></>}
            </span>
            {tagline && (
              <span className="text-[10px] font-medium tracking-wider text-slate-400 uppercase -mt-0.5">
                {tagline}
              </span>
            )}
          </div>
        )}
      </div>
    );
  }

  // ── Animated path (landing page only — unified brand logo coming alive) ───
  //
  // Animation timeline (0 – 1100ms):
  //  0 – 250ms   : Subtle opacity fade from 0.85 → 1 (complete logo recognizable immediately)
  //  250 – 700ms  : Entire logo container scale 0.985 → 1.00, y movement 3px → 0px (gentle upward settle)
  //  700 – 1100ms : One extremely subtle teal/cyan glow increase and return
  //  1100ms+      : Completely static
  //

  const logoContainerVariants = prefersReducedMotion
    ? {
        hidden: { opacity: 0.85 },
        visible: {
          opacity: 1,
          transition: { duration: 0.25, ease: 'easeOut' },
        },
      }
    : {
        hidden: {
          opacity: 0.85,
          scale: 0.985,
          y: 3,
          filter: 'drop-shadow(0 0 0px rgba(14,183,161,0))',
        },
        visible: {
          opacity: [0.85, 1.0, 1.0, 1.0],
          scale: [0.985, 0.985, 1.0, 1.0],
          y: [3, 3, 0, 0],
          filter: [
            'drop-shadow(0 0 0px rgba(14,183,161,0))',
            'drop-shadow(0 0 0px rgba(14,183,161,0))',
            'drop-shadow(0 0 10px rgba(14,183,161,0.28))',
            'drop-shadow(0 0 0px rgba(14,183,161,0))',
          ],
          transition: {
            duration: 1.10,
            times: [0, 0.227, 0.636, 1.0],
            ease: 'easeOut',
          },
        },
      };

  // ── Animated vertical layout ──────────────────────────────────────────────
  if (layout === 'vertical') {
    return (
      <motion.div
        className="flex flex-col items-center justify-center gap-3"
        initial="hidden"
        animate="visible"
        variants={logoContainerVariants}
      >
        <img
          src="/logo-transparent.png"
          alt="ORMA AI Logo"
          className={`${className} w-auto object-contain`}
          style={{ border: 'none', outline: 'none', boxShadow: 'none', background: 'transparent' }}
        />
        {showText && (
          <div className="flex flex-col items-center">
            <span
              className={`font-bold tracking-tight ${textColor} ${textClassName}`}
              style={{ border: 'none', outline: 'none', boxShadow: 'none', background: 'transparent' }}
            >
              {textOverride || <>Orma<span className={accentColor}>AI</span></>}
            </span>
            {tagline && (
              <span className="text-[10px] font-medium tracking-wider text-slate-400 uppercase -mt-0.5">
                {tagline}
              </span>
            )}
          </div>
        )}
      </motion.div>
    );
  }

  // ── Animated horizontal layout (default — used in landing navbar) ─────────
  return (
    <motion.div
      className="flex items-center gap-3.5"
      style={{ border: 'none', outline: 'none', boxShadow: 'none', background: 'transparent' }}
      initial="hidden"
      animate="visible"
      variants={logoContainerVariants}
    >
      <img
        src="/logo-transparent.png"
        alt="ORMA AI Logo"
        className={`${className} w-auto object-contain`}
        style={{ border: 'none', outline: 'none', boxShadow: 'none', background: 'transparent' }}
      />
      {showText && (
        <div className="flex flex-col">
          <span
            className={`font-bold tracking-tight ${textColor} ${textClassName}`}
            style={{ border: 'none', outline: 'none', boxShadow: 'none', background: 'transparent' }}
          >
            {textOverride || <>Orma<span className={accentColor}>AI</span></>}
          </span>
          {tagline && (
            <span className="text-[10px] font-medium tracking-wider text-slate-400 uppercase -mt-0.5">
              {tagline}
            </span>
          )}
        </div>
      )}
    </motion.div>
  );
}

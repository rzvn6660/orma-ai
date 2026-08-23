import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';

export default function AnimatedHeroHeadline({ className = "" }) {
  const [isReducedMotion, setIsReducedMotion] = useState(false);

  useEffect(() => {
    if (typeof window !== 'undefined') {
      const mediaQuery = window.matchMedia('(prefers-reduced-motion: reduce)');
      setIsReducedMotion(mediaQuery.matches);
      const listener = (e) => setIsReducedMotion(e.matches);
      mediaQuery.addEventListener('change', listener);
      return () => mediaQuery.removeEventListener('change', listener);
    }
  }, []);

  const line1Words = ["Voice-First", "AI", "Companion"];
  const line2Words = ["for", "Senior", "Care", "&", "Family", "Safety"];

  if (isReducedMotion) {
    return (
      <h1 className={`text-3xl sm:text-4xl lg:text-[2.65rem] xl:text-5xl font-extrabold text-white tracking-tight leading-[1.14] mb-4 ${className}`}>
        Voice-First AI Companion <br/>
        <span className="text-transparent bg-clip-text bg-gradient-to-r from-blue-400 via-cyan-400 to-purple-400">
          for Senior Care & Family Safety
        </span>
      </h1>
    );
  }

  const container = {
    hidden: { opacity: 0 },
    visible: {
      opacity: 1,
      transition: { 
        staggerChildren: 0.05, 
        delayChildren: 0.05 
      }
    }
  };

  const wordVariant = {
    hidden: { opacity: 0, y: 10 },
    visible: {
      opacity: 1,
      y: 0,
      transition: {
        duration: 0.45,
        ease: [0.25, 0.1, 0.25, 1.0]
      }
    }
  };

  return (
    <motion.h1 
      variants={container}
      initial="hidden"
      animate="visible"
      className={`text-3xl sm:text-4xl lg:text-[2.65rem] xl:text-5xl font-extrabold text-white tracking-tight leading-[1.14] mb-4 ${className}`}
    >
      <span className="inline-block mr-1">
        {line1Words.map((word, i) => (
          <motion.span 
            key={i} 
            variants={wordVariant}
            className="inline-block mr-2"
          >
            {word}
          </motion.span>
        ))}
      </span>
      <br/>
      <span className="text-transparent bg-clip-text bg-gradient-to-r from-blue-400 via-cyan-400 to-purple-400 inline-block">
        {line2Words.map((word, i) => (
          <motion.span 
            key={i} 
            variants={wordVariant}
            className="inline-block mr-2"
          >
            {word}
          </motion.span>
        ))}
      </span>
    </motion.h1>
  );
}

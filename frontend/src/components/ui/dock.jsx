import React, { useRef, useState, useEffect, createContext, useContext } from 'react';
import { motion, useMotionValue, useSpring, useTransform, AnimatePresence } from 'framer-motion';
import { 
  Home, Heart, Calendar, Brain, AlertOctagon, Settings, Users, User, Bell 
} from 'lucide-react';

const DockContext = createContext({
  mouseX: null,
  magnification: 60,
  distance: 130,
  isReducedMotion: false,
});

export function Dock({ 
  children, 
  className = '', 
  magnification = 60, 
  distance = 130 
}) {
  const mouseX = useMotionValue(Infinity);
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

  return (
    <DockContext.Provider value={{ mouseX, magnification, distance, isReducedMotion }}>
      <motion.nav
        aria-label="Liquid Glass Dock Navigation"
        onMouseMove={(e) => {
          if (!isReducedMotion) {
            mouseX.set(e.pageX);
          }
        }}
        onMouseLeave={() => {
          if (!isReducedMotion) {
            mouseX.set(Infinity);
          }
        }}
        className={`relative flex items-center gap-2.5 sm:gap-3.5 px-4 py-2.5 rounded-full bg-slate-900/70 backdrop-blur-2xl border border-white/10 shadow-[0_20px_50px_rgba(0,0,0,0.6),0_0_30px_rgba(59,130,246,0.08)] z-40 transition-all ${className}`}
      >
        {/* Specular top highlight */}
        <div className="absolute inset-0 rounded-full bg-gradient-to-b from-white/15 via-transparent to-transparent pointer-events-none" />
        {children}
      </motion.nav>
    </DockContext.Provider>
  );
}

export function DockItem({ 
  children, 
  onClick, 
  isActive = false, 
  label = '', 
  className = '',
  badge = null
}) {
  const ref = useRef(null);
  const { mouseX, magnification, distance, isReducedMotion } = useContext(DockContext);
  const [isHovered, setIsHovered] = useState(false);
  const [isFocused, setIsFocused] = useState(false);

  const baseSize = 48;
  const distanceCalc = useTransform(mouseX, (val) => {
    if (isReducedMotion || !ref.current) return 0;
    const bounds = ref.current.getBoundingClientRect();
    return val - bounds.x - bounds.width / 2;
  });

  const widthSync = useTransform(
    distanceCalc,
    [-distance, 0, distance],
    [baseSize, magnification, baseSize]
  );

  const width = useSpring(widthSync, {
    mass: 0.1,
    stiffness: 170,
    damping: 15,
  });

  const showLabel = isHovered || isFocused;

  return (
    <motion.button
      ref={ref}
      type="button"
      style={isReducedMotion ? { width: `${baseSize}px`, height: `${baseSize}px` } : { width, height: width }}
      onMouseEnter={() => setIsHovered(true)}
      onMouseLeave={() => setIsHovered(false)}
      onFocus={() => setIsFocused(true)}
      onBlur={() => setIsFocused(false)}
      onClick={onClick}
      aria-label={label}
      aria-current={isActive ? 'page' : undefined}
      className={`relative flex items-center justify-center rounded-2xl transition-all cursor-pointer outline-none focus-visible:ring-2 focus-visible:ring-blue-400 focus-visible:ring-offset-2 focus-visible:ring-offset-slate-950 ${
        isActive
          ? 'bg-blue-600/25 text-blue-400 border border-blue-500/40 shadow-[0_0_20px_rgba(59,130,246,0.3)]'
          : 'text-slate-400 hover:text-white hover:bg-white/5 border border-transparent'
      } ${className}`}
    >
      <AnimatePresence>
        {showLabel && label && (
          <DockLabel>{label}</DockLabel>
        )}
      </AnimatePresence>

      {children}

      {/* Active Indicator Dot */}
      {isActive && (
        <span className="absolute -bottom-1 w-1.5 h-1.5 rounded-full bg-blue-400 shadow-[0_0_8px_#60a5fa]" />
      )}

      {/* Notification badge */}
      {badge !== null && badge > 0 && (
        <span className="absolute -top-1 -right-1 min-w-[18px] h-[18px] px-1 rounded-full bg-red-500 text-[10px] font-extrabold text-white flex items-center justify-center shadow-md">
          {badge}
        </span>
      )}
    </motion.button>
  );
}

export function DockIcon({ children, className = '' }) {
  return (
    <div className={`flex items-center justify-center ${className}`}>
      {children}
    </div>
  );
}

export function DockLabel({ children }) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 6, scale: 0.9 }}
      animate={{ opacity: 1, y: -6, scale: 1 }}
      exit={{ opacity: 0, y: 6, scale: 0.9 }}
      transition={{ duration: 0.15 }}
      className="absolute -top-9 px-2.5 py-1 rounded-xl bg-slate-950/95 border border-white/10 text-white text-xs font-bold tracking-wide shadow-xl backdrop-blur-md whitespace-nowrap pointer-events-none z-50"
    >
      {children}
    </motion.div>
  );
}

export default function OrmaDock({ currentView, onViewChange, user, onLogout }) {
  const isCaregiver = user?.role === 'caregiver';

  const elderlyItems = [
    { id: 'home', icon: Home, label: 'Home' },
    { id: 'calendar', icon: Calendar, label: 'Calendar' },
    { id: 'my-health', icon: Heart, label: 'My Health' },
    { id: 'orma', icon: Brain, label: 'ORMA' },
    { id: 'emergency', icon: AlertOctagon, label: 'Emergency' },
    { id: 'settings', icon: Settings, label: 'Settings' },
  ];

  const caregiverItems = [
    { id: 'caregiver', icon: Home, label: 'Dashboard' },
    { id: 'calendar', icon: Calendar, label: 'Calendar' },
    { id: 'family', icon: Users, label: 'Family' },
    { id: 'my-health', icon: Heart, label: 'Patient Health' },
    { id: 'orma', icon: Brain, label: 'ORMA' },
    { id: 'emergency', icon: AlertOctagon, label: 'Emergency' },
    { id: 'settings', icon: Settings, label: 'Settings' },
  ];

  const visibleItems = isCaregiver ? caregiverItems : elderlyItems;

  return (
    <>
      {/* 1. Desktop Liquid Glass Dock (md and above) */}
      <div className="hidden md:block fixed bottom-6 left-1/2 -translate-x-1/2 z-40 pointer-events-auto">
        <Dock>
          {visibleItems.map((item) => {
            const Icon = item.icon;
            const isActive = currentView === item.id || 
              (item.id === 'home' && currentView === 'dashboard') ||
              (item.id === 'my-health' && ['medicines', 'planner', 'records', 'vitals'].includes(currentView)) ||
              (item.id === 'orma' && currentView === 'conversations');

            return (
              <DockItem
                key={item.id}
                onClick={() => onViewChange(item.id)}
                isActive={isActive}
                label={item.label}
              >
                <DockIcon>
                  <Icon className={`w-5 h-5 transition-colors ${isActive ? 'text-blue-400' : 'text-slate-300'}`} />
                </DockIcon>
              </DockItem>
            );
          })}
        </Dock>
      </div>

      {/* 2. Mobile Liquid Glass Bottom Navigation (< md) */}
      <nav 
        aria-label="Mobile Navigation Bar"
        className="md:hidden fixed bottom-0 left-0 right-0 z-40 bg-slate-950/90 backdrop-blur-2xl border-t border-white/10 px-3 py-2 flex justify-around items-center shadow-2xl safe-area-pb"
      >
        {visibleItems.map((item) => {
          const Icon = item.icon;
          const isActive = currentView === item.id || 
            (item.id === 'home' && currentView === 'dashboard') ||
            (item.id === 'my-health' && ['medicines', 'planner', 'records', 'vitals'].includes(currentView)) ||
            (item.id === 'orma' && currentView === 'conversations');

          return (
            <button
              key={item.id}
              type="button"
              onClick={() => onViewChange(item.id)}
              aria-label={item.label}
              aria-current={isActive ? 'page' : undefined}
              className={`flex flex-col items-center justify-center p-2 rounded-xl transition-all cursor-pointer min-w-[50px] min-h-[44px] ${
                isActive 
                  ? 'text-blue-400 font-bold' 
                  : 'text-slate-400 hover:text-slate-200 font-medium'
              }`}
            >
              <Icon className={`w-5 h-5 ${isActive ? 'text-blue-400' : 'text-slate-400'}`} />
              <span className="text-[10px] mt-0.5 tracking-tight">{item.label}</span>
            </button>
          );
        })}
      </nav>
    </>
  );
}

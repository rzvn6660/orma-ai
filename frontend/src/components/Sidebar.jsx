import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  Home, Heart, Calendar, Brain, AlertOctagon, Settings, User, LogOut, Users, X, 
  ChevronLeft, ChevronRight 
} from 'lucide-react';
import BrandLogo from './BrandLogo';

export default function Sidebar({ 
  currentView, 
  onViewChange, 
  onLogout, 
  user, 
  isOpen, 
  onClose, 
  className = '',
  isCollapsed: externalIsCollapsed,
  onToggleCollapse: externalToggleCollapse
}) {
  const isCaregiver = user?.role === 'caregiver';

  // Internal collapse state persisted in localStorage
  const [isCollapsed, setIsCollapsed] = useState(() => {
    return localStorage.getItem('orma_sidebar_collapsed') === 'true';
  });

  const [hoveredItemId, setHoveredItemId] = useState(null);
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

  const handleToggle = () => {
    const nextState = !isCollapsed;
    setIsCollapsed(nextState);
    localStorage.setItem('orma_sidebar_collapsed', String(nextState));
    window.dispatchEvent(new Event('sidebarCollapseChange'));
    if (externalToggleCollapse) {
      externalToggleCollapse(nextState);
    }
  };

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
    <motion.aside 
      aria-label="Caregiver Navigation Sidebar"
      initial={false}
      animate={{
        width: isOpen ? 260 : isCollapsed ? 80 : 260,
      }}
      transition={isReducedMotion ? { duration: 0 } : { duration: 0.25, ease: "easeInOut" }}
      className={`fixed left-0 top-0 h-screen bg-slate-900/80 md:bg-slate-900/70 backdrop-blur-2xl border-r border-white/10 z-50 flex flex-col transition-transform duration-300 transform ${
        isOpen ? 'translate-x-0 !w-[260px]' : '-translate-x-full'
      } md:translate-x-0 shadow-2xl ${className}`}
    >
      {/* Specular top highlight */}
      <div className="absolute inset-0 bg-gradient-to-b from-white/10 via-transparent to-transparent pointer-events-none" />

      <div className="pt-6 pb-5 px-3.5 flex flex-col h-full relative z-10">
        
        {/* ================================================================== */}
        {/* Header: Logo & Collapse Toggle                                     */}
        {/* ================================================================== */}
        <div className="flex items-center justify-between mb-8 px-1">
          <div 
            className="cursor-pointer transition-transform hover:scale-[1.02] flex items-center gap-2 overflow-hidden" 
            onClick={() => {
              onViewChange(isCaregiver ? 'caregiver' : 'home');
              if (isOpen && onClose) onClose();
            }}
            title="ORMA AI"
          >
            <BrandLogo 
              className="h-[38px] shrink-0" 
              textClassName="text-[20px]" 
              textColor="text-white" 
              accentColor="text-blue-400"
              textOverride={!isCollapsed || isOpen ? <>ORMA <span className="text-blue-400">AI</span></> : null}
            />
          </div>

          {/* Mobile close button */}
          <div className="md:hidden">
            <button 
              type="button"
              onClick={onClose} 
              className="text-slate-400 hover:text-white p-2 bg-slate-800/80 rounded-xl border border-slate-700/50 cursor-pointer"
              aria-label="Close navigation"
            >
              <X className="w-5 h-5" />
            </button>
          </div>

          {/* Desktop collapse/expand toggle */}
          <div className="hidden md:block">
            <button
              type="button"
              onClick={handleToggle}
              className="p-1.5 rounded-xl text-slate-400 hover:text-white hover:bg-white/10 border border-white/5 transition-colors cursor-pointer outline-none focus-visible:ring-2 focus-visible:ring-blue-400"
              aria-label={isCollapsed ? "Expand sidebar" : "Collapse sidebar"}
              title={isCollapsed ? "Expand sidebar" : "Collapse sidebar"}
            >
              {isCollapsed ? <ChevronRight className="w-4 h-4" /> : <ChevronLeft className="w-4 h-4" />}
            </button>
          </div>
        </div>

        {/* ================================================================== */}
        {/* Navigation items                                                   */}
        {/* ================================================================== */}
        <nav className="flex-1 flex flex-col gap-2 overflow-y-auto custom-scrollbar min-h-0 py-1">
          {visibleItems.map((item) => {
            const Icon = item.icon;
            const isActive = currentView === item.id || 
              (item.id === 'home' && currentView === 'dashboard') ||
              (item.id === 'my-health' && ['medicines', 'planner', 'records', 'vitals'].includes(currentView)) ||
              (item.id === 'orma' && currentView === 'conversations');

            const isHovered = hoveredItemId === item.id;
            const showTooltip = isCollapsed && !isOpen && isHovered;

            return (
              <div key={item.id} className="relative">
                <button
                  type="button"
                  onClick={() => {
                    onViewChange(item.id);
                    if (isOpen && onClose) onClose();
                  }}
                  onMouseEnter={() => setHoveredItemId(item.id)}
                  onMouseLeave={() => setHoveredItemId(null)}
                  onFocus={() => setHoveredItemId(item.id)}
                  onBlur={() => setHoveredItemId(null)}
                  aria-label={item.label}
                  aria-current={isActive ? 'page' : undefined}
                  className={`w-full flex items-center rounded-2xl font-bold transition-all duration-200 text-sm cursor-pointer outline-none focus-visible:ring-2 focus-visible:ring-blue-400 ${
                    isCollapsed && !isOpen ? 'justify-center h-12 px-0' : 'gap-3.5 px-3.5 py-3'
                  } ${
                    isActive 
                      ? 'bg-blue-600/20 text-blue-400 border border-blue-500/40 shadow-[0_0_20px_rgba(59,130,246,0.25)]' 
                      : 'text-slate-300 hover:text-white hover:bg-white/5 border border-transparent'
                  }`}
                >
                  <Icon className={`w-5 h-5 shrink-0 transition-colors ${isActive ? 'text-blue-400' : 'text-slate-400'}`} />

                  {(!isCollapsed || isOpen) && (
                    <motion.span 
                      initial={{ opacity: 0, x: -6 }}
                      animate={{ opacity: 1, x: 0 }}
                      exit={{ opacity: 0, x: -6 }}
                      transition={{ duration: 0.15 }}
                      className="truncate font-semibold tracking-wide"
                    >
                      {item.label}
                    </motion.span>
                  )}

                  {/* Active dot indicator on right when expanded */}
                  {isActive && (!isCollapsed || isOpen) && (
                    <span className="ml-auto w-1.5 h-1.5 rounded-full bg-blue-400 shadow-[0_0_6px_#60a5fa] shrink-0" />
                  )}
                </button>

                {/* Collapsed Tooltip on Hover / Focus */}
                <AnimatePresence>
                  {showTooltip && (
                    <motion.div
                      initial={{ opacity: 0, x: 10, scale: 0.95 }}
                      animate={{ opacity: 1, x: 14, scale: 1 }}
                      exit={{ opacity: 0, x: 10, scale: 0.95 }}
                      transition={{ duration: 0.12 }}
                      className="fixed left-[72px] px-3 py-1.5 rounded-xl bg-slate-950/95 border border-white/10 text-white text-xs font-bold tracking-wide shadow-2xl backdrop-blur-xl whitespace-nowrap pointer-events-none z-50 flex items-center gap-1.5"
                    >
                      <span>{item.label}</span>
                      {isActive && <span className="w-1.5 h-1.5 rounded-full bg-blue-400" />}
                    </motion.div>
                  )}
                </AnimatePresence>
              </div>
            );
          })}
        </nav>

        {/* ================================================================== */}
        {/* User Card & Sign Out                                               */}
        {/* ================================================================== */}
        <div className="mt-auto pt-4 border-t border-white/10 flex flex-col gap-2">
          
          {/* User Profile Info */}
          <div 
            className={`flex items-center rounded-2xl bg-slate-800/40 border border-white/5 transition-all relative ${
              isCollapsed && !isOpen ? 'justify-center p-2' : 'p-3 gap-3'
            }`}
            title={`${user?.name || 'User'} (${user?.role || 'caregiver'})`}
          >
            <div className="w-9 h-9 rounded-xl bg-blue-600/20 border border-blue-500/30 flex items-center justify-center text-blue-400 font-bold text-xs shrink-0 shadow-inner">
              {user?.name?.charAt(0) || <User className="w-4 h-4" />}
            </div>

            {(!isCollapsed || isOpen) && (
              <motion.div 
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                className="flex-1 overflow-hidden"
              >
                <p className="text-xs font-bold text-white tracking-wide truncate">{user?.name || 'User'}</p>
                <p className="text-[10px] font-bold text-slate-400 uppercase tracking-widest">{user?.role || 'caregiver'}</p>
              </motion.div>
            )}
          </div>

          {/* Sign Out Button */}
          <button 
            type="button"
            onClick={onLogout} 
            title="Sign Out"
            aria-label="Sign Out"
            className={`flex items-center text-red-400 hover:text-red-300 hover:bg-red-500/10 rounded-2xl transition-all cursor-pointer font-bold text-xs outline-none focus-visible:ring-2 focus-visible:ring-red-500/50 ${
              isCollapsed && !isOpen ? 'justify-center h-10 px-0' : 'gap-3 px-3.5 py-2.5'
            }`}
          >
            <LogOut className="w-4 h-4 shrink-0" />
            {(!isCollapsed || isOpen) && (
              <motion.span 
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                className="truncate"
              >
                Sign Out
              </motion.span>
            )}
          </button>

        </div>
      </div>
    </motion.aside>
  );
}

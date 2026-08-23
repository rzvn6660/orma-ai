import React, { useState, useRef, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  User, 
  Settings, 
  HelpCircle, 
  LogOut, 
  ChevronDown, 
  ShieldCheck, 
  Sparkles 
} from 'lucide-react';

export default function ProfileDropdown({
  user,
  onLogout,
  onViewChange,
  className = ''
}) {
  const [isOpen, setIsOpen] = useState(false);
  const containerRef = useRef(null);

  const isCaregiver = user?.role === 'caregiver';
  const displayName = user?.name || (isCaregiver ? 'Caregiver' : 'Elderly User');
  const displayEmail = user?.email || 'user@orma.ai';
  const roleLabel = isCaregiver ? 'Caregiver' : 'Elderly Member';

  // Close on outside click
  useEffect(() => {
    const handleClickOutside = (e) => {
      if (containerRef.current && !containerRef.current.contains(e.target)) {
        setIsOpen(false);
      }
    };
    if (isOpen) {
      document.addEventListener('mousedown', handleClickOutside);
    }
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, [isOpen]);

  return (
    <div className={`relative ${className}`} ref={containerRef}>
      {/* Trigger Button */}
      <button
        type="button"
        onClick={() => setIsOpen(!isOpen)}
        className={`flex items-center gap-2.5 p-1.5 sm:pr-3 rounded-2xl border transition-all cursor-pointer ${
          isOpen
            ? 'bg-slate-900 border-blue-500 shadow-[0_0_15px_rgba(59,130,246,0.2)]'
            : 'bg-slate-950/60 border-white/10 hover:border-white/20 hover:bg-slate-900/60'
        }`}
        aria-expanded={isOpen}
        aria-haspopup="true"
      >
        <div className="w-8 h-8 rounded-xl bg-gradient-to-tr from-blue-600 to-indigo-600 flex items-center justify-center text-white font-bold text-xs shadow-md">
          {displayName.charAt(0).toUpperCase()}
        </div>

        <div className="hidden sm:flex flex-col text-left">
          <span className="text-xs font-bold text-white tracking-tight line-clamp-1">
            {displayName}
          </span>
          <span className="text-[10px] text-slate-400 font-medium">
            {roleLabel}
          </span>
        </div>

        <ChevronDown className={`w-3.5 h-3.5 text-slate-400 transition-transform ${isOpen ? 'rotate-180' : ''}`} />
      </button>

      {/* Dropdown Menu */}
      <AnimatePresence>
        {isOpen && (
          <motion.div
            initial={{ opacity: 0, y: 6, scale: 0.98 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: 4, scale: 0.98 }}
            transition={{ duration: 0.15 }}
            className="absolute right-0 top-full mt-2 w-64 p-2 rounded-3xl bg-slate-900/95 backdrop-blur-2xl border border-white/15 shadow-2xl z-50 overflow-hidden"
          >
            {/* Header: User Info */}
            <div className="p-3 bg-slate-950/60 rounded-2xl border border-white/5 mb-1.5">
              <div className="flex items-center gap-2.5 mb-1">
                <div className="w-8 h-8 rounded-xl bg-blue-500/15 border border-blue-500/25 flex items-center justify-center text-blue-400 font-bold text-xs">
                  {displayName.charAt(0).toUpperCase()}
                </div>
                <div className="flex-1 min-w-0">
                  <p className="text-xs font-bold text-white truncate">{displayName}</p>
                  <p className="text-[10px] text-slate-400 truncate">{displayEmail}</p>
                </div>
              </div>
              <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[9px] font-extrabold uppercase bg-blue-500/10 text-blue-400 border border-blue-500/20">
                <ShieldCheck className="w-2.5 h-2.5" /> {roleLabel}
              </span>
            </div>

            {/* Menu Links */}
            <div className="space-y-0.5">
              <button
                type="button"
                onClick={() => {
                  setIsOpen(false);
                  if (onViewChange) onViewChange('settings');
                }}
                className="w-full px-3 py-2 rounded-xl text-xs font-medium text-slate-300 hover:text-white hover:bg-white/10 transition-colors flex items-center gap-2.5 cursor-pointer text-left"
              >
                <User className="w-4 h-4 text-slate-400" />
                <span>Account Profile</span>
              </button>

              <button
                type="button"
                onClick={() => {
                  setIsOpen(false);
                  if (onViewChange) onViewChange('settings');
                }}
                className="w-full px-3 py-2 rounded-xl text-xs font-medium text-slate-300 hover:text-white hover:bg-white/10 transition-colors flex items-center gap-2.5 cursor-pointer text-left"
              >
                <Settings className="w-4 h-4 text-slate-400" />
                <span>Settings & Preferences</span>
              </button>

              <button
                type="button"
                onClick={() => {
                  setIsOpen(false);
                  if (onViewChange) onViewChange('orma');
                }}
                className="w-full px-3 py-2 rounded-xl text-xs font-medium text-slate-300 hover:text-white hover:bg-white/10 transition-colors flex items-center gap-2.5 cursor-pointer text-left"
              >
                <HelpCircle className="w-4 h-4 text-slate-400" />
                <span>ORMA Help & Voice</span>
              </button>
            </div>

            {/* Separator */}
            <div className="my-1.5 h-[1px] bg-white/10" />

            {/* Sign Out */}
            <button
              type="button"
              onClick={() => {
                setIsOpen(false);
                if (onLogout) onLogout();
              }}
              className="w-full px-3 py-2 rounded-xl text-xs font-bold text-red-400 hover:text-red-300 hover:bg-red-500/10 transition-colors flex items-center gap-2.5 cursor-pointer text-left"
            >
              <LogOut className="w-4 h-4" />
              <span>Sign Out</span>
            </button>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}

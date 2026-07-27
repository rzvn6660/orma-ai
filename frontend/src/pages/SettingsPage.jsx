import { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  Settings, User, ShieldCheck, Bell, Eye, Users, Globe, 
  Clock, Check, Volume2, Moon, Sparkles, AlertCircle
} from 'lucide-react';
import CaregiverLinkManager from '../components/CaregiverLinkManager';
import ErrorBoundary from '../components/ErrorBoundary';

export default function SettingsPage({ user }) {
  const [activeSection, setActiveSection] = useState('profile');
  const [languageMode, setLanguageMode] = useState(localStorage.getItem('orma_language_pref') || 'auto');
  const [textSize, setTextSize] = useState(localStorage.getItem('orma_text_size') || 'normal');
  const [soundEnabled, setSoundEnabled] = useState(localStorage.getItem('orma_sound') !== 'disabled');
  const [savedSuccess, setSavedSuccess] = useState(false);

  const handleLanguageChange = (lang) => {
    setLanguageMode(lang);
    localStorage.setItem('orma_language_pref', lang);
    window.dispatchEvent(new Event('languageChange'));
    showSavedToast();
  };

  const handleTextSizeChange = (size) => {
    setTextSize(size);
    localStorage.setItem('orma_text_size', size);
    showSavedToast();
  };

  const handleToggleSound = () => {
    const nextState = !soundEnabled;
    setSoundEnabled(nextState);
    localStorage.setItem('orma_sound', nextState ? 'enabled' : 'disabled');
    showSavedToast();
  };

  const showSavedToast = () => {
    setSavedSuccess(true);
    setTimeout(() => setSavedSuccess(false), 2500);
  };

  const sections = [
    { id: 'profile', label: 'Profile', icon: User },
    { id: 'security', label: 'Security', icon: ShieldCheck },
    { id: 'notifications', label: 'Notifications', icon: Bell },
    { id: 'accessibility', label: 'Accessibility', icon: Eye },
    { id: 'caregiver', label: 'Caregiver Access', icon: Users },
    { id: 'language', label: 'Language', icon: Globe },
    { id: 'preferences', label: 'Preferences', icon: Clock },
  ];

  return (
    <ErrorBoundary>
      <div className="w-full max-w-7xl mx-auto flex flex-col gap-8 pb-12">
        {/* Header */}
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 bg-slate-900/60 p-6 md:p-8 rounded-3xl border border-slate-800 backdrop-blur-xl">
          <div className="flex items-center gap-4">
            <div className="w-12 h-12 rounded-2xl bg-slate-800 flex items-center justify-center border border-slate-700/50">
              <Settings className="w-6 h-6 text-blue-400" />
            </div>
            <div>
              <h1 className="text-3xl font-extrabold text-white tracking-tight">Settings & Preferences</h1>
              <p className="text-slate-400 text-sm md:text-base mt-0.5">
                Manage your account, accessibility, notification alerts, and caregiver links.
              </p>
            </div>
          </div>

          {savedSuccess && (
            <div className="px-4 py-2 bg-emerald-500/20 text-emerald-400 border border-emerald-500/30 rounded-xl text-sm font-bold flex items-center gap-2 animate-fade-in">
              <Check className="w-4 h-4" /> Preferences Updated
            </div>
          )}
        </div>

        {/* Layout Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
          {/* Navigation Sidebar */}
          <div className="col-span-1 lg:col-span-4 flex flex-col gap-2">
            <div className="bg-slate-900/60 border border-slate-800 rounded-3xl p-3 flex flex-col gap-1.5">
              {sections.map((sec) => {
                const Icon = sec.icon;
                const isActive = activeSection === sec.id;
                return (
                  <button
                    key={sec.id}
                    onClick={() => setActiveSection(sec.id)}
                    className={`flex items-center gap-3.5 px-4 py-3.5 rounded-2xl font-bold text-sm transition-all duration-200 ${
                      isActive
                        ? 'bg-blue-600 text-white shadow-lg shadow-blue-500/20 border border-blue-400/30'
                        : 'text-slate-400 hover:text-white hover:bg-slate-800/60'
                    }`}
                  >
                    <Icon className={`w-5 h-5 ${isActive ? 'text-white' : 'text-slate-400'}`} />
                    <span>{sec.label}</span>
                  </button>
                );
              })}
            </div>
          </div>

          {/* Section Panel */}
          <div className="col-span-1 lg:col-span-8">
            <AnimatePresence mode="wait">
              <motion.div
                key={activeSection}
                initial={{ opacity: 0, x: 10 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, x: -10 }}
                transition={{ duration: 0.15 }}
                className="bg-slate-900/60 border border-slate-800 rounded-3xl p-6 sm:p-8"
              >
                {activeSection === 'profile' && (
                  <div className="space-y-6">
                    <h2 className="text-xl font-bold text-white flex items-center gap-2">
                      <User className="text-blue-400 w-5 h-5" /> User Profile
                    </h2>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-6 bg-slate-800/40 p-6 rounded-2xl border border-slate-700/40">
                      <div>
                        <label className="text-xs uppercase font-bold text-slate-400 tracking-wider">Full Name</label>
                        <p className="text-lg font-bold text-white mt-1">{user?.name || 'User'}</p>
                      </div>
                      <div>
                        <label className="text-xs uppercase font-bold text-slate-400 tracking-wider">Role</label>
                        <p className="text-lg font-bold text-blue-400 uppercase tracking-wider mt-1">{user?.role || 'elderly'}</p>
                      </div>
                      <div>
                        <label className="text-xs uppercase font-bold text-slate-400 tracking-wider">Email</label>
                        <p className="text-lg font-medium text-slate-300 mt-1">{user?.email || 'user@orma.ai'}</p>
                      </div>
                      <div>
                        <label className="text-xs uppercase font-bold text-slate-400 tracking-wider">Timezone</label>
                        <p className="text-lg font-medium text-slate-300 mt-1">{user?.timezone || Intl.DateTimeFormat().resolvedOptions().timeZone}</p>
                      </div>
                    </div>
                  </div>
                )}

                {activeSection === 'security' && (
                  <div className="space-y-6">
                    <h2 className="text-xl font-bold text-white flex items-center gap-2">
                      <ShieldCheck className="text-emerald-400 w-5 h-5" /> Security & Privacy
                    </h2>
                    <div className="bg-slate-800/40 p-6 rounded-2xl border border-slate-700/40 space-y-4">
                      <p className="text-slate-300 text-sm">Your data is stored securely and encrypted in compliance with healthcare privacy standards.</p>
                      <button className="orma-btn-secondary text-sm">Change Password</button>
                    </div>
                  </div>
                )}

                {activeSection === 'notifications' && (
                  <div className="space-y-6">
                    <h2 className="text-xl font-bold text-white flex items-center gap-2">
                      <Bell className="text-amber-400 w-5 h-5" /> Notification & Audio Alerts
                    </h2>
                    <div className="bg-slate-800/40 p-6 rounded-2xl border border-slate-700/40 space-y-6">
                      <div className="flex items-center justify-between">
                        <div>
                          <p className="text-white font-bold">Medication Sound Reminders</p>
                          <p className="text-xs text-slate-400">Play spoken reminders when doses are due</p>
                        </div>
                        <button
                          onClick={handleToggleSound}
                          className={`w-14 h-8 rounded-full transition-colors flex items-center p-1 ${
                            soundEnabled ? 'bg-blue-600 justify-end' : 'bg-slate-700 justify-start'
                          }`}
                        >
                          <div className="w-6 h-6 rounded-full bg-white shadow-md"></div>
                        </button>
                      </div>
                    </div>
                  </div>
                )}

                {activeSection === 'accessibility' && (
                  <div className="space-y-6">
                    <h2 className="text-xl font-bold text-white flex items-center gap-2">
                      <Eye className="text-purple-400 w-5 h-5" /> Accessibility Options
                    </h2>
                    <div className="bg-slate-800/40 p-6 rounded-2xl border border-slate-700/40 space-y-6">
                      <div>
                        <label className="text-sm font-bold text-white mb-2 block">Text Display Size</label>
                        <div className="grid grid-cols-3 gap-3">
                          {['normal', 'large', 'extra-large'].map((size) => (
                            <button
                              key={size}
                              onClick={() => handleTextSizeChange(size)}
                              className={`py-3 px-4 rounded-xl font-bold text-sm capitalize transition-all border ${
                                textSize === size
                                  ? 'bg-blue-600 text-white border-blue-400'
                                  : 'bg-slate-900 text-slate-400 border-slate-700 hover:text-white'
                              }`}
                            >
                              {size.replace('-', ' ')}
                            </button>
                          ))}
                        </div>
                      </div>
                    </div>
                  </div>
                )}

                {activeSection === 'caregiver' && (
                  <CaregiverLinkManager user={user} />
                )}

                {activeSection === 'language' && (
                  <div className="space-y-6">
                    <h2 className="text-xl font-bold text-white flex items-center gap-2">
                      <Globe className="text-cyan-400 w-5 h-5" /> Language Preference
                    </h2>
                    <div className="bg-slate-800/40 p-6 rounded-2xl border border-slate-700/40 space-y-4">
                      <p className="text-slate-300 text-sm">Select spoken & text language for Orma AI:</p>
                      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
                        {[
                          { id: 'auto', name: 'Auto Detect' },
                          { id: 'en', name: 'English' },
                          { id: 'ml', name: 'Malayalam (മലയാളം)' },
                        ].map((lang) => (
                          <button
                            key={lang.id}
                            onClick={() => handleLanguageChange(lang.id)}
                            className={`p-4 rounded-2xl font-bold text-sm border text-left transition-all ${
                              languageMode === lang.id
                                ? 'bg-blue-600 text-white border-blue-400 shadow-md'
                                : 'bg-slate-900 text-slate-300 border-slate-700 hover:border-slate-500'
                            }`}
                          >
                            {lang.name}
                          </button>
                        ))}
                      </div>
                    </div>
                  </div>
                )}

                {activeSection === 'preferences' && (
                  <div className="space-y-6">
                    <h2 className="text-xl font-bold text-white flex items-center gap-2">
                      <Clock className="text-pink-400 w-5 h-5" /> System & Timezone Preferences
                    </h2>
                    <div className="bg-slate-800/40 p-6 rounded-2xl border border-slate-700/40 space-y-4">
                      <div>
                        <p className="text-white font-bold">Detected Timezone</p>
                        <p className="text-sm text-slate-400 mt-1">{Intl.DateTimeFormat().resolvedOptions().timeZone}</p>
                      </div>
                    </div>
                  </div>
                )}
              </motion.div>
            </AnimatePresence>
          </div>
        </div>
      </div>
    </ErrorBoundary>
  );
}

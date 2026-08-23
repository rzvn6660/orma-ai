import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  Sparkles, 
  User, 
  Users, 
  Globe, 
  Clock, 
  CheckCircle2, 
  ArrowRight, 
  ArrowLeft, 
  X,
  Heart
} from 'lucide-react';
import BrandLogo from '../BrandLogo';
import OrmaRadioGroup from './OrmaRadioGroup';

export default function OrmaOnboardingModal({
  isOpen,
  onClose,
  user,
  onUpdatePreferences
}) {
  const [step, setStep] = useState(1);
  const [selectedRole, setSelectedRole] = useState(user?.role || 'elderly');
  const [selectedLang, setSelectedLang] = useState(localStorage.getItem('orma_language_pref') || 'auto');
  const [timezone] = useState(user?.timezone || Intl.DateTimeFormat().resolvedOptions().timeZone || 'UTC');

  if (!isOpen) return null;

  const handleFinish = () => {
    localStorage.setItem('orma_onboarding_completed', 'true');
    localStorage.setItem('orma_language_pref', selectedLang);
    if (onUpdatePreferences) {
      onUpdatePreferences({ role: selectedRole, language: selectedLang });
    }
    onClose();
  };

  const roleOptions = [
    {
      value: 'elderly',
      label: "I'm using ORMA for myself",
      description: 'Hands-free voice assistant, clear reminders, and daily companionship.',
      icon: User
    },
    {
      value: 'caregiver',
      label: "I'm a family caregiver",
      description: 'Manage medicine schedules, monitor health events, and check adherence.',
      icon: Users
    }
  ];

  const languageOptions = [
    { value: 'auto', label: 'Auto-detect Voice Language', description: 'Automatically detects language as you speak.' },
    { value: 'en', label: 'English', description: 'Standard English voice interaction.' },
    { value: 'hi', label: 'Hindi (हिंदी)', description: 'Hindi voice prompts and responses.' }
  ];

  return (
    <AnimatePresence>
      <div className="fixed inset-0 z-[120] flex items-center justify-center p-4 sm:p-6 bg-slate-950/85 backdrop-blur-xl">
        <motion.div
          initial={{ opacity: 0, scale: 0.95, y: 15 }}
          animate={{ opacity: 1, scale: 1, y: 0 }}
          exit={{ opacity: 0, scale: 0.95, y: 15 }}
          transition={{ duration: 0.25 }}
          className="w-full max-w-lg bg-slate-900/95 border border-white/15 rounded-3xl p-6 sm:p-8 shadow-2xl relative overflow-hidden"
        >
          {/* Ambient Glow */}
          <div className="absolute -top-16 -right-16 w-48 h-48 bg-blue-500/20 rounded-full blur-3xl pointer-events-none" />

          {/* Header */}
          <div className="flex items-center justify-between mb-6 relative z-10">
            <BrandLogo size="default" />
            <div className="flex items-center gap-1.5">
              {[1, 2, 3, 4].map((i) => (
                <div
                  key={i}
                  className={`h-1.5 rounded-full transition-all ${
                    step === i ? 'w-6 bg-blue-500' : step > i ? 'w-3 bg-blue-400/50' : 'w-2 bg-slate-700'
                  }`}
                />
              ))}
            </div>
          </div>

          {/* STEP 1: WELCOME */}
          {step === 1 && (
            <motion.div
              key="step1"
              initial={{ opacity: 0, x: 20 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: -20 }}
              className="text-center py-4"
            >
              <div className="w-16 h-16 rounded-3xl bg-blue-500/10 border border-blue-500/20 text-blue-400 flex items-center justify-center mx-auto mb-5 shadow-lg">
                <Heart className="w-8 h-8 text-blue-400 fill-blue-400/20" />
              </div>
              <h2 className="text-2xl sm:text-3xl font-black text-white tracking-tight mb-2">
                Welcome to ORMA AI
              </h2>
              <p className="text-slate-300 text-sm sm:text-base leading-relaxed max-w-sm mx-auto mb-8">
                Your calm, intelligent companion for medicine schedules, doctor appointments, and family health peace of mind.
              </p>
              <button
                type="button"
                onClick={() => setStep(2)}
                className="w-full py-3.5 rounded-2xl bg-blue-600 hover:bg-blue-500 text-white font-bold text-base transition-all shadow-lg shadow-blue-600/30 flex items-center justify-center gap-2 cursor-pointer"
              >
                <span>Get Started</span>
                <ArrowRight className="w-5 h-5" />
              </button>
            </motion.div>
          )}

          {/* STEP 2: ROLE CONFIRMATION */}
          {step === 2 && (
            <motion.div
              key="step2"
              initial={{ opacity: 0, x: 20 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: -20 }}
              className="py-2"
            >
              <h2 className="text-xl sm:text-2xl font-bold text-white tracking-tight mb-1 text-center">
                How will you use ORMA?
              </h2>
              <p className="text-slate-400 text-xs sm:text-sm text-center mb-6">
                We'll tailor your layout and font sizes accordingly.
              </p>

              <OrmaRadioGroup
                options={roleOptions}
                value={selectedRole}
                onChange={setSelectedRole}
                className="mb-8"
              />

              <div className="flex items-center gap-3">
                <button
                  type="button"
                  onClick={() => setStep(1)}
                  className="px-4 py-3 rounded-2xl bg-slate-800 hover:bg-slate-700 text-slate-300 text-sm font-bold transition-colors cursor-pointer"
                >
                  <ArrowLeft className="w-4 h-4" />
                </button>
                <button
                  type="button"
                  onClick={() => setStep(3)}
                  className="flex-1 py-3 rounded-2xl bg-blue-600 hover:bg-blue-500 text-white text-sm font-bold transition-all shadow-md shadow-blue-600/20 flex items-center justify-center gap-2 cursor-pointer"
                >
                  <span>Continue</span>
                  <ArrowRight className="w-4 h-4" />
                </button>
              </div>
            </motion.div>
          )}

          {/* STEP 3: PREFERENCES */}
          {step === 3 && (
            <motion.div
              key="step3"
              initial={{ opacity: 0, x: 20 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: -20 }}
              className="py-2"
            >
              <h2 className="text-xl sm:text-2xl font-bold text-white tracking-tight mb-1 text-center">
                Language & Timezone
              </h2>
              <p className="text-slate-400 text-xs sm:text-sm text-center mb-5">
                Ensure reminders ring accurately in your local time.
              </p>

              <OrmaRadioGroup
                label="Voice Interaction Language"
                options={languageOptions}
                value={selectedLang}
                onChange={setSelectedLang}
                className="mb-4"
              />

              <div className="p-3 bg-slate-950/60 rounded-2xl border border-white/10 flex items-center gap-3 mb-8">
                <Clock className="w-4 h-4 text-blue-400 shrink-0" />
                <div className="text-xs">
                  <span className="text-slate-400">Detected Timezone: </span>
                  <strong className="text-white">{timezone}</strong>
                </div>
              </div>

              <div className="flex items-center gap-3">
                <button
                  type="button"
                  onClick={() => setStep(2)}
                  className="px-4 py-3 rounded-2xl bg-slate-800 hover:bg-slate-700 text-slate-300 text-sm font-bold transition-colors cursor-pointer"
                >
                  <ArrowLeft className="w-4 h-4" />
                </button>
                <button
                  type="button"
                  onClick={() => setStep(4)}
                  className="flex-1 py-3 rounded-2xl bg-blue-600 hover:bg-blue-500 text-white text-sm font-bold transition-all shadow-md shadow-blue-600/20 flex items-center justify-center gap-2 cursor-pointer"
                >
                  <span>Continue</span>
                  <ArrowRight className="w-4 h-4" />
                </button>
              </div>
            </motion.div>
          )}

          {/* STEP 4: READY */}
          {step === 4 && (
            <motion.div
              key="step4"
              initial={{ opacity: 0, x: 20 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: -20 }}
              className="text-center py-4"
            >
              <div className="w-16 h-16 rounded-3xl bg-emerald-500/15 border border-emerald-500/30 text-emerald-400 flex items-center justify-center mx-auto mb-4 shadow-lg">
                <CheckCircle2 className="w-8 h-8" />
              </div>
              <h2 className="text-2xl sm:text-3xl font-black text-white tracking-tight mb-2">
                You're All Set!
              </h2>
              <p className="text-slate-300 text-sm sm:text-base leading-relaxed max-w-sm mx-auto mb-8">
                Your profile is configured. You can change these preferences anytime under Settings.
              </p>
              <button
                type="button"
                onClick={handleFinish}
                className="w-full py-3.5 rounded-2xl bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-500 hover:to-indigo-500 text-white font-bold text-base transition-all shadow-xl shadow-blue-600/25 flex items-center justify-center gap-2 cursor-pointer"
              >
                <span>Enter ORMA Dashboard</span>
                <ArrowRight className="w-5 h-5" />
              </button>
            </motion.div>
          )}
        </motion.div>
      </div>
    </AnimatePresence>
  );
}

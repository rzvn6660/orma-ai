import { useState, useEffect, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Globe, Check, X, Volume2, VolumeX, Info } from 'lucide-react';
import { REMINDER_LANGUAGES, getLanguageConfig } from '../../config/reminderLanguages';
import { tts } from '../../services/tts';
import { getSampleSentence } from '../../utils/reminderLocalization';

export default function ReminderLanguageModal({
  isOpen,
  onClose,
  currentLanguage = "en-IN",
  onSelectLanguage,
  isPending = false
}) {
  const modalRef = useRef(null);
  const [previewNotice, setPreviewNotice] = useState(null);

  useEffect(() => {
    if (isOpen) {
      document.body.style.overflow = 'hidden';
      if (modalRef.current) modalRef.current.focus();
    } else {
      document.body.style.overflow = '';
      setPreviewNotice(null);
    }
    return () => {
      document.body.style.overflow = '';
    };
  }, [isOpen]);

  const handleKeyDown = (e) => {
    if (e.key === 'Escape') {
      onClose();
    }
  };

  const handlePreviewVoice = (e, langCode) => {
    e.stopPropagation();
    setPreviewNotice(null);

    const voiceInfo = tts.getAvailableReminderVoice(langCode);
    if (!voiceInfo.voiceFound) {
      setPreviewNotice(`Voice preview isn't available on this device for ${getLanguageConfig(langCode).name}.`);
      setTimeout(() => setPreviewNotice(null), 4000);
      return;
    }

    const sampleText = getSampleSentence(langCode);
    tts.speak(sampleText, { langCode });
  };

  if (!isOpen) return null;

  const selectedCfg = getLanguageConfig(currentLanguage);

  return (
    <AnimatePresence>
      <div 
        className="fixed inset-0 z-[100] flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-md animate-fade-in"
        onClick={onClose}
        role="dialog"
        aria-modal="true"
        aria-labelledby="reminder-language-modal-title"
      >
        <motion.div
          ref={modalRef}
          tabIndex="-1"
          onKeyDown={handleKeyDown}
          onClick={(e) => e.stopPropagation()}
          initial={{ opacity: 0, scale: 0.95, y: 15 }}
          animate={{ opacity: 1, scale: 1, y: 0 }}
          exit={{ opacity: 0, scale: 0.95, y: 15 }}
          transition={{ duration: 0.2, ease: "easeOut" }}
          className="relative w-full max-w-lg bg-[#0B132B] border-2 border-blue-500/30 rounded-3xl p-6 sm:p-8 shadow-[0_20px_60px_rgba(0,0,0,0.6)] text-white space-y-6 outline-none"
        >
          {/* Header */}
          <div className="flex items-start justify-between gap-4 border-b border-slate-800 pb-5">
            <div className="flex items-center gap-3.5">
              <div className="w-12 h-12 rounded-2xl bg-blue-600/20 border border-blue-500/40 text-blue-400 flex items-center justify-center shrink-0 shadow-inner">
                <Globe className="w-6 h-6" />
              </div>
              <div>
                <h2 id="reminder-language-modal-title" className="text-xl sm:text-2xl font-black text-white tracking-tight">
                  Reminder Language
                </h2>
                <p className="text-xs sm:text-sm text-slate-300 font-medium mt-0.5">
                  Choose the language ORMA uses when speaking your medication reminders.
                </p>
              </div>
            </div>

            <button
              type="button"
              onClick={onClose}
              className="p-2.5 rounded-2xl bg-slate-900 hover:bg-slate-800 text-slate-400 hover:text-white border border-slate-700/80 transition-colors cursor-pointer min-w-[44px] min-h-[44px] flex items-center justify-center shrink-0"
              aria-label="Close language selector"
            >
              <X className="w-5 h-5" />
            </button>
          </div>

          {/* Voice Preview Notice Banner if unavailable */}
          {previewNotice && (
            <div className="p-3.5 rounded-2xl bg-slate-900 border border-amber-500/40 text-amber-300 text-xs font-semibold flex items-center gap-2 animate-fade-in">
              <VolumeX className="w-4 h-4 text-amber-400 shrink-0" />
              <span>{previewNotice}</span>
            </div>
          )}

          {/* Languages List */}
          <div className="space-y-2.5 max-h-[55vh] overflow-y-auto custom-scrollbar pr-1">
            {REMINDER_LANGUAGES.map((lang) => {
              const isSelected = selectedCfg.code === lang.code;

              return (
                <div
                  key={lang.code}
                  onClick={() => {
                    onSelectLanguage(lang.code);
                  }}
                  role="button"
                  tabIndex={0}
                  onKeyDown={(e) => { if (e.key === 'Enter' || e.key === ' ') onSelectLanguage(lang.code); }}
                  className={`w-full p-4 rounded-2xl border text-left transition-all duration-200 flex items-center justify-between gap-3 min-h-[64px] cursor-pointer outline-none focus-visible:ring-4 focus-visible:ring-blue-400 ${
                    isSelected
                      ? 'bg-blue-600/25 border-blue-500 text-white shadow-lg shadow-blue-600/10 ring-1 ring-blue-400/50'
                      : 'bg-slate-900/80 hover:bg-slate-800/90 border-slate-800 text-slate-200 hover:border-slate-700'
                  }`}
                  aria-selected={isSelected}
                >
                  <div className="flex items-center gap-3.5">
                    <span className="text-2xl sm:text-3xl shrink-0 leading-none select-none">
                      {lang.flag}
                    </span>

                    <div className="flex flex-col">
                      <span className="text-lg sm:text-xl font-bold tracking-tight text-white leading-tight">
                        {lang.nativeName}
                      </span>
                      {lang.name !== lang.nativeName && (
                        <span className="text-xs font-semibold text-slate-400">
                          {lang.name}
                        </span>
                      )}
                    </div>
                  </div>

                  <div className="flex items-center gap-2.5 shrink-0">
                    <button
                      type="button"
                      onClick={(e) => handlePreviewVoice(e, lang.code)}
                      className="px-3 py-1.5 rounded-xl bg-slate-800 hover:bg-slate-700 text-xs font-bold text-cyan-300 hover:text-cyan-200 border border-slate-700/80 flex items-center gap-1.5 cursor-pointer shrink-0 transition-colors"
                      title="Hear sample voice"
                    >
                      <Volume2 className="w-3.5 h-3.5 text-cyan-400" />
                      <span className="hidden sm:inline">Hear sample</span>
                      <span className="sm:hidden">Sample</span>
                    </button>

                    {isSelected && (
                      <div className="w-8 h-8 rounded-full bg-blue-500 text-white flex items-center justify-center shadow-md">
                        <Check className="w-5 h-5 stroke-[3]" />
                      </div>
                    )}
                  </div>
                </div>
              );
            })}
          </div>

          {/* Scope Note Banner */}
          <div className="p-3.5 rounded-2xl bg-slate-900/90 border border-slate-800 text-xs text-slate-400 flex items-start gap-2.5">
            <Info className="w-4 h-4 text-cyan-400 shrink-0 mt-0.5" />
            <span>
              This setting applies exclusively to medication reminder spoken alerts, reminder text, and voice confirmations. Emergency systems remain independent.
            </span>
          </div>
        </motion.div>
      </div>
    </AnimatePresence>
  );
}

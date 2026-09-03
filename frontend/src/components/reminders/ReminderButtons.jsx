import { useState, useRef, useEffect } from 'react';
import { Check, Clock, Mic, Loader2, ChevronLeft, AlertCircle, RefreshCw } from 'lucide-react';
import { getReminderStrings, isRTL } from '../../utils/reminderLocalization';
import { getLanguageConfig, DEFAULT_REMINDER_LANGUAGE } from '../../config/reminderLanguages';

export default function ReminderButtons({ 
  onMarkTaken, 
  onSnooze, 
  onSkip, 
  loading, 
  medicineName,
  apiError,
  user
}) {
  const [showSkipConfirm, setShowSkipConfirm] = useState(false);
  const [showSnoozeOptions, setShowSnoozeOptions] = useState(false);
  
  // Voice confirmation state: null | 'listening' | 'confirming' | 'success' | 'error'
  const [voiceState, setVoiceState] = useState(null);
  const [voiceErrorMessage, setVoiceErrorMessage] = useState('');
  const recognitionRef = useRef(null);

  const prefs = user?.notification_preferences || {};
  const reminderLang = prefs.reminder_language || localStorage.getItem('orma_reminder_language') || DEFAULT_REMINDER_LANGUAGE;
  const langConfig = getLanguageConfig(reminderLang);
  const strings = getReminderStrings(reminderLang);
  const rtl = isRTL(reminderLang);

  useEffect(() => {
    return () => {
      if (recognitionRef.current) {
        try {
          recognitionRef.current.stop();
        } catch (e) {
          console.debug('[VoiceRecognition] Stop cleanup:', e);
        }
      }
    };
  }, []);

  const startVoiceRecognition = () => {
    setVoiceErrorMessage('');
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;

    if (!SpeechRecognition) {
      setVoiceState('error');
      setVoiceErrorMessage("Voice recognition is not supported in this browser. Please tap '" + strings.buttonTookIt + "'.");
      return;
    }

    try {
      if (recognitionRef.current) {
        try { recognitionRef.current.stop(); } catch (e) { console.debug(e); }
      }

      const recognition = new SpeechRecognition();
      recognition.continuous = false;
      recognition.interimResults = false;
      recognition.lang = langConfig.locale || 'en-US';

      recognition.onstart = () => {
        setVoiceState('listening');
      };

      recognition.onresult = (event) => {
        setVoiceState('confirming');
        const transcript = (event.results[0][0].transcript || '').toLowerCase();
        console.log('[Voice Recognition Result]:', transcript);

        const medLower = (medicineName || '').toLowerCase();
        
        // Multilingual confirmation keywords matching
        const positiveKeywords = [
          'took', 'taken', 'yes', 'done', 'did', 'confirm', 'okay', 'ok',
          'കഴിച്ചു', 'എടുത്തു', 'അതെ', 'തീർന്നു', 'ഉവ്വ്',
          'ले ली', 'हाँ', 'हो गया', 'खा ली', 'जी',
          'أخذت', 'نعم', 'تم', 'تناولت',
          'சாப்பிட்டேன்', 'ஆம்', 'முடித்தேன்',
          'వేసుకున్నాను', 'అవును', 'పూర్తయింది',
          'ತೆಗೆದುಕೊಂಡಿದ್ದೇನೆ', 'ಹೌದು', 'ಆಯಿತು'
        ];

        const matchesIntent = 
          positiveKeywords.some(keyword => transcript.includes(keyword)) ||
          (medLower && transcript.includes(medLower));

        if (matchesIntent) {
          setVoiceState('success');
          setTimeout(() => {
            setVoiceState(null);
            onMarkTaken();
          }, 700);
        } else {
          setVoiceState('error');
          const errText = (strings.voiceError || "Didn't catch confirmation for {medName}.")
            .replace('{medName}', medicineName || 'medicine');
          setVoiceErrorMessage(`${errText} Said: "${transcript}"`);
        }
      };

      recognition.onerror = (err) => {
        console.warn('[Voice Recognition Error]:', err);
        setVoiceState('error');
        setVoiceErrorMessage("Sorry, I didn't catch that.");
      };

      recognition.onend = () => {
        setVoiceState(prev => prev === 'listening' ? 'error' : prev);
      };

      recognitionRef.current = recognition;
      recognition.start();
    } catch (err) {
      console.warn('Speech recognition init error:', err);
      setVoiceState('error');
      setVoiceErrorMessage("Could not start microphone.");
    }
  };

  const stopVoiceRecognition = () => {
    if (recognitionRef.current) {
      try { recognitionRef.current.stop(); } catch (e) { console.debug(e); }
    }
    setVoiceState(null);
  };

  if (showSkipConfirm) {
    return (
      <div className={`flex flex-col gap-3 w-full animate-in fade-in duration-200 ${rtl ? 'rtl' : 'ltr'}`} dir={rtl ? 'rtl' : 'ltr'}>
        <div className="p-4 bg-slate-900 border border-slate-800 rounded-2xl text-center space-y-1">
          <p className="text-sm text-slate-200 font-bold">{strings.skipConfirmTitle}</p>
          <p className="text-xs text-amber-400 font-medium">{strings.skipConfirmSubtext}</p>
        </div>
        <div className="flex gap-3">
          <button 
            type="button"
            onClick={onSkip}
            disabled={loading}
            className="flex-1 h-14 bg-red-600/20 hover:bg-red-600/30 text-red-300 hover:text-red-200 border border-red-500/40 rounded-2xl font-bold text-base transition-all flex items-center justify-center gap-2 cursor-pointer outline-none focus-visible:ring-4 focus-visible:ring-red-500/50"
          >
            {strings.buttonConfirmSkip}
          </button>
          <button 
            type="button"
            onClick={() => setShowSkipConfirm(false)}
            disabled={loading}
            className="flex-1 h-14 bg-slate-800 hover:bg-slate-700 text-slate-200 rounded-2xl font-bold text-base transition-all flex items-center justify-center gap-2 cursor-pointer outline-none focus-visible:ring-4 focus-visible:ring-slate-500/50 border border-slate-700"
          >
            {strings.buttonCancel}
          </button>
        </div>
      </div>
    );
  }

  if (showSnoozeOptions) {
    return (
      <div className={`flex flex-col gap-3 w-full animate-in fade-in duration-200 ${rtl ? 'rtl' : 'ltr'}`} dir={rtl ? 'rtl' : 'ltr'}>
        <button 
          type="button"
          onClick={() => setShowSnoozeOptions(false)}
          className="flex items-center gap-1.5 text-slate-400 hover:text-white mb-1 text-sm font-semibold cursor-pointer w-fit"
        >
          <ChevronLeft className={`w-4 h-4 ${rtl ? 'rotate-180' : ''}`} /> {strings.buttonCancel}
        </button>
        <div className="grid grid-cols-3 gap-2.5">
          {[10, 15, 30].map(mins => (
            <button
              key={mins}
              type="button"
              onClick={() => {
                setShowSnoozeOptions(false);
                onSnooze(mins);
              }}
              disabled={loading}
              className={`h-14 rounded-2xl font-bold text-sm transition-all flex items-center justify-center gap-2 cursor-pointer outline-none focus-visible:ring-4 ${
                mins === 10 
                  ? 'bg-blue-600 hover:bg-blue-500 text-white shadow-md shadow-blue-600/20' 
                  : 'bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700'
              }`}
            >
              <Clock className="w-4 h-4 text-blue-300" /> {mins} min
            </button>
          ))}
        </div>
      </div>
    );
  }

  const successText = (strings.markedTaken || "Got it. {medName} has been marked as taken.")
    .replace('{medName}', medicineName || 'Medicine');

  const snoozeLabel = (strings.buttonSnoozeMins || "Snooze {mins} minutes")
    .replace('{mins}', 10);

  return (
    <div className={`flex flex-col gap-2.5 sm:gap-3 w-full shrink-0 ${rtl ? 'rtl' : 'ltr'}`} dir={rtl ? 'rtl' : 'ltr'}>
      {/* API ERROR BANNER */}
      {apiError && (
        <div className="p-3 rounded-2xl bg-red-950/70 border border-red-500/40 text-red-200 text-xs font-semibold text-center flex items-center justify-between gap-3 animate-fade-in">
          <div className="flex items-center gap-2">
            <AlertCircle className="w-4 h-4 text-red-400 shrink-0" />
            <span>{strings.connectionError || "Couldn't confirm the medication."}</span>
          </div>
          <button
            type="button"
            onClick={onMarkTaken}
            className="px-3 py-1 bg-red-600 hover:bg-red-500 text-white rounded-lg font-bold text-xs shrink-0 cursor-pointer"
          >
            {strings.tryAgain || "Try Again"}
          </button>
        </div>
      )}

      {/* 1. DOMINANT PRIMARY ACTION: I TOOK IT */}
      <button 
        type="button"
        onClick={onMarkTaken}
        disabled={loading || Boolean(voiceState)}
        className="w-full min-h-[52px] h-14 sm:h-15 bg-emerald-600 hover:bg-emerald-500 active:scale-[0.99] text-white rounded-2xl font-black text-lg sm:text-xl tracking-tight transition-all flex items-center justify-center gap-3 shadow-lg shadow-emerald-600/30 border border-emerald-500/50 cursor-pointer outline-none focus-visible:ring-4 focus-visible:ring-emerald-400 disabled:opacity-50"
      >
        {loading ? (
          <>
            <Loader2 className="w-5 h-5 sm:w-6 sm:h-6 animate-spin" />
            <span>{strings.voiceChecking || "Confirming..."}</span>
          </>
        ) : (
          <>
            <Check className="w-6 h-6 sm:w-7 sm:h-7 stroke-[3]" />
            <span>{strings.buttonTookIt}</span>
          </>
        )}
      </button>

      {/* 2. VOICE CONFIRMATION FLOW */}
      {voiceState === 'listening' ? (
        <div className="p-3.5 rounded-2xl bg-cyan-950/80 border border-cyan-500/50 text-center space-y-2 backdrop-blur-md animate-fade-in">
          <div className="flex items-center justify-center gap-2 text-cyan-300 font-black text-sm">
            <span className="w-3 h-3 rounded-full bg-cyan-400 animate-ping inline-block" />
            <Mic className="w-4 h-4 text-cyan-400 animate-bounce" />
            <span>{strings.voiceListening}</span>
          </div>
          <p className="text-xs text-slate-200 font-semibold">
            &quot;{strings.voicePrompt}&quot;
          </p>
          <button
            type="button"
            onClick={stopVoiceRecognition}
            className="px-3 py-1 rounded-xl bg-slate-900 text-slate-300 hover:text-white text-xs font-bold border border-slate-700 cursor-pointer"
          >
            {strings.buttonCancel}
          </button>
        </div>
      ) : voiceState === 'confirming' ? (
        <div className="p-3 rounded-2xl bg-cyan-950/80 border border-cyan-500/40 text-center text-xs font-bold text-cyan-200 flex items-center justify-center gap-2">
          <Loader2 className="w-4 h-4 animate-spin text-cyan-400" />
          <span>{strings.voiceChecking}</span>
        </div>
      ) : voiceState === 'success' ? (
        <div className="p-3 rounded-2xl bg-emerald-950/80 border border-emerald-500/40 text-center text-xs font-bold text-emerald-300 flex items-center justify-center gap-2">
          <Check className="w-4 h-4 text-emerald-400" />
          <span>{successText}</span>
        </div>
      ) : voiceState === 'error' ? (
        <div className="p-3 rounded-2xl bg-slate-900 border border-amber-500/40 text-center space-y-2 animate-fade-in">
          <p className="text-xs font-bold text-amber-300">
            {voiceErrorMessage || "Sorry, I didn't catch that."}
          </p>
          <div className="flex items-center justify-center gap-2">
            <button
              type="button"
              onClick={startVoiceRecognition}
              className="px-3 py-1 rounded-xl bg-blue-600 hover:bg-blue-500 text-white font-bold text-xs flex items-center gap-1.5 cursor-pointer"
            >
              <RefreshCw className="w-3.5 h-3.5" />
              <span>{strings.tryAgain || "Try Again"}</span>
            </button>
            <button
              type="button"
              onClick={() => setVoiceState(null)}
              className="px-3 py-1 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-bold cursor-pointer"
            >
              {strings.buttonCancel}
            </button>
          </div>
        </div>
      ) : (
        /* SECONDARY ACTION: CONFIRM BY VOICE */
        <button 
          type="button"
          onClick={startVoiceRecognition}
          disabled={loading}
          className="w-full min-h-[44px] h-11 sm:h-12 bg-cyan-950/50 hover:bg-cyan-900/60 active:scale-[0.99] text-cyan-300 border border-cyan-500/40 rounded-2xl font-bold text-sm sm:text-base transition-all flex items-center justify-center gap-2.5 shadow-md cursor-pointer outline-none focus-visible:ring-4 focus-visible:ring-cyan-400/50 disabled:opacity-50"
        >
          <Mic className="w-4 h-4 sm:w-5 sm:h-5 text-cyan-400" />
          <span>{strings.buttonConfirmVoice}</span>
        </button>
      )}
      
      {/* 3. TERTIARY ACTION: REMIND ME LATER (SNOOZE 10 MINUTES) */}
      <button 
        type="button"
        onClick={() => onSnooze(10)}
        disabled={loading}
        className="w-full min-h-[42px] h-10 sm:h-11 bg-slate-900 hover:bg-slate-800 active:scale-[0.99] text-slate-200 border border-slate-700/80 rounded-2xl font-bold text-xs sm:text-sm transition-all flex items-center justify-center gap-2 shadow-sm cursor-pointer outline-none focus-visible:ring-4 focus-visible:ring-blue-400/50 disabled:opacity-50"
      >
        <Clock className="w-4 h-4 text-amber-400" />
        <span>{strings.buttonRemindLater || "Remind me later"}</span>
        <span className="text-[11px] text-slate-400 font-normal">({snoozeLabel})</span>
      </button>
      
      {/* 4. QUATERNARY ACTION: REMIND ME LATER / SKIP */}
      <button 
        type="button"
        onClick={() => setShowSkipConfirm(true)}
        disabled={loading}
        className="py-1 text-center text-slate-400 hover:text-slate-200 text-xs font-semibold transition-colors cursor-pointer outline-none focus-visible:underline disabled:opacity-50"
      >
        {strings.buttonRemindLater}
      </button>
    </div>
  );
}

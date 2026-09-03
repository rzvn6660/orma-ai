import { useContext, useEffect, useState, useRef } from 'react';
import { AnimatePresence, motion } from 'framer-motion';
import { ReminderContext } from '../../contexts/ReminderContext';
import ReminderOverlay from './ReminderOverlay';
import ReminderHeader from './ReminderHeader';
import ReminderContent from './ReminderContent';
import ReminderButtons from './ReminderButtons';
import { ReminderSoundService } from '../../services/ReminderSoundService';
import { ReminderSpeechService } from '../../services/ReminderSpeechService';
import { BrowserNotificationService } from '../../services/BrowserNotificationService';
import { 
  ChevronLeft, 
  ChevronRight, 
  Check, 
  Clock, 
  CheckCircle2,
  VolumeX
} from 'lucide-react';
import { tts } from '../../services/tts';
import { getReminderStrings, getVoiceUnavailableStatus, isRTL } from '../../utils/reminderLocalization';
import { DEFAULT_REMINDER_LANGUAGE } from '../../config/reminderLanguages';

export default function ReminderModal({ user }) {
  const { 
    currentReminder, 
    currentReminderGroup, 
    markTaken, 
    clearReminder, 
    snoozeReminder, 
    skipReminder 
  } = useContext(ReminderContext);

  const [loadingId, setLoadingId] = useState(null);
  const [apiErrorId, setApiErrorId] = useState(null);
  const [showModal, setShowModal] = useState(false);
  const [currentIndex, setCurrentIndex] = useState(0);
  const [touchStartX, setTouchStartX] = useState(null);

  const modalRef = useRef(null);

  const prefs = user?.notification_preferences || {};
  const reminderLang = prefs.reminder_language || localStorage.getItem('orma_reminder_language') || DEFAULT_REMINDER_LANGUAGE;
  const strings = getReminderStrings(reminderLang);
  const rtl = isRTL(reminderLang);

  const voiceCapability = tts.getAvailableReminderVoice(reminderLang);
  const showVoiceUnavailableStatus = Boolean(
    user?.role !== 'caregiver' &&
    user?.notification_preferences?.medication_spoken_alerts !== false &&
    reminderLang !== 'en-IN' &&
    !voiceCapability.voiceFound
  );

  // Determine active session & medicines list
  const isMultiGroup = Boolean(
    currentReminderGroup && 
    currentReminderGroup.medicines && 
    currentReminderGroup.medicines.length > 1
  );

  const medicines = isMultiGroup 
    ? currentReminderGroup.medicines 
    : (currentReminderGroup?.medicines || (currentReminder ? [currentReminder] : []));

  const activeMed = medicines[currentIndex] || medicines[0] || null;

  // Track state counts
  const pendingCount = medicines.filter(m => m.status === 'pending').length;
  const isAllHandled = medicines.length > 0 && pendingCount === 0;

  // 1. Audio, Speech, and Browser Notification Triggers on open
  useEffect(() => {
    if (currentReminderGroup || currentReminder) {
      setShowModal(true);
      if (modalRef.current) modalRef.current.focus();

      const runAudioVoice = async () => {
        try {
          await ReminderSoundService.play();
        } catch (e) {
          console.warn('[ReminderModal] Sound playback bypassed:', e);
        }

        try {
          const medToAnnounce = activeMed || currentReminder;
          if (medToAnnounce) {
            await ReminderSpeechService.speak(medToAnnounce, user);
          }
        } catch (e) {
          console.warn('[ReminderModal] Voice announcement bypassed:', e);
        }

        try {
          if (activeMed) {
            BrowserNotificationService.notify(activeMed, user);
          }
        } catch (e) {
          console.warn('[ReminderModal] Notification error:', e);
        }
      };

      runAudioVoice();
    } else {
      setShowModal(false);
      setCurrentIndex(0);
      setApiErrorId(null);
    }
  }, [currentReminderGroup?.sessionId, currentReminder?.id]);

  // Lock background page scroll when reminder modal is active
  useEffect(() => {
    if (showModal && medicines.length > 0) {
      const originalOverflow = document.body.style.overflow;
      document.body.style.overflow = 'hidden';
      return () => {
        document.body.style.overflow = originalOverflow;
      };
    }
  }, [showModal, medicines.length]);

  // Caregiver check: suppress normal medication reminder modal if caregiver preference is OFF (default OFF)
  if (user?.role === 'caregiver' && user?.notification_preferences?.medication_reminder_notifications !== true) {
    return null;
  }

  if (!showModal || medicines.length === 0) return null;

  // Helper: Advance to next pending medicine in multi-group session
  const advanceToNextPending = (updatedIndex = currentIndex) => {
    if (!isMultiGroup) {
      if (isAllHandled) {
        setTimeout(() => clearReminder(), 600);
      }
      return;
    }

    let nextIdx = -1;
    for (let i = updatedIndex + 1; i < medicines.length; i++) {
      if (medicines[i].status === 'pending') {
        nextIdx = i;
        break;
      }
    }
    if (nextIdx === -1) {
      for (let i = 0; i < updatedIndex; i++) {
        if (medicines[i].status === 'pending') {
          nextIdx = i;
          break;
        }
      }
    }

    if (nextIdx !== -1) {
      setCurrentIndex(nextIdx);
    }
  };

  // Action: Mark Taken with Error Handling & Auto Advancement
  const handleMarkTakenSingle = async (medToTake = activeMed) => {
    if (!medToTake) return;
    setLoadingId(medToTake.id);
    setApiErrorId(null);
    
    try {
      await markTaken(medToTake);
      const confirmText = (strings.markedTaken || "Got it. {medName} has been marked as taken.").replace('{medName}', medToTake.medicine_name || 'medicine');
      tts.speak(confirmText, { langCode: reminderLang });
      
      window.dispatchEvent(new CustomEvent('orma:toast', { 
        detail: { type: 'success', message: confirmText } 
      }));

      setLoadingId(null);
      advanceToNextPending(currentIndex);
    } catch (err) {
      console.error('Failed to mark medicine taken:', err);
      setLoadingId(null);
      setApiErrorId(medToTake.id);
      window.dispatchEvent(new CustomEvent('orma:toast', {
        detail: { type: 'error', message: strings.connectionError || "Connection lost. Couldn't confirm the medication." }
      }));
    }
  };

  // Action: Snooze with Error Handling
  const handleSnoozeSingle = async (medToSnooze = activeMed, minutes = 10) => {
    if (!medToSnooze) return;
    setLoadingId(medToSnooze.id);
    setApiErrorId(null);

    try {
      await snoozeReminder(medToSnooze, minutes);
      setLoadingId(null);

      const snoozeText = (strings.snoozedConfirmation || "Your reminder has been snoozed for {mins} minutes.").replace('{mins}', minutes);
      tts.speak(snoozeText, { langCode: reminderLang });

      window.dispatchEvent(new CustomEvent('orma:toast', { 
        detail: { type: 'info', message: snoozeText } 
      }));

      advanceToNextPending(currentIndex);
    } catch (err) {
      console.error('Failed to snooze medicine:', err);
      setLoadingId(null);
      setApiErrorId(medToSnooze.id);
      window.dispatchEvent(new CustomEvent('orma:toast', {
        detail: { type: 'error', message: strings.connectionError || "Connection lost. Couldn't snooze the medication." }
      }));
    }
  };

  // Action: Skip with Error Handling
  const handleSkipSingle = async (medToSkip = activeMed) => {
    if (!medToSkip) return;
    setLoadingId(medToSkip.id);
    setApiErrorId(null);

    try {
      await skipReminder(medToSkip);
      setLoadingId(null);

      window.dispatchEvent(new CustomEvent('orma:toast', { 
        detail: { type: 'info', message: `Skipped ${medToSkip.medicine_name}.` } 
      }));

      advanceToNextPending(currentIndex);
    } catch (err) {
      console.error('Failed to skip medicine:', err);
      setLoadingId(null);
      setApiErrorId(medToSkip.id);
      window.dispatchEvent(new CustomEvent('orma:toast', {
        detail: { type: 'error', message: strings.connectionError || "Connection lost. Couldn't update medication status." }
      }));
    }
  };

  // Touch Swipe Navigation for Carousel
  const handleTouchStart = (e) => {
    setTouchStartX(e.touches[0].clientX);
  };

  const handleTouchEnd = (e) => {
    if (!touchStartX || !isMultiGroup) return;
    const touchEndX = e.changedTouches[0].clientX;
    const diff = touchStartX - touchEndX;

    if (diff > 45 && currentIndex < medicines.length - 1) {
      setCurrentIndex(prev => prev + 1);
    } else if (diff < -45 && currentIndex > 0) {
      setCurrentIndex(prev => prev - 1);
    }
    setTouchStartX(null);
  };

  // Keyboard Navigation
  const handleKeyDown = (e) => {
    if (e.key === 'Escape') {
      e.preventDefault();
      e.stopPropagation();
    } else if (e.key === 'ArrowRight' && isMultiGroup && currentIndex < medicines.length - 1) {
      setCurrentIndex(prev => prev + 1);
    } else if (e.key === 'ArrowLeft' && isMultiGroup && currentIndex > 0) {
      setCurrentIndex(prev => prev - 1);
    }
  };

  // =========================================================================
  // SINGLE MEDICINE REMINDER MODE
  // =========================================================================
  if (!isMultiGroup && activeMed) {
    return (
      <AnimatePresence>
        <ReminderOverlay>
          <motion.div
            ref={modalRef}
            tabIndex="-1"
            onKeyDown={handleKeyDown}
            aria-labelledby="reminder-title"
            role="region"
            aria-label="Medication reminder"
            initial={{ scale: 0.96, opacity: 0, y: 15 }}
            animate={{ scale: 1, opacity: 1, y: 0 }}
            exit={{ scale: 0.96, opacity: 0, y: 15 }}
            transition={{ duration: 0.2 }}
            className={`relative w-full max-w-md max-h-[min(calc(100dvh-1.5rem),720px)] sm:max-h-[min(calc(100dvh-2rem),720px)] bg-[#0B132B] border-2 border-blue-500/30 rounded-3xl p-4 sm:p-6 shadow-[0_20px_60px_rgba(0,0,0,0.6)] z-10 text-white outline-none overflow-y-auto custom-scrollbar flex flex-col my-auto ${rtl ? 'rtl' : 'ltr'}`}
            dir={rtl ? 'rtl' : 'ltr'}
          >
            <ReminderHeader 
              userName={user?.first_name || user?.name || 'User'} 
              currentCount={1}
              totalCount={1}
              user={user}
              medicineName={activeMed.medicine_name}
            />

            {showVoiceUnavailableStatus && (
              <div className="mb-4 p-3.5 rounded-2xl bg-slate-900/90 border border-slate-700/60 text-slate-300 text-xs font-semibold flex items-center justify-center gap-2.5 text-center">
                <VolumeX className="w-4 h-4 text-amber-400 shrink-0" />
                <span>{getVoiceUnavailableStatus(reminderLang)}</span>
              </div>
            )}
            
            <ReminderContent medicine={activeMed} user={user} />
            
            <ReminderButtons 
              onMarkTaken={() => handleMarkTakenSingle(activeMed)} 
              onSnooze={(mins) => handleSnoozeSingle(activeMed, mins)} 
              onSkip={() => handleSkipSingle(activeMed)} 
              loading={loadingId === activeMed.id}
              medicineName={activeMed.medicine_name}
              apiError={apiErrorId === activeMed.id}
              user={user}
            />
          </motion.div>
        </ReminderOverlay>
      </AnimatePresence>
    );
  }

  // =========================================================================
  // MULTI-MEDICATION GROUPED REMINDER MODE
  // =========================================================================
  return (
    <AnimatePresence>
      <ReminderOverlay>
        <motion.div
          ref={modalRef}
          tabIndex="-1"
          onKeyDown={handleKeyDown}
          aria-labelledby="grouped-reminder-title"
          role="region"
          aria-label="Grouped medication reminders"
          initial={{ scale: 0.96, opacity: 0, y: 15 }}
          animate={{ scale: 1, opacity: 1, y: 0 }}
          exit={{ scale: 0.96, opacity: 0, y: 15 }}
          transition={{ duration: 0.2 }}
          className={`relative w-full max-w-lg max-h-[min(calc(100dvh-1.5rem),760px)] sm:max-h-[min(calc(100dvh-2rem),760px)] bg-[#0B132B] border-2 border-blue-500/40 rounded-3xl p-4 sm:p-6 shadow-[0_20px_60px_rgba(0,0,0,0.6)] z-10 text-white space-y-4 sm:space-y-5 outline-none overflow-y-auto custom-scrollbar flex flex-col my-auto ${rtl ? 'rtl' : 'ltr'}`}
          dir={rtl ? 'rtl' : 'ltr'}
        >
          {/* Screen Reader Announcement */}
          <div className="sr-only" aria-live="polite">
            {activeMed 
              ? `Medicine ${currentIndex + 1} of ${medicines.length}: ${activeMed.medicine_name}, ${activeMed.dosage || ''}` 
              : 'All medicines handled.'
            }
          </div>

          {/* Header & Multi-Medicine Progress */}
          <div className="flex flex-col items-center text-center space-y-3">
            <ReminderHeader 
              userName={user?.first_name || user?.name || 'User'} 
              currentCount={currentIndex + 1}
              totalCount={medicines.length}
              user={user}
              medicineName={activeMed?.medicine_name}
            />

            {showVoiceUnavailableStatus && (
              <div className="w-full p-3.5 rounded-2xl bg-slate-900/90 border border-slate-700/60 text-slate-300 text-xs font-semibold flex items-center justify-center gap-2.5 text-center">
                <VolumeX className="w-4 h-4 text-amber-400 shrink-0" />
                <span>{getVoiceUnavailableStatus(reminderLang)}</span>
              </div>
            )}

            {/* Medicine Status Pills Bar */}
            <div className="w-full flex items-center justify-center gap-2 overflow-x-auto pb-1 custom-scrollbar">
              {medicines.map((med, idx) => {
                const isCurrent = idx === currentIndex;
                const isTaken = med.status === 'taken';
                const isSnoozed = med.status === 'snoozed';
                const isSkipped = med.status === 'skipped';

                return (
                  <button
                    key={med.id || idx}
                    type="button"
                    onClick={() => setCurrentIndex(idx)}
                    className={`px-3 py-1.5 rounded-xl text-xs font-extrabold transition-all cursor-pointer shrink-0 flex items-center gap-1.5 border min-h-[36px] ${
                      isCurrent
                        ? 'bg-blue-600 text-white border-blue-400 shadow-md shadow-blue-600/30 ring-2 ring-blue-400/40'
                        : isTaken
                        ? 'bg-emerald-950/60 text-emerald-300 border-emerald-500/40'
                        : isSnoozed
                        ? 'bg-amber-950/60 text-amber-300 border-amber-500/40'
                        : isSkipped
                        ? 'bg-slate-900 text-slate-400 border-white/10'
                        : 'bg-slate-900/80 text-slate-300 hover:text-white border-white/10'
                    }`}
                  >
                    {isTaken ? (
                      <Check className="w-3.5 h-3.5 text-emerald-400 stroke-[3]" />
                    ) : isSnoozed ? (
                      <Clock className="w-3.5 h-3.5 text-amber-400" />
                    ) : isCurrent ? (
                      <span className="w-2 h-2 rounded-full bg-white animate-pulse" />
                    ) : null}
                    <span>{med.medicine_name}</span>
                  </button>
                );
              })}
            </div>
          </div>

          {/* SESSION COMPLETION VIEW */}
          {isAllHandled ? (
            <motion.div
              initial={{ opacity: 0, scale: 0.96 }}
              animate={{ opacity: 1, scale: 1 }}
              className="p-6 sm:p-8 rounded-3xl bg-slate-900/90 border border-emerald-500/40 text-center space-y-6 backdrop-blur-xl shadow-xl"
            >
              <div className="w-16 h-16 rounded-2xl bg-emerald-500/20 border border-emerald-500/40 text-emerald-400 flex items-center justify-center mx-auto shadow-lg shadow-emerald-500/20">
                <CheckCircle2 className="w-10 h-10" />
              </div>

              <div className="space-y-1.5">
                <h2 className="text-2xl sm:text-3xl font-black text-white tracking-tight">{strings.allDoneTitle || "✓ ALL DONE"}</h2>
                <h3 className="text-base font-bold text-emerald-400">{strings.allDoneSubtext || "All medicines handled"}</h3>
                <p className="text-xs text-slate-300">
                  {strings.allDoneMessage || "You're all set for this reminder session. Great job!"}
                </p>
              </div>

              {/* Handled Summary List */}
              <div className="space-y-2 text-left text-xs max-h-48 overflow-y-auto custom-scrollbar pt-2 border-t border-white/10">
                {medicines.map((med) => (
                  <div key={med.id} className="flex items-center justify-between p-3 rounded-xl bg-slate-950/70 border border-white/5">
                    <span className="font-bold text-white text-sm">{med.medicine_name} ({med.dosage})</span>
                    <span className={`px-2.5 py-0.5 rounded-full font-extrabold text-[10px] uppercase border ${
                      med.status === 'taken' 
                        ? 'bg-emerald-500/20 text-emerald-300 border-emerald-500/40' 
                        : med.status === 'snoozed'
                        ? 'bg-amber-500/20 text-amber-300 border-amber-500/40'
                        : 'bg-slate-800 text-slate-400 border-white/10'
                    }`}>
                      {med.status === 'taken' ? '✓ Taken' : med.status === 'snoozed' ? '⏰ Snoozed' : med.status}
                    </span>
                  </div>
                ))}
              </div>

              <button
                type="button"
                onClick={clearReminder}
                className="w-full py-4 rounded-2xl bg-emerald-600 hover:bg-emerald-500 text-white font-black text-lg shadow-lg shadow-emerald-600/30 transition-all cursor-pointer min-h-[52px]"
              >
                {strings.buttonDone || "Done"}
              </button>
            </motion.div>
          ) : (
            /* FOCUSED MEDICINE CAROUSEL CARD */
            <div className="space-y-5">
              <div
                onTouchStart={handleTouchStart}
                onTouchEnd={handleTouchEnd}
                className="relative overflow-hidden"
              >
                <AnimatePresence mode="wait">
                  <motion.div
                    key={activeMed?.id || currentIndex}
                    initial={{ opacity: 0, x: 20 }}
                    animate={{ opacity: 1, x: 0 }}
                    exit={{ opacity: 0, x: -20 }}
                    transition={{ duration: 0.18, ease: 'easeOut' }}
                  >
                    <ReminderContent medicine={activeMed} user={user} />
                  </motion.div>
                </AnimatePresence>
              </div>

              {/* Prominent Multi-Medicine Schedule List */}
              <div className="bg-slate-950/70 border border-blue-500/20 rounded-2xl p-3 sm:p-4 text-left space-y-2">
                <div className="text-xs font-extrabold uppercase tracking-wider text-blue-400 flex items-center justify-between">
                  <span>{strings.multipleMedicinesLabel || "Medicines to take at this time:"}</span>
                  <span className="text-slate-400 font-medium">({medicines.length})</span>
                </div>
                <div className="space-y-1.5" role="list">
                  {medicines.map((med, idx) => {
                    const isCurrent = idx === currentIndex;
                    const isDone = med.status === 'taken';
                    const isSnoozed = med.status === 'snoozed';
                    return (
                      <div
                        key={med.id || idx}
                        onClick={() => setCurrentIndex(idx)}
                        className={`p-2.5 rounded-xl border flex items-center justify-between gap-2 transition-all cursor-pointer ${
                          isCurrent
                            ? 'bg-blue-600/25 border-blue-400 text-white shadow-sm ring-1 ring-blue-400/40'
                            : isDone
                            ? 'bg-emerald-950/30 border-emerald-500/30 text-emerald-300'
                            : isSnoozed
                            ? 'bg-amber-950/30 border-amber-500/30 text-amber-300'
                            : 'bg-slate-900/60 border-white/5 text-slate-300 hover:bg-slate-900'
                        }`}
                      >
                        <div className="flex items-center gap-2 min-w-0">
                          <span className="text-base shrink-0">💊</span>
                          <span className="font-extrabold text-sm text-white truncate">
                            {med.medicine_name || med.title || strings.genericMedicine || 'Medicine'}
                          </span>
                          {med.dosage && (
                            <span className="text-xs text-slate-400 shrink-0 font-mono">({med.dosage})</span>
                          )}
                        </div>
                        <div className="shrink-0 text-xs font-bold">
                          {isDone ? (
                            <span className="text-emerald-400 flex items-center gap-1">
                              <Check className="w-3.5 h-3.5 stroke-[3]" /> Done
                            </span>
                          ) : isCurrent ? (
                            <span className="text-blue-400 uppercase text-[10px] tracking-wider font-extrabold">Active</span>
                          ) : isSnoozed ? (
                            <span className="text-amber-400 text-[11px]">Snoozed</span>
                          ) : (
                            <span className="text-slate-400 text-[11px]">View</span>
                          )}
                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>

              {/* Action Buttons for Active Medicine */}
              <ReminderButtons 
                onMarkTaken={() => handleMarkTakenSingle(activeMed)} 
                onSnooze={(mins) => handleSnoozeSingle(activeMed, mins)} 
                onSkip={() => handleSkipSingle(activeMed)} 
                loading={loadingId === activeMed.id}
                medicineName={activeMed.medicine_name}
                apiError={apiErrorId === activeMed.id}
                user={user}
              />

              {/* Carousel Navigation Controls */}
              <div className="flex items-center justify-between gap-3 pt-3 border-t border-slate-800">
                <button
                  type="button"
                  onClick={() => setCurrentIndex(prev => Math.max(0, prev - 1))}
                  disabled={currentIndex === 0}
                  className="flex-1 py-3 px-4 rounded-2xl bg-slate-900 hover:bg-slate-800 disabled:opacity-30 disabled:hover:bg-slate-900 text-slate-200 font-extrabold text-sm border border-slate-700/60 transition-all flex items-center justify-center gap-2 min-h-[48px] cursor-pointer"
                  aria-label="Previous Medicine"
                >
                  <ChevronLeft className={`w-5 h-5 text-blue-400 ${rtl ? 'rotate-180' : ''}`} />
                  <span>Previous</span>
                </button>

                <span className="text-xs font-extrabold text-slate-400 px-2 shrink-0">
                  {currentIndex + 1} / {medicines.length}
                </span>

                <button
                  type="button"
                  onClick={() => setCurrentIndex(prev => Math.min(medicines.length - 1, prev + 1))}
                  disabled={currentIndex === medicines.length - 1}
                  className="flex-1 py-3 px-4 rounded-2xl bg-slate-900 hover:bg-slate-800 disabled:opacity-30 disabled:hover:bg-slate-900 text-slate-200 font-extrabold text-sm border border-slate-700/60 transition-all flex items-center justify-center gap-2 min-h-[48px] cursor-pointer"
                  aria-label="Next Medicine"
                >
                  <span>Next</span>
                  <ChevronRight className={`w-5 h-5 text-blue-400 ${rtl ? 'rotate-180' : ''}`} />
                </button>
              </div>
            </div>
          )}
        </motion.div>
      </ReminderOverlay>
    </AnimatePresence>
  );
}

import { useContext, useEffect, useState, useRef } from 'react';
import { AnimatePresence, motion } from 'framer-motion';
import { ReminderContext } from '../../contexts/ReminderContext';
import { medicineApi } from '../../services/api';
import ReminderOverlay from './ReminderOverlay';
import ReminderHeader from './ReminderHeader';
import ReminderContent from './ReminderContent';
import ReminderButtons from './ReminderButtons';
import { ReminderSoundService } from '../../services/ReminderSoundService';
import { ReminderSpeechService } from '../../services/ReminderSpeechService';
import { BrowserNotificationService } from '../../services/BrowserNotificationService';

import { tts } from '../../services/tts';

export default function ReminderModal({ user }) {
  const { currentReminder, markTaken, clearReminder, snoozeReminder, skipReminder } = useContext(ReminderContext);
  const [loading, setLoading] = useState(false);
  
  const [showModal, setShowModal] = useState(false);
  const modalRef = useRef(null);

  useEffect(() => {
    if (currentReminder) {
      const runFlow = async () => {
        // 1. Play sound (awaits 1.2s max)
        await ReminderSoundService.play();
        
        // 2. Display modal
        setShowModal(true);
        
        // Focus modal if ref exists
        if (modalRef.current) {
          modalRef.current.focus();
        }

        // 3. Speak reminder
        await ReminderSpeechService.speak(currentReminder, user);
        
        // 4. Show browser notification
        BrowserNotificationService.notify(currentReminder);
      };
      runFlow();
    } else {
      setShowModal(false);
    }
  }, [currentReminder, user]);

  if (!showModal || !currentReminder) return null;

  const handleMarkTaken = async () => {
    setLoading(true);
    
    // Play voice before we unmount the modal
    tts.speak("Great. I've marked your medicine as taken.");
    
    window.dispatchEvent(new CustomEvent('orma:toast', { 
      detail: { type: 'success', message: '✓ Your medication has been recorded successfully.' } 
    }));

    await markTaken(currentReminder);
    // Modal will unmount because currentReminder becomes null
  };

  const handleSnooze = (minutes) => {
    snoozeReminder(currentReminder, minutes);
    const now = new Date();
    now.setMinutes(now.getMinutes() + minutes);
    const snoozeTime = now.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' });
    
    window.dispatchEvent(new CustomEvent('orma:toast', { 
      detail: { type: 'info', message: `Reminder snoozed until ${snoozeTime}` } 
    }));
  };

  const handleSkip = () => {
    skipReminder(currentReminder);
    window.dispatchEvent(new CustomEvent('orma:toast', { 
      detail: { type: 'info', message: 'This reminder has been skipped.' } 
    }));
  };

  // Prevent keyboard dismiss for Escape
  const handleKeyDown = (e) => {
    if (e.key === 'Escape') {
      e.preventDefault();
      e.stopPropagation();
    }
  };

  return (
    <AnimatePresence>
      <ReminderOverlay>
        <motion.div
          ref={modalRef}
          tabIndex="-1"
          onKeyDown={handleKeyDown}
          aria-labelledby="reminder-title"
          initial={{ scale: 0.95, opacity: 0, y: 20 }}
          animate={{ scale: 1, opacity: 1, y: 0 }}
          exit={{ scale: 0.95, opacity: 0, y: 20 }}
          className="orma-modal-content"
        >
          <ReminderHeader userName={user?.first_name || user?.name || 'User'} />
          <ReminderContent medicine={currentReminder} />
          <ReminderButtons 
            onMarkTaken={handleMarkTaken} 
            onSnooze={handleSnooze} 
            onSkip={handleSkip} 
            loading={loading}
          />
        </motion.div>
      </ReminderOverlay>
    </AnimatePresence>
  );
}

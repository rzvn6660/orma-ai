import { tts } from './tts';
import { getSpokenReminderSentence } from '../utils/reminderLocalization';
import { DEFAULT_REMINDER_LANGUAGE } from '../config/reminderLanguages';

export const ReminderSpeechService = {
  isEnabled: () => localStorage.getItem('orma_voice_enabled') !== 'false',
  
  toggle: (enabled) => localStorage.setItem('orma_voice_enabled', enabled),

  speak: async (medicine, user) => {
    if (!ReminderSpeechService.isEnabled()) return;
    
    // Role & preference enforcement for spoken alerts
    if (user) {
      const prefs = user.notification_preferences;
      if (user.role === 'caregiver') {
        // Spoken alerts for caregiver are OFF by default unless explicitly enabled
        if (!prefs || prefs.medication_spoken_alerts !== true) {
          return;
        }
      } else if (user.role === 'elderly') {
        if (prefs && prefs.medication_spoken_alerts === false) {
          return;
        }
      }
    }

    try {
      const prefs = user?.notification_preferences || {};
      const langCode = prefs.reminder_language || localStorage.getItem('orma_reminder_language') || DEFAULT_REMINDER_LANGUAGE;
      const userName = user?.first_name || user?.name || '';
      
      const isHealthEvent = medicine.event_type !== undefined;
      const eventType = isHealthEvent ? medicine.event_type : 'medicine';
      const title = isHealthEvent ? medicine.title : medicine.medicine_name;
      const description = isHealthEvent ? medicine.description : medicine.dosage;

      const sentence = getSpokenReminderSentence({
        langCode,
        userName,
        medicineName: title,
        dosage: description,
        purpose: medicine.purpose,
        eventType
      });

      return new Promise((resolve) => {
        tts.speak(sentence, {
          langCode,
          onEnd: resolve,
          onError: (err) => {
            console.warn('[ReminderSpeechService] TTS Error:', err);
            resolve();
          }
        });
      });
    } catch (err) {
      console.warn('[ReminderSpeechService] Failed to speak:', err);
    }
  }
};

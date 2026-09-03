import { getReminderStrings } from '../utils/reminderLocalization';
import { DEFAULT_REMINDER_LANGUAGE } from '../config/reminderLanguages';

export const BrowserNotificationService = {
  isEnabled: () => localStorage.getItem('orma_notification_enabled') !== 'false',
  
  toggle: (enabled) => localStorage.setItem('orma_notification_enabled', enabled),

  requestPermissionOnce: async () => {
    if (!('Notification' in window)) return false;
    
    if (localStorage.getItem('orma_notification_asked') === 'true') {
      return Notification.permission === 'granted';
    }

    try {
      localStorage.setItem('orma_notification_asked', 'true');
      const permission = await Notification.requestPermission();
      return permission === 'granted';
    } catch (err) {
      console.warn('[BrowserNotificationService] Failed to request permission:', err);
      return false;
    }
  },

  notify: async (medicine, user = null) => {
    if (!BrowserNotificationService.isEnabled()) return;
    if (!('Notification' in window)) return;

    // Role & preference enforcement
    if (user) {
      const prefs = user.notification_preferences;
      if (user.role === 'caregiver') {
        // Default caregiver value is OFF unless explicitly enabled
        if (!prefs || prefs.medication_reminder_notifications !== true) {
          return;
        }
      } else if (user.role === 'elderly') {
        if (prefs && prefs.medication_reminder_notifications === false) {
          return;
        }
      }
    }

    if (Notification.permission === 'default') {
       await BrowserNotificationService.requestPermissionOnce();
    }
    
    if (Notification.permission !== 'granted') return;

    try {
      const prefs = user?.notification_preferences || {};
      const langCode = prefs.reminder_language || localStorage.getItem('orma_reminder_language') || DEFAULT_REMINDER_LANGUAGE;
      const strings = getReminderStrings(langCode);

      const title = strings.browserTitle || '💊 Medication Reminder';
      const rawMedName = (medicine.medicine_name || medicine.title)?.trim();
      const hasMedName = Boolean(rawMedName);
      const medName = hasMedName ? rawMedName : (strings.genericMedicine || 'Medicine');
      const dosage = medicine.dosage || medicine.description || '';
      
      let body = '';
      if (hasMedName) {
        body = (strings.browserBody || "It's time to take {medName} {dosage}.")
          .replace('{medName}', medName)
          .replace('{dosage}', dosage ? `(${dosage})` : '')
          .trim();
      } else {
        body = strings.reminderHeadline || "It's time to take your medicine.";
      }

      const notification = new Notification(title, {
        body,
        icon: '/logo-transparent.png',
        requireInteraction: true
      });

      notification.onclick = () => {
        window.focus();
        notification.close();
      };
    } catch (err) {
      console.warn('[BrowserNotificationService] Failed to show notification:', err);
    }
  }
};

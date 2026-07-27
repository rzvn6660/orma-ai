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

  notify: async (medicine) => {
    if (!BrowserNotificationService.isEnabled()) return;
    if (!('Notification' in window)) return;

    if (Notification.permission === 'default') {
       await BrowserNotificationService.requestPermissionOnce();
    }
    
    if (Notification.permission !== 'granted') return;

    try {
      const notification = new Notification('💊 Medication Reminder', {
        body: `Time to take ${medicine.medicine_name} ${medicine.dosage}.`,
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

/**
 * notificationStorage.js
 * 
 * Persistent store for read notifications to ensure:
 * - Read notifications remain read across polling, navigation, reconnect, and refresh.
 * - No duplicate toasts or badges pop up for already-read alerts.
 */

const STORAGE_KEY = 'orma_read_notification_ids';

export const getReadNotificationIds = () => {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    return raw ? new Set(JSON.parse(raw)) : new Set();
  } catch {
    return new Set();
  }
};

export const markNotificationReadInStorage = (id) => {
  if (!id) return;
  try {
    const current = getReadNotificationIds();
    current.add(String(id));
    const list = Array.from(current).slice(-500); // cap at 500 entries
    localStorage.setItem(STORAGE_KEY, JSON.stringify(list));
  } catch (e) {
    console.warn('[NotificationStorage] Failed to write read id:', e);
  }
};

export const isNotificationReadInStorage = (id) => {
  if (!id) return false;
  const current = getReadNotificationIds();
  return current.has(String(id));
};

export const syncReadNotifications = (notifications = []) => {
  if (!Array.isArray(notifications) || notifications.length === 0) return;
  try {
    const current = getReadNotificationIds();
    let updated = false;
    for (const n of notifications) {
      if (n && n.id && n.is_read && !current.has(String(n.id))) {
        current.add(String(n.id));
        updated = true;
      }
    }
    if (updated) {
      const list = Array.from(current).slice(-500);
      localStorage.setItem(STORAGE_KEY, JSON.stringify(list));
    }
  } catch (e) {
    console.warn('[NotificationStorage] Sync error:', e);
  }
};

export const reconcileWithReadStorage = (notifications = []) => {
  if (!Array.isArray(notifications)) return [];
  const readIds = getReadNotificationIds();
  return notifications.map(n => {
    if (n && n.id && readIds.has(String(n.id))) {
      return { ...n, is_read: true };
    }
    return n;
  });
};

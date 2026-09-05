import { createContext, useContext, useEffect, useState, useRef } from 'react';
import { medicineApi, authApi } from '../services/api';

export const ReminderContext = createContext();

// Helper to generate a date string for the daily occurrence storage key
const getTodayDateKey = () => {
  const d = new Date();
  return `orma_triggered_${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`;
};

// Retrieve persisted triggered keys for today
const getPersistedTriggeredKeys = () => {
  try {
    const key = getTodayDateKey();
    const raw = sessionStorage.getItem(key) || localStorage.getItem(key);
    return raw ? new Set(JSON.parse(raw)) : new Set();
  } catch {
    return new Set();
  }
};

// Persist a newly triggered reminder occurrence
const persistTriggeredKey = (occurrenceKey) => {
  try {
    const storageKey = getTodayDateKey();
    const current = getPersistedTriggeredKeys();
    current.add(String(occurrenceKey));
    const serialized = JSON.stringify(Array.from(current));
    sessionStorage.setItem(storageKey, serialized);
    localStorage.setItem(storageKey, serialized);
  } catch (e) {
    console.warn('[ReminderContext] Storage write bypassed:', e);
  }
};

// Helper for date-scoped missed occurrence storage key
const getTodayMissedDateKey = () => {
  const d = new Date();
  return `orma_missed_${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`;
};

const getPersistedMissedKeys = () => {
  try {
    const key = getTodayMissedDateKey();
    const raw = sessionStorage.getItem(key) || localStorage.getItem(key);
    return raw ? new Set(JSON.parse(raw)) : new Set();
  } catch {
    return new Set();
  }
};

const persistMissedKey = (missedKey) => {
  try {
    const storageKey = getTodayMissedDateKey();
    const current = getPersistedMissedKeys();
    current.add(String(missedKey));
    const serialized = JSON.stringify(Array.from(current));
    sessionStorage.setItem(storageKey, serialized);
    localStorage.setItem(storageKey, serialized);
  } catch (e) {
    console.warn('[ReminderContext] Storage write bypassed:', e);
  }
};

// Remove a triggered reminder occurrence (e.g. on Snooze)
const removePersistedTriggeredKey = (occurrenceKey) => {
  try {
    const storageKey = getTodayDateKey();
    const current = getPersistedTriggeredKeys();
    current.delete(String(occurrenceKey));
    const serialized = JSON.stringify(Array.from(current));
    sessionStorage.setItem(storageKey, serialized);
    localStorage.setItem(storageKey, serialized);
  } catch (e) {
    console.warn('[ReminderContext] Storage remove bypassed:', e);
  }
};

export function ReminderProvider({ children }) {
  const [currentUser, setCurrentUser] = useState(null);
  const [pendingReminders, setPendingReminders] = useState([]);
  const [nextReminder, setNextReminder] = useState(null);
  const [currentReminder, setCurrentReminder] = useState(null);
  const [currentReminderGroup, setCurrentReminderGroup] = useState(null); // { scheduledTime: string, medicines: Array }
  const [timeline, setTimeline] = useState([]);
  
  const timerRef = useRef(null);
  // Initialized with persisted keys to prevent duplicate modals on browser refresh
  const triggeredSet = useRef(getPersistedTriggeredKeys());
  // Occurrence deduplication set for missed medication toasts and events (persisted across reloads/nav)
  const triggeredMissedSet = useRef(getPersistedMissedKeys());

  useEffect(() => {
    let isMounted = true;
    const fetchUser = async () => {
      try {
        const u = await authApi.getMe();
        if (isMounted && u) setCurrentUser(u);
      } catch (_err) {
        // no-op
      }
    };
    fetchUser();

    const handleUserUpdate = (e) => {
      if (e.detail) {
        setCurrentUser(prev => ({ ...prev, ...e.detail }));
      }
    };
    window.addEventListener('orma_user_updated', handleUserUpdate);
    return () => {
      isMounted = false;
      window.removeEventListener('orma_user_updated', handleUserUpdate);
    };
  }, []);

  const loadReminders = async () => {
    try {
      const allReminders = await medicineApi.getReminders();
      
      // Filter out medicines already taken or without a valid reminder_time
      const pending = allReminders.filter(med => !med.taken_status && med.reminder_time);
      
      // Sort by time
      pending.sort((a, b) => {
        const timeA = parseTime(a.reminder_time);
        const timeB = parseTime(b.reminder_time);
        return timeA - timeB;
      });

      setPendingReminders(pending);

      // Find the next one that hasn't passed yet
      const now = new Date();
      const currentMinutes = now.getHours() * 60 + now.getMinutes();
      
      const upcoming = pending.find(med => {
        const medTime = parseTime(med.reminder_time);
        const occurrenceKey = `${med.id}_${med.reminder_time}`;
        return medTime >= currentMinutes && !triggeredSet.current.has(occurrenceKey) && !triggeredSet.current.has(String(med.id));
      });

      if (upcoming) {
        setNextReminder(upcoming);
      } else {
        setNextReminder(null);
      }

      // Clear stale, deleted, or taken medicines from active modal
      if (currentRef.current && !pending.some(m => m.id === currentRef.current.id)) {
        setCurrentReminder(null);
      }
      if (currentGroupRef.current) {
        const activeIds = new Set(pending.map(m => m.id));
        const remainingGroupMeds = currentGroupRef.current.medicines.filter(m => activeIds.has(m.id));
        if (remainingGroupMeds.length === 0) {
          setCurrentReminderGroup(null);
        } else if (remainingGroupMeds.length !== currentGroupRef.current.medicines.length) {
          setCurrentReminderGroup(prev => prev ? ({ ...prev, medicines: remainingGroupMeds }) : null);
        }
      }
    } catch (err) {
      console.error('[Reminder] Error loading reminders:', err);
    }
  };

  const addTimelineEvent = (medicineId, event, medName = '') => {
    const time = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    setTimeline(prev => [...prev, { medicineId, medicineName: medName, event, time }]);
  };

  const parseTime = (timeStr) => {
    if (!timeStr) return 0;
    const match = timeStr.match(/(\d+):(\d+)\s*(AM|PM)?/i);
    if (!match) return 0;
    
    let hours = parseInt(match[1]);
    const minutes = parseInt(match[2]);
    const modifier = match[3]?.toUpperCase();

    if (modifier === 'PM' && hours < 12) hours += 12;
    if (modifier === 'AM' && hours === 12) hours = 0;

    return hours * 60 + minutes;
  };

  const pendingRef = useRef(pendingReminders);
  const currentRef = useRef(currentReminder);
  const currentGroupRef = useRef(currentReminderGroup);
  
  useEffect(() => {
    pendingRef.current = pendingReminders;
  }, [pendingReminders]);

  useEffect(() => {
    currentRef.current = currentReminder;
  }, [currentReminder]);

  useEffect(() => {
    currentGroupRef.current = currentReminderGroup;
  }, [currentReminderGroup]);

  const getOccurrenceKey = (med) => `${med.id}_${med.reminder_time}`;

  const checkScheduleWithRef = () => {
    if (pendingRef.current.length === 0) return;

    const now = new Date();
    const currentMinutes = now.getHours() * 60 + now.getMinutes();

    // 1. Check for Overdue (>30 minutes past scheduled time to match backend caregiver escalation window)
    const overdueReminders = pendingRef.current.filter(med => {
      const medTime = parseTime(med.reminder_time);
      return (currentMinutes - medTime) >= 30;
    });

    const todayDateKey = new Date().toISOString().slice(0, 10);

    overdueReminders.forEach(async (med) => {
      const missedKey = `missed_${med.id}_${todayDateKey}_${med.reminder_time}`;
      if (triggeredMissedSet.current.has(missedKey)) {
        return;
      }
      triggeredMissedSet.current.add(missedKey);
      persistMissedKey(missedKey);

      addTimelineEvent(med.id, 'Missed', med.medicine_name);
      
      // Remove from pending optimistically
      setPendingReminders(prev => prev.filter(p => p.id !== med.id));
      
      try {
        if (typeof med.id === 'number') {
          await medicineApi.missMedicine(med.id);
        }
      } catch(e) {
        console.error('Failed to mark miss:', e);
        setPendingReminders(prev => [...prev, med].sort((a,b) => parseTime(a.reminder_time) - parseTime(b.reminder_time)));
      }
      
      // If the modal was sitting open for this medicine, update session
      setCurrentReminderGroup(prev => {
        if (!prev) return null;
        const updated = prev.medicines.filter(p => p.id !== med.id);
        if (updated.length === 0) return null;
        return { ...prev, medicines: updated };
      });
      setCurrentReminder(prev => prev?.id === med.id ? null : prev);
      
      window.dispatchEvent(new CustomEvent('orma:toast', { 
        detail: { 
          id: missedKey,
          type: 'error', 
          message: `Medication "${med.medicine_name || 'scheduled'}" was marked as missed.` 
        } 
      }));
      window.dispatchEvent(new CustomEvent('orma:remindersUpdated'));
    });

    // If a modal or group session is already active, don't pop another one
    if (currentRef.current || currentGroupRef.current) {
      return;
    }

    // Role & preference check: Do not pop normal scheduled reminder modal for caregiver unless preference is enabled (default OFF)
    if (currentUser?.role === 'caregiver') {
      const isEnabled = currentUser?.notification_preferences?.medication_reminder_notifications === true;
      if (!isEnabled) return;
    }

    // 2. Trigger Due Reminders (Grouped by scheduled time)
    const dueReminder = pendingRef.current.find(med => {
      const occKey = getOccurrenceKey(med);
      if (triggeredSet.current.has(occKey) || triggeredSet.current.has(String(med.id))) return false;
      const medTime = parseTime(med.reminder_time);
      return currentMinutes >= medTime && (currentMinutes - medTime) < 30;
    });

    if (dueReminder) {
      // Find ALL pending medicines sharing the exact same reminder_time
      const dueGroup = pendingRef.current.filter(med => {
        const occKey = getOccurrenceKey(med);
        if (triggeredSet.current.has(occKey) || triggeredSet.current.has(String(med.id))) return false;
        return med.reminder_time === dueReminder.reminder_time;
      });

      triggerReminderGroup(dueGroup);
    }
  };

  const triggerReminderGroup = (dueGroup) => {
    if (!dueGroup || dueGroup.length === 0) return;

    // Persist occurrence keys for all medicines in this group immediately
    dueGroup.forEach(med => {
      const occKey = getOccurrenceKey(med);
      persistTriggeredKey(occKey);
      triggeredSet.current.add(occKey);

      addTimelineEvent(med.id, 'Reminder Triggered', med.medicine_name);
    });

    const scheduledTime = dueGroup[0].reminder_time;
    const groupSession = {
      sessionId: `session_${scheduledTime.replace(/\s+/g, '')}_${getTodayDateKey()}`,
      scheduledTime,
      medicines: dueGroup.map(med => ({
        ...med,
        status: 'pending' // 'pending' | 'taken' | 'snoozed' | 'skipped'
      }))
    };

    setCurrentReminderGroup(groupSession);
    setCurrentReminder(dueGroup[0]);
    loadReminders();
  };

  const triggerReminder = (reminder) => {
    triggerReminderGroup([reminder]);
  };

  const clearReminder = () => {
    setCurrentReminderGroup(null);
    setCurrentReminder(null);
    checkNextInQueue();
  };

  const checkNextInQueue = () => {
    setTimeout(() => {
      checkScheduleWithRef();
    }, 1200);
  };

  const markTaken = async (reminder) => {
    const occKey = getOccurrenceKey(reminder);
    persistTriggeredKey(occKey);
    addTimelineEvent(reminder.id, 'Taken', reminder.medicine_name);
    
    // Optimistically remove from pendingReminders
    setPendingReminders(prev => prev.filter(med => med.id !== reminder.id));

    // Update status in active group session
    setCurrentReminderGroup(prev => {
      if (!prev) return null;
      const updatedMeds = prev.medicines.map(m => m.id === reminder.id ? { ...m, status: 'taken' } : m);
      return { ...prev, medicines: updatedMeds };
    });
    
    try {
      await medicineApi.takeMedicine(reminder.id);
    } catch (err) {
      console.error('Failed to mark taken:', err);
      // Rollback
      setPendingReminders(prev => [...prev, reminder].sort((a,b) => parseTime(a.reminder_time) - parseTime(b.reminder_time)));
      removePersistedTriggeredKey(occKey);
      triggeredSet.current.delete(occKey);
      window.dispatchEvent(new CustomEvent('orma:toast', { 
        detail: { type: 'error', message: 'Unable to connect. Please try again.' } 
      }));
    }
    
    window.dispatchEvent(new CustomEvent('orma:remindersUpdated'));
  };

  const snoozeReminder = async (reminder, minutes = 10) => {
    const oldOccKey = getOccurrenceKey(reminder);
    addTimelineEvent(reminder.id, `Snoozed (${minutes}m)`, reminder.medicine_name);
    
    // Reschedule
    const now = new Date();
    now.setMinutes(now.getMinutes() + minutes);
    const newTime = now.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' });
    
    // Remove old occurrence key so new snooze time triggers cleanly
    removePersistedTriggeredKey(oldOccKey);
    triggeredSet.current.delete(oldOccKey);
    
    // Optimistic update in group session
    setCurrentReminderGroup(prev => {
      if (!prev) return null;
      const updatedMeds = prev.medicines.map(m => m.id === reminder.id ? { ...m, status: 'snoozed', reminder_time: newTime } : m);
      return { ...prev, medicines: updatedMeds };
    });

    setPendingReminders(prev => prev.map(med => med.id === reminder.id ? { ...med, reminder_time: newTime } : med));
    
    try {
      await medicineApi.snoozeMedicine(reminder.id, minutes);
    } catch(err) {
      console.error('Failed to snooze:', err);
      // Rollback snooze
      setPendingReminders(prev => {
        const reverted = prev.filter(p => p.id !== reminder.id);
        return [...reverted, reminder].sort((a,b) => parseTime(a.reminder_time) - parseTime(b.reminder_time));
      });
      persistTriggeredKey(oldOccKey);
      triggeredSet.current.add(oldOccKey);
      window.dispatchEvent(new CustomEvent('orma:toast', { 
        detail: { type: 'error', message: 'Unable to connect. Please try again.' } 
      }));
    }
    window.dispatchEvent(new CustomEvent('orma:remindersUpdated'));
  };

  const skipReminder = async (reminder) => {
    const occKey = getOccurrenceKey(reminder);
    persistTriggeredKey(occKey);
    addTimelineEvent(reminder.id, 'Skipped', reminder.medicine_name);
    
    setCurrentReminderGroup(prev => {
      if (!prev) return null;
      const updatedMeds = prev.medicines.map(m => m.id === reminder.id ? { ...m, status: 'skipped' } : m);
      return { ...prev, medicines: updatedMeds };
    });

    setPendingReminders(prev => prev.filter(med => med.id !== reminder.id));
    
    try {
      await medicineApi.skipMedicine(reminder.id);
    } catch (err) {
      console.error('Failed to skip:', err);
      // Rollback
      setPendingReminders(prev => [...prev, reminder].sort((a,b) => parseTime(a.reminder_time) - parseTime(b.reminder_time)));
      removePersistedTriggeredKey(occKey);
      triggeredSet.current.delete(occKey);
      window.dispatchEvent(new CustomEvent('orma:toast', { 
        detail: { type: 'error', message: 'Unable to connect. Please try again.' } 
      }));
    }
    
    window.dispatchEvent(new CustomEvent('orma:remindersUpdated'));
  };

  useEffect(() => {
    // 1. Synchronize triggered occurrences across multiple tabs
    const handleStorage = (e) => {
      if (e.key === getTodayDateKey()) {
        triggeredSet.current = getPersistedTriggeredKeys();
        loadReminders();
      }
    };

    // 2. Custom window events for instant local/WS update
    const handleRemindersUpdate = () => {
      loadReminders();
    };

    const handleWsMessage = (e) => {
      const msg = e.detail;
      if (!msg || !msg.type) return;
      if ([
        'medicine_created', 
        'medicine_updated', 
        'medicine_deleted', 
        'medicine_taken', 
        'medicine_snoozed', 
        'medicine_skipped', 
        'medicine_missed', 
        'reminders_updated'
      ].includes(msg.type)) {
        loadReminders();
      }
    };

    // 3. Tab visibility / Sleep / Focus Recovery
    const handleVisibilityChange = () => {
      if (document.visibilityState === 'visible') {
        triggeredSet.current = getPersistedTriggeredKeys();
        triggeredMissedSet.current = getPersistedMissedKeys();
        loadReminders();
        checkScheduleWithRef();
      }
    };

    window.addEventListener('storage', handleStorage);
    window.addEventListener('orma:remindersUpdated', handleRemindersUpdate);
    window.addEventListener('medicationUpdated', handleRemindersUpdate);
    window.addEventListener('orma_websocket_message', handleWsMessage);
    document.addEventListener('visibilitychange', handleVisibilityChange);
    window.addEventListener('focus', handleVisibilityChange);
    window.addEventListener('online', handleVisibilityChange);

    loadReminders();

    timerRef.current = setInterval(() => {
      checkScheduleWithRef();
    }, 15000);

    return () => {
      window.removeEventListener('storage', handleStorage);
      window.removeEventListener('orma:remindersUpdated', handleRemindersUpdate);
      window.removeEventListener('medicationUpdated', handleRemindersUpdate);
      window.removeEventListener('orma_websocket_message', handleWsMessage);
      document.removeEventListener('visibilitychange', handleVisibilityChange);
      window.removeEventListener('focus', handleVisibilityChange);
      window.removeEventListener('online', handleVisibilityChange);
      if (timerRef.current) {
        clearInterval(timerRef.current);
      }
    };
  }, []);

  return (
    <ReminderContext.Provider value={{
      currentReminder,
      currentReminderGroup,
      nextReminder,
      pendingReminders,
      timeline,
      triggerReminder,
      triggerReminderGroup,
      clearReminder,
      markTaken,
      snoozeReminder,
      skipReminder,
      addTimelineEvent,
      loadReminders
    }}>
      {children}
    </ReminderContext.Provider>
  );
}

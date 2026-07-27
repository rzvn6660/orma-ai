/* eslint-disable react-refresh/only-export-components */
import { createContext, useContext, useEffect, useState, useRef } from 'react';
import { medicineApi } from '../services/api';

export const ReminderContext = createContext();

export function ReminderProvider({ children }) {
  const [pendingReminders, setPendingReminders] = useState([]);
  const [nextReminder, setNextReminder] = useState(null);
  const [currentReminder, setCurrentReminder] = useState(null);
  const [timeline, setTimeline] = useState([]);
  
  const timerRef = useRef(null);
  const triggeredSet = useRef(new Set()); // To track which medicine IDs we've already triggered today

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
        return medTime >= currentMinutes && !triggeredSet.current.has(med.id);
      });

      if (upcoming) {
        setNextReminder(upcoming);
        console.log(`[Reminder] Next reminder ${upcoming.reminder_time}`);
      } else {
        setNextReminder(null);
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
    // Handle "08:00 AM" or "14:00"
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
  
  useEffect(() => {
    pendingRef.current = pendingReminders;
  }, [pendingReminders]);

  useEffect(() => {
    currentRef.current = currentReminder;
  }, [currentReminder]);

  const checkScheduleWithRef = () => {
    if (pendingRef.current.length === 0) return;

    const now = new Date();
    const currentMinutes = now.getHours() * 60 + now.getMinutes();

    // 1. Check for Missed (45 minutes past)
    const missedReminders = pendingRef.current.filter(med => {
      const medTime = parseTime(med.reminder_time);
      return (currentMinutes - medTime) >= 45;
    });

    missedReminders.forEach(async (med) => {
      console.log(`[Reminder] ${med.medicine_name} missed.`);
      addTimelineEvent(med.id, 'Missed', med.medicine_name);
      
      // Remove from pending optimistically
      setPendingReminders(prev => prev.filter(p => p.id !== med.id));
      
      try {
        await medicineApi.missMedicine(med.id);
      } catch(e) {
        // Rollback on miss failure is tricky since it's background, but we can restore it to pending.
        console.error('Failed to mark miss:', e);
        setPendingReminders(prev => [...prev, med].sort((a,b) => parseTime(a.reminder_time) - parseTime(b.reminder_time)));
      }
      
      // If the modal was sitting open for this medicine, close it
      setCurrentReminder(prev => prev?.id === med.id ? null : prev);
      
      window.dispatchEvent(new CustomEvent('orma:toast', { 
        detail: { type: 'error', message: 'This medication reminder was missed.' } 
      }));
      window.dispatchEvent(new CustomEvent('orma:remindersUpdated'));
    });

    // If a modal is already active, don't pop another one.
    // It will be processed via checkNextInQueue when the current one is closed.
    if (currentRef.current) {
      return;
    }

    // 2. Trigger Due Reminders
    const dueReminder = pendingRef.current.find(med => {
      if (triggeredSet.current.has(med.id)) return false;
      const medTime = parseTime(med.reminder_time);
      // Wait, ensure we only trigger if it's NOT missed (already handled above but due to state delays we double check)
      return currentMinutes >= medTime && (currentMinutes - medTime) < 45;
    });

    if (dueReminder) {
      triggerReminder(dueReminder);
    }
  };

  const triggerReminder = (reminder) => {
    console.log('[Reminder] Reminder triggered');
    setCurrentReminder(reminder);
    triggeredSet.current.add(reminder.id);
    addTimelineEvent(reminder.id, 'Reminder Triggered', reminder.medicine_name);
    loadReminders();
  };

  const clearReminder = () => {
    setCurrentReminder(null);
    checkNextInQueue();
  };

  const checkNextInQueue = () => {
    // Check queue slightly after closing modal
    setTimeout(() => {
      checkScheduleWithRef();
    }, 1500);
  };

  const markTaken = async (reminder) => {
    setCurrentReminder(null);
    addTimelineEvent(reminder.id, 'Taken', reminder.medicine_name);
    
    // Optimistically remove
    setPendingReminders(prev => prev.filter(med => med.id !== reminder.id));
    
    try {
      await medicineApi.takeMedicine(reminder.id);
    } catch (err) {
      console.error('Failed to mark taken:', err);
      // Rollback
      setPendingReminders(prev => [...prev, reminder].sort((a,b) => parseTime(a.reminder_time) - parseTime(b.reminder_time)));
      triggeredSet.current.delete(reminder.id);
      window.dispatchEvent(new CustomEvent('orma:toast', { 
        detail: { type: 'error', message: 'Unable to connect. Please try again.' } 
      }));
    }
    
    window.dispatchEvent(new CustomEvent('orma:remindersUpdated'));
    checkNextInQueue();
  };

  const snoozeReminder = async (reminder, minutes = 10) => {
    setCurrentReminder(null);
    addTimelineEvent(reminder.id, `Snoozed (${minutes}m)`, reminder.medicine_name);
    
    // Reschedule
    const now = new Date();
    now.setMinutes(now.getMinutes() + minutes);
    const newTime = now.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' });
    
    triggeredSet.current.delete(reminder.id);
    
    // Optimistic update
    const updatedPending = pendingReminders.map(med => {
      if (med.id === reminder.id) {
        return { ...med, reminder_time: newTime };
      }
      return med;
    });
    setPendingReminders(updatedPending);
    
    try {
      await medicineApi.snoozeMedicine(reminder.id, minutes);
    } catch(err) {
      console.error('Failed to snooze:', err);
      // Rollback snooze
      setPendingReminders(prev => {
        const reverted = prev.filter(p => p.id !== reminder.id);
        return [...reverted, reminder].sort((a,b) => parseTime(a.reminder_time) - parseTime(b.reminder_time));
      });
      window.dispatchEvent(new CustomEvent('orma:toast', { 
        detail: { type: 'error', message: 'Unable to connect. Please try again.' } 
      }));
    }
    window.dispatchEvent(new CustomEvent('orma:remindersUpdated'));
    checkNextInQueue();
  };

  const skipReminder = async (reminder) => {
    setCurrentReminder(null);
    addTimelineEvent(reminder.id, 'Skipped', reminder.medicine_name);
    
    setPendingReminders(prev => prev.filter(med => med.id !== reminder.id));
    
    try {
      await medicineApi.skipMedicine(reminder.id);
    } catch (err) {
      console.error('Failed to skip:', err);
      // Rollback
      setPendingReminders(prev => [...prev, reminder].sort((a,b) => parseTime(a.reminder_time) - parseTime(b.reminder_time)));
      triggeredSet.current.delete(reminder.id);
      window.dispatchEvent(new CustomEvent('orma:toast', { 
        detail: { type: 'error', message: 'Unable to connect. Please try again.' } 
      }));
    }
    
    window.dispatchEvent(new CustomEvent('orma:remindersUpdated'));
    checkNextInQueue();
  };

  useEffect(() => {
    console.log('[Reminder] Scheduler started');
    
    loadReminders();

    timerRef.current = setInterval(() => {
      checkScheduleWithRef();
    }, 30000);

    return () => {
      console.log('[Reminder] Scheduler stopped');
      if (timerRef.current) {
        clearInterval(timerRef.current);
      }
    };
  }, []);

  return (
    <ReminderContext.Provider value={{
      currentReminder,
      nextReminder,
      pendingReminders,
      timeline,
      triggerReminder,
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

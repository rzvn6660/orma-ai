import React, { useState, useEffect, useCallback } from 'react';
import { healthPlannerApi, medicineApi } from '../services/api';
import OrmaCalendar from '../components/calendar/OrmaCalendar';
import ErrorBoundary from '../components/ErrorBoundary';

export default function CalendarPage({ user, onViewChange }) {
  const [events, setEvents] = useState([]);
  const [medicines, setMedicines] = useState([]);
  const [loading, setLoading] = useState(true);

  const fetchEvents = useCallback(async () => {
    try {
      setLoading(true);
      const [eventsData, medsData] = await Promise.allSettled([
        healthPlannerApi.getEvents(),
        (medicineApi.getReminders ? medicineApi.getReminders() : medicineApi.getMedicines())
      ]);
      
      if (eventsData.status === 'fulfilled') {
        setEvents(Array.isArray(eventsData.value) ? eventsData.value : []);
      }
      if (medsData.status === 'fulfilled') {
        setMedicines(Array.isArray(medsData.value) ? medsData.value : []);
      }
    } catch (err) {
      console.error('Failed to fetch calendar events:', err);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchEvents();
    const handleUpdates = () => fetchEvents();
    const handleVisibility = () => {
      if (document.visibilityState === 'visible') fetchEvents();
    };

    window.addEventListener('orma:plannerUpdated', handleUpdates);
    window.addEventListener('orma_websocket_message', handleUpdates);
    window.addEventListener('orma:medicinesUpdated', handleUpdates);
    window.addEventListener('orma:remindersUpdated', handleUpdates);
    window.addEventListener('medicationUpdated', handleUpdates);
    document.addEventListener('visibilitychange', handleVisibility);
    window.addEventListener('focus', handleVisibility);

    return () => {
      window.removeEventListener('orma:plannerUpdated', handleUpdates);
      window.removeEventListener('orma_websocket_message', handleUpdates);
      window.removeEventListener('orma:medicinesUpdated', handleUpdates);
      window.removeEventListener('orma:remindersUpdated', handleUpdates);
      window.removeEventListener('medicationUpdated', handleUpdates);
      document.removeEventListener('visibilitychange', handleVisibility);
      window.removeEventListener('focus', handleVisibility);
    };
  }, [fetchEvents]);

  const handleCompleteEvent = async (id) => {
    try {
      await healthPlannerApi.completeEvent(id);
      fetchEvents();
    } catch (err) {
      console.error('Failed to mark event complete:', err);
    }
  };

  const handleDeleteEvent = async (id) => {
    try {
      await healthPlannerApi.deleteEvent(id);
      fetchEvents();
    } catch (err) {
      console.error('Failed to delete scheduled event:', err);
    }
  };

  return (
    <ErrorBoundary>
      <div className="w-full max-w-7xl mx-auto pb-12">
        <OrmaCalendar
          events={events}
          medicines={medicines}
          user={user}
          mode={user?.role === 'caregiver' ? 'caregiver' : 'elderly'}
          onCompleteEvent={handleCompleteEvent}
          onDeleteEvent={handleDeleteEvent}
          onRefreshEvents={fetchEvents}
        />
      </div>
    </ErrorBoundary>
  );
}

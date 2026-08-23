import React, { useState, useMemo } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  ChevronLeft, 
  ChevronRight, 
  Plus, 
  Calendar as CalendarIcon, 
  Stethoscope, 
  Droplet, 
  Syringe, 
  HeartPulse, 
  Activity, 
  MapPin, 
  User, 
  Clock, 
  Check, 
  Trash2, 
  Bell, 
  CheckCircle2,
  Pill,
  Building2,
  Edit2,
  CalendarCheck,
  AlertCircle
} from 'lucide-react';
import HealthEventModal from './HealthEventModal';
import { formatToDateKey, formatFriendlyDate } from './OrmaDatePicker';

const EVENT_TYPE_ICONS = {
  doctor_appointment: Stethoscope,
  hospital_visit: Building2,
  blood_test: Droplet,
  custom_reminder: CalendarIcon,
  exercise: Activity,
  vaccination: Syringe,
  blood_pressure_check: HeartPulse,
  blood_sugar_check: Activity,
  medicine: Pill
};

export default function OrmaCalendar({
  events = [],
  medicines = [],
  onCompleteEvent,
  onDeleteEvent,
  onRefreshEvents,
  user,
  mode = 'elderly', // 'caregiver' | 'elderly'
  className = ''
}) {
  const [currentDate, setCurrentDate] = useState(new Date());
  const [selectedDateKey, setSelectedDateKey] = useState(formatToDateKey(new Date()));
  const [viewMode, setViewMode] = useState('month'); // 'month' | 'agenda'
  const [activeFilter, setActiveFilter] = useState('all');
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [eventToEdit, setEventToEdit] = useState(null);
  const [eventToDeleteId, setEventToDeleteId] = useState(null);

  const year = currentDate.getFullYear();
  const month = currentDate.getMonth();

  const monthNames = [
    'January', 'February', 'March', 'April', 'May', 'June',
    'July', 'August', 'September', 'October', 'November', 'December'
  ];

  const handlePrevMonth = () => {
    setCurrentDate(new Date(year, month - 1, 1));
  };

  const handleNextMonth = () => {
    setCurrentDate(new Date(year, month + 1, 1));
  };

  const handleToday = () => {
    const today = new Date();
    setCurrentDate(today);
    setSelectedDateKey(formatToDateKey(today));
  };

  const todayKey = formatToDateKey(new Date());

  // Map health planner events by date key
  const eventsByDate = useMemo(() => {
    const map = {};
    if (Array.isArray(events)) {
      events.forEach((evt) => {
        let dateKey = evt.event_date;
        if (!dateKey && evt.completed_at) {
          dateKey = evt.completed_at.split('T')[0];
        }
        if (!dateKey) {
          dateKey = formatToDateKey(new Date());
        }
        if (!map[dateKey]) map[dateKey] = [];
        map[dateKey].push(evt);
      });
    }
    return map;
  }, [events]);

  // Generate calendar days grid starting with Monday
  const firstDay = new Date(year, month, 1).getDay(); // 0 is Sun
  const firstDayIndex = (firstDay + 6) % 7; // Convert Sun(0)->6, Mon(1)->0, Tue(2)->1
  const totalDays = new Date(year, month + 1, 0).getDate();

  const daysGrid = [];
  for (let i = 0; i < firstDayIndex; i++) {
    daysGrid.push(null);
  }
  for (let d = 1; d <= totalDays; d++) {
    daysGrid.push(d);
  }

  // Calculate metrics for TODAY
  const todayMetrics = useMemo(() => {
    const todayAppointments = (eventsByDate[todayKey] || []).filter(
      e => e.event_type === 'doctor_appointment' || e.event_type === 'hospital_visit'
    );
    const todayTests = (eventsByDate[todayKey] || []).filter(
      e => e.event_type === 'blood_test' || e.event_type === 'blood_sugar_check' || e.event_type === 'blood_pressure_check'
    );
    const medsCount = Array.isArray(medicines) ? medicines.length : 0;
    const takenMedsCount = Array.isArray(medicines) ? medicines.filter(m => m.taken_status).length : 0;

    return {
      medsCount,
      takenMedsCount,
      appointmentsCount: todayAppointments.length,
      testsCount: todayTests.length,
      hasAny: medsCount > 0 || todayAppointments.length > 0 || todayTests.length > 0
    };
  }, [eventsByDate, todayKey, medicines]);

  // Build unified items for selected day (Appointments + Medical Tests + Medications if today or recurring)
  const selectedDayItems = useMemo(() => {
    const dayEvents = eventsByDate[selectedDateKey] || [];
    let items = [];

    // Add health events
    dayEvents.forEach(e => {
      let cat = 'appointments';
      if (e.event_type === 'blood_test' || e.event_type === 'blood_sugar_check' || e.event_type === 'blood_pressure_check') {
        cat = 'tests';
      } else if (e.event_type === 'custom_reminder') {
        cat = 'followups';
      }
      items.push({
        id: `evt-${e.id}`,
        rawId: e.id,
        category: cat,
        type: e.event_type,
        title: e.title,
        time: e.reminder_time || 'Scheduled',
        description: e.description,
        location: e.location,
        notes: e.notes,
        reminderPref: e.reminder_timing_preference,
        isCompleted: Boolean(e.status),
        isMedicine: false,
        rawEvent: e
      });
    });

    // If today is selected (or any date with medicine schedule), include medications
    if (selectedDateKey === todayKey && Array.isArray(medicines)) {
      medicines.forEach(m => {
        items.push({
          id: `med-${m.id}`,
          rawId: m.id,
          category: 'medicines',
          type: 'medicine',
          title: m.medicine_name,
          dosage: m.dosage,
          time: m.reminder_time || 'Daily',
          isCompleted: Boolean(m.taken_status),
          isMedicine: true,
          statusText: m.taken_status ? 'Taken' : 'Scheduled'
        });
      });
    }

    // Filter by active category
    if (activeFilter !== 'all') {
      items = items.filter(it => it.category === activeFilter);
    }

    // Sort chronologically
    return items.sort((a, b) => (a.time || '').localeCompare(b.time || ''));
  }, [eventsByDate, selectedDateKey, todayKey, medicines, activeFilter]);

  // Next upcoming appointment (within next 14 days)
  const nextAppointment = useMemo(() => {
    if (!Array.isArray(events)) return null;
    const upcoming = events
      .filter(evt => {
        const dKey = evt.event_date || (evt.completed_at ? evt.completed_at.split('T')[0] : null);
        return dKey && dKey >= todayKey && !evt.status;
      })
      .sort((a, b) => (a.event_date || '').localeCompare(b.event_date || ''));
    return upcoming.length > 0 ? upcoming[0] : null;
  }, [events, todayKey]);

  // Upcoming appointments in the next 14 days
  const upcomingEvents = useMemo(() => {
    if (!Array.isArray(events)) return [];
    return events
      .filter(evt => {
        const dKey = evt.event_date || (evt.completed_at ? evt.completed_at.split('T')[0] : null);
        return dKey && dKey >= todayKey && !evt.status;
      })
      .sort((a, b) => (a.event_date || '').localeCompare(b.event_date || ''))
      .slice(0, 4);
  }, [events, todayKey]);

  const confirmDelete = (id) => {
    setEventToDeleteId(id);
  };

  const handleExecuteDelete = () => {
    if (eventToDeleteId && onDeleteEvent) {
      onDeleteEvent(eventToDeleteId);
      setEventToDeleteId(null);
    }
  };

  return (
    <div className={`space-y-6 ${className}`}>
      
      {/* 1. Header Toolbar */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 bg-slate-900/70 backdrop-blur-xl border border-white/10 p-5 sm:p-6 rounded-3xl shadow-lg">
        <div className="flex items-center gap-3.5">
          <div className="w-11 h-11 rounded-2xl bg-blue-600/20 border border-blue-500/30 flex items-center justify-center text-blue-400 shadow-md shrink-0">
            <CalendarIcon className="w-6 h-6" />
          </div>
          <div>
            <h1 className="text-xl sm:text-2xl font-extrabold text-white tracking-tight">
              Calendar
            </h1>
            <p className="text-xs sm:text-sm text-slate-400 mt-0.5">
              Your appointments, medicines, and healthcare schedule.
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2.5 flex-wrap">
          <button
            type="button"
            onClick={handleToday}
            className="px-3.5 py-2 rounded-xl bg-slate-950/70 hover:bg-slate-800 border border-white/10 text-xs font-bold text-slate-200 hover:text-white transition-colors cursor-pointer"
          >
            Today
          </button>

          {/* Month / Agenda Switcher */}
          <div className="flex items-center p-1 bg-slate-950/70 border border-white/10 rounded-xl">
            <button
              type="button"
              onClick={() => setViewMode('month')}
              className={`px-3 py-1.5 rounded-lg text-xs font-bold transition-all cursor-pointer ${
                viewMode === 'month' ? 'bg-blue-600 text-white shadow-sm' : 'text-slate-400 hover:text-white'
              }`}
            >
              Month View
            </button>
            <button
              type="button"
              onClick={() => setViewMode('agenda')}
              className={`px-3 py-1.5 rounded-lg text-xs font-bold transition-all cursor-pointer ${
                viewMode === 'agenda' ? 'bg-blue-600 text-white shadow-sm' : 'text-slate-400 hover:text-white'
              }`}
            >
              Agenda View
            </button>
          </div>

          <button
            type="button"
            onClick={() => { setEventToEdit(null); setIsModalOpen(true); }}
            className="px-4 py-2 rounded-xl bg-blue-600 hover:bg-blue-500 text-white text-xs font-bold shadow-md shadow-blue-600/20 transition-all flex items-center gap-1.5 cursor-pointer ml-auto sm:ml-0"
          >
            <Plus className="w-4 h-4" />
            <span>Add Event</span>
          </button>
        </div>
      </div>

      {/* 2. Today's Summary & Next Appointment Row */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {/* Metric 1: Today's Medicines */}
        <div className="orma-card p-4 flex items-center gap-3.5">
          <div className="w-10 h-10 rounded-2xl bg-blue-600/20 border border-blue-500/30 flex items-center justify-center text-blue-400 shrink-0">
            <Pill className="w-5 h-5" />
          </div>
          <div>
            <span className="text-[11px] font-bold uppercase tracking-wider text-slate-400 block">
              Today's Medicines
            </span>
            <p className="text-sm font-extrabold text-white">
              {todayMetrics.medsCount > 0 
                ? `${todayMetrics.medsCount} Scheduled (${todayMetrics.takenMedsCount} Taken)`
                : 'No medicines today'}
            </p>
          </div>
        </div>

        {/* Metric 2: Today's Appointments & Tests */}
        <div className="orma-card p-4 flex items-center gap-3.5">
          <div className="w-10 h-10 rounded-2xl bg-amber-500/20 border border-amber-500/30 flex items-center justify-center text-amber-400 shrink-0">
            <Stethoscope className="w-5 h-5" />
          </div>
          <div>
            <span className="text-[11px] font-bold uppercase tracking-wider text-slate-400 block">
              Today's Clinical Events
            </span>
            <p className="text-sm font-extrabold text-white">
              {todayMetrics.appointmentsCount + todayMetrics.testsCount > 0
                ? `${todayMetrics.appointmentsCount} Appointment · ${todayMetrics.testsCount} Test`
                : 'No clinical visits today'}
            </p>
          </div>
        </div>

        {/* Metric 3: Next Appointment Highlight */}
        <div className="orma-card p-4 flex items-center justify-between gap-3">
          <div className="flex items-center gap-3.5 min-w-0">
            <div className="w-10 h-10 rounded-2xl bg-cyan-600/20 border border-cyan-500/30 flex items-center justify-center text-cyan-400 shrink-0">
              <CalendarCheck className="w-5 h-5" />
            </div>
            <div className="min-w-0">
              <span className="text-[11px] font-bold uppercase tracking-wider text-slate-400 block">
                Next Appointment
              </span>
              <p className="text-sm font-extrabold text-white truncate">
                {nextAppointment ? nextAppointment.title : 'No upcoming appointments'}
              </p>
              {nextAppointment && (
                <p className="text-xs text-cyan-300 font-mono">
                  {formatFriendlyDate(nextAppointment.event_date)} · {nextAppointment.reminder_time}
                </p>
              )}
            </div>
          </div>
          {nextAppointment && (
            <button
              type="button"
              onClick={() => setSelectedDateKey(nextAppointment.event_date)}
              className="text-xs font-bold text-blue-400 hover:text-blue-300 transition-colors shrink-0 cursor-pointer"
            >
              View →
            </button>
          )}
        </div>
      </div>

      {/* 3. Month Navigation Bar */}
      <div className="flex items-center justify-between px-2">
        <h2 className="text-lg sm:text-xl font-bold text-white tracking-tight">
          {monthNames[month]} {year}
        </h2>

        <div className="flex items-center gap-1.5">
          <button
            type="button"
            onClick={handlePrevMonth}
            className="p-2 rounded-xl bg-slate-900 border border-white/10 hover:border-white/20 text-slate-300 hover:text-white transition-colors cursor-pointer"
            aria-label="Previous month"
          >
            <ChevronLeft className="w-4 h-4" />
          </button>
          <button
            type="button"
            onClick={handleNextMonth}
            className="p-2 rounded-xl bg-slate-900 border border-white/10 hover:border-white/20 text-slate-300 hover:text-white transition-colors cursor-pointer"
            aria-label="Next month"
          >
            <ChevronRight className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* 4. Main View: Month Calendar (Left) + Selected Day Agenda (Right) */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        
        {/* Month Calendar Grid (7 cols) */}
        {viewMode === 'month' && (
          <div className="lg:col-span-7 orma-card p-5 sm:p-6 flex flex-col justify-between">
            <div>
              {/* Day of Week Headers starting on Monday */}
              <div className="grid grid-cols-7 gap-1.5 sm:gap-2 text-center mb-3">
                {['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'].map((wd) => (
                  <div key={wd} className="text-xs font-extrabold uppercase text-slate-400 py-1">
                    {wd}
                  </div>
                ))}
              </div>

              {/* Days Grid */}
              <div className="grid grid-cols-7 gap-1.5 sm:gap-2">
                {daysGrid.map((day, idx) => {
                  if (day === null) {
                    return <div key={`pad-${idx}`} className="h-12 sm:h-14 rounded-2xl bg-transparent" />;
                  }

                  const dayKey = `${year}-${String(month + 1).padStart(2, '0')}-${String(day).padStart(2, '0')}`;
                  const isSelected = selectedDateKey === dayKey;
                  const isToday = todayKey === dayKey;
                  const dayEvents = eventsByDate[dayKey] || [];
                  const hasMeds = isToday && medicines.length > 0;
                  const hasEvents = dayEvents.length > 0 || hasMeds;

                  return (
                    <button
                      key={dayKey}
                      type="button"
                      onClick={() => setSelectedDateKey(dayKey)}
                      className={`h-12 sm:h-14 rounded-2xl p-1.5 flex flex-col items-center justify-between border transition-all cursor-pointer relative ${
                        isSelected
                          ? 'bg-blue-600/30 border-blue-400 shadow-[0_0_15px_rgba(59,130,246,0.3)] text-white'
                          : isToday
                          ? 'bg-slate-900 border-cyan-500/40 text-cyan-300'
                          : hasEvents
                          ? 'bg-slate-950/70 border-white/10 hover:border-white/20 text-slate-200'
                          : 'bg-slate-950/30 border-transparent hover:bg-slate-900/50 text-slate-400'
                      }`}
                    >
                      <span className={`text-xs font-bold ${isSelected ? 'text-white' : isToday ? 'text-cyan-400 font-extrabold' : 'text-slate-300'}`}>
                        {day}
                      </span>

                      {/* Event Dot Indicators */}
                      <div className="flex items-center gap-1 min-h-[6px]">
                        {hasMeds && (
                          <span className="w-1.5 h-1.5 rounded-full bg-blue-400 shadow-sm" title="Medications" />
                        )}
                        {dayEvents.slice(0, 2).map((evt, eIdx) => {
                          const isDoc = evt.event_type === 'doctor_appointment' || evt.event_type === 'hospital_visit';
                          const isTest = evt.event_type === 'blood_test';
                          const dotColor = isDoc ? 'bg-amber-400' : isTest ? 'bg-cyan-400' : 'bg-emerald-400';
                          return (
                            <span 
                              key={evt.id || eIdx} 
                              className={`w-1.5 h-1.5 rounded-full ${dotColor} shadow-sm`} 
                            />
                          );
                        })}
                        {(dayEvents.length + (hasMeds ? 1 : 0)) > 3 && (
                          <span className="text-[9px] font-mono text-slate-400 leading-none">+</span>
                        )}
                      </div>
                    </button>
                  );
                })}
              </div>
            </div>

            {/* Calendar Legend */}
            <div className="mt-6 pt-4 border-t border-white/5 flex items-center justify-center gap-4 text-[11px] text-slate-400 flex-wrap">
              <div className="flex items-center gap-1.5">
                <span className="w-2 h-2 rounded-full bg-blue-400" />
                <span>Medications</span>
              </div>
              <div className="flex items-center gap-1.5">
                <span className="w-2 h-2 rounded-full bg-amber-400" />
                <span>Doctor Visits</span>
              </div>
              <div className="flex items-center gap-1.5">
                <span className="w-2 h-2 rounded-full bg-cyan-400" />
                <span>Medical Tests</span>
              </div>
              <div className="flex items-center gap-1.5">
                <span className="w-2 h-2 rounded-full bg-emerald-400" />
                <span>Follow-ups</span>
              </div>
            </div>
          </div>
        )}

        {/* Selected-Day Agenda (5 cols on Month View, 12 cols on Agenda View) */}
        <div className={`${viewMode === 'month' ? 'lg:col-span-5' : 'lg:col-span-12'} orma-card p-5 sm:p-6 flex flex-col justify-between`}>
          <div>
            {/* Agenda Header */}
            <div className="flex items-center justify-between mb-4 pb-3 border-b border-white/10">
              <div>
                <span className="text-[10px] font-extrabold uppercase tracking-wider text-blue-400 block mb-0.5">
                  Healthcare Schedule
                </span>
                <h3 className="text-base sm:text-lg font-bold text-white tracking-tight">
                  {formatFriendlyDate(selectedDateKey)}
                </h3>
              </div>

              <span className="text-xs font-bold text-slate-300 bg-slate-950/70 px-2.5 py-1 rounded-xl border border-white/10">
                {selectedDayItems.length} {selectedDayItems.length === 1 ? 'item' : 'items'}
              </span>
            </div>

            {/* Filter Pills */}
            <div className="flex items-center gap-1.5 overflow-x-auto custom-scrollbar pb-2 mb-4">
              {[
                { id: 'all', label: 'All Schedule' },
                { id: 'medicines', label: 'Medicines' },
                { id: 'appointments', label: 'Appointments' },
                { id: 'tests', label: 'Medical Tests' },
                { id: 'followups', label: 'Follow-ups' },
              ].map((flt) => (
                <button
                  key={flt.id}
                  type="button"
                  onClick={() => setActiveFilter(flt.id)}
                  className={`px-2.5 py-1 rounded-xl text-xs font-bold transition-colors shrink-0 cursor-pointer ${
                    activeFilter === flt.id
                      ? 'bg-blue-600/30 text-blue-300 border border-blue-500/40'
                      : 'bg-slate-950/50 text-slate-400 hover:text-slate-200 border border-white/5'
                  }`}
                >
                  {flt.label}
                </button>
              ))}
            </div>

            {/* Items Chronological Agenda Feed */}
            {selectedDayItems.length > 0 ? (
              <div className="relative space-y-3">
                {/* Vertical Timeline Track */}
                <div 
                  className="absolute left-4 -translate-x-1/2 top-4 bottom-4 w-[2px] bg-slate-800 pointer-events-none" 
                  aria-hidden="true" 
                />

                {selectedDayItems.map((item) => {
                  const Icon = EVENT_TYPE_ICONS[item.type] || CalendarIcon;

                  return (
                    <motion.div
                      key={item.id}
                      initial={{ opacity: 0, x: -6 }}
                      animate={{ opacity: 1, x: 0 }}
                      className="relative flex items-start gap-3.5 sm:gap-4 group"
                    >
                      {/* Fixed Node Column */}
                      <div className="w-8 flex items-center justify-center shrink-0 pt-0.5">
                        <div className={`relative z-10 w-7 h-7 sm:w-8 sm:h-8 rounded-full border-2 flex items-center justify-center shrink-0 shadow-sm ${
                          item.isCompleted
                            ? 'bg-emerald-500/20 border-emerald-500/50 text-emerald-400'
                            : item.isMedicine
                            ? 'bg-blue-500/20 border-blue-500/50 text-blue-400'
                            : 'bg-amber-500/20 border-amber-500/50 text-amber-400'
                        }`}>
                          <Icon className="w-3.5 h-3.5" />
                        </div>
                      </div>

                      {/* Event/Med Details Card */}
                      <div className="flex-1 min-w-0 rounded-2xl bg-slate-950/60 border border-white/10 p-3.5 backdrop-blur-xl transition-colors hover:border-white/20">
                        <div className="flex items-start justify-between gap-2 mb-1">
                          <div>
                            <span className="text-[11px] font-mono font-bold text-slate-300 bg-slate-900 px-2 py-0.5 rounded-md border border-white/5 mr-2">
                              {item.time}
                            </span>
                            <h4 className={`text-sm font-bold inline ${item.isCompleted && !item.isMedicine ? 'text-slate-400 line-through' : 'text-white'}`}>
                              {item.title} {item.dosage ? `(${item.dosage})` : ''}
                            </h4>
                          </div>

                          {/* Completed Status Badge */}
                          {item.isCompleted && (
                            <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-[10px] font-bold bg-emerald-500/10 text-emerald-400 border border-emerald-500/25 shrink-0">
                              <Check className="w-3 h-3" /> Taken / Done
                            </span>
                          )}
                        </div>

                        {/* Provider & Location Subtitle */}
                        <div className="text-xs text-slate-400 space-y-0.5 mt-1">
                          {item.description && (
                            <div className="flex items-center gap-1.5 text-slate-300">
                              <User className="w-3 h-3 text-slate-500" />
                              <span>{item.description}</span>
                            </div>
                          )}
                          {item.location && (
                            <div className="flex items-center gap-1.5">
                              <MapPin className="w-3 h-3 text-slate-500" />
                              <span>{item.location}</span>
                            </div>
                          )}
                          {item.reminderPref && (
                            <div className="flex items-center gap-1.5 text-[11px] text-blue-400">
                              <Bell className="w-3 h-3" />
                              <span>Reminder: {item.reminderPref}</span>
                            </div>
                          )}
                          {item.notes && (
                            <p className="text-[11px] text-slate-400 bg-slate-900/60 p-2 rounded-xl border border-white/5 mt-1.5 italic">
                              "{item.notes}"
                            </p>
                          )}
                        </div>

                        {/* Action Buttons for non-medicine health events */}
                        {!item.isMedicine && (
                          <div className="flex items-center justify-end gap-2 mt-3 pt-2 border-t border-white/5">
                            {!item.isCompleted && onCompleteEvent && (
                              <button
                                type="button"
                                onClick={() => onCompleteEvent(item.rawId)}
                                className="px-3 py-1 rounded-xl bg-emerald-600/20 hover:bg-emerald-600/30 text-emerald-300 border border-emerald-500/30 text-xs font-bold transition-all flex items-center gap-1 cursor-pointer"
                              >
                                <Check className="w-3 h-3" /> Mark Completed
                              </button>
                            )}
                            <button
                              type="button"
                              onClick={() => { setEventToEdit(item.rawEvent); setIsModalOpen(true); }}
                              className="p-1.5 rounded-xl text-slate-400 hover:text-white hover:bg-white/10 transition-colors cursor-pointer"
                              title="Edit Event"
                            >
                              <Edit2 className="w-3.5 h-3.5" />
                            </button>
                            {onDeleteEvent && (
                              <button
                                type="button"
                                onClick={() => confirmDelete(item.rawId)}
                                className="p-1.5 rounded-xl text-slate-500 hover:text-red-400 hover:bg-red-500/10 transition-colors cursor-pointer"
                                title="Delete Event"
                              >
                                <Trash2 className="w-3.5 h-3.5" />
                              </button>
                            )}
                          </div>
                        )}
                      </div>
                    </motion.div>
                  );
                })}
              </div>
            ) : (
              <div className="p-8 text-center border border-dashed border-white/10 rounded-2xl bg-slate-950/30 my-4">
                <CalendarIcon className="w-8 h-8 text-slate-500 mx-auto mb-2" />
                <p className="text-sm font-bold text-white">Nothing scheduled for this day.</p>
                <p className="text-xs text-slate-400 max-w-xs mx-auto mt-1 mb-4">
                  Your schedule is clear.
                </p>
                <button
                  type="button"
                  onClick={() => { setEventToEdit(null); setIsModalOpen(true); }}
                  className="px-4 py-2 rounded-xl bg-blue-600 hover:bg-blue-500 text-white text-xs font-bold transition-all inline-flex items-center gap-1.5 cursor-pointer shadow-md"
                >
                  <Plus className="w-3.5 h-3.5" />
                  <span>Add Event</span>
                </button>
              </div>
            )}
          </div>

          <div className="pt-3 border-t border-white/5 flex items-center justify-between text-xs text-slate-500">
            <span>Healthcare & Care Coordination</span>
            <span className="font-mono">Live Sync</span>
          </div>
        </div>

      </div>

      {/* 5. Upcoming Healthcare Schedule (Next 14 Days) */}
      {upcomingEvents.length > 0 && (
        <div className="orma-card p-5 sm:p-6">
          <div className="flex items-center justify-between mb-4 pb-2 border-b border-white/10">
            <div className="flex items-center gap-2.5">
              <div className="w-8 h-8 rounded-xl bg-amber-500/15 border border-amber-500/30 flex items-center justify-center text-amber-400">
                <Clock className="w-4 h-4" />
              </div>
              <div>
                <h3 className="text-base font-bold text-white tracking-tight">Upcoming Healthcare Events</h3>
                <p className="text-xs text-slate-400">Scheduled doctor appointments and clinical events ahead</p>
              </div>
            </div>
            <span className="text-xs font-bold text-amber-400 bg-amber-500/10 px-2.5 py-0.5 rounded-full border border-amber-500/20">
              Next 14 Days
            </span>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
            {upcomingEvents.map((evt) => (
              <div 
                key={evt.id} 
                className="p-3.5 rounded-2xl bg-slate-950/50 border border-white/5 hover:border-white/15 transition-all flex flex-col justify-between gap-2"
              >
                <div>
                  <div className="flex items-center justify-between gap-2 mb-1">
                    <span className="text-[11px] font-bold text-blue-400 uppercase tracking-wider">
                      {formatFriendlyDate(evt.event_date)}
                    </span>
                    <span className="text-xs font-mono font-bold text-slate-300">
                      {evt.reminder_time}
                    </span>
                  </div>
                  <h4 className="text-sm font-bold text-white truncate">{evt.title}</h4>
                  {evt.location && (
                    <p className="text-xs text-slate-400 mt-1 flex items-center gap-1 truncate">
                      <MapPin className="w-3 h-3 text-slate-500 shrink-0" />
                      <span>{evt.location}</span>
                    </p>
                  )}
                </div>

                <button
                  type="button"
                  onClick={() => setSelectedDateKey(evt.event_date)}
                  className="text-xs font-bold text-blue-400 hover:text-blue-300 text-left pt-1 border-t border-white/5 cursor-pointer"
                >
                  View Day Schedule →
                </button>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Delete Confirmation Dialog */}
      {eventToDeleteId && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-md">
          <div className="w-full max-w-sm rounded-3xl bg-slate-900 border border-red-500/30 p-6 shadow-2xl space-y-4">
            <h4 className="text-base font-bold text-white">Delete Scheduled Event?</h4>
            <p className="text-xs text-slate-300 leading-relaxed">
              Are you sure you want to remove this health event? This cannot be undone.
            </p>
            <div className="flex items-center justify-end gap-2.5 pt-2">
              <button
                type="button"
                onClick={() => setEventToDeleteId(null)}
                className="px-4 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-xs font-bold text-white transition-colors cursor-pointer"
              >
                Cancel
              </button>
              <button
                type="button"
                onClick={handleExecuteDelete}
                className="px-4 py-2 rounded-xl bg-red-600 hover:bg-red-500 text-xs font-bold text-white shadow-md shadow-red-600/20 transition-colors cursor-pointer"
              >
                Delete Event
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Add / Edit Health Event Modal */}
      <HealthEventModal
        isOpen={isModalOpen}
        onClose={() => { setIsModalOpen(false); setEventToEdit(null); }}
        onEventSaved={onRefreshEvents}
        initialDate={selectedDateKey}
        eventToEdit={eventToEdit}
      />
    </div>
  );
}

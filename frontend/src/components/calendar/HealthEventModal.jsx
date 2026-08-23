import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  X, 
  Calendar as CalendarIcon, 
  Stethoscope, 
  Droplet, 
  Syringe, 
  HeartPulse, 
  Activity, 
  MapPin, 
  User, 
  FileText, 
  Bell, 
  Check, 
  AlertCircle,
  Building2
} from 'lucide-react';
import OrmaDatePicker, { formatToDateKey } from './OrmaDatePicker';
import OrmaTimePicker from './OrmaTimePicker';
import { healthPlannerApi } from '../../services/api';

const EVENT_TYPE_OPTIONS = [
  { value: 'doctor_appointment', label: 'Doctor Appointment', icon: Stethoscope },
  { value: 'hospital_visit', label: 'Hospital Visit', icon: Building2 },
  { value: 'blood_test', label: 'Medical Test / Labs', icon: Droplet },
  { value: 'custom_reminder', label: 'Follow-up Consultation', icon: CalendarIcon },
  { value: 'exercise', label: 'Therapy Session', icon: Activity },
  { value: 'vaccination', label: 'Vaccination', icon: Syringe },
  { value: 'blood_pressure_check', label: 'Vitals Check', icon: HeartPulse },
];

const REMINDER_OPTIONS = [
  'At appointment time',
  '10 minutes before',
  '30 minutes before',
  '1 hour before',
  '1 day before'
];

export default function HealthEventModal({
  isOpen,
  onClose,
  onEventSaved,
  initialDate,
  eventToEdit = null
}) {
  const [formData, setFormData] = useState({
    event_type: 'doctor_appointment',
    title: '',
    description: '',
    event_date: initialDate || formatToDateKey(new Date()),
    reminder_time: '10:30 AM',
    location: '',
    contact_number: '',
    notes: '',
    reminder_timing_preference: '30 minutes before',
    priority: 'normal'
  });

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (eventToEdit) {
      setFormData({
        event_type: eventToEdit.event_type || 'doctor_appointment',
        title: eventToEdit.title || '',
        description: eventToEdit.description || '',
        event_date: eventToEdit.event_date || initialDate || formatToDateKey(new Date()),
        reminder_time: eventToEdit.reminder_time || '10:30 AM',
        location: eventToEdit.location || '',
        contact_number: eventToEdit.contact_number || '',
        notes: eventToEdit.notes || '',
        reminder_timing_preference: eventToEdit.reminder_timing_preference || '30 minutes before',
        priority: eventToEdit.priority || 'normal'
      });
    } else {
      setFormData({
        event_type: 'doctor_appointment',
        title: '',
        description: '',
        event_date: initialDate || formatToDateKey(new Date()),
        reminder_time: '10:30 AM',
        location: '',
        contact_number: '',
        notes: '',
        reminder_timing_preference: '30 minutes before',
        priority: 'normal'
      });
    }
    setError(null);
  }, [eventToEdit, initialDate, isOpen]);

  if (!isOpen) return null;

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!formData.title.trim()) {
      setError('Please provide a title for the appointment/event.');
      return;
    }

    setLoading(true);
    setError(null);

    try {
      await healthPlannerApi.createEvent({
        ...formData,
        timezone: Intl.DateTimeFormat().resolvedOptions().timeZone
      });

      if (onEventSaved) onEventSaved();
      onClose();
    } catch (err) {
      console.error('Failed to save health event:', err);
      setError(err?.response?.data?.detail || 'Failed to save appointment. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-md overflow-y-auto">
      <motion.div
        initial={{ opacity: 0, scale: 0.95, y: 10 }}
        animate={{ opacity: 1, scale: 1, y: 0 }}
        exit={{ opacity: 0, scale: 0.95, y: 10 }}
        className="w-full max-w-lg bg-slate-900/95 border border-white/15 rounded-3xl p-6 sm:p-7 shadow-2xl backdrop-blur-2xl my-8 relative overflow-hidden"
      >
        {/* Ambient Top Glow */}
        <div className="absolute -top-24 -left-24 w-48 h-48 bg-blue-500/20 rounded-full blur-3xl pointer-events-none" />

        {/* Modal Header */}
        <div className="flex items-center justify-between pb-4 mb-5 border-b border-white/10 relative z-10">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-2xl bg-blue-500/10 border border-blue-500/20 flex items-center justify-center text-blue-400">
              <Stethoscope className="w-5 h-5" />
            </div>
            <div>
              <h3 className="text-lg font-bold text-white tracking-tight">
                {eventToEdit ? 'Edit Health Event' : 'Schedule Appointment / Event'}
              </h3>
              <p className="text-xs text-slate-400">Doctor visits, tests, and medical appointments</p>
            </div>
          </div>

          <button
            type="button"
            onClick={onClose}
            className="p-2 rounded-xl text-slate-400 hover:text-white hover:bg-white/10 transition-colors cursor-pointer"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {error && (
          <div className="mb-4 p-3 rounded-xl bg-red-500/15 border border-red-500/30 flex items-center gap-2 text-xs text-red-300">
            <AlertCircle className="w-4 h-4 text-red-400 shrink-0" />
            <span>{error}</span>
          </div>
        )}

        {/* Form Body */}
        <form onSubmit={handleSubmit} className="space-y-4 relative z-10">
          {/* Event Type Select */}
          <div>
            <label className="block text-xs font-bold text-slate-300 uppercase tracking-wider mb-1.5">
              Event Type
            </label>
            <div className="grid grid-cols-2 sm:grid-cols-3 gap-2">
              {EVENT_TYPE_OPTIONS.map((opt) => {
                const Icon = opt.icon;
                const isSelected = formData.event_type === opt.value;
                return (
                  <button
                    key={opt.value}
                    type="button"
                    onClick={() => setFormData({ ...formData, event_type: opt.value })}
                    className={`p-2.5 rounded-2xl border text-left flex items-center gap-2 transition-all cursor-pointer ${
                      isSelected
                        ? 'bg-blue-600/30 border-blue-500 text-white shadow-sm'
                        : 'bg-slate-950/60 border-white/5 text-slate-400 hover:border-white/15 hover:text-slate-200'
                    }`}
                  >
                    <Icon className={`w-4 h-4 shrink-0 ${isSelected ? 'text-blue-400' : 'text-slate-400'}`} />
                    <span className="text-xs font-bold leading-tight line-clamp-1">{opt.label}</span>
                  </button>
                );
              })}
            </div>
          </div>

          {/* Title / Provider */}
          <div>
            <label className="block text-xs font-bold text-slate-300 uppercase tracking-wider mb-1.5">
              Event Title / Specialty
            </label>
            <input
              type="text"
              required
              placeholder="e.g. Cardiology Follow-up, Dr. Sharma"
              value={formData.title}
              onChange={(e) => setFormData({ ...formData, title: e.target.value })}
              className="w-full px-4 py-2.5 rounded-2xl bg-slate-950/80 border border-white/10 text-sm text-white placeholder-slate-500 focus:border-blue-500 focus:outline-none transition-colors"
            />
          </div>

          {/* Date & Time Row using OrmaDatePicker and OrmaTimePicker */}
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            <OrmaDatePicker
              value={formData.event_date}
              onChange={(newDate) => setFormData({ ...formData, event_date: newDate })}
              label="Date"
            />

            <OrmaTimePicker
              value={formData.reminder_time}
              onChange={(newTime) => setFormData({ ...formData, reminder_time: newTime })}
              label="Time"
            />
          </div>

          {/* Location / Clinic */}
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            <div>
              <label className="block text-xs font-bold text-slate-300 uppercase tracking-wider mb-1.5">
                Location / Hospital
              </label>
              <div className="relative">
                <input
                  type="text"
                  placeholder="e.g. City Hospital, Suite 402"
                  value={formData.location}
                  onChange={(e) => setFormData({ ...formData, location: e.target.value })}
                  className="w-full pl-9 pr-4 py-2.5 rounded-2xl bg-slate-950/80 border border-white/10 text-sm text-white placeholder-slate-500 focus:border-blue-500 focus:outline-none transition-colors"
                />
                <MapPin className="w-4 h-4 text-slate-500 absolute left-3 top-3" />
              </div>
            </div>

            <div>
              <label className="block text-xs font-bold text-slate-300 uppercase tracking-wider mb-1.5">
                Doctor / Provider Name
              </label>
              <div className="relative">
                <input
                  type="text"
                  placeholder="e.g. Dr. Rajesh Sharma"
                  value={formData.description}
                  onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                  className="w-full pl-9 pr-4 py-2.5 rounded-2xl bg-slate-950/80 border border-white/10 text-sm text-white placeholder-slate-500 focus:border-blue-500 focus:outline-none transition-colors"
                />
                <User className="w-4 h-4 text-slate-500 absolute left-3 top-3" />
              </div>
            </div>
          </div>

          {/* Reminder Timing Preference */}
          <div>
            <label className="block text-xs font-bold text-slate-300 uppercase tracking-wider mb-1.5">
              Reminder Notification
            </label>
            <div className="relative">
              <select
                value={formData.reminder_timing_preference}
                onChange={(e) => setFormData({ ...formData, reminder_timing_preference: e.target.value })}
                className="w-full pl-9 pr-4 py-2.5 rounded-2xl bg-slate-950/80 border border-white/10 text-sm text-white focus:border-blue-500 focus:outline-none transition-colors cursor-pointer appearance-none"
              >
                {REMINDER_OPTIONS.map((opt) => (
                  <option key={opt} value={opt} className="bg-slate-900 text-white">
                    {opt}
                  </option>
                ))}
              </select>
              <Bell className="w-4 h-4 text-blue-400 absolute left-3 top-3 pointer-events-none" />
            </div>
          </div>

          {/* Notes / Special Instructions */}
          <div>
            <label className="block text-xs font-bold text-slate-300 uppercase tracking-wider mb-1.5">
              Notes & Preparation
            </label>
            <textarea
              rows={2}
              placeholder="e.g. Bring recent blood test reports, fasting required for 8 hours"
              value={formData.notes}
              onChange={(e) => setFormData({ ...formData, notes: e.target.value })}
              className="w-full px-4 py-2 rounded-2xl bg-slate-950/80 border border-white/10 text-sm text-white placeholder-slate-500 focus:border-blue-500 focus:outline-none transition-colors resize-none"
            />
          </div>

          {/* Modal Actions */}
          <div className="flex items-center justify-end gap-3 pt-3 border-t border-white/10">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2.5 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-bold transition-colors cursor-pointer"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={loading}
              className="px-5 py-2.5 rounded-xl bg-blue-600 hover:bg-blue-500 text-white text-xs font-bold transition-all shadow-lg shadow-blue-600/30 flex items-center gap-1.5 cursor-pointer disabled:opacity-50"
            >
              <Check className="w-4 h-4" />
              <span>{loading ? 'Saving...' : 'Save Appointment'}</span>
            </button>
          </div>
        </form>
      </motion.div>
    </div>
  );
}

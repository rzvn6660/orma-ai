import { Clock, MapPin, Phone } from 'lucide-react';
import { getReminderStrings, isRTL } from '../../utils/reminderLocalization';
import { DEFAULT_REMINDER_LANGUAGE } from '../../config/reminderLanguages';

export default function ReminderContent({ medicine, user }) {
  if (!medicine) return null;
  
  const prefs = user?.notification_preferences || {};
  const reminderLang = prefs.reminder_language || localStorage.getItem('orma_reminder_language') || DEFAULT_REMINDER_LANGUAGE;
  const strings = getReminderStrings(reminderLang);
  const rtl = isRTL(reminderLang);

  const isHealthEvent = medicine.event_type !== undefined;
  const eventType = isHealthEvent ? medicine.event_type : 'medicine';
  const title = isHealthEvent ? medicine.title : medicine.medicine_name;
  const description = isHealthEvent ? medicine.description : medicine.dosage;

  const getEventTypeName = (type) => {
    switch (type) {
      case 'doctor_appointment': return 'Doctor Appointment';
      case 'blood_test': return 'Blood Test';
      case 'vaccination': return 'Vaccination';
      case 'blood_pressure_check': return 'Blood Pressure Check';
      case 'blood_sugar_check': return 'Blood Sugar Check';
      case 'exercise': return 'Exercise';
      case 'water_reminder': return 'Water Reminder';
      case 'sleep_reminder': return 'Sleep Reminder';
      case 'custom_reminder': return 'Reminder';
      default: return strings.reminderTitle || 'Scheduled Medication';
    }
  };

  const scheduledText = (strings.scheduledFor || "Scheduled for {time}").replace('{time}', medicine.reminder_time || '');

  return (
    <div 
      className={`bg-slate-900/90 border border-slate-800 rounded-3xl p-6 mb-5 backdrop-blur-xl shadow-xl text-center space-y-3 relative overflow-hidden ${rtl ? 'rtl' : 'ltr'}`} 
      dir={rtl ? 'rtl' : 'ltr'}
    >
      {/* Category Tag */}
      <span className="text-[11px] font-extrabold uppercase tracking-widest text-blue-400 bg-blue-500/10 px-3 py-1 rounded-full border border-blue-500/20 inline-block">
        {getEventTypeName(eventType)}
      </span>

      {/* Primary Focus 1: Medication Name (kept exact) */}
      <h2 className="text-3xl sm:text-4xl font-black text-white tracking-tight leading-none pt-1">
        {title}
      </h2>

      {/* Primary Focus 2: Dosage (kept exact) */}
      {description && (
        <div className="text-xl sm:text-2xl font-black text-blue-400 font-mono" dir="ltr">
          {description}
        </div>
      )}

      {/* Primary Focus 3: Scheduled Time */}
      <div className="flex items-center justify-center gap-2 pt-3 text-slate-300 text-sm font-semibold border-t border-slate-800/80">
        <Clock className="w-4 h-4 text-amber-400 shrink-0" />
        <span>{scheduledText}</span>
      </div>

      {medicine.purpose && (
        <p className="text-xs text-slate-300 bg-slate-950/50 p-3 rounded-xl border border-white/5 leading-relaxed font-medium">
          <span className="font-bold text-slate-200">{strings.purposeLabel || "Purpose: "}</span>{medicine.purpose}
        </p>
      )}

      {(medicine.location || medicine.contact_number) && (
        <div className="flex flex-col gap-1.5 pt-2 border-t border-slate-800/60 text-xs text-slate-300">
          {medicine.location && (
            <div className="flex items-center justify-center gap-2">
              <MapPin className="w-3.5 h-3.5 text-blue-400" />
              <span>{medicine.location}</span>
            </div>
          )}
          {medicine.contact_number && (
            <div className="flex items-center justify-center gap-2">
              <Phone className="w-3.5 h-3.5 text-emerald-400" />
              <span>{medicine.contact_number}</span>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

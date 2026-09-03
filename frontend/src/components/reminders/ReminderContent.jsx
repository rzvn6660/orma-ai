import { Clock, MapPin, Phone } from 'lucide-react';
import { getReminderStrings, isRTL } from '../../utils/reminderLocalization';
import { DEFAULT_REMINDER_LANGUAGE } from '../../config/reminderLanguages';

export default function ReminderContent({ medicine, user }) {
  if (!medicine) return null;
  
  const prefs = user?.notification_preferences || {};
  const reminderLang = prefs.reminder_language || localStorage.getItem('orma_reminder_language') || DEFAULT_REMINDER_LANGUAGE;
  const strings = getReminderStrings(reminderLang);
  const rtl = isRTL(reminderLang);

  const isHealthEvent = medicine.event_type !== undefined && medicine.event_type !== 'medicine';
  const eventType = isHealthEvent ? medicine.event_type : 'medicine';
  const rawMedName = (medicine.medicine_name || medicine.title)?.trim();
  const hasValidName = Boolean(rawMedName);
  const displayTitle = hasValidName ? rawMedName : (strings.reminderTitle || 'Medicine Reminder');
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

  return (
    <div 
      className={`bg-slate-900/90 border border-slate-800 rounded-2xl sm:rounded-3xl p-3.5 sm:p-4 mb-3 sm:mb-4 backdrop-blur-xl shadow-xl text-center space-y-2 relative overflow-hidden shrink-0 ${rtl ? 'rtl' : 'ltr'}`} 
      dir={rtl ? 'rtl' : 'ltr'}
    >
      {/* Category Tag */}
      <span className="text-[10px] sm:text-[11px] font-extrabold uppercase tracking-widest text-blue-400 bg-blue-500/10 px-2.5 py-0.5 rounded-full border border-blue-500/20 inline-block">
        {getEventTypeName(eventType)}
      </span>

      {/* Prominent "Time to take:" Label */}
      <div className="text-xs sm:text-sm font-extrabold uppercase tracking-wider text-blue-400 pt-0.5">
        {strings.timeToTake || "Time to take:"}
      </div>

      {/* Prominent Medicine Name with 💊 Icon */}
      <div className="flex items-center justify-center gap-2.5 py-1 px-2">
        <span className="text-2xl sm:text-3xl select-none shrink-0" role="img" aria-label="medicine">💊</span>
        <h2 className="text-2xl sm:text-3xl md:text-4xl font-black text-white tracking-tight leading-tight break-words">
          {displayTitle}
        </h2>
      </div>

      {/* Verified Dosage (if present) */}
      {description && (
        <div className="text-base sm:text-lg font-bold text-slate-300 font-mono" dir="ltr">
          {description}
        </div>
      )}

      {/* Scheduled Time */}
      <div className="flex items-center justify-center gap-1.5 pt-2 text-slate-300 text-xs sm:text-sm font-semibold border-t border-slate-800/80">
        <Clock className="w-3.5 h-3.5 sm:w-4 sm:h-4 text-amber-400 shrink-0" />
        <span>
          <span className="text-slate-400 font-normal">{strings.scheduledTimeLabel || "Scheduled time:"} </span>
          <span className="text-white font-bold">{medicine.reminder_time || ''}</span>
        </span>
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

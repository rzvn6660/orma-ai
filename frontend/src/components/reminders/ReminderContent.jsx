import { Clock, Info, MapPin, Phone } from 'lucide-react';

export default function ReminderContent({ medicine }) {
  if (!medicine) return null;
  
  // Backward compatibility: medicine object might be a MedicineReminder or HealthEvent
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
      default: return 'Medicine';
    }
  };

  return (
    <div className="orma-card">
      <div className="flex flex-col gap-4">
        <div className="flex justify-between items-start">
          <div>
            <p className="text-xs uppercase tracking-wider font-bold text-slate-500 mb-1">{getEventTypeName(eventType)}</p>
            <p className="text-2xl font-bold text-white">{title}</p>
          </div>
          {description && (
            <div className="text-right max-w-[120px]">
              <p className="text-xs uppercase tracking-wider font-bold text-slate-500 mb-1">Details</p>
              <p className="text-lg font-bold text-blue-400 break-words">{description}</p>
            </div>
          )}
        </div>
        
        <hr className="border-slate-700/50" />
        
        <div className="flex items-center gap-6">
          <div className="flex items-center gap-2">
            <Clock className="w-5 h-5 text-amber-400" />
            <span className="text-white font-medium">{medicine.reminder_time}</span>
          </div>
          {medicine.purpose && (
            <div className="flex items-center gap-2">
              <Info className="w-5 h-5 text-emerald-400" />
              <span className="text-slate-300">{medicine.purpose}</span>
            </div>
          )}
        </div>

        {(medicine.location || medicine.contact_number) && (
          <div className="flex flex-col gap-2 mt-2">
            {medicine.location && (
              <div className="flex items-center gap-2 text-slate-300">
                <MapPin className="w-4 h-4 text-blue-400" />
                <span className="text-sm">{medicine.location}</span>
              </div>
            )}
            {medicine.contact_number && (
              <div className="flex items-center gap-2 text-slate-300">
                <Phone className="w-4 h-4 text-emerald-400" />
                <span className="text-sm">{medicine.contact_number}</span>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}

import { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { CheckCircle2, AlertTriangle, Sparkles, HeartPulse } from 'lucide-react';
import { medicineApi } from '../services/api';

export default function TimeAwareDashboard({ user, timeContext }) {
  const [currentTime, setCurrentTime] = useState(new Date());
  const [medicines, setMedicines] = useState([]);

  useEffect(() => {
    const timer = setInterval(() => setCurrentTime(new Date()), 1000);
    return () => clearInterval(timer);
  }, []);

  const fetchMedicines = async () => {
    try {
      const data = await medicineApi.getReminders();
      setMedicines(data);
    } catch (err) {
      console.error("Failed to fetch medicines", err);
    }
  };

  useEffect(() => {
    fetchMedicines();

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
        fetchMedicines();
      }
    };

    const handleVisibility = () => {
      if (document.visibilityState === 'visible') {
        fetchMedicines();
      }
    };

    const interval = setInterval(fetchMedicines, 30000);
    window.addEventListener('medicationUpdated', fetchMedicines);
    window.addEventListener('orma:remindersUpdated', fetchMedicines);
    window.addEventListener('orma_websocket_message', handleWsMessage);
    document.addEventListener('visibilitychange', handleVisibility);
    window.addEventListener('focus', handleVisibility);
    window.addEventListener('online', fetchMedicines);

    return () => {
      clearInterval(interval);
      window.removeEventListener('medicationUpdated', fetchMedicines);
      window.removeEventListener('orma:remindersUpdated', fetchMedicines);
      window.removeEventListener('orma_websocket_message', handleWsMessage);
      document.removeEventListener('visibilitychange', handleVisibility);
      window.removeEventListener('focus', handleVisibility);
      window.removeEventListener('online', fetchMedicines);
    };
  }, []);

  const dateString = currentTime.toLocaleDateString([], { weekday: 'long' });
  const timeString = currentTime.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });

  const takenCount = medicines.filter(m => m.taken_status).length;
  const totalCount = medicines.length;
  const progressPercentage = totalCount > 0 ? (takenCount / totalCount) * 100 : 100;
  
  const pendingMedicines = medicines.filter(m => !m.taken_status);
  
  const isOverdue = (reminderStr) => {
    if (!reminderStr) return false;
    const current = new Date();
    const [timeStr, modifier] = reminderStr.split(' ');
    if (!timeStr || !modifier) return false;
    let [hours, minutes] = timeStr.split(':');
    if (hours === '12') hours = '00';
    if (modifier.toLowerCase() === 'pm') hours = parseInt(hours, 10) + 12;
    const reminderDate = new Date();
    reminderDate.setHours(hours, minutes, 0, 0);
    return current > reminderDate;
  };

  const nextMedicine = pendingMedicines.length > 0 ? pendingMedicines[0] : null;
  const hasOverdue = pendingMedicines.some(m => isOverdue(m.reminder_time));
  const allCompleted = totalCount > 0 && pendingMedicines.length === 0;

  let statusMessage = "";
  let statusIcon = null;
  let statusColor = "";
  
  if (totalCount === 0) {
    statusMessage = "No medicines scheduled for today.";
    statusIcon = <CheckCircle2 className="w-5 h-5" />;
    statusColor = "text-slate-300 bg-slate-800/60 border-slate-700/60";
  } else if (allCompleted) {
    statusMessage = "Excellent work! You've completed all your medicines today.";
    statusIcon = <Sparkles className="w-5 h-5 text-emerald-400" />;
    statusColor = "text-emerald-300 bg-emerald-950/40 border-emerald-500/40";
  } else if (hasOverdue) {
    statusMessage = "One medicine is past its scheduled time. Take your dose when ready.";
    statusIcon = <AlertTriangle className="w-5 h-5 text-amber-400 shrink-0" />;
    statusColor = "text-amber-200 bg-amber-950/40 border-amber-500/40";
  } else {
    statusMessage = `You have ${pendingMedicines.length} medicine${pendingMedicines.length > 1 ? 's' : ''} remaining today.`;
    statusIcon = <HeartPulse className="w-5 h-5 text-blue-400 shrink-0" />;
    statusColor = "text-blue-200 bg-blue-950/40 border-blue-500/40";
  }

  return (
    <div className="flex flex-col gap-6">
      {/* Card 1: Greeting & Status */}
      <motion.div 
        initial={{ opacity: 0, x: -20 }}
        animate={{ opacity: 1, x: 0 }}
        className="orma-card p-6 border border-slate-700/50 shadow-xl rounded-[2rem]"
      >
        <div className="flex justify-between items-start mb-6">
          <h1 className="text-2xl font-light text-white tracking-tight leading-snug">
            {timeContext.icon} {timeContext.greeting},<br/>
            <span className="font-semibold">{user?.name?.split(' ')[0] || user?.email?.split('@')[0] || 'there'}</span>
          </h1>
          <div className="text-right">
            <p className="text-[12px] text-slate-400 font-medium uppercase tracking-widest">{dateString}</p>
            <p className="text-[15px] text-white font-light tracking-wide">{timeString}</p>
          </div>
        </div>
        
        <AnimatePresence mode="wait">
          <motion.div 
            key={statusMessage}
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            className={`flex items-center gap-3 p-4 rounded-xl border ${statusColor}`}
          >
            {statusIcon}
            <p className="text-[14px] font-medium leading-relaxed">{statusMessage}</p>
          </motion.div>
        </AnimatePresence>
      </motion.div>
      
      {/* Card 2: Today's Summary & Progress */}
      <motion.div 
        initial={{ opacity: 0, x: -20 }}
        animate={{ opacity: 1, x: 0 }}
        transition={{ delay: 0.1 }}
        className="orma-card p-6 border border-slate-700/50 shadow-xl rounded-[2rem] flex flex-col gap-6"
      >
        <div>
          <h2 className="text-lg font-light text-white tracking-wide mb-4">Today's Summary</h2>
          <div className="flex justify-between items-end mb-2">
            <p className="text-xs text-slate-400 font-medium uppercase tracking-widest">Adherence</p>
            <p className="text-xs text-slate-400 font-medium">{takenCount} / {totalCount} Taken</p>
          </div>
          <div className="w-full h-2.5 bg-slate-800/80 rounded-full overflow-hidden shadow-inner flex items-center">
            <motion.div 
              initial={{ width: 0 }}
              animate={{ width: `${progressPercentage}%` }}
              transition={{ duration: 1, ease: "easeOut" }}
              className="h-full bg-gradient-to-r from-blue-500 via-cyan-400 to-emerald-400 rounded-full"
            />
          </div>
          <div className="mt-2 text-right">
             <span className="text-lg font-medium text-white">{Math.round(progressPercentage)}%</span>
          </div>
        </div>

        <div className="bg-slate-800/30 rounded-2xl p-4 border border-slate-700/40 backdrop-blur-sm">
          <p className="text-[10px] text-slate-500 font-semibold uppercase tracking-widest mb-2">Next Reminder</p>
          <div className="flex items-center gap-3">
             <div className={`w-2 h-2 rounded-full ${nextMedicine ? 'bg-amber-400 animate-pulse' : 'bg-emerald-500'}`} />
             <p className="text-[15px] font-medium text-white tracking-wide leading-tight">
               {nextMedicine ? (
                 <>{nextMedicine.medicine_name} <br/> <span className="text-slate-400 text-sm font-light">{nextMedicine.reminder_time}</span></>
               ) : totalCount > 0 ? (
                 <>Tomorrow <br/> <span className="text-slate-400 text-sm font-light">First Scheduled Medicine</span></>
               ) : (
                 'All caught up'
               )}
             </p>
          </div>
        </div>
      </motion.div>
    </div>
  );
}

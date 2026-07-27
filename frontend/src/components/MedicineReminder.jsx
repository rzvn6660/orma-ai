import { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Pill, CheckCircle2, Clock, ChevronDown, ChevronUp, Sunrise, Sun, Sunset, Moon } from 'lucide-react';
import { medicineApi } from '../services/api';

export default function MedicineReminder({ onViewChange }) {
  const [medicines, setMedicines] = useState([]);
  const [expandedId, setExpandedId] = useState(null);
  const [expandedGroups, setExpandedGroups] = useState({
    Morning: true,
    Afternoon: true,
    Evening: true,
    Night: true
  });
  
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
    const interval = setInterval(fetchMedicines, 60000);
    window.addEventListener('medicationUpdated', fetchMedicines);
    return () => {
      clearInterval(interval);
      window.removeEventListener('medicationUpdated', fetchMedicines);
    };
  }, []);

  const handleMarkTaken = async (id, e) => {
    e.stopPropagation();
    try {
      await medicineApi.takeMedicine(id);
      fetchMedicines();
      window.dispatchEvent(new Event('medicationUpdated'));
    } catch (err) {
      console.error("Failed to mark medicine as taken", err);
    }
  };

  const toggleExpand = (id) => {
    setExpandedId(expandedId === id ? null : id);
  };

  const toggleGroup = (groupName) => {
    setExpandedGroups(prev => ({ ...prev, [groupName]: !prev[groupName] }));
  };

  // Helper to categorize time
  const getTimeCategory = (timeStr) => {
    if (!timeStr) return 'Other';
    const [time, modifier] = timeStr.split(' ');
    if (!time || !modifier) return 'Other';
    let [hours] = time.split(':');
    hours = parseInt(hours, 10);
    if (modifier.toUpperCase() === 'AM') {
      if (hours === 12) hours = 0;
      if (hours >= 5 && hours < 12) return 'Morning';
      return 'Night';
    } else {
      if (hours !== 12) hours += 12;
      if (hours >= 12 && hours < 17) return 'Afternoon';
      if (hours >= 17 && hours < 21) return 'Evening';
      return 'Night';
    }
  };

  const groups = [
    { name: 'Morning', icon: <Sunrise className="w-4 h-4 text-orange-400" /> },
    { name: 'Afternoon', icon: <Sun className="w-4 h-4 text-sky-400" /> },
    { name: 'Evening', icon: <Sunset className="w-4 h-4 text-indigo-400" /> },
    { name: 'Night', icon: <Moon className="w-4 h-4 text-slate-400" /> }
  ];

  const renderMedicineRow = (med) => {
    let takenTimeStr = "";
    if (med.taken_status && med.taken_at) {
       const takenDate = new Date(med.taken_at + "Z");
       takenTimeStr = takenDate.toLocaleTimeString('en-US', {
         hour: '2-digit',
         minute: '2-digit'
       });
    }
    const isExpanded = expandedId === med.id;

    return (
      <div 
        key={med.id} 
        onClick={() => toggleExpand(med.id)}
        className={`rounded-xl border transition-all duration-300 cursor-pointer overflow-hidden ${
          med.taken_status 
            ? 'bg-emerald-900/10 border-emerald-500/20 hover:border-emerald-500/40' 
            : 'bg-slate-800/40 border-slate-600/30 hover:border-slate-500/50 hover:bg-slate-800/60'
        }`}
      >
        <div className="p-3 flex justify-between items-center">
          <div className="flex items-center gap-3">
            <div className={`w-8 h-8 rounded-full flex items-center justify-center shadow-inner ${med.taken_status ? 'bg-emerald-500/20 text-emerald-400' : 'bg-slate-700/50 text-slate-300'}`}>
              <Pill className="w-3.5 h-3.5" />
            </div>
            <div>
              <h4 className={`text-[14px] font-medium tracking-wide leading-tight ${med.taken_status ? 'text-slate-400 line-through decoration-emerald-500/30' : 'text-white'}`}>
                {med.medicine_name}
              </h4>
              <p className="text-[11px] text-slate-400 font-light mt-0.5">{med.reminder_time}</p>
            </div>
          </div>
          
          <div className="flex items-center gap-2">
            {med.taken_status ? (
              <CheckCircle2 className="w-4 h-4 text-emerald-500" />
            ) : (
              <Clock className="w-3.5 h-3.5 text-amber-400 opacity-80" />
            )}
            {isExpanded ? <ChevronUp className="w-4 h-4 text-slate-500" /> : <ChevronDown className="w-4 h-4 text-slate-500" />}
          </div>
        </div>
        
        <AnimatePresence>
          {isExpanded && (
            <motion.div 
              initial={{ height: 0, opacity: 0 }}
              animate={{ height: 'auto', opacity: 1 }}
              exit={{ height: 0, opacity: 0 }}
              transition={{ duration: 0.2 }}
              className="px-3 pb-3 border-t border-slate-700/30"
            >
              <div className="pt-3 flex justify-between items-center gap-4">
                <div>
                  <p className="text-[10px] text-slate-500 font-semibold uppercase tracking-widest mb-0.5">Dosage</p>
                  <p className="text-[13px] text-slate-200">{med.dosage}</p>
                </div>
                <div className="text-right">
                  <p className="text-[10px] text-slate-500 font-semibold uppercase tracking-widest mb-0.5">Status</p>
                  <p className={`text-[13px] font-medium ${med.taken_status ? 'text-emerald-400' : 'text-amber-400'}`}>
                    {med.taken_status ? `Taken at ${takenTimeStr}` : 'Pending'}
                  </p>
                </div>
              </div>

              {!med.taken_status && (
                <button 
                  onClick={(e) => handleMarkTaken(med.id, e)}
                  className="orma-btn-success"
                >
                  <CheckCircle2 className="w-4 h-4" /> Mark Taken
                </button>
              )}
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    );
  };

  return (
    <motion.div 
      initial={{ opacity: 0, x: 20 }}
      animate={{ opacity: 1, x: 0 }}
      transition={{ duration: 0.6, delay: 0.2 }}
      className="orma-card p-6 border border-slate-700/50 shadow-xl rounded-[2rem]"
    >
      <div className="flex items-center justify-between mb-4 pb-3 border-b border-slate-700/50">
        <h3 className="text-[17px] font-medium text-white tracking-wide">
          Medications
        </h3>
        <button 
          onClick={() => onViewChange('medicines')}
          className="text-[11px] font-medium text-cyan-400 hover:text-cyan-300 uppercase tracking-widest transition-colors"
        >
          Manage
        </button>
      </div>

      <div className="space-y-4">
        {medicines.length === 0 ? (
          <div className="text-center py-6 text-slate-400">
            <p className="text-sm font-light mb-2">No medicines scheduled.</p>
          </div>
        ) : (
          groups.map(group => {
            const groupMeds = medicines.filter(m => getTimeCategory(m.reminder_time) === group.name);
            if (groupMeds.length === 0) return null;

            return (
              <div key={group.name} className="flex flex-col gap-2">
                <div 
                  className="flex justify-between items-center cursor-pointer"
                  onClick={() => toggleGroup(group.name)}
                >
                  <div className="flex items-center gap-2">
                    {group.icon}
                    <h4 className="text-[13px] font-medium text-slate-300">{group.name}</h4>
                  </div>
                  <div className="flex items-center gap-2">
                    <span className="text-[11px] text-slate-500">{groupMeds.length}</span>
                    {expandedGroups[group.name] ? <ChevronUp className="w-3.5 h-3.5 text-slate-500" /> : <ChevronDown className="w-3.5 h-3.5 text-slate-500" />}
                  </div>
                </div>
                
                <AnimatePresence>
                  {expandedGroups[group.name] && (
                    <motion.div 
                      initial={{ height: 0, opacity: 0 }}
                      animate={{ height: 'auto', opacity: 1 }}
                      exit={{ height: 0, opacity: 0 }}
                      className="flex flex-col gap-2 overflow-hidden"
                    >
                      {groupMeds.map(renderMedicineRow)}
                    </motion.div>
                  )}
                </AnimatePresence>
              </div>
            );
          })
        )}
      </div>
    </motion.div>
  );
}

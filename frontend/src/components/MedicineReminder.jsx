import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { Pill, CheckCircle2, Clock, Plus } from 'lucide-react';
import { medicineApi } from '../services/api';
import AddMedicineModal from './AddMedicineModal';

export default function MedicineReminder() {
  const [medicines, setMedicines] = useState([]);
  const [isModalOpen, setIsModalOpen] = useState(false);
  
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
    // Refresh list every minute to stay synced with backend
    const interval = setInterval(fetchMedicines, 60000);
    return () => clearInterval(interval);
  }, []);

  const handleMarkTaken = async (id) => {
    try {
      await medicineApi.takeMedicine(id);
      fetchMedicines();
    } catch (err) {
      console.error("Failed to mark medicine as taken", err);
    }
  };

  const takenCount = medicines.filter(m => m.taken_status).length;
  const totalCount = medicines.length;

  return (
    <motion.div 
      initial={{ opacity: 0, x: 20 }}
      animate={{ opacity: 1, x: 0 }}
      transition={{ duration: 0.6, delay: 0.4 }}
      className="glass-card p-6"
    >
      <div className="flex items-center justify-between mb-6">
        <h3 className="text-xl font-bold text-white flex items-center gap-2">
          <Pill className="text-blue-400 w-5 h-5" />
          Today's Medication
        </h3>
        <div className="flex items-center gap-3">
          <span className="text-sm font-medium px-3 py-1 bg-slate-800 rounded-full text-slate-300">
            {takenCount} / {totalCount} Taken
          </span>
          <button 
            onClick={() => setIsModalOpen(true)}
            className="p-1.5 bg-blue-600 hover:bg-blue-500 rounded-lg text-white transition-colors"
          >
            <Plus className="w-5 h-5" />
          </button>
        </div>
      </div>

      <div className="relative">
        {/* Timeline line */}
        <div className="absolute left-6 top-4 bottom-4 w-px bg-slate-700/50"></div>
        
        <div className="space-y-4 relative">
          {medicines.map((med) => (
            <div key={med.id} className="flex gap-4 group">
              {/* Timeline dot */}
              <div className="relative z-10 w-12 flex justify-center pt-2">
                {med.taken_status ? (
                  <CheckCircle2 className="w-5 h-5 text-emerald-400 bg-slate-900 rounded-full" />
                ) : (
                  <Clock className="w-5 h-5 text-slate-500 bg-slate-900 rounded-full" />
                )}
              </div>
              
              {/* Card */}
              <div className={`flex-1 p-4 rounded-xl border transition-all duration-300
                ${med.taken_status 
                  ? 'bg-emerald-900/10 border-emerald-500/20 opacity-60' 
                  : 'bg-slate-800/50 border-slate-700/50 hover:border-blue-500/30 hover:bg-slate-800/80'
                }`}
              >
                <div className="flex justify-between items-start mb-1">
                  <h4 className={`font-semibold ${med.taken_status ? 'text-emerald-300' : 'text-white'}`}>
                    {med.medicine_name}
                  </h4>
                  <span className={`text-xs font-medium px-2 py-1 rounded-md 
                    ${med.taken_status ? 'bg-emerald-500/10 text-emerald-400' : 'bg-blue-500/10 text-blue-400'}`}
                  >
                    {med.reminder_time}
                  </span>
                </div>
                <div className="flex justify-between items-end">
                  <p className="text-sm text-slate-400">{med.dosage}</p>
                  {!med.taken_status && (
                    <button 
                      onClick={() => handleMarkTaken(med.id)}
                      className="text-xs font-medium text-blue-400 hover:text-blue-300 bg-blue-500/10 px-3 py-1.5 rounded-lg transition-colors"
                    >
                      Mark Taken
                    </button>
                  )}
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
      
      <AddMedicineModal 
        isOpen={isModalOpen} 
        onClose={() => setIsModalOpen(false)} 
        onAdded={fetchMedicines} 
      />
    </motion.div>
  );
}

import { useState, useEffect, useCallback } from 'react';
import { User, ChevronDown } from 'lucide-react';
import { linkApi } from '../services/api';
import { motion, AnimatePresence } from 'framer-motion';

export default function PatientSwitcher({ user }) {
  const [isOpen, setIsOpen] = useState(false);
  const [patients, setPatients] = useState([]);
  const [activePatient, setActivePatient] = useState(null);

  const fetchPatients = useCallback(async () => {
    if (user?.role !== 'caregiver') return;
    try {
      const data = await linkApi.getLinkedUsers();
      const usersList = data?.linked_users || [];
      setPatients(usersList);

      if (usersList.length > 0) {
        const stored = localStorage.getItem('orma_subject_id');
        const found = usersList.find(u => u.id === stored);
        if (found) {
          setActivePatient(found);
        } else {
          setActivePatient(usersList[0]);
          localStorage.setItem('orma_subject_id', usersList[0].id);
        }
      } else {
        setActivePatient(null);
        localStorage.removeItem('orma_subject_id');
      }
    } catch (err) {
      console.error("Failed to fetch linked patients for PatientSwitcher", err);
    }
  }, [user]);

  useEffect(() => {
    fetchPatients();

    const handleSyncEvent = () => fetchPatients();
    window.addEventListener('subjectChange', handleSyncEvent);

    const handleWsMessage = (e) => {
      const msg = e.detail;
      const relevantTypes = ['caregiver_linked', 'caregiver_removed', 'pending_request_approved'];
      if (relevantTypes.includes(msg?.type)) {
        fetchPatients();
      }
    };
    window.addEventListener('orma_websocket_message', handleWsMessage);

    return () => {
      window.removeEventListener('subjectChange', handleSyncEvent);
      window.removeEventListener('orma_websocket_message', handleWsMessage);
    };
  }, [fetchPatients]);

  if (user?.role !== 'caregiver') return null;

  const handleSelect = (p) => {
    setActivePatient(p);
    localStorage.setItem('orma_subject_id', p.id);
    setIsOpen(false);
    window.dispatchEvent(new Event('subjectChange'));
    window.location.reload(); 
  };

  if (patients.length === 0) {
    return (
      <div className="flex items-center gap-2 bg-slate-800/40 text-slate-400 border border-slate-700 px-3 py-1.5 rounded-full text-xs font-medium">
        <User className="w-3.5 h-3.5 text-slate-500" />
        <span>No linked patient selected</span>
      </div>
    );
  }

  return (
    <div className="relative">
      <button 
        onClick={() => setIsOpen(!isOpen)}
        className="flex items-center gap-2 bg-blue-500/10 hover:bg-blue-500/20 text-blue-400 border border-blue-500/30 px-3 py-1.5 rounded-full transition-colors cursor-pointer"
      >
        <User className="w-4 h-4" />
        <span className="text-sm font-medium">Assisting: {activePatient?.name || 'Select Patient'}</span>
        <ChevronDown className="w-4 h-4 opacity-70" />
      </button>

      <AnimatePresence>
        {isOpen && (
          <motion.div 
            initial={{ opacity: 0, y: 10, scale: 0.95 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: 10, scale: 0.95 }}
            className="absolute top-full mt-2 right-0 w-52 bg-slate-900 border border-slate-700 rounded-xl shadow-xl z-50 overflow-hidden"
          >
            <div className="p-2 border-b border-slate-800 bg-slate-900/50">
              <span className="text-xs text-slate-400 font-semibold uppercase tracking-wider pl-2">Select Patient</span>
            </div>
            <div className="p-1">
              {patients.map(p => (
                <button
                  key={p.id}
                  onClick={() => handleSelect(p)}
                  className={`w-full text-left px-3 py-2 text-sm rounded-lg transition-colors cursor-pointer ${activePatient?.id === p.id ? 'bg-blue-600/20 text-blue-400 font-semibold' : 'text-slate-300 hover:bg-slate-800'}`}
                >
                  <p className="font-medium truncate">{p.name}</p>
                  <p className="text-[10px] text-slate-400 font-mono truncate">{p.email}</p>
                </button>
              ))}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}

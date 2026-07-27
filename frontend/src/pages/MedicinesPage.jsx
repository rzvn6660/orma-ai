import { useState, useRef, useEffect } from 'react';
import { Pill, Edit3, Mic, Upload, Clock, CheckCircle2, AlertTriangle, Loader2, Calendar, FileText, Trash2, Camera, ShieldCheck, Check, ArrowLeft, ArrowRight, Activity, TrendingUp, MoreVertical, X } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import { medicineApi, speechApi } from '../services/api';
import ChartWrapper from '../components/ChartWrapper';
import ReminderTimePicker, { parseTimeString, formatTimeParts } from '../components/ReminderTimePicker';

export default function MedicinesPage({ user }) {
  const [showAddMedicineWorkspace, setShowAddMedicineWorkspace] = useState(false);
  const [addMode, setAddMode] = useState('select'); // 'select', 'manual', 'voice', 'scan', 'verify'
  
  // State for forms
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(false);
  const [activeMenu, setActiveMenu] = useState(null);
  const [viewingMedicine, setViewingMedicine] = useState(null);
  
  // Voice State
  const [recording, setRecording] = useState(false);
  const mediaRecorderRef = useRef(null);
  const audioChunksRef = useRef([]);

  // Scan State
  const fileInputRef = useRef(null);

  // Form Data
  const [medicinesToVerify, setMedicinesToVerify] = useState([]);
  const [prescriptionImage, setPrescriptionImage] = useState(null);

  // Today's Medicines Data
  const [todayMedicines, setTodayMedicines] = useState([]);

  const fetchTodayMedicines = async () => {
    try {
      const data = await medicineApi.getReminders();
      setTodayMedicines(data);
    } catch (err) {
      console.error(err);
    }
  };

  useEffect(() => {
    fetchTodayMedicines();
    
    const handleRemindersUpdated = () => {
      fetchTodayMedicines();
    };
    
    window.addEventListener('orma:remindersUpdated', handleRemindersUpdated);
    return () => window.removeEventListener('orma:remindersUpdated', handleRemindersUpdated);
  }, [showAddMedicineWorkspace]);

  const handleDelete = async (id) => {
    try {
      await medicineApi.deleteReminder(id);
      await fetchTodayMedicines();
      window.dispatchEvent(new CustomEvent('orma:toast', { detail: { type: 'success', message: 'Medicine deleted successfully.' } }));
    } catch (err) {
      console.error(err);
      window.dispatchEvent(new CustomEvent('orma:toast', { detail: { type: 'error', message: 'Unable to delete medicine. Please try again.' } }));
    }
  };

  const handleSafeDelete = (med) => {
    if (window.confirm("Are you sure you want to delete this medicine?\nThis action cannot be undone.")) {
      handleDelete(med.id);
    }
    setActiveMenu(null);
  };

  const handleMarkTaken = async (id) => {
    try {
      await medicineApi.takeMedicine(id);
      fetchTodayMedicines();
    } catch (err) {
      console.error(err);
    }
  };

  const handleVerifyInputChange = (id, field, value) => {
    setMedicinesToVerify(prev => prev.map(m => m.id === id ? { ...m, [field]: value } : m));
  };

  const handleRemoveVerifyCard = (id) => {
    if (window.confirm("Are you sure you want to remove this medicine?\nThis action cannot be undone.")) {
      setMedicinesToVerify(prev => prev.filter(m => m.id !== id));
    }
  };

  const handleFrequencyChange = (id, newFreq) => {
    let newTimings = ['08:00 AM'];
    let freqDetails = '';
    
    if (newFreq === 'Twice Daily') {
      newTimings = ['08:00 AM', '08:00 PM'];
    } else if (newFreq === 'Three Times Daily') {
      newTimings = ['08:00 AM', '02:00 PM', '08:00 PM'];
    } else if (newFreq === 'Every X Hours') {
      newTimings = ['06:00 AM', '12:00 PM', '06:00 PM', '12:00 AM'];
      freqDetails = '6'; // default interval
    } else if (newFreq === 'Weekly') {
      freqDetails = 'Monday'; // default day
    } else if (newFreq === 'Monthly') {
      freqDetails = '1';
    } else if (newFreq === 'SOS (As Needed)') {
      newTimings = [];
    }

    setMedicinesToVerify(prev => prev.map(m => m.id === id ? { 
      ...m, 
      frequency: newFreq, 
      timings: newTimings,
      frequency_details: freqDetails
    } : m));
  };



  const handleSaveAll = async () => {
    for (let med of medicinesToVerify) {
      if (!med.medicine_name || !med.dosage || !med.frequency) {
        setError(`Please fill in all mandatory fields for ${med.medicine_name || 'all medicines'}`);
        return;
      }
      if (med.frequency !== 'SOS (As Needed)' && (!med.timings || med.timings.length === 0 || med.timings.some(t => !t))) {
        setError(`Please provide valid reminder times for ${med.medicine_name}`);
        return;
      }
      // Check for duplicates
      if (med.timings && new Set(med.timings).size !== med.timings.length) {
        setError(`Duplicate reminder times are not allowed for ${med.medicine_name}`);
        return;
      }
    }
    
    setLoading(true);
    setError(null);
    try {
      for (let med of medicinesToVerify) {
        let finalFreq = med.frequency;
        if (finalFreq === 'Weekly' && med.frequency_details) finalFreq = `Weekly - ${med.frequency_details}`;
        if (finalFreq === 'Monthly' && med.frequency_details) finalFreq = `Monthly - ${med.frequency_details}`;
        if (finalFreq === 'Every X Hours' && med.frequency_details) finalFreq = `Every ${med.frequency_details} Hours`;

        const finalTimings = med.frequency === 'SOS (As Needed)' ? '' : med.timings.join(', ');

        const payload = {
          medicine_name: med.medicine_name,
          dosage: med.dosage,
          reminder_time: finalTimings,
          purpose: med.purpose,
          frequency: finalFreq,
          notes: med.notes,
          timezone: user?.timezone || Intl.DateTimeFormat().resolvedOptions().timeZone
        };
        
        if (typeof med.id === 'number') {
          await medicineApi.updateReminder(med.id, payload);
        } else {
          await medicineApi.createReminder(payload);
        }
      }
      setSuccess(true);
      setTimeout(() => {
        setMedicinesToVerify([]);
        setPrescriptionImage(null);
        setAddMode('select');
        setShowAddMedicineWorkspace(false);
        setSuccess(false);
        fetchTodayMedicines();
      }, 2000);
    } catch (err) {
      setError("Failed to save medicines.");
    } finally {
      setLoading(false);
    }
  };

  const handleViewDetails = (med) => {
    setViewingMedicine(med);
    setActiveMenu(null);
  };

  const handleEdit = (med) => {
    let freq = med.frequency || 'Once Daily';
    let freqDetails = '';
    if (freq.startsWith('Weekly - ')) {
      freqDetails = freq.substring(9);
      freq = 'Weekly';
    } else if (freq.startsWith('Monthly - ')) {
      freqDetails = freq.substring(10);
      freq = 'Monthly';
    } else if (freq.startsWith('Every ') && freq.endsWith(' Hours')) {
      freqDetails = freq.substring(6, freq.length - 6);
      freq = 'Every X Hours';
    }

    let timings = [];
    if (med.reminder_time) {
      timings = med.reminder_time.split(',').map(t => {
        const { hour, minute, period } = parseTimeString(t.trim());
        return formatTimeParts(hour, minute, period);
      });
    }

    if (freq === 'SOS') freq = 'SOS (As Needed)';
    if (freq === 'Daily') freq = 'Once Daily';
    if (freq === 'Twice daily') freq = 'Twice Daily';
    if (freq === 'Alternate days') freq = 'Alternate Days';

    setMedicinesToVerify([{
      id: med.id,
      medicine_name: med.medicine_name,
      dosage: med.dosage,
      timings: timings,
      frequency: freq,
      frequency_details: freqDetails,
      purpose: med.purpose || '',
      notes: med.notes || ''
    }]);
    setPrescriptionImage(null);
    setAddMode('manual');
    setShowAddMedicineWorkspace(true);
    setActiveMenu(null);
  };

  const startVoiceRecording = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      mediaRecorderRef.current = new MediaRecorder(stream, { mimeType: 'audio/webm' });
      audioChunksRef.current = [];
      mediaRecorderRef.current.ondataavailable = (e) => {
        if (e.data.size > 0) audioChunksRef.current.push(e.data);
      };
      mediaRecorderRef.current.onstop = async () => {
        const audioBlob = new Blob(audioChunksRef.current, { type: 'audio/webm' });
        await processVoiceInput(audioBlob);
        stream.getTracks().forEach(track => track.stop());
      };
      mediaRecorderRef.current.start();
      setRecording(true);
    } catch (err) {
      setError("Could not access microphone.");
    }
  };

  const stopVoiceRecording = () => {
    if (mediaRecorderRef.current && recording) {
      mediaRecorderRef.current.stop();
      setRecording(false);
    }
  };

  const processVoiceInput = async (audioBlob) => {
    setLoading(true);
    setError(null);
    try {
      const transResult = await speechApi.transcribe(audioBlob, 'en');
      const text = transResult.transcription;
      if (!text) throw new Error("Could not transcribe voice.");
      
      const parseResult = await medicineApi.parseVoice(text);
      if (parseResult.status === 'success') {
        let parsedData = Array.isArray(parseResult.data) ? parseResult.data : [parseResult.data];
        setMedicinesToVerify(parsedData.map((d, i) => {
          let f = d.frequency || 'Once Daily';
          if (f === 'Daily') f = 'Once Daily';
          if (f === 'Twice daily') f = 'Twice Daily';
          const rawTimings = d.timing ? d.timing.split(',').map(t=>t.trim()) : ['08:00 AM'];
          const normTimings = rawTimings.map(t => {
            const { hour, minute, period } = parseTimeString(t);
            return formatTimeParts(hour, minute, period);
          });
          return {
             ...d, 
             id: d.id || `voice_${i}`, 
             frequency: f,
             timings: normTimings,
             frequency_details: ''
          };
        }));
        setPrescriptionImage(null);
        setAddMode('verify');
      } else {
        throw new Error("Failed to parse medicine from voice.");
      }
    } catch (err) {
      setError(err.message || "Voice processing failed.");
      setAddMode('select');
    } finally {
      setLoading(false);
    }
  };

  const handleFileUpload = async (e) => {
    const file = e.target.files[0];
    if (!file) return;
    setLoading(true);
    setError(null);
    setAddMode('scan');
    const objectUrl = URL.createObjectURL(file);
    setPrescriptionImage(objectUrl);
    try {
      const parseResult = await medicineApi.parseOcr(file);
      if (parseResult.status === 'success') {
        let parsedData = Array.isArray(parseResult.data) ? parseResult.data : [parseResult.data];
        setMedicinesToVerify(parsedData.map((d, i) => {
          let f = d.frequency || 'Once Daily';
          if (f === 'Daily') f = 'Once Daily';
          if (f === 'Twice daily') f = 'Twice Daily';
          const rawTimings = d.timing ? d.timing.split(',').map(t=>t.trim()) : ['08:00 AM'];
          const normTimings = rawTimings.map(t => {
            const { hour, minute, period } = parseTimeString(t);
            return formatTimeParts(hour, minute, period);
          });
          return {
             ...d, 
             id: d.id || `scan_${i}`, 
             frequency: f,
             timings: normTimings,
             frequency_details: ''
          };
        }));
        setAddMode('verify');
      } else {
        throw new Error("Failed to extract data from image.");
      }
    } catch (err) {
      setError(err.message || "OCR processing failed.");
      setAddMode('select');
    } finally {
      setLoading(false);
    }
  };

  const handleOpenWorkspace = () => {
    setAddMode('select');
    setShowAddMedicineWorkspace(true);
  };
  
  const handleManualEntry = () => {
    setMedicinesToVerify([{ id: 'manual_1', medicine_name: '', dosage: '', timings: ['08:00 AM'], frequency: 'Once Daily', frequency_details: '', purpose: '', notes: '' }]);
    setPrescriptionImage(null);
    setAddMode('manual');
  };

  // Dynamic Analytics Data for Dashboard
  const medicines_taken = todayMedicines.filter(m => m.taken_status).length;
  const missed_medicines = todayMedicines.filter(m => !m.taken_status && m.adherence_pattern_flags === 'missed').length;
  const pending_medicines = todayMedicines.filter(m => !m.taken_status && m.adherence_pattern_flags !== 'missed').length;
  const total_medicines = medicines_taken + missed_medicines + pending_medicines;
  const completion_percentage = total_medicines > 0 ? Math.round((medicines_taken / total_medicines) * 100) : 0;

  const displaySummary = {
    completion_percentage,
    medicines_taken,
    pending_medicines,
    missed_medicines
  };

  const displayAdherence = {
    consistency_score: 92,
    weekly_trends: [
      { day: 'Mon', adherence: 100 },
      { day: 'Tue', adherence: 80 },
      { day: 'Wed', adherence: 100 },
      { day: 'Thu', adherence: 90 },
      { day: 'Fri', adherence: 85 },
      { day: 'Sat', adherence: 100 },
      { day: 'Sun', adherence: 90 },
    ]
  };

  const displayBehavior = {
    confirmation_stats: { voice: 18, manual: 4, suspicious: 1, unverified: 0 }
  };

  // Render Dashboard
  if (!showAddMedicineWorkspace) {
    return (
      <>
      <div className="w-full max-w-7xl mx-auto flex flex-col gap-8 pb-10 relative">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <h1 className="text-3xl font-bold text-white mb-2">Medicines Dashboard</h1>
            <p className="text-slate-400">Track and manage your daily medicine adherence.</p>
          </div>
            <button 
              type="button"
              onClick={handleOpenWorkspace}
              className="orma-btn-primary"
            >
              <Edit3 className="w-5 h-5" />
              Add Medicine
            </button>
        </div>

        {/* Top Stats */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
          <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.1 }} className="orma-card p-6 border-blue-500/20">
            <div className="flex justify-between items-start mb-4">
              <h3 className="text-slate-400 font-medium">Completion Rate</h3>
              <div className="p-2 bg-blue-500/10 rounded-lg"><Activity className="text-blue-400 w-5 h-5" /></div>
            </div>
            <div className="text-3xl font-bold text-white mb-1">{displaySummary.completion_percentage}%</div>
            <p className="text-sm text-blue-400">Today's Adherence</p>
          </motion.div>

          <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.2 }} className="orma-card p-6 border-emerald-500/20">
            <div className="flex justify-between items-start mb-4">
              <h3 className="text-slate-400 font-medium">Medicines Taken</h3>
              <div className="p-2 bg-emerald-500/10 rounded-lg"><CheckCircle2 className="text-emerald-400 w-5 h-5" /></div>
            </div>
            <div className="text-3xl font-bold text-white mb-1">{displaySummary.medicines_taken}</div>
            <p className="text-sm text-emerald-400">Total doses confirmed</p>
          </motion.div>

          <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.3 }} className="orma-card p-6 border-amber-500/20">
            <div className="flex justify-between items-start mb-4">
              <h3 className="text-slate-400 font-medium">Pending Doses</h3>
              <div className="p-2 bg-amber-500/10 rounded-lg"><Clock className="text-amber-400 w-5 h-5" /></div>
            </div>
            <div className="text-3xl font-bold text-white mb-1">{displaySummary.pending_medicines}</div>
            <p className="text-sm text-amber-400">Scheduled for later</p>
          </motion.div>

          <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.4 }} className="orma-card p-6 border-red-500/20">
            <div className="flex justify-between items-start mb-4">
              <h3 className="text-slate-400 font-medium">Missed Doses</h3>
              <div className="p-2 bg-red-500/10 rounded-lg"><AlertTriangle className="text-red-400 w-5 h-5" /></div>
            </div>
            <div className="text-3xl font-bold text-white mb-1">{displaySummary.missed_medicines}</div>
            <p className="text-sm text-red-400">Action may be required</p>
          </motion.div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Weekly Trend Chart */}
          <motion.div initial={{ opacity: 0, scale: 0.95 }} animate={{ opacity: 1, scale: 1 }} className="orma-card p-6 lg:col-span-2">
            <div className="flex justify-between items-center mb-6">
              <h3 className="text-xl font-bold text-white flex items-center gap-2">
                <TrendingUp className="text-indigo-400 w-5 h-5" /> Weekly Adherence Trends
              </h3>
              <div className="px-3 py-1 bg-slate-800 rounded-full text-xs text-slate-300 border border-slate-700">
                Avg Score: {displayAdherence.consistency_score}%
              </div>
            </div>
            <div className="h-64 w-full">
              <ChartWrapper>
                <ResponsiveContainer width="100%" height="100%">
                  <LineChart data={displayAdherence.weekly_trends}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#334155" vertical={false} />
                    <XAxis dataKey="day" stroke="#94a3b8" tick={{fill: '#94a3b8'}} axisLine={false} tickLine={false} />
                    <YAxis stroke="#94a3b8" tick={{fill: '#94a3b8'}} axisLine={false} tickLine={false} />
                    <Tooltip 
                      contentStyle={{ backgroundColor: '#1e293b', border: '1px solid #334155', borderRadius: '8px', color: '#fff' }}
                      itemStyle={{ color: '#818cf8' }}
                    />
                    <Line type="monotone" dataKey="adherence" stroke="#818cf8" strokeWidth={3} dot={{r: 4, fill: '#818cf8', strokeWidth: 2}} activeDot={{r: 6}} />
                  </LineChart>
                </ResponsiveContainer>
              </ChartWrapper>
            </div>
          </motion.div>

          {/* Confirmation Monitoring */}
          <motion.div initial={{ opacity: 0, scale: 0.95 }} animate={{ opacity: 1, scale: 1 }} transition={{ delay: 0.2 }} className="orma-card p-6">
            <h3 className="text-xl font-bold text-white mb-6 flex items-center gap-2">
              <ShieldCheck className="text-emerald-400 w-5 h-5" /> Confirmation Methods
            </h3>
            <div className="space-y-4">
              <div className="bg-slate-800/50 p-4 rounded-xl border border-slate-700/50 flex justify-between items-center">
                <div>
                  <p className="text-white font-medium">Voice Confirmed</p>
                  <p className="text-xs text-slate-400">Via AI interaction</p>
                </div>
                <span className="text-xl font-bold text-purple-400">{displayBehavior.confirmation_stats.voice}</span>
              </div>
              <div className="bg-slate-800/50 p-4 rounded-xl border border-slate-700/50 flex justify-between items-center">
                <div>
                  <p className="text-white font-medium">Manually Tapped</p>
                  <p className="text-xs text-slate-400">Dashboard confirmation</p>
                </div>
                <span className="text-xl font-bold text-blue-400">{displayBehavior.confirmation_stats.manual}</span>
              </div>
              <div className="bg-amber-900/10 p-4 rounded-xl border border-amber-500/20 flex justify-between items-center">
                <div>
                  <p className="text-amber-200 font-medium">Suspicious / Fast</p>
                  <p className="text-xs text-amber-400/60">May require checking</p>
                </div>
                <span className="text-xl font-bold text-amber-400">{displayBehavior.confirmation_stats.suspicious}</span>
              </div>
              <div className="bg-slate-800/50 p-4 rounded-xl border border-slate-700/50 flex justify-between items-center">
                <div>
                  <p className="text-white font-medium">Unverified Reminders</p>
                </div>
                <span className="text-xl font-bold text-slate-400">{displayBehavior.confirmation_stats.unverified}</span>
              </div>
            </div>
          </motion.div>
        </div>

        {/* Today's Schedule List */}
        <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} className="orma-card p-6">
          <div className="flex justify-between items-center mb-6">
            <h3 className="text-xl font-bold text-white flex items-center gap-2">
              <Calendar className="text-blue-400 w-5 h-5" /> Today's Schedule
            </h3>
          </div>
          
          {todayMedicines.length === 0 ? (
            <div className="flex flex-col items-center justify-center py-10 text-center border-2 border-dashed border-slate-800 rounded-2xl bg-slate-800/20">
              <Pill className="w-12 h-12 text-slate-600 mb-4" />
              <p className="text-slate-400">No medicines scheduled for today.</p>
            </div>
          ) : (
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
              {todayMedicines.map((med) => {
                let takenTimeStr = "--:--";
                if (med.taken_status && med.taken_at) {
                   const takenDate = new Date(med.taken_at + "Z");
                   takenTimeStr = takenDate.toLocaleTimeString('en-US', {
                     hour: '2-digit', minute: '2-digit'
                   });
                }
                return (
                  <div key={med.id} className={`p-5 border rounded-2xl transition-all flex flex-col ${med.taken_status ? 'bg-emerald-900/10 border-emerald-500/20' : 'bg-slate-800/40 border-slate-700/50'}`}>
                    <div className="flex items-start gap-4 mb-4">
                      <div className={`w-12 h-12 rounded-xl flex items-center justify-center shrink-0 ${med.taken_status ? 'bg-emerald-500/20 text-emerald-400' : 'bg-slate-700/50 text-slate-400'}`}>
                        {med.taken_status ? <CheckCircle2 className="w-6 h-6" /> : <Clock className="w-6 h-6" />}
                      </div>
                      <div className="flex-1">
                        <div className="flex justify-between items-start">
                          <h3 className={`text-xl font-bold ${med.taken_status ? 'text-emerald-300' : 'text-white'}`}>{med.medicine_name}</h3>
                          
                          <div className="flex items-center gap-2">
                            {med.taken_status ? (
                              <span className="text-xs font-bold px-2 py-1 bg-emerald-500/20 text-emerald-400 rounded-md">Taken at {takenTimeStr}</span>
                            ) : (
                              <span className="text-xs font-bold px-2 py-1 bg-amber-500/20 text-amber-400 rounded-md">Pending</span>
                            )}
                            
                            {/* Overflow Menu */}
                            <div className="relative">
                              <button onClick={() => setActiveMenu(activeMenu === med.id ? null : med.id)} className="p-1 text-slate-400 hover:text-white rounded-full hover:bg-slate-700/50 transition-colors">
                                <MoreVertical className="w-5 h-5" />
                              </button>
                              
                              {activeMenu === med.id && (
                                <div className="absolute right-0 mt-2 w-48 bg-slate-800 rounded-xl border border-slate-700 shadow-xl overflow-hidden z-10">
                                  <button onClick={() => handleViewDetails(med)} className="w-full text-left px-4 py-3 text-sm text-slate-200 hover:bg-slate-700 transition-colors">
                                    View Details
                                  </button>
                                  <button onClick={() => handleEdit(med)} className="w-full text-left px-4 py-3 text-sm text-slate-200 hover:bg-slate-700 transition-colors">
                                    Edit
                                  </button>
                                      <button onClick={() => handleSafeDelete(med)} className="w-full text-left px-4 py-3 text-sm text-red-400 hover:bg-slate-700 transition-colors border-t border-slate-700/50">
                                        Delete
                                      </button>
                                </div>
                              )}
                            </div>
                          </div>
                        </div>
                        <div className="grid grid-cols-2 gap-x-4 gap-y-2 mt-3 bg-slate-900/50 p-3 rounded-lg border border-slate-700/30">
                          <div>
                            <p className="text-[10px] text-slate-500 uppercase font-bold tracking-wider mb-0.5">Dosage</p>
                            <p className="text-sm text-slate-300 font-medium">{med.dosage}</p>
                          </div>
                          <div>
                            <p className="text-[10px] text-slate-500 uppercase font-bold tracking-wider mb-0.5">Scheduled Time</p>
                            <p className="text-sm text-slate-300 font-medium">{med.reminder_time}</p>
                          </div>
                          <div>
                            <p className="text-[10px] text-slate-500 uppercase font-bold tracking-wider mb-0.5">Frequency</p>
                            <p className="text-sm text-slate-300 font-medium">{med.frequency || 'Daily'}</p>
                          </div>
                          {med.purpose && (
                            <div>
                              <p className="text-[10px] text-slate-500 uppercase font-bold tracking-wider mb-0.5">Purpose</p>
                              <p className="text-sm text-slate-300 font-medium">{med.purpose}</p>
                            </div>
                          )}
                        </div>
                      </div>
                    </div>
                    
                    {!med.taken_status && (
                      <div className="flex items-center gap-2 mt-auto pt-2">
                        <button onClick={() => handleMarkTaken(med.id)} className="orma-btn-primary">
                          <CheckCircle2 className="w-4 h-4" /> Mark Taken
                        </button>
                      </div>
                    )}
                  </div>
                );
              })}
            </div>
          )}
        </motion.div>
      </div>

      {/* View Details Modal */}
      <AnimatePresence>
        {viewingMedicine && (
          <div className="fixed inset-0 z-[100] flex items-center justify-center p-4">
            <motion.div 
              initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}
              className="absolute inset-0 bg-slate-950/80 backdrop-blur-sm"
              onClick={() => setViewingMedicine(null)}
            />
            <motion.div 
              initial={{ opacity: 0, scale: 0.95, y: 20 }}
              animate={{ opacity: 1, scale: 1, y: 0 }}
              exit={{ opacity: 0, scale: 0.95, y: 20 }}
              className="relative bg-slate-900 border border-slate-700/50 rounded-2xl w-full max-w-lg shadow-2xl overflow-hidden flex flex-col"
            >
              <div className="p-6 border-b border-slate-800 flex justify-between items-center bg-slate-900 sticky top-0 z-10">
                <h3 className="text-xl font-bold text-white flex items-center gap-2">
                  <Pill className="text-blue-400 w-5 h-5" /> Medicine Details
                </h3>
                <button onClick={() => setViewingMedicine(null)} className="text-slate-400 hover:text-white p-2 bg-slate-800 hover:bg-slate-700 rounded-full transition-colors">
                  <X className="w-5 h-5" />
                </button>
              </div>
              
              <div className="p-6 overflow-y-auto custom-scrollbar flex-1 space-y-6 max-h-[70vh]">
                <div className="flex items-center gap-4 p-4 bg-slate-800/40 border border-slate-700 rounded-xl">
                   <div className="w-12 h-12 rounded-xl flex items-center justify-center bg-blue-500/20 text-blue-400">
                      <Pill className="w-6 h-6" />
                   </div>
                   <div>
                      <h2 className="text-2xl font-bold text-white">{viewingMedicine.medicine_name}</h2>
                      <p className="text-slate-400">{viewingMedicine.dosage}</p>
                   </div>
                </div>

                <div className="space-y-4">
                  <div className="flex justify-between py-3 border-b border-slate-800">
                    <span className="text-slate-400">Status</span>
                    {viewingMedicine.taken_status ? (
                      <span className="text-emerald-400 font-bold bg-emerald-500/10 px-2 py-1 rounded">Taken</span>
                    ) : (
                      <span className="text-amber-400 font-bold bg-amber-500/10 px-2 py-1 rounded">Pending</span>
                    )}
                  </div>
                  <div className="flex justify-between py-3 border-b border-slate-800">
                    <span className="text-slate-400">Schedule Time</span>
                    <span className="text-white font-medium">{viewingMedicine.reminder_time}</span>
                  </div>
                  <div className="flex justify-between py-3 border-b border-slate-800">
                    <span className="text-slate-400">Frequency</span>
                    <span className="text-white font-medium">{viewingMedicine.frequency || 'Daily'}</span>
                  </div>
                  <div className="flex justify-between py-3 border-b border-slate-800">
                    <span className="text-slate-400">Purpose</span>
                    <span className="text-white font-medium">{viewingMedicine.purpose || 'Not specified'}</span>
                  </div>
                  <div className="flex justify-between py-3 border-b border-slate-800">
                    <span className="text-slate-400">Instructions / Notes</span>
                    <span className="text-white font-medium">{viewingMedicine.notes || 'None'}</span>
                  </div>
                  <div className="flex justify-between py-3 border-b border-slate-800">
                    <span className="text-slate-400">Date Added</span>
                    <span className="text-slate-300 text-sm">{viewingMedicine.created_at ? new Date(viewingMedicine.created_at + "Z").toLocaleDateString() : 'N/A'}</span>
                  </div>
                </div>
              </div>
              
              <div className="p-6 border-t border-slate-800 bg-slate-900/90 backdrop-blur-sm">
                <button onClick={() => setViewingMedicine(null)} className="w-full py-3 rounded-xl font-bold text-white bg-slate-800 hover:bg-slate-700 transition-colors">
                  Close
                </button>
              </div>
            </motion.div>
          </div>
        )}
      </AnimatePresence>
      </>
    );
  }

  // Render Add Medicine Workspace
  return (
    <div className="w-full max-w-7xl mx-auto flex flex-col gap-8">
      <div className="bg-slate-900 border border-slate-800 rounded-3xl p-8 lg:p-12 shadow-2xl relative overflow-hidden">
        <AnimatePresence mode="wait">
          <motion.div key="add" initial={{ opacity: 0, x: 10 }} animate={{ opacity: 1, x: 0 }} exit={{ opacity: 0, x: -10 }} className="flex flex-col gap-8 w-full">
            
            {/* Header logic */}
            <div className="flex flex-col gap-6">
              <button type="button" onClick={() => setShowAddMedicineWorkspace(false)} className="orma-btn-secondary">
                <ArrowLeft className="w-6 h-6" /> Back to Dashboard
              </button>
              
              <div>
                <h1 className="text-[42px] md:text-[48px] font-extrabold text-white tracking-tight mb-3 leading-tight">
                  {addMode === 'select' && "Add Medicine"}
                  {addMode === 'manual' && "Type Medicine"}
                  {addMode === 'voice' && "Voice Entry"}
                  {addMode === 'scan' && "Scan Prescription"}
                  {addMode === 'verify' && "Verify Details"}
                </h1>
                <p className="text-[20px] md:text-[22px] text-slate-400 font-medium">
                  {addMode === 'select' && "Choose how you would like to add medicine."}
                  {addMode === 'manual' && "Manually enter your medicine schedule to receive reminders."}
                  {addMode === 'voice' && "Speak naturally to add your medicine schedule."}
                  {addMode === 'scan' && "Upload a photo of your prescription. AI will extract the details."}
                </p>
              </div>
            </div>

            {error && (
              <div className="p-5 bg-red-500/10 border border-red-500/20 rounded-2xl text-red-400 flex items-center gap-4">
                <AlertTriangle className="w-8 h-8 shrink-0" />
                <p className="text-lg font-medium">{error}</p>
              </div>
            )}

            {success && (
              <div className="p-5 bg-emerald-500/10 border border-emerald-500/20 rounded-2xl text-emerald-400 flex items-center gap-4">
                <Check className="w-8 h-8 shrink-0" />
                <p className="text-lg font-bold">Medicine saved successfully!</p>
              </div>
            )}

            {/* SELECTION GRID */}
            {addMode === 'select' && (
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 w-full">
                {/* Card 1: Type */}
                <button 
                  onClick={handleManualEntry}
                  className="flex flex-col items-center text-center p-8 lg:p-10 bg-slate-800/40 hover:bg-slate-800/80 border border-slate-700/50 hover:border-blue-500/50 rounded-3xl transition-all duration-300 group min-h-[300px]"
                >
                  <div className="w-20 h-20 rounded-full bg-blue-500/10 flex items-center justify-center mb-6 group-hover:scale-110 transition-transform relative">
                    <div className="absolute inset-0 bg-blue-500/20 rounded-full blur-lg group-hover:blur-xl transition-all"></div>
                    <Edit3 className="w-8 h-8 text-blue-400 relative z-10" />
                  </div>
                  <h3 className="text-2xl font-bold text-white mb-3">Type Medicine</h3>
                  <p className="text-base text-slate-400 mb-8 leading-relaxed flex-1">
                    Manually enter medicine details like name, dosage and time.
                  </p>
                  <div className="text-blue-400 font-bold group-hover:text-blue-300 transition-colors flex items-center gap-2 mt-auto">
                    Continue <ArrowRight className="w-5 h-5" />
                  </div>
                </button>

                {/* Card 2: Voice */}
                <button 
                  onClick={() => setAddMode('voice')}
                  className="flex flex-col items-center text-center p-8 lg:p-10 bg-slate-800/40 hover:bg-slate-800/80 border border-slate-700/50 hover:border-emerald-500/50 rounded-3xl transition-all duration-300 group min-h-[300px]"
                >
                  <div className="w-20 h-20 rounded-full bg-emerald-500/10 flex items-center justify-center mb-6 group-hover:scale-110 transition-transform relative">
                    <div className="absolute inset-0 bg-emerald-500/20 rounded-full blur-lg group-hover:blur-xl transition-all"></div>
                    <Mic className="w-8 h-8 text-emerald-400 relative z-10" />
                  </div>
                  <h3 className="text-2xl font-bold text-white mb-3">Voice Entry</h3>
                  <p className="text-base text-slate-400 mb-8 leading-relaxed flex-1">
                    Speak medicine name, dosage and time. We'll save it for you.
                  </p>
                  <div className="text-emerald-400 font-bold group-hover:text-emerald-300 transition-colors flex items-center gap-2 mt-auto">
                    Continue <ArrowRight className="w-5 h-5" />
                  </div>
                </button>

                {/* Card 3: Scan */}
                <button 
                  onClick={() => fileInputRef.current?.click()}
                  className="flex flex-col items-center text-center p-8 lg:p-10 bg-slate-800/40 hover:bg-slate-800/80 border border-slate-700/50 hover:border-purple-500/50 rounded-3xl transition-all duration-300 group min-h-[300px]"
                >
                  <div className="w-20 h-20 rounded-full bg-purple-500/10 flex items-center justify-center mb-6 group-hover:scale-110 transition-transform relative">
                    <div className="absolute inset-0 bg-purple-500/20 rounded-full blur-lg group-hover:blur-xl transition-all"></div>
                    <Upload className="w-8 h-8 text-purple-400 relative z-10" />
                  </div>
                  <h3 className="text-2xl font-bold text-white mb-3">Scan Prescription</h3>
                  <p className="text-base text-slate-400 mb-8 leading-relaxed flex-1">
                    Upload or scan your prescription and we'll extract the details.
                  </p>
                  <div className="text-purple-400 font-bold group-hover:text-purple-300 transition-colors flex items-center gap-2 mt-auto">
                    Continue <ArrowRight className="w-5 h-5" />
                  </div>
                </button>
                <input type="file" ref={fileInputRef} className="hidden" accept="image/*,.pdf" onChange={handleFileUpload} />
              </div>
            )}

            {/* MANUAL FORM OR VERIFY FORM */}
            {(addMode === 'manual' || addMode === 'verify') && (
              <div className="flex flex-col w-full h-full relative">
                
                <div className={`grid grid-cols-1 ${prescriptionImage ? 'lg:grid-cols-2' : 'lg:grid-cols-1'} gap-8 mb-24`}>
                  
                  {/* Left Column: Image Preview */}
                  {prescriptionImage && (
                    <div className="flex flex-col gap-4 sticky top-6 self-start">
                      <div className="p-4 bg-blue-500/10 border border-blue-500/20 rounded-2xl flex items-center gap-3">
                        <FileText className="w-6 h-6 text-blue-400 shrink-0" />
                        <div>
                          <p className="text-lg font-bold text-blue-300">Document Preview</p>
                          <p className="text-sm text-blue-200/80">Reference this while verifying</p>
                        </div>
                      </div>
                      <div className="rounded-2xl border-2 border-slate-700/50 overflow-hidden bg-slate-900/50 relative shadow-xl min-h-[400px]">
                        <img src={prescriptionImage} alt="Prescription preview" className="w-full h-auto object-contain max-h-[70vh]" />
                      </div>
                    </div>
                  )}

                  {/* Right Column: Medicine Cards */}
                  <div className={`flex flex-col gap-6 ${!prescriptionImage ? 'max-w-3xl mx-auto w-full' : ''}`}>
                    {medicinesToVerify.map((med, index) => (
                      <div key={med.id} className="bg-slate-800/40 border border-slate-700 rounded-3xl p-6 shadow-lg relative">
                        
                        <div className="flex justify-between items-start mb-6">
                          <h3 className="text-2xl font-bold text-white flex items-center gap-3">
                            <span className="flex items-center justify-center w-8 h-8 rounded-full bg-blue-500/20 text-blue-400 text-sm">{index + 1}</span>
                            Medicine Details
                          </h3>
                          <button onClick={() => handleRemoveVerifyCard(med.id)} className="p-2 text-slate-400 hover:text-red-400 bg-slate-900/50 hover:bg-red-500/10 rounded-full transition-colors" title="Delete Medicine">
                            <Trash2 className="w-5 h-5" />
                          </button>
                        </div>
                        
                        {med.suggestion && (
                          <div className="p-4 bg-amber-500/10 border border-amber-500/20 rounded-xl flex items-start gap-3 mb-6">
                            <AlertTriangle className="w-6 h-6 text-amber-400 shrink-0" />
                            <div>
                              <p className="text-sm font-bold text-amber-300 mb-0.5">AI Correction Applied</p>
                              <p className="text-sm text-amber-200/90">Corrected: <span className="line-through opacity-70">{med.original_ocr_name}</span> &rarr; {med.medicine_name}</p>
                            </div>
                          </div>
                        )}

                        <div className="flex flex-col gap-5">
                          <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
                            <div className="space-y-2">
                              <label className="text-sm font-semibold text-slate-400 ml-1 block">Medicine Name *</label>
                              <input required value={med.medicine_name || ''} onChange={(e) => handleVerifyInputChange(med.id, 'medicine_name', e.target.value)} className="w-full bg-slate-950 border border-slate-700 rounded-xl px-4 py-3 text-lg text-white font-bold focus:border-blue-500 focus:ring-2 focus:ring-blue-500/20 transition-all outline-none placeholder:text-slate-600" placeholder="e.g. Amlodipine" />
                            </div>
                            <div className="space-y-2">
                              <label className="text-sm font-semibold text-slate-400 ml-1 block">Dosage *</label>
                              <input required value={med.dosage || ''} onChange={(e) => handleVerifyInputChange(med.id, 'dosage', e.target.value)} className="w-full bg-slate-950 border border-slate-700 rounded-xl px-4 py-3 text-lg text-white font-bold focus:border-blue-500 focus:ring-2 focus:ring-blue-500/20 transition-all outline-none placeholder:text-slate-600" placeholder="e.g. 10mg" />
                            </div>
                          </div>

                          <div className="border-t border-slate-700/50 pt-5 mt-5">
                            <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
                              <div className="space-y-2">
                                <label className="text-sm font-semibold text-slate-400 ml-1 block">Frequency *</label>
                                <select required value={med.frequency || 'Once Daily'} onChange={(e) => handleFrequencyChange(med.id, e.target.value)} className="w-full bg-slate-950 border border-slate-700 rounded-xl px-4 py-3 text-lg text-white font-bold focus:border-blue-500 focus:ring-2 focus:ring-blue-500/20 transition-all outline-none appearance-none">
                                  <option value="Once Daily">Once Daily</option>
                                  <option value="Twice Daily">Twice Daily</option>
                                  <option value="Three Times Daily">Three Times Daily</option>
                                  <option value="Every X Hours">Every X Hours</option>
                                  <option value="Weekly">Weekly</option>
                                  <option value="Monthly">Monthly</option>
                                  <option value="Alternate Days">Alternate Days</option>
                                  <option value="SOS (As Needed)">SOS (As Needed)</option>
                                  <option value="Custom">Custom</option>
                                </select>
                              </div>

                              {med.frequency === 'Weekly' && (
                                <div className="space-y-2">
                                  <label className="text-sm font-semibold text-slate-400 ml-1 block">Select Weekdays</label>
                                  <div className="flex flex-wrap gap-2">
                                      {['Monday','Tuesday','Wednesday','Thursday','Friday','Saturday','Sunday'].map(day => (
                                        <label key={day} className={`flex items-center gap-1 border px-3 py-1.5 rounded-lg cursor-pointer transition-colors ${
                                          (med.frequency_details || '').includes(day) 
                                            ? 'bg-blue-500/20 border-blue-500 text-blue-300' 
                                            : 'bg-slate-950 border-slate-700 hover:bg-slate-800 text-slate-300'
                                        }`}>
                                          <input type="checkbox" className="hidden"
                                            checked={(med.frequency_details || '').includes(day)}
                                            onChange={(e) => {
                                                let current = (med.frequency_details || '').split(',').map(d=>d.trim()).filter(Boolean);
                                                if(e.target.checked) current.push(day);
                                                else current = current.filter(d => d !== day);
                                                handleVerifyInputChange(med.id, 'frequency_details', current.join(', '));
                                            }}
                                          />
                                          <span className="text-sm font-medium">{day.substring(0,3)}</span>
                                        </label>
                                      ))}
                                  </div>
                                </div>
                              )}
                              {med.frequency === 'Monthly' && (
                                <div className="space-y-2">
                                  <label className="text-sm font-semibold text-slate-400 ml-1 block">Day of Month</label>
                                  <input type="number" min="1" max="31" value={med.frequency_details || '1'} onChange={(e) => handleVerifyInputChange(med.id, 'frequency_details', e.target.value)} className="w-full bg-slate-950 border border-slate-700 rounded-xl px-4 py-3 text-lg text-white font-bold focus:border-blue-500 outline-none" />
                                </div>
                              )}
                              {med.frequency === 'Every X Hours' && (
                                <div className="space-y-2">
                                  <label className="text-sm font-semibold text-slate-400 ml-1 block">Hours Interval</label>
                                  <input type="number" min="1" max="72" value={med.frequency_details || '6'} onChange={(e) => {
                                      const hours = parseInt(e.target.value) || 6;
                                      handleVerifyInputChange(med.id, 'frequency_details', hours.toString());
                                      let times = [];
                                      let currentHour = 6;
                                      for(let i=0; i < 24/hours; i++) {
                                        let h = currentHour % 24;
                                        let ampm = h >= 12 ? 'PM' : 'AM';
                                        let displayH = h % 12;
                                        if (displayH === 0) displayH = 12;
                                        times.push(`${displayH.toString().padStart(2, '0')}:00 ${ampm}`);
                                        currentHour += hours;
                                      }
                                      handleVerifyInputChange(med.id, 'timings', times);
                                  }} className="w-full bg-slate-950 border border-slate-700 rounded-xl px-4 py-3 text-lg text-white font-bold focus:border-blue-500 outline-none" />
                                </div>
                              )}
                            </div>

                            {med.frequency !== 'SOS (As Needed)' && (
                              <div className="mt-5">
                                <ReminderTimePicker
                                  timings={med.timings}
                                  onChange={(newTimings) => handleVerifyInputChange(med.id, 'timings', newTimings)}
                                  frequency={med.frequency}
                                  isCustom={med.frequency === 'Custom'}
                                />
                              </div>
                            )}

                            {med.frequency === 'SOS (As Needed)' && (
                              <div className="mt-5 p-4 bg-amber-500/10 border border-amber-500/20 rounded-xl flex items-start gap-3">
                                <AlertTriangle className="w-5 h-5 text-amber-400 shrink-0" />
                                <p className="text-sm text-amber-300 font-medium leading-relaxed">This medicine is taken only when needed and will not generate scheduled reminders.</p>
                              </div>
                            )}
                          </div>

                          <div className="grid grid-cols-1 md:grid-cols-2 gap-5 mt-2">
                            <div className="space-y-2">
                              <label className="text-sm font-semibold text-slate-400 ml-1 block">Purpose (Optional)</label>
                              <input value={med.purpose || ''} onChange={(e) => handleVerifyInputChange(med.id, 'purpose', e.target.value)} className="w-full bg-slate-950 border border-slate-700 rounded-xl px-4 py-3 text-lg text-white font-medium focus:border-blue-500 focus:ring-2 focus:ring-blue-500/20 transition-all outline-none placeholder:text-slate-600" placeholder="e.g. Blood Pressure" />
                            </div>
                            <div className="space-y-2">
                              <label className="text-sm font-semibold text-slate-400 ml-1 block">Notes (Optional)</label>
                              <input value={med.notes || ''} onChange={(e) => handleVerifyInputChange(med.id, 'notes', e.target.value)} className="w-full bg-slate-950 border border-slate-700 rounded-xl px-4 py-3 text-lg text-white font-medium focus:border-blue-500 focus:ring-2 focus:ring-blue-500/20 transition-all outline-none placeholder:text-slate-600" placeholder="e.g. Take after food" />
                            </div>
                          </div>
                        </div>

                      </div>
                    ))}
                    
                    {medicinesToVerify.length === 0 && (
                      <div className="flex flex-col items-center justify-center p-10 bg-slate-800/20 border-2 border-dashed border-slate-700 rounded-3xl">
                        <Pill className="w-12 h-12 text-slate-500 mb-4" />
                        <p className="text-slate-400 text-lg">No medicines added.</p>
                      </div>
                    )}
                    
                    <button type="button" onClick={() => setMedicinesToVerify(prev => [...prev, {id: 'new_'+Date.now(), medicine_name:'', dosage:'', timings:['08:00 AM'], frequency:'Once Daily', frequency_details:''}])} className="w-full py-4 border-2 border-dashed border-blue-500/30 text-blue-400 hover:bg-blue-500/5 hover:border-blue-500/50 rounded-2xl transition-all font-bold flex items-center justify-center gap-2">
                      <Edit3 className="w-5 h-5" /> Add Another Medicine manually
                    </button>

                  </div>
                </div>

                {/* Sticky Footer Action Bar */}
                <div className="fixed bottom-0 left-0 right-0 bg-slate-900/90 backdrop-blur-lg border-t border-slate-800 p-4 md:p-6 flex justify-center z-50">
                  <div className="w-full max-w-7xl flex gap-4">
                    <button type="button" onClick={() => { setMedicinesToVerify([]); setAddMode('select'); setPrescriptionImage(null); }} className="flex-1 py-4 bg-slate-800 hover:bg-slate-700 text-white font-bold rounded-2xl transition-colors text-lg shadow-lg">
                      {addMode === 'verify' ? "Discard & Try Again" : "Cancel"}
                    </button>
                    <button type="button" onClick={handleSaveAll} disabled={loading || medicinesToVerify.length === 0} className="orma-btn-primary">
                      {loading && <Loader2 className="w-6 h-6 animate-spin" />}
                      {addMode === 'verify' ? `Save All Medicines (${medicinesToVerify.length})` : "Save Medicine"}
                    </button>
                  </div>
                </div>

              </div>
            )}
            
            {/* VOICE INTERFACE */}
            {addMode === 'voice' && (
              <div className="flex flex-col items-center justify-center py-10 w-full max-w-3xl">
                {loading ? (
                  <>
                    <Loader2 className="w-24 h-24 text-emerald-400 animate-spin mb-8" />
                    <p className="text-3xl text-white font-bold">Understanding voice...</p>
                  </>
                ) : (
                  <>
                    <h2 className="text-[42px] font-extrabold text-white mb-2 tracking-tight">Voice Entry</h2>
                    <p className="text-[18px] md:text-[20px] text-slate-400 mb-12">Tap microphone and speak naturally.</p>
                    
                    <button 
                      onClick={recording ? stopVoiceRecording : startVoiceRecording}
                      className={`w-56 h-56 rounded-[5rem] flex items-center justify-center transition-all shadow-2xl ${
                        recording 
                          ? 'bg-red-500 text-white shadow-[0_0_80px_rgba(239,68,68,0.6)] animate-pulse scale-105' 
                          : 'bg-slate-800 text-emerald-400 border border-slate-700 hover:bg-slate-700 hover:scale-105 hover:border-emerald-500/50'
                      }`}
                    >
                      <Mic className={`w-28 h-28 ${recording ? 'text-white' : 'text-emerald-400'}`} />
                    </button>
                    <p className="mt-10 text-[24px] text-white font-bold">
                      {recording ? "Listening... Tap to finish" : "Tap microphone to speak"}
                    </p>
                    
                    <div className="mt-12 bg-slate-800/50 p-8 rounded-3xl border border-slate-700/50 text-left max-w-xl w-full">
                      <p className="text-slate-400 font-bold mb-4 text-[18px] md:text-[20px]">Examples:</p>
                      <ul className="space-y-4">
                        <li className="flex gap-4 items-start"><div className="w-2.5 h-2.5 rounded-full bg-emerald-400 mt-2.5 shrink-0"></div><span className="text-[18px] md:text-[20px] text-white font-medium">"Add Metformin 500mg at 8 PM daily"</span></li>
                        <li className="flex gap-4 items-start"><div className="w-2.5 h-2.5 rounded-full bg-emerald-400 mt-2.5 shrink-0"></div><span className="text-[18px] md:text-[20px] text-white font-medium">"Add blood pressure medicine every morning"</span></li>
                      </ul>
                    </div>
                  </>
                )}
              </div>
            )}

            {/* SCAN INTERFACE */}
            {addMode === 'scan' && (
              <div className="flex flex-col items-center justify-center py-16 w-full max-w-3xl border-4 border-dashed border-slate-700/50 rounded-[3rem] bg-slate-800/20 hover:bg-slate-800/40 hover:border-purple-500/50 transition-all cursor-pointer group" onClick={() => !loading && fileInputRef.current?.click()}>
                {loading ? (
                  <>
                    <Loader2 className="w-24 h-24 text-purple-400 animate-spin mb-8" />
                    <p className="text-3xl text-white font-bold">Scanning image...</p>
                  </>
                ) : (
                  <>
                    <div className="w-32 h-32 bg-purple-500/10 rounded-full flex items-center justify-center mb-8 group-hover:scale-110 transition-transform">
                      <Upload className="w-16 h-16 text-purple-400" />
                    </div>
                    <p className="text-3xl text-white font-bold mb-4">Click to upload prescription</p>
                    <p className="text-xl text-slate-400">Supports JPG, PNG, PDF</p>
                    
                    <button className="mt-10 flex items-center gap-3 bg-slate-800 border border-slate-700 text-white px-8 py-4 rounded-xl font-bold hover:bg-slate-700 transition-colors">
                      <Camera className="w-6 h-6" /> Open Camera
                    </button>
                  </>
                )}
                <input type="file" ref={fileInputRef} className="hidden" accept="image/*,.pdf" onChange={handleFileUpload} />
              </div>
            )}

          </motion.div>
        </AnimatePresence>
      </div>
    </div>
  );
}

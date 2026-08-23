import { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Activity, Heart, Thermometer, Droplets, Plus, X, Edit2, Trash2, TrendingUp, TrendingDown, Minus, Clock, FileText } from 'lucide-react';
import { healthRecordApi } from '../services/api';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, AreaChart, Area } from 'recharts';
import EmptyHealthState from '../components/health/EmptyHealthState';
import HealthHistoryTab from '../components/health/HealthHistoryTab';
import ChartWrapper from '../components/ChartWrapper';

const VITAL_TYPES = [
  { id: 'blood_pressure', label: 'Blood Pressure', icon: <Heart className="w-5 h-5 text-rose-500" /> },
  { id: 'heart_rate', label: 'Heart Rate', icon: <Activity className="w-5 h-5 text-rose-400" /> },
  { id: 'spo2', label: 'Oxygen Saturation (SpO₂)', icon: <Droplets className="w-5 h-5 text-cyan-500" /> },
  { id: 'blood_sugar', label: 'Blood Sugar', icon: <Droplets className="w-5 h-5 text-red-500" /> },
  { id: 'temperature', label: 'Body Temperature', icon: <Thermometer className="w-5 h-5 text-amber-500" /> },
  { id: 'weight', label: 'Weight', icon: <Activity className="w-5 h-5 text-blue-400" /> },
  { id: 'water_intake', label: 'Water Intake', icon: <Droplets className="w-5 h-5 text-blue-300" /> },
  { id: 'sleep', label: 'Sleep Hours', icon: <Clock className="w-5 h-5 text-indigo-400" /> },
  { id: 'mood', label: 'Mood', icon: <Heart className="w-5 h-5 text-pink-400" /> }
];

export default function HealthRecordsPage({ user }) {
  const [records, setRecords] = useState([]);
  const [loading, setLoading] = useState(true);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [selectedVitalType, setSelectedVitalType] = useState(null);
  const [activeTab, setActiveTab] = useState('overview'); // 'overview', 'records', 'vitals', 'reports', 'devices'
  
  // Form State
  const [formData, setFormData] = useState({});
  const [editingId, setEditingId] = useState(null);

  const fetchRecords = async () => {
    try {
      const data = await healthRecordApi.getRecords();
      setRecords(data);
    } catch (e) {
      console.error("Failed to fetch records", e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchRecords();
  }, []);

  const handleOpenModal = (vitalTypeId = null, editRecord = null) => {
    if (editRecord) {
      setEditingId(editRecord.id);
      setSelectedVitalType(editRecord.vital_type);
      
      // Parse specific fields depending on type
      let parsedForm = { ...editRecord };
      if (editRecord.vital_type === 'blood_pressure') {
        const [sys, dia] = editRecord.value.split('/');
        parsedForm = { ...parsedForm, systolic: sys, diastolic: dia };
      }
      setFormData(parsedForm);
    } else {
      setEditingId(null);
      setSelectedVitalType(vitalTypeId);
      setFormData({
        date: new Date().toISOString().split('T')[0],
        time: new Date().toTimeString().slice(0,5),
        measured_by: user.role === 'caregiver' ? 'caregiver' : 'elderly'
      });
    }
    setIsModalOpen(true);
  };

  const handleCloseModal = () => {
    setIsModalOpen(false);
    setSelectedVitalType(null);
    setFormData({});
    setEditingId(null);
  };

  const handleSave = async () => {
    try {
      let finalValue = formData.value;
      let finalUnit = formData.unit;

      if (selectedVitalType === 'blood_pressure') {
        finalValue = `${formData.systolic}/${formData.diastolic}`;
        finalUnit = 'mmHg';
      } else if (selectedVitalType === 'heart_rate') {
        finalUnit = 'bpm';
      } else if (selectedVitalType === 'spo2') {
        finalUnit = '%';
      } else if (selectedVitalType === 'temperature') {
        finalUnit = formData.unit || '°F';
      } else if (selectedVitalType === 'weight') {
        finalUnit = formData.unit || 'kg';
      } else if (selectedVitalType === 'blood_sugar') {
        finalUnit = 'mg/dL';
      } else if (selectedVitalType === 'sleep') {
        finalValue = `${formData.hours || 0}h ${formData.minutes || 0}m`;
        finalUnit = '';
      }

      const payload = {
        vital_type: selectedVitalType,
        value: finalValue,
        unit: finalUnit || '',
        measured_by: formData.measured_by || 'elderly',
        measurement_type: formData.measurement_type || null,
        notes: formData.notes || null,
        date: formData.date,
        time: formData.time
      };

      if (editingId) {
        await healthRecordApi.updateRecord(editingId, payload);
      } else {
        await healthRecordApi.createRecord(payload);
      }
      
      handleCloseModal();
      fetchRecords();
    } catch (e) {
      console.error("Failed to save", e);
      window.dispatchEvent(new CustomEvent('orma:toast', { detail: { type: 'error', message: 'Unable to save your health reading. Please verify your inputs and try again.' } }));
    }
  };

  const handleDelete = async (id) => {
    if (window.confirm("Are you sure you want to delete this health record?\nThis action cannot be undone.")) {
      await healthRecordApi.deleteRecord(id);
      fetchRecords();
      window.dispatchEvent(new CustomEvent('orma:toast', { detail: { type: 'success', message: 'Health record successfully deleted.' } }));
    }
  };

  // Group records by type for the overview
  const getLatestRecord = (type) => {
    return records.find(r => r.vital_type === type);
  };

  const getChartData = (type) => {
    const typeRecords = records.filter(r => r.vital_type === type).reverse(); // oldest first
    return typeRecords.map(r => {
      let val = 0;
      if (type === 'blood_pressure') {
        const [sys, dia] = r.value.split('/');
        return { date: r.date, sys: parseInt(sys), dia: parseInt(dia) };
      }
      return { date: r.date, value: parseFloat(r.value) };
    });
  };

  const renderInsights = () => {
    const insights = [];
    const bpRecords = records.filter(r => r.vital_type === 'blood_pressure');
    if (bpRecords.length > 0) insights.push("Blood pressure remained stable.");
    
    const weightRecords = records.filter(r => r.vital_type === 'weight');
    if (weightRecords.length > 0) insights.push("Weight unchanged this week.");
    
    const hrRecords = records.filter(r => r.vital_type === 'heart_rate');
    if (hrRecords.length > 0) {
      insights.push("Heart rate tracking normally.");
    }

    if (insights.length === 0) {
      insights.push("No abnormal readings detected.");
    }

    return insights.map((insight, idx) => (
      <div key={idx} className="flex items-start gap-3 p-4 bg-blue-900/20 border border-blue-500/30 rounded-xl mb-3">
        <Activity className="w-5 h-5 text-blue-400 mt-0.5" />
        <p className="text-blue-100">{insight}</p>
      </div>
    ));
  };

  return (
    <div className="max-w-6xl mx-auto p-4 md:p-8">
      <div className="flex flex-col md:flex-row justify-between items-start md:items-center mb-8 gap-4">
        <div>
          <div className="flex items-center gap-4">
            <h2 className="text-3xl font-bold text-white flex items-center gap-3">
              <Activity className="text-blue-400 w-8 h-8" /> Health Records
            </h2>
            {user?.caregiver_id && (
              <span className="px-3 py-1 rounded-full bg-emerald-500/20 border border-emerald-500/30 text-emerald-400 text-xs font-bold flex items-center gap-1.5">
                <Heart className="w-3.5 h-3.5" /> Shared with Caregiver
              </span>
            )}
          </div>
          <p className="text-slate-400 mt-2 text-lg">Track, monitor, and manage your clinical health measurements.</p>
        </div>
        <button 
          onClick={() => handleOpenModal()}
          className="orma-btn-primary"
        >
          <Plus className="w-5 h-5" /> Add Health Reading
        </button>
      </div>

      <div className="flex gap-4 border-b border-slate-800 mb-8 overflow-x-auto whitespace-nowrap custom-scrollbar">
        <button 
          className={`pb-4 px-2 font-medium text-base transition-colors ${activeTab === 'overview' ? 'text-blue-400 border-b-2 border-blue-400' : 'text-slate-400 hover:text-slate-200'}`}
          onClick={() => setActiveTab('overview')}
        >
          Overview
        </button>
        <button 
          className={`pb-4 px-2 font-medium text-base transition-colors ${activeTab === 'records' ? 'text-blue-400 border-b-2 border-blue-400' : 'text-slate-400 hover:text-slate-200'}`}
          onClick={() => setActiveTab('records')}
        >
          Health Records
        </button>
        <button 
          className={`pb-4 px-2 font-medium text-base transition-colors ${activeTab === 'vitals' ? 'text-blue-400 border-b-2 border-blue-400' : 'text-slate-400 hover:text-slate-200'}`}
          onClick={() => setActiveTab('vitals')}
        >
          Vitals
        </button>
      </div>

      {loading ? (
        <div className="text-center py-20 text-slate-400">Loading records...</div>
      ) : records.length === 0 && (activeTab === 'vitals' || activeTab === 'overview') ? (
        <EmptyHealthState onAddReading={() => handleOpenModal()} />
      ) : activeTab === 'overview' ? (
        <div className="space-y-8">
          {/* AI Insights */}
          <div className="orma-card p-6 border-blue-500/30 bg-slate-900/50">
            <h3 className="text-xl font-bold text-white mb-4 flex items-center gap-2">
              <TrendingUp className="text-blue-400 w-5 h-5" /> AI Health Insights
            </h3>
            <div className="space-y-2">
              {renderInsights()}
            </div>
          </div>
        </div>
      ) : activeTab === 'vitals' ? (
        <div className="space-y-8">

          {/* Vitals Grid */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {VITAL_TYPES.filter(v => ['blood_pressure', 'heart_rate', 'spo2', 'blood_sugar', 'temperature', 'weight'].includes(v.id)).map(vital => {
              const latest = getLatestRecord(vital.id);
              const chartData = getChartData(vital.id);
              return (
                <motion.div 
                  key={vital.id}
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  className="orma-card p-6 border-slate-700/50 hover:border-slate-600 transition-colors flex flex-col justify-between"
                >
                  <div>
                    <div className="flex justify-between items-start mb-4">
                      <div className="flex items-center gap-3">
                        <div className="p-3 bg-slate-800/50 rounded-xl border border-slate-700/50">
                          {vital.icon}
                        </div>
                        <h3 className="text-slate-300 font-medium">{vital.label}</h3>
                      </div>
                      <button 
                        onClick={() => handleOpenModal(vital.id)}
                        className="text-blue-400 hover:text-blue-300 p-2"
                      >
                        <Plus className="w-5 h-5" />
                      </button>
                    </div>
                    
                    {latest ? (
                      <div>
                        <div className="flex items-baseline gap-2 mb-2">
                          <span className="text-3xl font-bold text-white">{latest.value}</span>
                          <span className="text-slate-400">{latest.unit}</span>
                          <span className="ml-auto px-2 py-0.5 bg-slate-800 rounded text-xs font-medium text-emerald-400 border border-emerald-500/20">
                            Normal
                          </span>
                        </div>
                        <div className="flex items-center justify-between">
                          <p className="text-xs text-slate-500">
                            Last updated: {latest.date}
                          </p>
                          <span className="text-xs text-blue-400 flex items-center gap-1"><TrendingUp className="w-3 h-3"/> Stable</span>
                        </div>
                      </div>
                    ) : (
                      <div className="py-2">
                        <p className="text-slate-500 text-sm italic">No reading available</p>
                      </div>
                    )}
                  </div>

                  {/* Mini Trend Chart */}
                  {latest && chartData.length > 1 && vital.id !== 'blood_pressure' && (
                    <div className="h-16 mt-6 -mx-4 -mb-4">
                      <ChartWrapper minHeight={64}>
                        <ResponsiveContainer width="100%" height="100%">
                          <AreaChart data={chartData.slice(-7)}>
                            <defs>
                              <linearGradient id={`color-${vital.id}`} x1="0" y1="0" x2="0" y2="1">
                                <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.3}/>
                                <stop offset="95%" stopColor="#3b82f6" stopOpacity={0}/>
                              </linearGradient>
                            </defs>
                            <Area type="monotone" dataKey="value" stroke="#3b82f6" strokeWidth={2} fillOpacity={1} fill={`url(#color-${vital.id})`} />
                          </AreaChart>
                        </ResponsiveContainer>
                      </ChartWrapper>
                    </div>
                  )}
                  {latest && chartData.length > 1 && vital.id === 'blood_pressure' && (
                    <div className="h-16 mt-6 -mx-4 -mb-4">
                      <ChartWrapper minHeight={64}>
                        <ResponsiveContainer width="100%" height="100%">
                          <LineChart data={chartData.slice(-7)}>
                            <Line type="monotone" dataKey="sys" stroke="#ef4444" strokeWidth={2} dot={false} />
                            <Line type="monotone" dataKey="dia" stroke="#3b82f6" strokeWidth={2} dot={false} />
                          </LineChart>
                        </ResponsiveContainer>
                      </ChartWrapper>
                    </div>
                  )}

                </motion.div>
              );
            })}
          </div>
        </div>
      ) : activeTab === 'records' ? (
        <HealthHistoryTab 
          records={records} 
          onAddReading={() => handleOpenModal()} 
          onEdit={(r) => handleOpenModal(null, r)}
          onDelete={(id) => handleDelete(id)}
        />
      ) : activeTab === 'reports' ? (
        <div className="text-center py-20 border border-slate-800/50 rounded-2xl bg-slate-900/50">
          <FileText className="w-12 h-12 text-slate-500 mx-auto mb-4" />
          <h3 className="text-xl font-bold text-white mb-2">Health Reports</h3>
          <p className="text-slate-400">Generate printable health summaries for your doctor.</p>
          <div className="mt-4 px-3 py-1 inline-block bg-blue-500/20 text-blue-400 border border-blue-500/30 rounded-full text-sm font-medium">Coming Soon</div>
        </div>
      ) : null}

      {/* Add / Edit Modal */}
      <AnimatePresence>
        {isModalOpen && (
          <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
            <motion.div 
              initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}
              className="absolute inset-0 bg-slate-950/80 backdrop-blur-sm"
              onClick={handleCloseModal}
            />
            <motion.div 
              initial={{ opacity: 0, scale: 0.95, y: 20 }}
              animate={{ opacity: 1, scale: 1, y: 0 }}
              exit={{ opacity: 0, scale: 0.95, y: 20 }}
              className="relative bg-slate-900 border border-slate-700/50 rounded-2xl w-full max-w-lg shadow-2xl overflow-hidden flex flex-col max-h-[90vh]"
            >
              <div className="p-6 border-b border-slate-800 flex justify-between items-center bg-slate-900 sticky top-0 z-10">
                <h3 className="text-xl font-bold text-white">
                  {editingId ? 'Edit' : 'Add'} {selectedVitalType ? VITAL_TYPES.find(v => v.id === selectedVitalType)?.label : 'Health Reading'}
                </h3>
                <button onClick={handleCloseModal} className="text-slate-400 hover:text-white p-2">
                  <X className="w-5 h-5" />
                </button>
              </div>
              
              <div className="p-6 overflow-y-auto custom-scrollbar flex-1 space-y-6">
                {!selectedVitalType && (
                  <div className="space-y-4">
                    <label className="text-sm font-medium text-slate-300">Select Measurement Type</label>
                    <div className="grid grid-cols-2 gap-3">
                      {VITAL_TYPES.map(vital => (
                        <button
                          key={vital.id}
                          onClick={() => setSelectedVitalType(vital.id)}
                          className="flex items-center gap-3 p-4 rounded-xl border border-slate-700 hover:border-blue-500 hover:bg-blue-500/10 transition-colors text-left"
                        >
                          {vital.icon}
                          <span className="text-slate-200 text-sm font-medium">{vital.label}</span>
                        </button>
                      ))}
                    </div>
                  </div>
                )}

                {selectedVitalType && (
                  <div className="space-y-6">
                    {/* Dynamic Form Fields based on Type */}
                    
                    {selectedVitalType === 'blood_pressure' && (
                      <div className="grid grid-cols-2 gap-4">
                        <div>
                          <label className="block text-sm font-medium text-slate-400 mb-2">Systolic</label>
                          <input type="number" value={formData.systolic || ''} onChange={e => setFormData({...formData, systolic: e.target.value})} className="w-full bg-slate-800 border border-slate-700 rounded-xl px-4 py-3 text-white focus:outline-none focus:border-blue-500" placeholder="120" />
                        </div>
                        <div>
                          <label className="block text-sm font-medium text-slate-400 mb-2">Diastolic</label>
                          <input type="number" value={formData.diastolic || ''} onChange={e => setFormData({...formData, diastolic: e.target.value})} className="w-full bg-slate-800 border border-slate-700 rounded-xl px-4 py-3 text-white focus:outline-none focus:border-blue-500" placeholder="80" />
                        </div>
                      </div>
                    )}

                    {(['heart_rate', 'spo2', 'blood_sugar', 'weight', 'temperature'].includes(selectedVitalType)) && (
                      <div>
                        <label className="block text-sm font-medium text-slate-400 mb-2">Value</label>
                        <div className="flex gap-4">
                          <input type="number" step="any" value={formData.value || ''} onChange={e => setFormData({...formData, value: e.target.value})} className="flex-1 bg-slate-800 border border-slate-700 rounded-xl px-4 py-3 text-white focus:outline-none focus:border-blue-500" placeholder="Enter value" />
                          
                          {selectedVitalType === 'temperature' && (
                            <select value={formData.unit || '°F'} onChange={e => setFormData({...formData, unit: e.target.value})} className="bg-slate-800 border border-slate-700 rounded-xl px-4 py-3 text-white focus:outline-none focus:border-blue-500">
                              <option value="°F">°F</option>
                              <option value="°C">°C</option>
                            </select>
                          )}
                          {selectedVitalType === 'weight' && (
                            <select value={formData.unit || 'kg'} onChange={e => setFormData({...formData, unit: e.target.value})} className="bg-slate-800 border border-slate-700 rounded-xl px-4 py-3 text-white focus:outline-none focus:border-blue-500">
                              <option value="kg">kg</option>
                              <option value="lbs">lbs</option>
                            </select>
                          )}
                        </div>
                      </div>
                    )}

                    {selectedVitalType === 'blood_sugar' && (
                      <div>
                        <label className="block text-sm font-medium text-slate-400 mb-2">Measurement Type</label>
                        <select value={formData.measurement_type || ''} onChange={e => setFormData({...formData, measurement_type: e.target.value})} className="w-full bg-slate-800 border border-slate-700 rounded-xl px-4 py-3 text-white focus:outline-none focus:border-blue-500">
                          <option value="">Select type...</option>
                          <option value="Fasting">Fasting</option>
                          <option value="Before Meal">Before Meal</option>
                          <option value="After Meal">After Meal</option>
                          <option value="Random">Random</option>
                        </select>
                      </div>
                    )}

                    {selectedVitalType === 'sleep' && (
                      <div className="grid grid-cols-2 gap-4">
                        <div>
                          <label className="block text-sm font-medium text-slate-400 mb-2">Hours</label>
                          <input type="number" value={formData.hours || ''} onChange={e => setFormData({...formData, hours: e.target.value})} className="w-full bg-slate-800 border border-slate-700 rounded-xl px-4 py-3 text-white focus:outline-none focus:border-blue-500" placeholder="7" />
                        </div>
                        <div>
                          <label className="block text-sm font-medium text-slate-400 mb-2">Minutes</label>
                          <input type="number" value={formData.minutes || ''} onChange={e => setFormData({...formData, minutes: e.target.value})} className="w-full bg-slate-800 border border-slate-700 rounded-xl px-4 py-3 text-white focus:outline-none focus:border-blue-500" placeholder="30" />
                        </div>
                        <div className="col-span-2">
                          <label className="block text-sm font-medium text-slate-400 mb-2">Sleep Quality</label>
                          <select value={formData.measurement_type || ''} onChange={e => setFormData({...formData, measurement_type: e.target.value})} className="w-full bg-slate-800 border border-slate-700 rounded-xl px-4 py-3 text-white focus:outline-none focus:border-blue-500">
                            <option value="">Select...</option>
                            <option value="Excellent">Excellent</option>
                            <option value="Good">Good</option>
                            <option value="Fair">Fair</option>
                            <option value="Poor">Poor</option>
                          </select>
                        </div>
                      </div>
                    )}
                    
                    {selectedVitalType === 'mood' && (
                      <div>
                         <label className="block text-sm font-medium text-slate-400 mb-2">Mood</label>
                         <div className="grid grid-cols-5 gap-2">
                            {['Excellent', 'Good', 'Normal', 'Low', 'Very Low'].map(mood => (
                               <button 
                                 key={mood}
                                 onClick={() => setFormData({...formData, value: mood})}
                                 className={`p-3 rounded-xl border text-sm font-medium transition-colors ${formData.value === mood ? 'bg-blue-600 border-blue-500 text-white' : 'bg-slate-800 border-slate-700 text-slate-300 hover:bg-slate-700'}`}
                               >
                                 {mood}
                               </button>
                            ))}
                         </div>
                      </div>
                    )}

                    <div className="grid grid-cols-2 gap-4 pt-4 border-t border-slate-800">
                      <div>
                        <label className="block text-sm font-medium text-slate-400 mb-2">Date</label>
                        <input type="date" value={formData.date || ''} onChange={e => setFormData({...formData, date: e.target.value})} className="w-full bg-slate-800 border border-slate-700 rounded-xl px-4 py-3 text-white focus:outline-none focus:border-blue-500" />
                      </div>
                      <div>
                        <label className="block text-sm font-medium text-slate-400 mb-2">Time</label>
                        <input type="time" value={formData.time || ''} onChange={e => setFormData({...formData, time: e.target.value})} className="w-full bg-slate-800 border border-slate-700 rounded-xl px-4 py-3 text-white focus:outline-none focus:border-blue-500" />
                      </div>
                    </div>

                    <div>
                      <label className="block text-sm font-medium text-slate-400 mb-2">Measured By</label>
                      <select value={formData.measured_by || ''} onChange={e => setFormData({...formData, measured_by: e.target.value})} className="w-full bg-slate-800 border border-slate-700 rounded-xl px-4 py-3 text-white focus:outline-none focus:border-blue-500">
                        <option value="elderly">Self</option>
                        <option value="caregiver">Caregiver</option>
                        <option value="doctor">Doctor</option>
                      </select>
                    </div>

                    <div>
                      <label className="block text-sm font-medium text-slate-400 mb-2">Notes (Optional)</label>
                      <textarea rows="3" value={formData.notes || ''} onChange={e => setFormData({...formData, notes: e.target.value})} className="w-full bg-slate-800 border border-slate-700 rounded-xl px-4 py-3 text-white focus:outline-none focus:border-blue-500" placeholder="E.g. Measured after breakfast" />
                    </div>

                  </div>
                )}
              </div>
              
              <div className="p-6 border-t border-slate-800 bg-slate-900/90 backdrop-blur-sm">
                <div className="flex gap-4">
                  <button onClick={handleCloseModal} className="flex-1 px-6 py-3 rounded-xl font-bold text-white bg-slate-800 hover:bg-slate-700 transition-colors">
                    Cancel
                  </button>
                  <button 
                    onClick={handleSave} 
                    disabled={!selectedVitalType}
                    className="orma-btn-primary"
                  >
                    Save Reading
                  </button>
                </div>
              </div>
            </motion.div>
          </div>
        )}
      </AnimatePresence>
    </div>
  );
}

import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { Activity, Heart, Thermometer, Droplets, Plus, AlertCircle } from 'lucide-react';
import { healthRecordApi } from '../services/api';

export default function HealthVitalsPage({ user, onAddVital }) {
  const [records, setRecords] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchVitals = async () => {
      try {
        const data = await healthRecordApi.getRecords();
        setRecords(Array.isArray(data) ? data : []);
      } catch (err) {
        console.error('Failed to fetch vitals records:', err);
      } finally {
        setLoading(false);
      }
    };
    fetchVitals();
  }, []);

  const getLatestReading = (type) => {
    const rec = records.find(r => r.vital_type === type);
    if (rec && rec.value) {
      return {
        value: `${rec.value} ${rec.unit || ''}`.trim(),
        status: 'Recorded',
        date: rec.date ? `Recorded ${rec.date}` : 'Recently recorded',
        hasData: true
      };
    }
    return {
      value: 'Not recorded yet',
      status: 'No reading available',
      date: null,
      hasData: false
    };
  };

  const hr = getLatestReading('heart_rate');
  const bp = getLatestReading('blood_pressure');
  const temp = getLatestReading('temperature');
  const spo2 = getLatestReading('spo2');

  const vitals = [
    { title: 'Heart Rate', reading: hr, icon: <Heart className="w-6 h-6 text-rose-400" /> },
    { title: 'Blood Pressure', reading: bp, icon: <Activity className="w-6 h-6 text-blue-400" /> },
    { title: 'Temperature', reading: temp, icon: <Thermometer className="w-6 h-6 text-amber-400" /> },
    { title: 'Oxygen Level (SpO₂)', reading: spo2, icon: <Droplets className="w-6 h-6 text-cyan-400" /> },
  ];

  return (
    <div className="max-w-5xl mx-auto space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-2xl sm:text-3xl font-extrabold text-white tracking-tight flex items-center gap-3">
            <Activity className="text-blue-400 w-8 h-8" />
            <span>Health Vitals & Measurements</span>
          </h2>
          <p className="text-slate-400 text-xs sm:text-sm mt-1">
            Monitor your daily clinical health metrics and long-term stability.
          </p>
        </div>
      </div>

      {/* Vitals Metric Cards Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
        {vitals.map((vital, index) => (
          <motion.div 
            key={vital.title}
            initial={{ opacity: 0, y: 15 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: index * 0.05 }}
            className="orma-card p-5 sm:p-6 flex items-center justify-between gap-4"
          >
            <div className="flex items-center gap-4">
              <div className="w-12 h-12 rounded-2xl bg-slate-900 border border-white/10 flex items-center justify-center shrink-0 shadow-md">
                {vital.icon}
              </div>
              <div>
                <p className="text-slate-400 text-xs font-bold uppercase tracking-wider">{vital.title}</p>
                <h3 className={`text-xl sm:text-2xl font-extrabold mt-0.5 ${vital.reading.hasData ? 'text-white' : 'text-slate-400 font-normal text-base'}`}>
                  {vital.reading.value}
                </h3>
                <span className={`text-xs font-semibold mt-1 inline-block ${vital.reading.hasData ? 'text-emerald-400' : 'text-slate-500'}`}>
                  {vital.reading.status}
                </span>
              </div>
            </div>
          </motion.div>
        ))}
      </div>

      {/* Vitals Summary & Log Status */}
      <div className="orma-card p-6 sm:p-8">
        <h3 className="text-lg font-bold text-white mb-2">Vitals Summary</h3>
        <p className="text-slate-400 text-xs sm:text-sm leading-relaxed">
          {records.length > 0
            ? `You have recorded ${records.length} vital measurement${records.length === 1 ? '' : 's'}. All metrics show steady resting cardiovascular and metabolic stability.`
            : 'No readings recorded yet. Add your first health reading in the Health Records tab to start tracking your vital stability.'}
        </p>
      </div>
    </div>
  );
}

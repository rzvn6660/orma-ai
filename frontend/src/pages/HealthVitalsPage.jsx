import { motion } from 'framer-motion';
import { Activity, Heart, Thermometer, Droplets } from 'lucide-react';

export default function HealthVitalsPage({ user }) {
  const vitals = [
    { title: 'Heart Rate', value: '72 bpm', status: 'Normal', icon: <Heart className="w-6 h-6 text-rose-500" /> },
    { title: 'Blood Pressure', value: '120/80', status: 'Optimal', icon: <Activity className="w-6 h-6 text-blue-500" /> },
    { title: 'Temperature', value: '98.6 °F', status: 'Normal', icon: <Thermometer className="w-6 h-6 text-amber-500" /> },
    { title: 'Oxygen', value: '98%', status: 'Normal', icon: <Droplets className="w-6 h-6 text-cyan-500" /> },
  ];

  return (
    <div className="max-w-4xl mx-auto space-y-8 p-4 md:p-8">
      <div className="mb-8">
        <h2 className="text-3xl font-bold text-white flex items-center gap-3">
          <Activity className="text-blue-400 w-8 h-8" /> Health Vitals
        </h2>
        <p className="text-slate-400 mt-2 text-lg">Monitor your daily health metrics and trends.</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {vitals.map((vital, index) => (
          <motion.div 
            key={vital.title}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: index * 0.1 }}
            className="orma-card p-6 border-slate-700/50 flex items-center gap-6"
          >
            <div className="p-4 bg-slate-800/50 rounded-2xl border border-slate-700/50">
              {vital.icon}
            </div>
            <div>
              <p className="text-slate-400 text-sm font-medium uppercase tracking-widest">{vital.title}</p>
              <h3 className="text-3xl font-bold text-white mt-1">{vital.value}</h3>
              <p className="text-emerald-400 text-sm font-medium mt-1">{vital.status}</p>
            </div>
          </motion.div>
        ))}
      </div>

      <div className="orma-card p-8 border-slate-700/50 mt-8">
        <h3 className="text-xl font-bold text-white mb-4">Weekly Trend</h3>
        <div className="orma-empty-state">
          <p className="text-slate-500 font-medium">Wearable device integration coming soon.</p>
        </div>
      </div>
    </div>
  );
}

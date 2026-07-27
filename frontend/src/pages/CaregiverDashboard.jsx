import { useEffect } from 'react';
import DashboardLayout from '../layouts/DashboardLayout';
import { motion } from 'framer-motion';
import { caregiverApi, wellnessApi, medicineApi, healthPlannerApi } from '../services/api';
import { useApi } from '../hooks/useApi';
import { Activity, Pill, AlertOctagon, Heart, CheckCircle2, AlertTriangle, ShieldCheck, Clock, TrendingUp, User, Brain, Frown } from 'lucide-react';
import CaregiverLinkManager from '../components/CaregiverLinkManager';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import ErrorBoundary from '../components/ErrorBoundary';
import ChartWrapper from '../components/ChartWrapper';

export default function CaregiverDashboard({ currentView, onViewChange, user, onLogout }) {
  const { data: summary, execute: loadSummary } = useApi(caregiverApi.getSummary);
  const { data: adherence, execute: loadAdherence } = useApi(caregiverApi.getAdherence);
  const { data: emergencies, execute: loadEmergencies } = useApi(caregiverApi.getEmergencies);
  const { data: behavior, execute: loadBehavior } = useApi(caregiverApi.getBehavior);
  const { data: wellness, execute: loadWellness } = useApi(wellnessApi.getSummary);
  
  const { data: allEvents, execute: loadEvents } = useApi(healthPlannerApi.getEvents);

  useEffect(() => {
    const handleWsMessage = (e) => {
      if (e.detail?.type === 'medicine_taken') {
        loadEvents();
        loadSummary();
        loadBehavior();
      }
    };
    window.addEventListener('orma_websocket_message', handleWsMessage);
    return () => window.removeEventListener('orma_websocket_message', handleWsMessage);
  }, [loadEvents, loadSummary, loadBehavior]);

  useEffect(() => {
    loadSummary();
    loadAdherence();
    loadEmergencies();
    loadBehavior();
    loadWellness();
    loadEvents();
  }, [loadSummary, loadAdherence, loadEmergencies, loadBehavior, loadWellness, loadEvents]);

  const displaySummary = summary?.completion_percentage !== undefined ? summary : {
    completion_percentage: 88,
    medicines_taken: 5,
    pending_medicines: 2,
    missed_medicines: 0
  };

  const displayAdherence = adherence?.consistency_score !== undefined ? adherence : {
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

  const displayBehavior = behavior?.confirmation_stats ? behavior : {
    confirmation_stats: { voice: 18, manual: 4, suspicious: 1, unverified: 0 },
    insights: [
      "User consistently takes morning meds on time.",
      "Requires 2 prompts on average for evening doses.",
      "Shows slight confusion when schedule changes."
    ]
  };

  const displayEmergencies = emergencies?.total_history !== undefined ? emergencies : {
    total_history: 1,
    recent_triggers: [
      { id: 1, type: 'Missed Critical Meds', time: 'Yesterday, 9:00 AM', severity: 'medium', resolved: true }
    ]
  };

  const displayWellness = wellness?.status ? wellness : {
    status: 'Monitoring',
    emotions: { calmness: 8, anxiety: 1, sadness: 0 },
    confusion_events_recent: 0,
    repeated_questions: 1
  };

  return (
    <ErrorBoundary>
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-white mb-2">Family Caregiver Monitor</h1>
        <p className="text-slate-400">AI-assisted adherence monitoring and behavioral tracking.</p>
      </div>

      {/* Top Stats */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
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

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-8">
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

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Behavioral Insights */}
        <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} className="orma-card p-6">
          <h3 className="text-xl font-bold text-white mb-6 flex items-center gap-2">
            <Heart className="text-pink-400 w-5 h-5" /> Behavioral Insights
          </h3>
          <div className="space-y-3">
            {displayBehavior.insights.map((insight, idx) => (
              <div key={idx} className="flex items-start gap-3 p-3 bg-slate-800/30 rounded-lg border border-slate-700/30">
                <div className="w-2 h-2 rounded-full bg-pink-400 mt-2 shrink-0"></div>
                <p className="text-slate-300">{insight}</p>
              </div>
            ))}
            {displayBehavior.insights.length === 0 && (
              <p className="text-slate-500 italic">No behavioral insights available yet.</p>
            )}
          </div>
        </motion.div>

        {/* Emergency Alerts */}
        <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.1 }} className="orma-card p-6">
          <div className="flex justify-between items-center mb-6">
            <h3 className="text-xl font-bold text-white flex items-center gap-2">
              <AlertOctagon className="text-red-400 w-5 h-5" /> Recent Alerts
            </h3>
            <span className="text-xs text-slate-400">{displayEmergencies.total_history} total on record</span>
          </div>
          <div className="space-y-4">
            {displayEmergencies.recent_triggers.map((alert) => (
              <div key={alert.id} className={`p-4 rounded-xl border ${alert.severity === 'high' ? 'bg-red-500/10 border-red-500/30' : 'bg-amber-500/10 border-amber-500/30'}`}>
                <div className="flex justify-between items-start mb-1">
                  <h4 className={`font-bold ${alert.severity === 'high' ? 'text-red-400' : 'text-amber-400'}`}>{alert.type}</h4>
                  <span className="text-xs text-slate-400">{alert.time}</span>
                </div>
                <p className="text-sm text-slate-300">
                  Status: {alert.resolved ? <span className="text-emerald-400">Resolved</span> : <span className="text-red-400">Action Needed</span>}
                </p>
              </div>
            ))}
            {displayEmergencies.recent_triggers.length === 0 && (
              <div className="p-6 text-center border border-dashed border-slate-700 rounded-xl">
                <p className="text-emerald-400 font-medium">All clear</p>
                <p className="text-sm text-slate-500">No recent emergencies detected.</p>
              </div>
            )}
          </div>
        </motion.div>
      </div>

      <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.2 }} className="orma-card p-6 mt-6 border-blue-500/20">
        <div className="flex justify-between items-center mb-6">
          <h3 className="text-xl font-bold text-white flex items-center gap-2">
            <Brain className="text-purple-400 w-5 h-5" /> Cognitive & Emotional Wellness
          </h3>
          <div className={`px-3 py-1 rounded-full text-xs font-bold border 
            ${displayWellness.status === 'Needs Attention' ? 'bg-amber-500/20 text-amber-400 border-amber-500/30' : 
              displayWellness.status === 'High Cognitive Concern' ? 'bg-red-500/20 text-red-400 border-red-500/30' : 
              'bg-emerald-500/20 text-emerald-400 border-emerald-500/30'}`}>
            Status: {displayWellness.status}
          </div>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div className="bg-slate-800/30 p-4 rounded-xl border border-slate-700/50">
            <h4 className="text-slate-400 text-sm font-medium mb-1">Emotion Detection</h4>
            <div className="flex gap-4 mt-2">
              <div className="flex flex-col items-center">
                <span className="text-2xl font-bold text-slate-300">{displayWellness.emotions.calmness}</span>
                <span className="text-xs text-slate-500">Calm</span>
              </div>
              <div className="flex flex-col items-center">
                <span className="text-2xl font-bold text-amber-400">{displayWellness.emotions.anxiety}</span>
                <span className="text-xs text-slate-500">Anxious</span>
              </div>
              <div className="flex flex-col items-center">
                <span className="text-2xl font-bold text-blue-400">{displayWellness.emotions.sadness}</span>
                <span className="text-xs text-slate-500">Sad</span>
              </div>
            </div>
          </div>
          
          <div className="bg-slate-800/30 p-4 rounded-xl border border-slate-700/50">
            <h4 className="text-slate-400 text-sm font-medium mb-1">Confusion Incidents</h4>
            <div className="flex items-end gap-2">
              <span className="text-3xl font-bold text-white">{displayWellness.confusion_events_recent}</span>
              <span className="text-sm text-slate-400 mb-1">recently detected</span>
            </div>
            <p className="text-xs text-purple-400 mt-2">Repeated questions: {displayWellness.repeated_questions}</p>
          </div>
          
          <div className="bg-slate-800/30 p-4 rounded-xl border border-slate-700/50 flex flex-col justify-between">
            <div>
              <h4 className="text-slate-400 text-sm font-medium mb-1">AI Adaptation</h4>
              <p className="text-xs text-slate-300">
                Orma AI adjusts response complexity based on detected confusion levels.
              </p>
            </div>
            {displayWellness.confusion_events_recent > 0 ? (
              <p className="text-xs font-medium text-amber-400 flex items-center gap-1 mt-2">
                <AlertTriangle className="w-3 h-3" /> System is using simplified responses
              </p>
            ) : (
              <p className="text-xs font-medium text-emerald-400 flex items-center gap-1 mt-2">
                <CheckCircle2 className="w-3 h-3" /> Standard conversation mode active
              </p>
            )}
          </div>
        </div>
      </motion.div>

      {/* Recent Medicine Logs */}
      <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.3 }} className="orma-card p-6 mt-6">
        <div className="flex justify-between items-center mb-6">
          <h3 className="text-xl font-bold text-white flex items-center gap-2">
            <Pill className="text-blue-400 w-5 h-5" /> Recent Health Events Logs
          </h3>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse">
            <thead>
              <tr className="border-b border-slate-700 text-slate-400 text-sm">
                <th className="pb-3 pl-2">Event</th>
                <th className="pb-3">Status</th>
                <th className="pb-3">Time Taken (Local)</th>
              </tr>
            </thead>
            <tbody>
              {allEvents?.filter(e => e.status)?.map(event => {
                let takenTimeStr = "Not completed yet";
                if (event.completed_at) {
                  const takenDate = new Date(event.completed_at + "Z"); // Parse as UTC
                  takenTimeStr = takenDate.toLocaleTimeString('en-US', {
                    hour: '2-digit',
                    minute: '2-digit',
                    timeZone: user?.timezone || Intl.DateTimeFormat().resolvedOptions().timeZone,
                    timeZoneName: 'short'
                  });
                }

                return (
                  <tr key={event.id} className="border-b border-slate-800/50 hover:bg-slate-800/30 transition-colors">
                    <td className="py-4 pl-2 font-medium text-white">{event.title}</td>
                    <td className="py-4">
                      <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium bg-emerald-500/10 text-emerald-400">
                        <CheckCircle2 className="w-3 h-3" /> Completed
                      </span>
                    </td>
                    <td className="py-4 text-slate-300 font-medium">{takenTimeStr}</td>
                  </tr>
                );
              })}
              {(!allEvents || allEvents.filter(e => e.status).length === 0) && (
                <tr>
                  <td colSpan="3" className="py-8 text-center text-slate-500">
                    No recent events completed.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </motion.div>
    </ErrorBoundary>
  );
}

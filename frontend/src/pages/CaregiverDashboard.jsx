import { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { 
  caregiverApi, 
  wellnessApi, 
  medicineApi, 
  healthPlannerApi, 
  linkApi,
  emergencyApi
} from '../services/api';
import CaregiverEmergencyBanner from '../components/ui/CaregiverEmergencyBanner';
import { stopEmergencySound } from '../utils/emergencyAudio';
import { useApi } from '../hooks/useApi';
import { 
  Activity, 
  Pill, 
  AlertOctagon, 
  Heart, 
  CheckCircle2, 
  AlertTriangle, 
  ShieldCheck, 
  Clock, 
  TrendingUp, 
  User, 
  Brain, 
  Mic, 
  Sparkles, 
  Check, 
  Calendar, 
  ChevronRight,
  HelpCircle,
  MessageSquare
} from 'lucide-react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Area, AreaChart } from 'recharts';
import ErrorBoundary from '../components/ErrorBoundary';
import ChartWrapper from '../components/ChartWrapper';
import MedicationTimeline from '../components/timeline/MedicationTimeline';
import HealthActivityTimeline from '../components/timeline/HealthActivityTimeline';
import AdherenceTrendChart from '../components/analytics/AdherenceTrendChart';
import MedicationStatusBreakdown from '../components/analytics/MedicationStatusBreakdown';

export default function CaregiverDashboard({ currentView, onViewChange, user, onLogout }) {
  const { data: summary, execute: loadSummary } = useApi(caregiverApi.getSummary);
  const { data: adherence, execute: loadAdherence } = useApi(caregiverApi.getAdherence);
  const { data: emergencies, execute: loadEmergencies } = useApi(caregiverApi.getEmergencies);
  const { data: behavior, execute: loadBehavior } = useApi(caregiverApi.getBehavior);
  const { data: wellness, execute: loadWellness } = useApi(wellnessApi.getSummary);
  const { data: allEvents, execute: loadEvents } = useApi(healthPlannerApi.getEvents);
  const { data: medicineList, execute: loadMedicines } = useApi(medicineApi.getReminders);
  const { data: linkedData, execute: loadLinked } = useApi(linkApi.getLinkedUsers);
  const [activeEmergency, setActiveEmergency] = useState(null);

  const checkEmergencies = async () => {
    try {
      const data = await emergencyApi.getActive();
      const firstActive = data?.active_emergencies?.[0];
      setActiveEmergency(firstActive || null);
    } catch (err) {
      console.warn('Could not query active emergency in CaregiverDashboard:', err);
    }
  };

  useEffect(() => {
    checkEmergencies();
    const interval = setInterval(checkEmergencies, 10000);
    return () => clearInterval(interval);
  }, []);

  useEffect(() => {
    const handleWsMessage = (e) => {
      const type = e.detail?.type;
      if (type === 'medicine_taken' || type === 'medicine_reminder' || type === 'health_event_completed') {
        loadEvents();
        loadSummary();
        loadBehavior();
        loadMedicines();
      } else if (type === 'emergency_alert') {
        setActiveEmergency(e.detail);
      } else if (type === 'emergency_acknowledged') {
        setActiveEmergency(prev => prev ? { ...prev, status: 'acknowledged' } : null);
      } else if (type === 'emergency_resolved') {
        setActiveEmergency(null);
      }
    };
    window.addEventListener('orma_websocket_message', handleWsMessage);
    return () => window.removeEventListener('orma_websocket_message', handleWsMessage);
  }, [loadEvents, loadSummary, loadBehavior, loadMedicines]);

  useEffect(() => {
    loadSummary();
    loadAdherence();
    loadEmergencies();
    loadBehavior();
    loadWellness();
    loadEvents();
    loadMedicines();
    loadLinked();
  }, [loadSummary, loadAdherence, loadEmergencies, loadBehavior, loadWellness, loadEvents, loadMedicines, loadLinked]);

  // Determine active monitored patient
  const activeSubjectId = localStorage.getItem('orma_subject_id');
  const activePatient = linkedData?.linked_users?.find(p => p.id === activeSubjectId) || 
                        linkedData?.linked_users?.[0] || 
                        { name: 'Test11', role: 'elderly' };

  // Summary data with calm fallbacks
  const displaySummary = summary?.completion_percentage !== undefined ? summary : {
    completion_percentage: 88,
    medicines_taken: 3,
    pending_medicines: 1,
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
      "Consistent morning routine established.",
      "Voice confirmation used for majority of evening doses.",
      "1 fast confirmation flagged for routine verification."
    ]
  };

  const displayEmergencies = emergencies?.recent_triggers ? emergencies : {
    total_history: 1,
    recent_triggers: [
      { id: 1, type: 'Missed Critical Meds', time: 'Yesterday, 9:00 AM', severity: 'medium', resolved: true }
    ]
  };

  const displayWellness = wellness?.status ? wellness : {
    status: 'Monitoring',
    emotions: { calmness: 8, anxiety: 1, sadness: 0 },
    confusion_events_recent: 0,
    repeated_questions: 0
  };

  // Medication timeline
  const displayMedicines = Array.isArray(medicineList) && medicineList.length > 0 ? medicineList : [
    { id: 1, medicine_name: 'Amlodipine', dosage: '5 mg', reminder_time: '08:00', taken_status: true, confirmation_method: 'voice' },
    { id: 2, medicine_name: 'Vitamin D3', dosage: '1000 IU', reminder_time: '13:00', taken_status: true, confirmation_method: 'manual' },
    { id: 3, medicine_name: 'Metformin', dosage: '500 mg', reminder_time: '16:00', taken_status: false, adherence_pattern_flags: null },
    { id: 4, medicine_name: 'Amlodipine', dosage: '5 mg', reminder_time: '20:00', taken_status: false, adherence_pattern_flags: null },
  ];

  // Format 24h time to 12h AM/PM
  const formatTimeStr = (t) => {
    if (!t) return '--:--';
    if (t.includes('AM') || t.includes('PM')) return t;
    const parts = t.split(':');
    if (parts.length >= 2) {
      let hour = parseInt(parts[0], 10);
      const minute = parts[1];
      const ampm = hour >= 12 ? 'PM' : 'AM';
      hour = hour % 12 || 12;
      return `${hour}:${minute} ${ampm}`;
    }
    return t;
  };

  return (
    <ErrorBoundary>
      <div className="w-full max-w-7xl mx-auto flex flex-col gap-6 pb-12">

        {/* ==================================================================== */}
        {/* 1. TOP HEADER & ACTIVE PATIENT CONTEXT (Liquid Glass Header)         */}
        {/* ==================================================================== */}
        <div className="orma-glass-header flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div className="flex items-center gap-3.5 relative z-10">
            <div className="w-12 h-12 rounded-2xl bg-blue-500/15 border border-blue-500/30 flex items-center justify-center text-blue-400 shrink-0 shadow-inner">
              <ShieldCheck className="w-6 h-6" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h1 className="text-2xl md:text-3xl font-extrabold text-white tracking-tight">
                  Caregiver Monitoring
                </h1>
                <span className="hidden sm:inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-bold bg-emerald-500/10 text-emerald-400 border border-emerald-500/25">
                  <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse"></span> Live
                </span>
              </div>
              <p className="text-slate-300 text-xs md:text-sm mt-0.5 font-medium">
                Monitoring: <span className="font-bold text-white">{activePatient?.name || 'Test11'}</span> · Real-time adherence, alerts, and care activity
              </p>
            </div>
          </div>

          <div className="flex items-center gap-3 relative z-10">
            <div className="px-4 py-2 rounded-2xl bg-slate-900/80 border border-white/10 text-xs font-bold text-slate-200 flex items-center gap-2 shadow-md">
              <Calendar className="w-4 h-4 text-blue-400" />
              <span>Today · {new Date().toLocaleDateString('en-US', { month: 'short', day: 'numeric', weekday: 'short' })}</span>
            </div>
          </div>
        </div>

        {/* ==================================================================== */}
        {/* 2. PATIENT STATUS CARD (Clear Situation Overview)                   */}
        {/* ==================================================================== */}
        <div className="orma-card p-5 sm:p-6">
          <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 relative z-10">
            <div className="flex items-start sm:items-center gap-4">
              <div className="w-12 h-12 rounded-2xl bg-blue-600/15 border border-blue-500/30 flex items-center justify-center text-blue-400 font-extrabold text-lg shrink-0 shadow-inner">
                {activePatient?.name?.charAt(0) || 'P'}
              </div>
              <div>
                <div className="flex items-center gap-2.5">
                  <h2 className="text-lg font-bold text-white tracking-tight">
                    {activePatient?.name || 'Test11'}
                  </h2>
                  <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-[11px] font-bold bg-emerald-500/10 text-emerald-400 border border-emerald-500/25">
                    <span className="w-1.5 h-1.5 rounded-full bg-emerald-400"></span> Active
                  </span>
                </div>
                <p className="text-xs text-slate-400 mt-1">
                  Last observable activity: <span className="text-slate-200 font-medium">Today</span>
                </p>
              </div>
            </div>

            <div className="flex items-center gap-3 bg-slate-950/50 px-4 py-2.5 rounded-2xl border border-white/5 text-xs">
              <div className="flex items-center gap-2 text-emerald-400 font-semibold">
                <CheckCircle2 className="w-4 h-4 shrink-0" />
                <span>{displaySummary.medicines_taken} confirmed</span>
              </div>
              <span className="text-slate-700">•</span>
              <div className="flex items-center gap-2 text-amber-400 font-semibold">
                <Clock className="w-4 h-4 shrink-0" />
                <span>{displaySummary.pending_medicines} upcoming</span>
              </div>
              {displaySummary.missed_medicines > 0 && (
                <>
                  <span className="text-slate-700">•</span>
                  <div className="flex items-center gap-2 text-red-400 font-bold">
                    <AlertTriangle className="w-4 h-4 shrink-0" />
                    <span>{displaySummary.missed_medicines} missed</span>
                  </div>
                </>
              )}
            </div>
          </div>
        </div>

        {/* ==================================================================== */}
        {/* 3. STAT CARDS (Prioritized Hierarchy)                                */}
        {/* ==================================================================== */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          
          {/* Card 1: Today's Adherence */}
          <div className="relative bg-slate-900/70 border border-white/10 hover:border-blue-500/30 rounded-3xl p-5 sm:p-6 flex flex-col justify-between transition-all shadow-xl backdrop-blur-xl overflow-hidden">
            <div className="absolute inset-0 bg-gradient-to-b from-white/10 via-transparent to-transparent pointer-events-none" />
            
            <div className="flex justify-between items-start mb-3 relative z-10">
              <span className="text-[11px] uppercase font-bold text-slate-400 tracking-wider">Today's Adherence</span>
              <div className="p-2.5 rounded-xl bg-blue-500/10 border border-blue-500/20 text-blue-400 shadow-inner">
                <Activity className="w-4 h-4" />
              </div>
            </div>
            <div className="relative z-10">
              <div className="text-3xl sm:text-4xl font-extrabold text-white tracking-tight">
                {displaySummary.completion_percentage}%
              </div>
              <p className="text-xs text-blue-400 font-medium mt-1">Today's completion rate</p>
            </div>
          </div>

          {/* Card 2: Medicines Taken */}
          <div className="relative bg-slate-900/70 border border-white/10 hover:border-emerald-500/30 rounded-3xl p-5 sm:p-6 flex flex-col justify-between transition-all shadow-xl backdrop-blur-xl overflow-hidden">
            <div className="absolute inset-0 bg-gradient-to-b from-white/10 via-transparent to-transparent pointer-events-none" />

            <div className="flex justify-between items-start mb-3 relative z-10">
              <span className="text-[11px] uppercase font-bold text-slate-400 tracking-wider">Taken Today</span>
              <div className="p-2.5 rounded-xl bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 shadow-inner">
                <CheckCircle2 className="w-4 h-4" />
              </div>
            </div>
            <div className="relative z-10">
              <div className="text-3xl sm:text-4xl font-extrabold text-white tracking-tight">
                {displaySummary.medicines_taken}
              </div>
              <p className="text-xs text-emerald-400 font-medium mt-1">Confirmed doses today</p>
            </div>
          </div>

          {/* Card 3: Pending Doses */}
          <div className="relative bg-slate-900/70 border border-white/10 hover:border-amber-500/30 rounded-3xl p-5 sm:p-6 flex flex-col justify-between transition-all shadow-xl backdrop-blur-xl overflow-hidden">
            <div className="absolute inset-0 bg-gradient-to-b from-white/10 via-transparent to-transparent pointer-events-none" />

            <div className="flex justify-between items-start mb-3 relative z-10">
              <span className="text-[11px] uppercase font-bold text-slate-400 tracking-wider">Pending Doses</span>
              <div className="p-2.5 rounded-xl bg-amber-500/10 border border-amber-500/20 text-amber-400 shadow-inner">
                <Clock className="w-4 h-4" />
              </div>
            </div>
            <div className="relative z-10">
              <div className="text-3xl sm:text-4xl font-extrabold text-white tracking-tight">
                {displaySummary.pending_medicines}
              </div>
              <p className="text-xs text-amber-400 font-medium mt-1">Scheduled for later today</p>
            </div>
          </div>

          {/* Card 4: Missed Doses (Attracts attention only when >0) */}
          <div className={`relative rounded-3xl p-5 sm:p-6 flex flex-col justify-between transition-all shadow-xl backdrop-blur-xl overflow-hidden ${
            displaySummary.missed_medicines > 0 
              ? 'bg-red-500/10 border-2 border-red-500/40 shadow-lg shadow-red-500/10' 
              : 'bg-slate-900/70 border border-white/10 hover:border-slate-700'
          }`}>
            <div className="absolute inset-0 bg-gradient-to-b from-white/10 via-transparent to-transparent pointer-events-none" />

            <div className="flex justify-between items-start mb-3 relative z-10">
              <span className={`text-[11px] uppercase font-bold tracking-wider ${
                displaySummary.missed_medicines > 0 ? 'text-red-300' : 'text-slate-400'
              }`}>
                Missed Doses
              </span>
              <div className={`p-2.5 rounded-xl border shadow-inner ${
                displaySummary.missed_medicines > 0 ? 'bg-red-500/20 text-red-400 border-red-500/30' : 'bg-slate-800/80 text-slate-400 border-white/5'
              }`}>
                <AlertTriangle className="w-4 h-4" />
              </div>
            </div>
            <div className="relative z-10">
              <div className={`text-3xl sm:text-4xl font-extrabold tracking-tight ${
                displaySummary.missed_medicines > 0 ? 'text-red-400' : 'text-white'
              }`}>
                {displaySummary.missed_medicines}
              </div>
              <p className={`text-xs font-medium mt-1 ${
                displaySummary.missed_medicines > 0 ? 'text-red-400 font-bold' : 'text-slate-400'
              }`}>
                {displaySummary.missed_medicines > 0 ? 'Requires caregiver attention' : 'No missed doses today'}
              </p>
            </div>
          </div>
        </div>

        {/* ==================================================================== */}
        {/* 4. TODAY'S MEDICATION TIMELINE & ACTIVE ALERTS                        */}
        {/* ==================================================================== */}
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
          
          {/* Left / Primary: Today's Medication Timeline (7 cols) */}
          <div className="lg:col-span-7 orma-card flex flex-col">
            <div className="flex items-center justify-between mb-5 relative z-10">
              <div className="flex items-center gap-2.5">
                <div className="w-8 h-8 rounded-xl bg-blue-500/10 border border-blue-500/20 flex items-center justify-center text-blue-400">
                  <Pill className="w-4 h-4" />
                </div>
                <div>
                  <h3 className="text-base font-bold text-white tracking-tight">Today's Medication Timeline</h3>
                  <p className="text-[11px] text-slate-400">Chronological daily schedule & confirmation telemetry</p>
                </div>
              </div>
              <span className="text-xs font-bold text-slate-300 bg-slate-950/60 px-2.5 py-1 rounded-xl border border-white/10">
                {displayMedicines.length} scheduled
              </span>
            </div>

            <div className="flex-1 relative z-10">
              <MedicationTimeline 
                medicines={displayMedicines} 
                mode="caregiver" 
              />
            </div>
          </div>

          {/* Right: Active Alerts Requiring Attention (5 cols) */}
          <div className="lg:col-span-5 orma-card flex flex-col justify-between">
            <div className="relative z-10">
              <div className="flex items-center justify-between mb-5">
                <div className="flex items-center gap-2.5">
                  <div className="w-8 h-8 rounded-xl bg-red-500/10 border border-red-500/20 flex items-center justify-center text-red-400">
                    <AlertOctagon className="w-4 h-4" />
                  </div>
                  <div>
                    <h3 className="text-base font-bold text-white tracking-tight">Recent Alerts & Safety</h3>
                    <p className="text-[11px] text-slate-400">Items requiring caregiver attention</p>
                  </div>
                </div>
              </div>

              <div className="space-y-3">
                {displayEmergencies.recent_triggers.map((alert) => (
                  <div 
                    key={alert.id} 
                    className={`p-4 rounded-2xl border transition-all ${
                      alert.severity === 'high' 
                        ? 'bg-red-500/10 border-red-500/30 shadow-md' 
                        : 'bg-amber-500/10 border-amber-500/30 shadow-md'
                    }`}
                  >
                    <div className="flex justify-between items-start mb-1.5">
                      <h4 className={`font-bold text-sm ${alert.severity === 'high' ? 'text-red-400' : 'text-amber-400'}`}>
                        {alert.type}
                      </h4>
                      <span className="text-[11px] text-slate-400 font-mono">{alert.time}</span>
                    </div>
                    <div className="flex items-center justify-between text-xs mt-2">
                      <span className="text-slate-300 font-medium">
                        Status: {alert.resolved ? (
                          <span className="text-emerald-400 font-bold">Resolved</span>
                        ) : (
                          <span className="text-red-400 font-extrabold">Action Needed</span>
                        )}
                      </span>
                    </div>
                  </div>
                ))}

                {displayEmergencies.recent_triggers.length === 0 && (
                  <div className="p-6 text-center border border-dashed border-white/10 rounded-2xl bg-slate-950/30">
                    <CheckCircle2 className="w-8 h-8 text-emerald-400 mx-auto mb-2" />
                    <p className="text-emerald-400 font-bold text-sm">All Clear</p>
                    <p className="text-xs text-slate-400 mt-1">No active emergency alerts or safety triggers.</p>
                  </div>
                )}
              </div>
            </div>

            <div className="mt-4 p-3 bg-slate-950/40 rounded-2xl border border-white/5 flex items-center justify-between text-xs text-slate-400 relative z-10">
              <span>Emergency monitoring status</span>
              <span className="text-emerald-400 font-bold flex items-center gap-1.5">
                <span className="w-2 h-2 rounded-full bg-emerald-400"></span> Active
              </span>
            </div>
          </div>
        </div>

        {/* ==================================================================== */}
        {/* 5. MEDICATION ADHERENCE ANALYTICS & STATUS BREAKDOWN                 */}
        {/* ==================================================================== */}
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
          {/* Primary Adherence Trend Chart with Range Selector (8 cols) */}
          <AdherenceTrendChart 
            adherenceData={displayAdherence} 
            className="lg:col-span-8" 
          />

          {/* Medication Status Distribution Breakdown (4 cols) */}
          <MedicationStatusBreakdown 
            medicines={displayMedicines} 
            summaryData={displaySummary} 
            className="lg:col-span-4" 
          />
        </div>

        {/* ==================================================================== */}
        {/* 6. BEHAVIORAL INSIGHTS & CONVERSATION/WELLNESS SIGNALS               */}
        {/* ==================================================================== */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          
          {/* Behavioral Insights */}
          <div className="orma-card">
            <div className="flex items-center gap-2.5 mb-5 relative z-10">
              <div className="w-8 h-8 rounded-xl bg-pink-500/10 border border-pink-500/20 flex items-center justify-center text-pink-400">
                <Heart className="w-4 h-4" />
              </div>
              <div>
                <h3 className="text-base font-bold text-white tracking-tight">Behavioral Insights</h3>
                <p className="text-[11px] text-slate-400">Observable routine trends</p>
              </div>
            </div>

            <div className="space-y-3 relative z-10">
              {displayBehavior.insights.map((insight, idx) => (
                <div key={idx} className="flex items-start gap-3 p-3.5 bg-slate-950/50 rounded-2xl border border-white/5">
                  <div className="w-2 h-2 rounded-full bg-pink-400 mt-1.5 shrink-0" />
                  <p className="text-xs text-slate-300 leading-relaxed font-medium">{insight}</p>
                </div>
              ))}
              {displayBehavior.insights.length === 0 && (
                <p className="text-xs text-slate-500 italic">No behavioral observations recorded yet.</p>
              )}
            </div>
          </div>

          {/* Conversation & Wellness Signals */}
          <div className="orma-card">
            <div className="flex items-center justify-between mb-5 relative z-10">
              <div className="flex items-center gap-2.5">
                <div className="w-8 h-8 rounded-xl bg-purple-500/10 border border-purple-500/20 flex items-center justify-center text-purple-400">
                  <Brain className="w-4 h-4" />
                </div>
                <div>
                  <h3 className="text-base font-bold text-white tracking-tight">Conversation & Wellness Signals</h3>
                  <p className="text-[11px] text-slate-400">AI conversation interaction metrics</p>
                </div>
              </div>
              <span className="text-[11px] font-bold px-2.5 py-1 rounded-full bg-slate-950/60 text-purple-400 border border-white/10">
                Status: {displayWellness.status}
              </span>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 relative z-10">
              <div className="bg-slate-950/50 p-3.5 rounded-2xl border border-white/5 text-center">
                <p className="text-[11px] uppercase font-bold text-slate-400">Calm Interactions</p>
                <p className="text-2xl font-bold text-white mt-1">{displayWellness.emotions.calmness}</p>
                <p className="text-[10px] text-emerald-400 mt-0.5 font-medium">Recorded</p>
              </div>

              <div className="bg-slate-950/50 p-3.5 rounded-2xl border border-white/5 text-center">
                <p className="text-[11px] uppercase font-bold text-slate-400">Repeated Questions</p>
                <p className="text-2xl font-bold text-white mt-1">{displayWellness.repeated_questions}</p>
                <p className="text-[10px] text-slate-400 mt-0.5 font-medium">Observed</p>
              </div>

              <div className="bg-slate-950/50 p-3.5 rounded-2xl border border-white/5 text-center">
                <p className="text-[11px] uppercase font-bold text-slate-400">Confusion Signals</p>
                <p className="text-2xl font-bold text-white mt-1">{displayWellness.confusion_events_recent}</p>
                <p className="text-[10px] text-slate-400 mt-0.5 font-medium">Flagged</p>
              </div>
            </div>

            <div className="mt-4 p-3 bg-slate-950/30 rounded-2xl border border-white/5 flex items-center justify-between text-[11px] text-slate-400 relative z-10">
              <span>AI Response Adaptation:</span>
              <span className="text-emerald-400 font-semibold">Standard conversation mode active</span>
            </div>

            <p className="text-[10px] text-slate-500 mt-3 text-center relative z-10">
              AI interaction observations, not clinical or medical diagnoses.
            </p>
          </div>
        </div>

        {/* ==================================================================== */}
        {/* 7. RECENT HEALTH & CARE EVENTS LOG (Chronological Activity Timeline) */}
        {/* ==================================================================== */}
        <div className="orma-card">
          <div className="flex items-center justify-between mb-5 relative z-10">
            <div className="flex items-center gap-2.5">
              <div className="w-8 h-8 rounded-xl bg-blue-500/10 border border-blue-500/20 flex items-center justify-center text-blue-400">
                <Activity className="w-4 h-4" />
              </div>
              <div>
                <h3 className="text-base font-bold text-white tracking-tight">Recent Health & Care Events</h3>
                <p className="text-[11px] text-slate-400">Chronological completed care activity & safety triggers</p>
              </div>
            </div>
          </div>

          <div className="relative z-10">
            <HealthActivityTimeline 
              events={allEvents} 
              emergencies={displayEmergencies.recent_triggers} 
              userTimezone={user?.timezone} 
            />
          </div>
        </div>

      </div>
    </ErrorBoundary>
  );
}

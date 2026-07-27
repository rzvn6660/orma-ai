import { useState, useEffect } from 'react';
import DashboardLayout from '../layouts/DashboardLayout';
import MyHealthPage from './MyHealthPage';
import OrmaPage from './OrmaPage';
import FamilyPage from './FamilyPage';
import SettingsPage from './SettingsPage';
import EmergencyPage from './EmergencyPage';
import CaregiverDashboard from './CaregiverDashboard';
import { healthApi, speechApi, chatApi, emergencyApi, medicineApi, healthPlannerApi } from '../services/api';
import { useApi } from '../hooks/useApi';
import { tts } from '../services/tts';
import { motion } from 'framer-motion';
import MedicineReminder from '../components/MedicineReminder';
import EmergencyAlert from '../components/EmergencyAlert';
import HealthSnapshot from '../components/HealthSnapshot';
import ErrorBoundary from '../components/ErrorBoundary';
import TimeAwareDashboard from '../components/TimeAwareDashboard';
import { 
  Heart, Pill, Calendar, AlertOctagon, Brain, Mic, Clock, CheckCircle2, 
  ArrowRight, ShieldCheck, Activity, User, Sparkles
} from 'lucide-react';

const getTimeContext = () => {
  const hour = new Date().getHours();
  if (hour >= 5 && hour < 12) return {
      timeOfDay: 'Morning',
      greeting: 'Good Morning',
      icon: '☀️',
      suggestions: [
          "Did I take my morning medicine?",
          "What medicines are due this morning?",
          "What's my schedule today?"
      ]
  };
  if (hour >= 12 && hour < 17) return {
      timeOfDay: 'Afternoon',
      greeting: 'Good Afternoon',
      icon: '🌤️',
      suggestions: [
          "Have I taken my afternoon medicine?",
          "What's my next reminder?",
          "Show today's medications."
      ]
  };
  if (hour >= 17 && hour < 21) return {
      timeOfDay: 'Evening',
      greeting: 'Good Evening',
      icon: '🌆',
      suggestions: [
          "Did I miss any medicines today?",
          "What medicines should I take tonight?"
      ]
  };
  return {
      timeOfDay: 'Night',
      greeting: 'Good Night',
      icon: '🌙',
      suggestions: [
          "Have I completed today's medicines?",
          "What medicines are scheduled for tomorrow?"
      ]
  };
};

export default function Dashboard({ currentView, onViewChange, user, onLogout }) {
  const [messages, setMessages] = useState([]);
  const [isSpeaking, setIsSpeaking] = useState(false);
  const [isEmergencyActive, setIsEmergencyActive] = useState(false);
  const [emergencySeverity, setEmergencySeverity] = useState('low');
  
  const isListening = false;
  const [languageMode, setLanguageMode] = useState(localStorage.getItem('orma_language_pref') || 'auto');
  const [timeContext, setTimeContext] = useState(getTimeContext());
  const [todayEvents, setTodayEvents] = useState([]);
  
  useEffect(() => {
    const handleLangChange = () => {
      setLanguageMode(localStorage.getItem('orma_language_pref') || 'auto');
    };
    window.addEventListener('languageChange', handleLangChange);
    return () => window.removeEventListener('languageChange', handleLangChange);
  }, []);
  
  useEffect(() => {
    const interval = setInterval(() => {
      setTimeContext(getTimeContext());
    }, 60000);
    return () => clearInterval(interval);
  }, []);

  // Fetch today's planner appointments
  useEffect(() => {
    const loadEvents = async () => {
      try {
        const events = await healthPlannerApi.getEvents();
        const todayStr = new Date().toISOString().split('T')[0];
        setTodayEvents(events.filter(e => (!e.event_date || e.event_date === todayStr) && !e.status));
      } catch (err) {
        console.error(err);
      }
    };
    loadEvents();
  }, []);

  const { data: healthData, error: healthError, execute: checkHealth } = useApi(healthApi.check);
  const { execute: transcribe, loading: isTranscribing } = useApi(speechApi.transcribe);
  const { execute: sendMessage, loading: isThinking } = useApi(chatApi.sendMessage);
  const { execute: analyzeEmergency } = useApi(emergencyApi.analyze);

  const handleStopRecording = async (blobUrl, blob) => {
    if (!blob) return;
    try {
      const languageParam = languageMode !== 'auto' ? languageMode : undefined;
      const data = await transcribe(blob, languageParam);
      const userText = data.transcription;
      const detectedLang = data.detected_language || 'en';
      
      if (!userText || userText.trim() === '') {
        return;
      }
      
      const newMsg = {
        id: Date.now(),
        sender: 'user',
        text: userText,
        time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
      };
      setMessages(prev => [...prev, newMsg]);

      const emergencyData = await analyzeEmergency(userText);
      if (emergencyData && emergencyData.is_emergency) {
        setIsEmergencyActive(true);
        setEmergencySeverity(emergencyData.severity);
        
        const alertMsg = {
          id: Date.now() + 1,
          sender: 'ai',
          text: emergencyData.message,
          time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
        };
        setMessages(prev => [...prev, alertMsg]);
        
        tts.speak(alertMsg.text, {
          onStart: () => setIsSpeaking(true),
          onEnd: () => setIsSpeaking(false),
          onError: () => setIsSpeaking(false)
        });
        return;
      }

      const chatData = await sendMessage(userText, 'default_user', languageMode, detectedLang);
      const aiMsg = {
        id: Date.now() + 1,
        sender: 'ai',
        text: chatData.response,
        time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
      };
      
      setMessages(prev => [...prev, aiMsg]);
      tts.speak(chatData.response, {
        onStart: () => setIsSpeaking(true),
        onEnd: () => setIsSpeaking(false),
        onError: () => setIsSpeaking(false)
      });

    } catch (error) {
      console.error("Pipeline failed:", error);
      const errorMsg = {
        id: Date.now(),
        sender: 'ai',
        text: "I'm having trouble responding right now. Please try again.",
        time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
      };
      setMessages(prev => [...prev, errorMsg]);
    }
  };

  const handleAskAgain = async (text) => {
    if (!text) return;
    try {
      const isMl = /[\u0D00-\u0D7F]/.test(text);
      const detectedLang = isMl ? 'ml' : 'en';
      
      const newMsg = {
        id: Date.now(),
        sender: 'user',
        text: text,
        time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
      };
      setMessages(prev => [...prev, newMsg]);

      const chatData = await sendMessage(text, 'default_user', languageMode, detectedLang);
      const aiMsg = {
        id: Date.now() + 1,
        sender: 'ai',
        text: chatData.response,
        time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
      };
      setMessages(prev => [...prev, aiMsg]);
      tts.speak(chatData.response, {
        onStart: () => setIsSpeaking(true),
        onEnd: () => setIsSpeaking(false),
        onError: () => setIsSpeaking(false)
      });
    } catch (error) {
      console.error("Ask Again failed:", error);
    }
  };

  useEffect(() => {
    checkHealth();
  }, [checkHealth]);

  // Route mapping
  if (currentView === 'my-health' || ['medicines', 'planner', 'records', 'vitals'].includes(currentView)) {
    return (
      <DashboardLayout currentView="my-health" onViewChange={onViewChange} user={user} onLogout={onLogout}>
        <MyHealthPage user={user} onViewChange={onViewChange} />
      </DashboardLayout>
    );
  }

  if (currentView === 'orma' || currentView === 'conversations') {
    return (
      <DashboardLayout currentView="orma" onViewChange={onViewChange} user={user} onLogout={onLogout}>
        <OrmaPage
          user={user}
          messages={messages}
          isListening={isListening}
          isSpeaking={isSpeaking}
          isTranscribing={isTranscribing}
          isThinking={isThinking}
          handleStopRecording={handleStopRecording}
          onClearConversation={() => setMessages([])}
          handleAskAgain={handleAskAgain}
          timeContext={timeContext}
        />
      </DashboardLayout>
    );
  }

  if (currentView === 'family') {
    return (
      <DashboardLayout currentView="family" onViewChange={onViewChange} user={user} onLogout={onLogout}>
        <FamilyPage user={user} />
      </DashboardLayout>
    );
  }

  if (currentView === 'settings') {
    return (
      <DashboardLayout currentView="settings" onViewChange={onViewChange} user={user} onLogout={onLogout}>
        <SettingsPage user={user} />
      </DashboardLayout>
    );
  }

  if (currentView === 'emergency') {
    return (
      <DashboardLayout currentView="emergency" onViewChange={onViewChange} user={user} onLogout={onLogout}>
        <EmergencyPage user={user} />
      </DashboardLayout>
    );
  }

  if (currentView === 'caregiver') {
    return (
      <DashboardLayout currentView="caregiver" onViewChange={onViewChange} user={user} onLogout={onLogout}>
        <CaregiverDashboard currentView={currentView} onViewChange={onViewChange} user={user} onLogout={onLogout} />
      </DashboardLayout>
    );
  }

  // DEFAULT / HOME VIEW: Today's Healthcare Dashboard
  return (
    <ErrorBoundary>
      <DashboardLayout currentView="home" onViewChange={onViewChange} user={user} onLogout={onLogout}>
        <div className="w-full max-w-7xl mx-auto flex flex-col gap-8 pb-12">
          
          {/* Greeting Banner */}
          <div className="bg-gradient-to-r from-blue-900/60 via-slate-900 to-indigo-950/60 p-6 md:p-8 rounded-3xl border border-blue-500/20 backdrop-blur-xl flex flex-col md:flex-row md:items-center justify-between gap-6">
            <div className="flex items-center gap-4">
              <div className="w-14 h-14 rounded-2xl bg-blue-600/20 border border-blue-500/30 flex items-center justify-center text-3xl shadow-lg">
                {timeContext.icon}
              </div>
              <div>
                <h1 className="text-3xl font-extrabold text-white tracking-tight">
                  {timeContext.greeting}, {user?.name?.split(' ')[0] || 'Friend'}!
                </h1>
                <p className="text-slate-300 text-sm md:text-base mt-1">
                  Here is your unified healthcare summary for today.
                </p>
              </div>
            </div>

            <div className="flex items-center gap-3">
              <button 
                onClick={() => onViewChange('orma')}
                className="orma-btn-primary shadow-lg shadow-blue-500/20 text-base py-3 px-6"
              >
                <Mic className="w-5 h-5" /> Talk to ORMA
              </button>
              <button 
                onClick={() => onViewChange('emergency')}
                className="orma-btn-danger py-3 px-5 text-base"
                title="Emergency Help"
              >
                <AlertOctagon className="w-5 h-5" /> Emergency
              </button>
            </div>
          </div>

          {/* Today's Focus Grid */}
          <div className="grid grid-cols-1 xl:grid-cols-12 gap-8">
            
            {/* Left Main Column: Today's Medicines & Appointments */}
            <div className="col-span-1 xl:col-span-8 flex flex-col gap-8">
              
              {/* Today's Medicines Summary */}
              <div className="orma-card p-6 md:p-8 border-blue-500/20">
                <div className="flex items-center justify-between mb-6">
                  <div className="flex items-center gap-3">
                    <div className="w-10 h-10 rounded-xl bg-blue-500/10 flex items-center justify-center">
                      <Pill className="w-5 h-5 text-blue-400" />
                    </div>
                    <div>
                      <h2 className="text-xl font-bold text-white">Today's Medicines</h2>
                      <p className="text-xs text-slate-400">Scheduled doses for today</p>
                    </div>
                  </div>
                  <button 
                    onClick={() => onViewChange('my-health')} 
                    className="text-sm font-bold text-blue-400 hover:text-blue-300 flex items-center gap-1 transition-colors"
                  >
                    View All Medicines &rarr;
                  </button>
                </div>

                <MedicineReminder onViewChange={onViewChange} user={user} />
              </div>

              {/* Today's Appointments & Schedule */}
              <div className="orma-card p-6 md:p-8 border-emerald-500/20">
                <div className="flex items-center justify-between mb-6">
                  <div className="flex items-center gap-3">
                    <div className="w-10 h-10 rounded-xl bg-emerald-500/10 flex items-center justify-center">
                      <Calendar className="w-5 h-5 text-emerald-400" />
                    </div>
                    <div>
                      <h2 className="text-xl font-bold text-white">Today's Appointments & Events</h2>
                      <p className="text-xs text-slate-400">Doctor visits, tests, and reminders</p>
                    </div>
                  </div>
                  <button 
                    onClick={() => onViewChange('my-health')} 
                    className="text-sm font-bold text-emerald-400 hover:text-emerald-300 flex items-center gap-1 transition-colors"
                  >
                    Planner &rarr;
                  </button>
                </div>

                {todayEvents.length > 0 ? (
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    {todayEvents.map((evt) => (
                      <div key={evt.id} className="p-4 bg-slate-900/60 border border-slate-800 rounded-2xl flex items-center gap-4">
                        <div className="w-10 h-10 rounded-xl bg-emerald-500/20 text-emerald-400 flex items-center justify-center shrink-0">
                          <Calendar className="w-5 h-5" />
                        </div>
                        <div className="flex-1 overflow-hidden">
                          <p className="font-bold text-white text-base truncate">{evt.title}</p>
                          <p className="text-xs text-slate-400 flex items-center gap-1 mt-0.5">
                            <Clock className="w-3 h-3 text-emerald-400" /> {evt.reminder_time || 'Today'}
                          </p>
                        </div>
                      </div>
                    ))}
                  </div>
                ) : (
                  <div className="p-8 text-center border border-dashed border-slate-800 rounded-2xl bg-slate-900/30">
                    <CheckCircle2 className="w-10 h-10 text-emerald-400/80 mx-auto mb-2" />
                    <p className="text-slate-300 font-bold text-base">No appointments pending for today</p>
                    <p className="text-xs text-slate-500 mt-1">Check your planner for upcoming schedule</p>
                  </div>
                )}
              </div>

            </div>

            {/* Right Sidebar Column: Health Status & Widgets */}
            <div className="col-span-1 xl:col-span-4 flex flex-col gap-6">
              
              {/* Time Awareness Card */}
              <TimeAwareDashboard user={user} timeContext={timeContext} />

              {/* Health Status Snapshot */}
              <HealthSnapshot onViewChange={onViewChange} />

              {/* Emergency Alert Shortcut */}
              <EmergencyAlert isActive={isEmergencyActive} severity={emergencySeverity} onViewChange={onViewChange} />

            </div>

          </div>
        </div>
      </DashboardLayout>
    </ErrorBoundary>
  );
}

import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  Brain, 
  MessageSquare, 
  Mic, 
  Volume2, 
  Sparkles, 
  Clock, 
  History, 
  HelpCircle, 
  ChevronRight, 
  Pill,
  Calendar as CalendarIcon,
  ShieldCheck,
  CheckCircle2,
  Heart
} from 'lucide-react';
import AIConversationPanel from '../components/AIConversationPanel';
import ConversationsPage from './ConversationsPage';
import MemoryPage from './MemoryPage';
import ErrorBoundary from '../components/ErrorBoundary';
import { medicineApi, healthPlannerApi, ocmeMemoryApi } from '../services/api';

export default function OrmaPage({ 
  user, 
  messages = [], 
  isListening, 
  isSpeaking, 
  onStopSpeaking,
  isTranscribing, 
  isThinking, 
  handleStopRecording, 
  onClearConversation, 
  handleAskAgain,
  timeContext
}) {
  const [activeTab, setActiveTab] = useState('assistant'); // 'assistant', 'history', 'memory'
  const [nextMedicine, setNextMedicine] = useState(null);
  const [nextEvent, setNextEvent] = useState(null);
  const [memorySnippet, setMemorySnippet] = useState(null);

  // Load real contextual data for "Today's Context"
  useEffect(() => {
    const loadContextData = async () => {
      try {
        const [medsData, eventsData, memData] = await Promise.allSettled([
          (medicineApi.getReminders ? medicineApi.getReminders() : medicineApi.getMedicines()),
          healthPlannerApi.getEvents(),
          ocmeMemoryApi.getMemories({ limit: 3 })
        ]);

        // Find next pending medicine
        if (medsData.status === 'fulfilled' && Array.isArray(medsData.value)) {
          const pending = medsData.value.filter(m => !m.taken_status);
          setNextMedicine(pending.length > 0 ? pending[0] : (medsData.value[0] || null));
        }

        // Find next upcoming appointment
        if (eventsData.status === 'fulfilled' && Array.isArray(eventsData.value)) {
          const upcoming = eventsData.value.filter(e => !e.status);
          setNextEvent(upcoming.length > 0 ? upcoming[0] : null);
        }

        // Find top memory snippet
        if (memData.status === 'fulfilled' && memData.value) {
          const items = Array.isArray(memData.value.items) 
            ? memData.value.items 
            : Array.isArray(memData.value) 
            ? memData.value 
            : [];
          if (items.length > 0) {
            setMemorySnippet(items[0]);
          }
        }
      } catch (err) {
        console.error('Failed to load companion context:', err);
      }
    };

    loadContextData();
  }, []);

  const getStatusText = () => {
    if (isListening) return { label: 'Listening...', color: 'bg-cyan-400', textColor: 'text-cyan-300' };
    if (isTranscribing || isThinking) return { label: 'Thinking...', color: 'bg-blue-400 animate-pulse', textColor: 'text-blue-300' };
    if (isSpeaking) return { label: 'ORMA is speaking...', color: 'bg-cyan-400 animate-pulse', textColor: 'text-cyan-300' };
    return { label: 'Ready to listen', color: 'bg-emerald-400', textColor: 'text-emerald-400' };
  };

  const status = getStatusText();

  return (
    <ErrorBoundary>
      <div className="w-full max-w-6xl mx-auto flex flex-col gap-6 pb-12">
        
        {/* 1. Compact Header Toolbar */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 bg-slate-900/70 backdrop-blur-xl p-5 sm:p-6 rounded-3xl border border-white/10 shadow-lg">
          <div className="flex items-center gap-3.5">
            <div className="w-11 h-11 rounded-2xl bg-blue-600/20 border border-blue-500/30 flex items-center justify-center text-blue-400 shadow-md shrink-0">
              <Brain className="w-6 h-6" />
            </div>
            <div>
              <div className="flex items-center gap-2.5 flex-wrap">
                <h1 className="text-xl sm:text-2xl font-extrabold text-white tracking-tight">
                  ORMA AI Companion
                </h1>
                <span className={`inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-bold bg-slate-950/70 border border-white/10 ${status.textColor}`}>
                  <span className={`w-2 h-2 rounded-full ${status.color}`} />
                  {status.label}
                </span>
              </div>
              <p className="text-xs sm:text-sm text-slate-400 mt-0.5">
                Your personal voice-first healthcare companion
              </p>
            </div>
          </div>

          {/* Navigation Mode Switcher */}
          <div className="flex items-center gap-1.5 p-1 bg-slate-950/70 border border-white/10 rounded-2xl shrink-0">
            <button
              type="button"
              onClick={() => setActiveTab('assistant')}
              className={`flex items-center gap-1.5 px-3.5 py-2 rounded-xl font-bold text-xs transition-all cursor-pointer ${
                activeTab === 'assistant'
                  ? 'bg-blue-600 text-white shadow-md'
                  : 'text-slate-400 hover:text-white'
              }`}
            >
              <Mic className="w-3.5 h-3.5" />
              <span>Live Companion</span>
            </button>
            <button
              type="button"
              onClick={() => setActiveTab('history')}
              className={`flex items-center gap-1.5 px-3.5 py-2 rounded-xl font-bold text-xs transition-all cursor-pointer ${
                activeTab === 'history'
                  ? 'bg-blue-600 text-white shadow-md'
                  : 'text-slate-400 hover:text-white'
              }`}
            >
              <History className="w-3.5 h-3.5" />
              <span>History</span>
            </button>
            <button
              type="button"
              onClick={() => setActiveTab('memory')}
              className={`flex items-center gap-1.5 px-3.5 py-2 rounded-xl font-bold text-xs transition-all cursor-pointer ${
                activeTab === 'memory'
                  ? 'bg-blue-600 text-white shadow-md'
                  : 'text-slate-400 hover:text-white'
              }`}
            >
              <Sparkles className="w-3.5 h-3.5" />
              <span>Remembered</span>
            </button>
          </div>
        </div>

        {/* 2. Active Tab Content */}
        <AnimatePresence mode="wait">
          <motion.div
            key={activeTab}
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -10 }}
            transition={{ duration: 0.2 }}
          >
            {activeTab === 'assistant' && (
              <div className="space-y-6">
                {/* Voice-First Central Companion Surface */}
                <div className="orma-card p-6 sm:p-8">
                  <AIConversationPanel
                    user={user}
                    isListening={isListening}
                    isSpeaking={isSpeaking}
                    onStopSpeaking={onStopSpeaking}
                    messages={messages}
                    isTranscribing={isTranscribing}
                    isThinking={isThinking}
                    startRecording={() => {}}
                    stopRecording={handleStopRecording}
                    onClearConversation={onClearConversation}
                    onAskAgain={handleAskAgain}
                    timeContext={timeContext}
                  />
                </div>

                {/* 3. Today's Context — 3 Balanced Summary Cards */}
                <div className="space-y-3">
                  <div className="flex items-center justify-between px-2">
                    <span className="text-xs font-bold uppercase tracking-wider text-slate-400">
                      Today's Healthcare Context
                    </span>
                    <span className="text-[11px] text-slate-500 font-mono">
                      Live sync
                    </span>
                  </div>

                  <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                    {/* Context 1: Medication */}
                    <div className="orma-card p-5 flex flex-col justify-between gap-3">
                      <div className="flex items-center justify-between">
                        <span className="text-[11px] font-bold uppercase tracking-wider text-blue-400 flex items-center gap-1.5">
                          <Pill className="w-3.5 h-3.5" /> Medication
                        </span>
                        {nextMedicine && (
                          <span className={`text-[10px] font-bold px-2 py-0.5 rounded-full border ${
                            nextMedicine.taken_status 
                              ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20' 
                              : 'bg-blue-500/10 text-blue-300 border-blue-500/20'
                          }`}>
                            {nextMedicine.taken_status ? 'Taken' : 'Scheduled'}
                          </span>
                        )}
                      </div>

                      <div>
                        {nextMedicine ? (
                          <>
                            <h4 className="text-sm font-bold text-white tracking-tight">
                              {nextMedicine.medicine_name} {nextMedicine.dosage ? `(${nextMedicine.dosage})` : ''}
                            </h4>
                            <p className="text-xs text-slate-400 mt-0.5">
                              {nextMedicine.taken_status ? 'Dose confirmed' : `Next scheduled at ${nextMedicine.reminder_time}`}
                            </p>
                          </>
                        ) : (
                          <>
                            <h4 className="text-sm font-bold text-white">No medicines scheduled today</h4>
                            <p className="text-xs text-slate-400 mt-0.5">Your medication schedule is clear.</p>
                          </>
                        )}
                      </div>

                      <div className="pt-2 border-t border-white/5 text-[11px] text-slate-500 flex items-center gap-1">
                        <CheckCircle2 className="w-3 h-3 text-emerald-400" />
                        <span>Daily adherence tracker active</span>
                      </div>
                    </div>

                    {/* Context 2: Appointment */}
                    <div className="orma-card p-5 flex flex-col justify-between gap-3">
                      <div className="flex items-center justify-between">
                        <span className="text-[11px] font-bold uppercase tracking-wider text-amber-400 flex items-center gap-1.5">
                          <CalendarIcon className="w-3.5 h-3.5" /> Appointment
                        </span>
                        <span className="text-[10px] font-bold text-amber-300 bg-amber-500/10 px-2 py-0.5 rounded-full border border-amber-500/20">
                          Planner
                        </span>
                      </div>

                      <div>
                        {nextEvent ? (
                          <>
                            <h4 className="text-sm font-bold text-white tracking-tight">
                              {nextEvent.title}
                            </h4>
                            <p className="text-xs text-slate-400 mt-0.5">
                              {nextEvent.event_date || 'Today'} · {nextEvent.reminder_time || 'Scheduled time'}
                            </p>
                          </>
                        ) : (
                          <>
                            <h4 className="text-sm font-bold text-white">No appointments scheduled</h4>
                            <p className="text-xs text-slate-400 mt-0.5">You have no upcoming clinical events.</p>
                          </>
                        )}
                      </div>

                      <div className="pt-2 border-t border-white/5 text-[11px] text-slate-500 flex items-center gap-1">
                        <Clock className="w-3 h-3 text-amber-400" />
                        <span>Connected to Care Calendar</span>
                      </div>
                    </div>

                    {/* Context 3: Memory / Things ORMA Remembers */}
                    <div className="orma-card p-5 flex flex-col justify-between gap-3">
                      <div className="flex items-center justify-between">
                        <span className="text-[11px] font-bold uppercase tracking-wider text-cyan-400 flex items-center gap-1.5">
                          <Sparkles className="w-3.5 h-3.5" /> Remembered for You
                        </span>
                        <span className="text-[10px] font-bold text-cyan-300 bg-cyan-500/10 px-2 py-0.5 rounded-full border border-cyan-500/20">
                          Memory
                        </span>
                      </div>

                      <div>
                        {memorySnippet ? (
                          <>
                            <h4 className="text-sm font-bold text-white tracking-tight">
                              {memorySnippet.title || 'Personal Preference'}
                            </h4>
                            <p className="text-xs text-slate-400 mt-0.5 line-clamp-2">
                              "{memorySnippet.text || memorySnippet.content || 'Care details remembered'}"
                            </p>
                          </>
                        ) : (
                          <>
                            <h4 className="text-sm font-bold text-white">No important memories available</h4>
                            <p className="text-xs text-slate-400 mt-0.5">
                              Personal health preferences will appear here as you interact.
                            </p>
                          </>
                        )}
                      </div>

                      <div className="pt-2 border-t border-white/5 text-[11px] text-slate-500 flex items-center gap-1">
                        <ShieldCheck className="w-3 h-3 text-cyan-400" />
                        <span>Private care memory</span>
                      </div>
                    </div>
                  </div>
                </div>

              </div>
            )}

            {activeTab === 'history' && (
              <div className="orma-card p-6">
                <ConversationsPage messages={messages} user={user} />
              </div>
            )}

            {activeTab === 'memory' && (
              <div className="orma-card p-6">
                <MemoryPage currentView="memory" user={user} embedded={true} />
              </div>
            )}
          </motion.div>
        </AnimatePresence>

      </div>
    </ErrorBoundary>
  );
}

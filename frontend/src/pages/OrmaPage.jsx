import { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  Brain, MessageSquare, Mic, Volume2, Sparkles, Clock, History, 
  HelpCircle, ChevronRight, Bookmark, ShieldAlert, Cpu
} from 'lucide-react';
import AIConversationPanel from '../components/AIConversationPanel';
import ConversationsPage from './ConversationsPage';
import MemoryPage from './MemoryPage';
import AIInsightsWidget from '../components/AIInsightsWidget';
import ErrorBoundary from '../components/ErrorBoundary';

export default function OrmaPage({ 
  user, 
  messages, 
  isListening, 
  isSpeaking, 
  isTranscribing, 
  isThinking, 
  handleStopRecording, 
  onClearConversation, 
  handleAskAgain,
  timeContext
}) {
  const [activeTab, setActiveTab] = useState('assistant'); // 'assistant', 'history', 'memory'

  const quickQuestions = [
    "Did I take my morning medicine?",
    "What medicines are due today?",
    "When is my next doctor appointment?",
    "How is my adherence this week?",
    "Remind me what Amlodipine is for.",
    "Good morning! How are you feeling today?"
  ];

  return (
    <ErrorBoundary>
      <div className="w-full max-w-7xl mx-auto flex flex-col gap-8 pb-12">
        {/* Header */}
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 bg-gradient-to-r from-indigo-950/80 via-slate-900 to-purple-950/80 p-6 md:p-8 rounded-3xl border border-indigo-500/20 backdrop-blur-xl">
          <div className="flex items-center gap-4">
            <div className="w-14 h-14 rounded-2xl bg-gradient-to-tr from-indigo-500 to-purple-600 flex items-center justify-center shadow-lg shadow-indigo-500/25">
              <Brain className="w-8 h-8 text-white animate-pulse" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h1 className="text-3xl font-extrabold text-white tracking-tight">ORMA AI Companion</h1>
                <span className="px-2.5 py-0.5 rounded-full text-xs font-bold bg-indigo-500/20 text-indigo-300 border border-indigo-500/30">
                  Voice & Intelligence
                </span>
              </div>
              <p className="text-slate-300 text-sm md:text-base mt-1">
                Your empathetic, voice-enabled personal healthcare AI assistant.
              </p>
            </div>
          </div>

          <div className="flex items-center gap-2 p-1.5 bg-slate-900/80 border border-slate-800 rounded-2xl">
            <button
              onClick={() => setActiveTab('assistant')}
              className={`flex items-center gap-2 px-4 py-2.5 rounded-xl font-bold text-sm transition-all ${
                activeTab === 'assistant'
                  ? 'bg-indigo-600 text-white shadow-md'
                  : 'text-slate-400 hover:text-white'
              }`}
            >
              <Mic className="w-4 h-4" /> Live Companion
            </button>
            <button
              onClick={() => setActiveTab('history')}
              className={`flex items-center gap-2 px-4 py-2.5 rounded-xl font-bold text-sm transition-all ${
                activeTab === 'history'
                  ? 'bg-indigo-600 text-white shadow-md'
                  : 'text-slate-400 hover:text-white'
              }`}
            >
              <History className="w-4 h-4" /> Conversation History
            </button>
            <button
              onClick={() => setActiveTab('memory')}
              className={`flex items-center gap-2 px-4 py-2.5 rounded-xl font-bold text-sm transition-all ${
                activeTab === 'memory'
                  ? 'bg-indigo-600 text-white shadow-md'
                  : 'text-slate-400 hover:text-white'
              }`}
            >
              <Cpu className="w-4 h-4" /> Memory & Context
            </button>
          </div>
        </div>

        {/* Tab Content */}
        <AnimatePresence mode="wait">
          <motion.div
            key={activeTab}
            initial={{ opacity: 0, y: 15 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -15 }}
            transition={{ duration: 0.2 }}
          >
            {activeTab === 'assistant' && (
              <div className="grid grid-cols-1 xl:grid-cols-12 gap-8">
                {/* Center Column - AI Conversation */}
                <div className="col-span-1 xl:col-span-8 flex flex-col items-center">
                  <AIConversationPanel
                    user={user}
                    isListening={isListening}
                    isSpeaking={isSpeaking}
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

                {/* Right Column - Quick Questions & AI Insights */}
                <div className="col-span-1 xl:col-span-4 flex flex-col gap-6">
                  {/* Quick Questions Card */}
                  <div className="orma-card p-6 border-indigo-500/20">
                    <h3 className="text-lg font-bold text-white mb-4 flex items-center gap-2">
                      <HelpCircle className="w-5 h-5 text-indigo-400" /> Suggested Quick Questions
                    </h3>
                    <div className="flex flex-col gap-2.5">
                      {quickQuestions.map((q, idx) => (
                        <button
                          key={idx}
                          onClick={() => handleAskAgain(q)}
                          className="text-left px-4 py-3 bg-slate-900/60 hover:bg-indigo-600/20 hover:border-indigo-500/40 border border-slate-700/50 rounded-xl text-slate-200 text-sm font-medium transition-all duration-150 flex items-center justify-between group"
                        >
                          <span>{q}</span>
                          <ChevronRight className="w-4 h-4 text-slate-500 group-hover:text-indigo-400 transition-colors" />
                        </button>
                      ))}
                    </div>
                  </div>

                  <AIInsightsWidget user={user} />
                </div>
              </div>
            )}

            {activeTab === 'history' && (
              <ConversationsPage messages={messages} user={user} />
            )}

            {activeTab === 'memory' && (
              <MemoryPage user={user} />
            )}
          </motion.div>
        </AnimatePresence>
      </div>
    </ErrorBoundary>
  );
}

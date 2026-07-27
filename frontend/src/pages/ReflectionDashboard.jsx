import React, { useState, useEffect } from 'react';
import DashboardLayout from '../layouts/DashboardLayout';
import { motion } from 'framer-motion';
import { rljApi } from '../services/api';
import { useApi } from '../hooks/useApi';
import { 
  BookOpen, Calendar, Clock, Activity, FileText, Database, ShieldCheck, HeartPulse, History
} from 'lucide-react';

export default function ReflectionDashboard({ currentView, onViewChange, user, onLogout }) {
  const { data: journalEntries, execute: loadJournal } = useApi(rljApi.getJournalEntries);
  const { data: timeline, execute: loadTimeline } = useApi(rljApi.getTimeline);
  
  const [activeTab, setActiveTab] = useState('daily'); // daily, weekly, monthly, timeline

  const loadData = () => {
    if (activeTab === 'timeline') {
      loadTimeline(1);
    } else {
      loadJournal(1, activeTab);
    }
  };

  useEffect(() => {
    loadData();
  }, [activeTab]);

  const handleGenerate = async () => {
    if (activeTab !== 'timeline') {
      await rljApi.triggerGeneration(1, activeTab);
      loadData();
    } else {
      await rljApi.triggerMockEvent(1);
      loadData();
    }
  };

  const renderJournal = () => {
    if (!journalEntries || journalEntries.length === 0) {
      return (
        <div className="text-center py-12 border border-dashed border-slate-700 rounded-2xl bg-slate-900/50">
          <BookOpen className="w-12 h-12 text-slate-600 mx-auto mb-4" />
          <h3 className="text-xl font-bold text-slate-300 mb-2">No {activeTab} reflections yet</h3>
          <p className="text-slate-500 mb-6">Orma AI will generate factual summaries of your activity here.</p>
          <button onClick={handleGenerate} className="px-4 py-2 bg-purple-500/20 text-purple-400 rounded-lg hover:bg-purple-500/30 transition-colors">
            Generate {activeTab.charAt(0).toUpperCase() + activeTab.slice(1)} Reflection (Dev)
          </button>
        </div>
      );
    }

    return (
      <div className="space-y-6">
        <div className="flex justify-end">
          <button onClick={handleGenerate} className="px-4 py-2 bg-purple-500/20 text-purple-400 text-sm font-bold rounded-lg hover:bg-purple-500/30 transition-colors">
            Generate New
          </button>
        </div>
        {journalEntries.map((entry, idx) => (
          <motion.div 
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: idx * 0.1 }}
            key={entry.id} 
            className="orma-card p-6 border-purple-500/20 bg-purple-900/5"
          >
            <div className="flex items-start gap-4">
              <div className="p-3 bg-purple-500/20 rounded-xl">
                <FileText className="w-6 h-6 text-purple-400" />
              </div>
              <div className="flex-1">
                <div className="flex justify-between items-center mb-2">
                  <h3 className="text-lg font-bold text-white capitalize">{entry.entry_type} Reflection</h3>
                  <span className="text-sm font-medium text-slate-500">{new Date(entry.date).toLocaleString()}</span>
                </div>
                
                <p className="text-slate-300 text-base leading-relaxed mb-6 bg-slate-800/40 p-4 rounded-xl border border-slate-700/50">
                  {entry.content}
                </p>
                
                <div>
                  <h4 className="text-xs font-bold text-slate-500 uppercase tracking-wider mb-2 flex items-center gap-2">
                    <Database className="w-4 h-4" /> Data Sources Used
                  </h4>
                  <div className="flex flex-wrap gap-2">
                    {entry.sources_used?.map((src, i) => (
                      <span key={i} className="px-3 py-1 bg-slate-800 rounded-full text-xs text-slate-400 border border-slate-700">
                        {src}
                      </span>
                    ))}
                  </div>
                </div>
              </div>
            </div>
          </motion.div>
        ))}
      </div>
    );
  };

  const renderTimeline = () => {
    if (!timeline || timeline.length === 0) {
      return (
        <div className="text-center py-12 border border-dashed border-slate-700 rounded-2xl bg-slate-900/50">
          <History className="w-12 h-12 text-slate-600 mx-auto mb-4" />
          <h3 className="text-xl font-bold text-slate-300 mb-2">Your Life Timeline is empty</h3>
          <p className="text-slate-500 mb-6">Significant life events will appear here chronologically.</p>
          <button onClick={handleGenerate} className="px-4 py-2 bg-blue-500/20 text-blue-400 rounded-lg hover:bg-blue-500/30 transition-colors">
            Add Mock Event (Dev)
          </button>
        </div>
      );
    }

    return (
      <div className="relative border-l-2 border-slate-700 ml-4 pl-8 py-4 space-y-8">
        <div className="absolute top-0 right-0">
          <button onClick={handleGenerate} className="px-4 py-2 bg-blue-500/20 text-blue-400 text-sm font-bold rounded-lg hover:bg-blue-500/30 transition-colors">
            Add Event
          </button>
        </div>
        {timeline.map((item, idx) => (
          <motion.div 
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: idx * 0.1 }}
            key={item.id} 
            className="relative"
          >
            <div className="absolute -left-10 mt-1.5 w-4 h-4 bg-blue-500 rounded-full border-4 border-slate-900"></div>
            <div className="orma-card p-5 border-slate-700/50 hover:border-blue-500/50 transition-colors">
              <div className="flex justify-between items-start mb-2">
                <h3 className="text-lg font-bold text-white">{item.title}</h3>
                <span className="text-xs font-bold bg-slate-800 text-slate-400 px-3 py-1 rounded-full">
                  {new Date(item.event_date).toLocaleDateString()}
                </span>
              </div>
              <p className="text-slate-400 text-sm mb-3">{item.description}</p>
              <div className="flex items-center gap-1 text-xs text-slate-500 font-medium">
                <Activity className="w-3 h-3" /> Source: {item.source}
              </div>
            </div>
          </motion.div>
        ))}
      </div>
    );
  };

  return (
    <DashboardLayout currentView={currentView} onViewChange={onViewChange} user={user} onLogout={onLogout}>
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-white mb-2 flex items-center gap-3">
          <BookOpen className="text-purple-400" /> Life Journal
        </h1>
        <p className="text-slate-400">Review your factual health journey summaries and life timeline.</p>
      </div>

      <div className="flex gap-2 mb-8 border-b border-slate-800 pb-2">
        <button 
          onClick={() => setActiveTab('daily')}
          className={`px-4 py-2 font-bold transition-colors ${activeTab === 'daily' ? 'text-purple-400 border-b-2 border-purple-400' : 'text-slate-500 hover:text-slate-300'}`}
        >
          Daily Journal
        </button>
        <button 
          onClick={() => setActiveTab('weekly')}
          className={`px-4 py-2 font-bold transition-colors ${activeTab === 'weekly' ? 'text-purple-400 border-b-2 border-purple-400' : 'text-slate-500 hover:text-slate-300'}`}
        >
          Weekly Summary
        </button>
        <button 
          onClick={() => setActiveTab('monthly')}
          className={`px-4 py-2 font-bold transition-colors ${activeTab === 'monthly' ? 'text-purple-400 border-b-2 border-purple-400' : 'text-slate-500 hover:text-slate-300'}`}
        >
          Monthly Summary
        </button>
        <button 
          onClick={() => setActiveTab('timeline')}
          className={`px-4 py-2 font-bold transition-colors ${activeTab === 'timeline' ? 'text-blue-400 border-b-2 border-blue-400' : 'text-slate-500 hover:text-slate-300'}`}
        >
          Life Timeline
        </button>
      </div>

      <div>
        {activeTab === 'timeline' ? renderTimeline() : renderJournal()}
      </div>
    </DashboardLayout>
  );
}

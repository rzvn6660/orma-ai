import React, { useState, useEffect } from 'react';
import DashboardLayout from '../layouts/DashboardLayout';
import { motion } from 'framer-motion';
import { aleApi } from '../services/api';
import { useApi } from '../hooks/useApi';
import { 
  Lightbulb, CheckCircle2, XCircle, Clock, Info, 
  Settings2, Activity, User, MessageSquare, Bell, Languages
} from 'lucide-react';

export default function AleDashboard({ currentView, onViewChange, user, onLogout }) {
  const { data: profile, execute: loadProfile } = useApi(aleApi.getProfile);
  const { data: pendingCandidates, execute: loadPending } = useApi(aleApi.getCandidates);
  const { data: historyCandidates, execute: loadHistory } = useApi(aleApi.getCandidates);
  
  const [activeTab, setActiveTab] = useState('suggestions'); // suggestions, profile, history

  useEffect(() => {
    loadProfile(1);
    loadPending(1, 'pending');
    loadHistory(1, ''); // Load all for history, we'll filter on frontend for simplicity
  }, []);

  const handleResolve = async (id, resolution) => {
    await aleApi.resolveCandidate(id, resolution);
    loadProfile(1);
    loadPending(1, 'pending');
    loadHistory(1, '');
  };

  const handleTestGenerate = async () => {
    await aleApi.testGenerate();
    loadPending(1, 'pending');
  };

  const renderSuggestions = () => {
    if (!pendingCandidates || pendingCandidates.length === 0) {
      return (
        <div className="text-center py-12 border border-dashed border-slate-700 rounded-2xl bg-slate-900/50">
          <Lightbulb className="w-12 h-12 text-slate-600 mx-auto mb-4" />
          <h3 className="text-xl font-bold text-slate-300 mb-2">No New Suggestions</h3>
          <p className="text-slate-500 mb-6">Orma AI is currently observing your routines to learn how best to assist you.</p>
          <button onClick={handleTestGenerate} className="px-4 py-2 bg-blue-500/20 text-blue-400 rounded-lg hover:bg-blue-500/30 transition-colors">
            Simulate Pattern Detection (Dev)
          </button>
        </div>
      );
    }

    return (
      <div className="space-y-4">
        {pendingCandidates.map((candidate, idx) => (
          <motion.div 
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: idx * 0.1 }}
            key={candidate.id} 
            className="orma-card p-6 border-blue-500/30 bg-blue-900/10"
          >
            <div className="flex items-start gap-4">
              <div className="p-3 bg-blue-500/20 rounded-xl">
                <Lightbulb className="w-6 h-6 text-blue-400" />
              </div>
              <div className="flex-1">
                <h3 className="text-lg font-bold text-white mb-2">Pattern Detected</h3>
                <p className="text-slate-300 text-lg mb-4">{candidate.suggestion_text}</p>
                
                <div className="bg-slate-900/80 p-4 rounded-xl border border-slate-700/50 mb-4">
                  <div className="flex items-center gap-2 mb-2">
                    <Info className="w-4 h-4 text-purple-400" />
                    <span className="text-sm font-bold text-slate-300">Why are we suggesting this?</span>
                  </div>
                  <p className="text-sm text-slate-400 mb-2">{candidate.evidence}</p>
                  <div className="flex gap-4 text-xs font-medium">
                    <span className="text-emerald-400">Confidence: {Math.round(candidate.confidence * 100)}%</span>
                    <span className="text-slate-500">Last observed: {new Date(candidate.last_observed).toLocaleDateString()}</span>
                  </div>
                </div>

                <div className="flex flex-wrap gap-3 mt-4">
                  <button onClick={() => handleResolve(candidate.id, 'accepted')} className="flex items-center gap-2 px-4 py-2 bg-emerald-500/20 text-emerald-400 hover:bg-emerald-500/30 rounded-lg font-bold transition-colors">
                    <CheckCircle2 className="w-5 h-5" /> Accept Change
                  </button>
                  <button onClick={() => handleResolve(candidate.id, 'rejected')} className="flex items-center gap-2 px-4 py-2 bg-slate-800 text-slate-300 hover:bg-slate-700 rounded-lg font-medium transition-colors">
                    <XCircle className="w-5 h-5" /> No Thanks
                  </button>
                  <button onClick={() => handleResolve(candidate.id, 'postponed')} className="flex items-center gap-2 px-4 py-2 bg-slate-800 text-slate-300 hover:bg-slate-700 rounded-lg font-medium transition-colors">
                    <Clock className="w-5 h-5" /> Ask Later
                  </button>
                  <button onClick={() => handleResolve(candidate.id, 'never')} className="flex items-center gap-2 px-4 py-2 bg-red-500/10 text-red-400 hover:bg-red-500/20 rounded-lg font-medium transition-colors">
                    Never Ask Again
                  </button>
                </div>
              </div>
            </div>
          </motion.div>
        ))}
      </div>
    );
  };

  const renderProfile = () => {
    if (!profile) return <p className="text-slate-400">Loading profile...</p>;

    const attributes = [
      { key: 'preferred_language', label: 'Preferred Language', icon: Languages, val: profile.preferred_language },
      { key: 'speaking_speed', label: 'Speaking Speed', icon: Activity, val: profile.speaking_speed },
      { key: 'conversation_style', label: 'Conversation Style', icon: MessageSquare, val: profile.conversation_style },
      { key: 'reminder_behaviour', label: 'Reminder Style', icon: Bell, val: profile.reminder_behaviour },
      { key: 'wake_time', label: 'Typical Wake Time', icon: Clock, val: profile.wake_time },
      { key: 'sleep_time', label: 'Typical Sleep Time', icon: Clock, val: profile.sleep_time },
    ];

    return (
      <div className="orma-card p-6">
        <h3 className="text-xl font-bold text-white mb-6">Your Learned Preferences</h3>
        <p className="text-slate-400 mb-8">This is what Orma AI currently knows about how you like to interact. You can change these at any time.</p>
        
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {attributes.map(attr => {
            const Icon = attr.icon;
            return (
              <div key={attr.key} className="bg-slate-800/50 p-4 rounded-xl border border-slate-700/50 flex justify-between items-center">
                <div className="flex items-center gap-3">
                  <div className="p-2 bg-slate-700/50 rounded-lg"><Icon className="w-5 h-5 text-purple-400" /></div>
                  <div>
                    <p className="text-sm font-medium text-slate-400">{attr.label}</p>
                    <p className="text-lg font-bold text-white capitalize">{attr.val}</p>
                  </div>
                </div>
                <button className="text-sm text-blue-400 hover:text-blue-300">Edit</button>
              </div>
            );
          })}
        </div>
      </div>
    );
  };

  const renderHistory = () => {
    const history = historyCandidates?.filter(c => c.status !== 'pending') || [];
    
    if (history.length === 0) {
      return <p className="text-slate-500 text-center py-8">No history available.</p>;
    }

    return (
      <div className="space-y-3">
        {history.map(item => (
          <div key={item.id} className="bg-slate-800/50 p-4 rounded-xl border border-slate-700/50 flex justify-between items-center">
            <div>
              <p className="text-white font-medium">{item.pattern_type.replace('_', ' ')}</p>
              <p className="text-xs text-slate-400">Suggested: {item.suggestion_text}</p>
            </div>
            <div className={`px-3 py-1 rounded-full text-xs font-bold ${
              item.status === 'accepted' ? 'bg-emerald-500/20 text-emerald-400' :
              item.status === 'rejected' ? 'bg-slate-700 text-slate-300' :
              item.status === 'never' ? 'bg-red-500/20 text-red-400' :
              'bg-amber-500/20 text-amber-400'
            }`}>
              {item.status.toUpperCase()}
            </div>
          </div>
        ))}
      </div>
    );
  };

  return (
    <DashboardLayout currentView={currentView} onViewChange={onViewChange} user={user} onLogout={onLogout}>
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-white mb-2 flex items-center gap-3">
          <Settings2 className="text-blue-400" /> Learning About You
        </h1>
        <p className="text-slate-400">Review what Orma AI has learned about your daily routines and preferences.</p>
      </div>

      <div className="flex gap-2 mb-8 border-b border-slate-800 pb-2">
        <button 
          onClick={() => setActiveTab('suggestions')}
          className={`px-4 py-2 font-bold transition-colors ${activeTab === 'suggestions' ? 'text-blue-400 border-b-2 border-blue-400' : 'text-slate-500 hover:text-slate-300'}`}
        >
          New Suggestions 
          {pendingCandidates?.length > 0 && (
            <span className="ml-2 bg-blue-500 text-white text-xs px-2 py-0.5 rounded-full">{pendingCandidates.length}</span>
          )}
        </button>
        <button 
          onClick={() => setActiveTab('profile')}
          className={`px-4 py-2 font-bold transition-colors ${activeTab === 'profile' ? 'text-blue-400 border-b-2 border-blue-400' : 'text-slate-500 hover:text-slate-300'}`}
        >
          Active Profile
        </button>
        <button 
          onClick={() => setActiveTab('history')}
          className={`px-4 py-2 font-bold transition-colors ${activeTab === 'history' ? 'text-blue-400 border-b-2 border-blue-400' : 'text-slate-500 hover:text-slate-300'}`}
        >
          History Log
        </button>
      </div>

      <div>
        {activeTab === 'suggestions' && renderSuggestions()}
        {activeTab === 'profile' && renderProfile()}
        {activeTab === 'history' && renderHistory()}
      </div>
    </DashboardLayout>
  );
}

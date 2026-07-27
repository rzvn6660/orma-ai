import React, { useState, useEffect } from 'react';
import DashboardLayout from '../layouts/DashboardLayout';
import { motion } from 'framer-motion';
import { ocmeMemoryApi } from '../services/api';
import { useApi } from '../hooks/useApi';
import { 
  Brain, Search, Filter, Pin, Trash2, Edit2, Share2, 
  Info, AlertCircle, Clock, ShieldCheck, HeartPulse,
  Users, User, Activity, Star, Calendar, FileText, Database
} from 'lucide-react';

export default function MemoryPage({ currentView, onViewChange, user, onLogout }) {
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedCategory, setSelectedCategory] = useState('All');
  const [sortBy, setSortBy] = useState('recently_used');
  const [visibilityFilter, setVisibilityFilter] = useState('all');
  
  const [explainingId, setExplainingId] = useState(null);
  const [explanationText, setExplanationText] = useState('');
  
  const { data: memories, execute: loadMemories, loading } = useApi(ocmeMemoryApi.getMemories);

  const categories = [
    "All", "Personal", "Family", "Health", "Medicine", "Appointment",
    "Preference", "Important Event", "Temporary", "Conversation", "Custom"
  ];

  const fetchMemories = () => {
    const params = {
      sort_by: sortBy,
      ...(selectedCategory !== 'All' && { category: selectedCategory }),
      ...(searchTerm && { search: searchTerm }),
      ...(visibilityFilter !== 'all' && { visibility: visibilityFilter })
    };
    loadMemories(params);
  };

  useEffect(() => {
    fetchMemories();
  }, [searchTerm, selectedCategory, sortBy, visibilityFilter]);

  const handlePin = async (id) => {
    await ocmeMemoryApi.pinMemory(id);
    fetchMemories();
  };

  const handleDelete = async (id) => {
    if (window.confirm("Are you sure you want to delete this memory?")) {
      await ocmeMemoryApi.deleteMemory(id);
      fetchMemories();
    }
  };

  const handleShare = async (id) => {
    await ocmeMemoryApi.shareMemory(id);
    fetchMemories();
  };

  const handleExplain = async (id) => {
    if (explainingId === id) {
      setExplainingId(null);
      setExplanationText('');
      return;
    }
    setExplainingId(id);
    setExplanationText('Loading explanation...');
    try {
      const res = await ocmeMemoryApi.explainMemory(id);
      setExplanationText(res.explanation);
    } catch (e) {
      setExplanationText("Failed to explain memory.");
    }
  };

  const getCategoryIcon = (category) => {
    switch (category) {
      case 'Personal': return <User className="w-5 h-5 text-indigo-400" />;
      case 'Family': return <Users className="w-5 h-5 text-purple-400" />;
      case 'Health': return <HeartPulse className="w-5 h-5 text-red-400" />;
      case 'Medicine': return <Activity className="w-5 h-5 text-emerald-400" />;
      case 'Appointment': return <Calendar className="w-5 h-5 text-amber-400" />;
      case 'Preference': return <Star className="w-5 h-5 text-yellow-400" />;
      case 'Important Event': return <AlertCircle className="w-5 h-5 text-pink-400" />;
      default: return <Database className="w-5 h-5 text-blue-400" />;
    }
  };

  return (
    <DashboardLayout currentView={currentView} onViewChange={onViewChange} user={user} onLogout={onLogout}>
      <div className="mb-8 flex flex-col md:flex-row justify-between items-start md:items-end gap-4">
        <div>
          <h1 className="text-3xl font-bold text-white mb-2 flex items-center gap-3">
            <Brain className="text-purple-400" /> My Memory
          </h1>
          <p className="text-slate-400">View and manage everything Orma AI remembers about you.</p>
        </div>
        
        <div className="flex gap-2">
          <div className="relative">
            <Search className="w-5 h-5 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
            <input 
              type="text" 
              placeholder="Search memories..." 
              className="bg-slate-800/80 border border-slate-700 text-white pl-10 pr-4 py-2 rounded-xl focus:outline-none focus:border-purple-500 w-full md:w-64"
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
            />
          </div>
        </div>
      </div>

      <div className="flex flex-wrap gap-2 mb-6">
        {categories.map(cat => (
          <button 
            key={cat}
            onClick={() => setSelectedCategory(cat)}
            className={`px-4 py-2 rounded-full text-sm font-medium transition-colors border ${
              selectedCategory === cat 
                ? 'bg-purple-500/20 text-purple-300 border-purple-500/50' 
                : 'bg-slate-800/50 text-slate-400 border-slate-700/50 hover:bg-slate-700'
            }`}
          >
            {cat}
          </button>
        ))}
      </div>
      
      <div className="flex gap-4 mb-6 text-sm">
        <select 
          className="bg-slate-800 border border-slate-700 text-slate-300 rounded-lg px-3 py-2"
          value={sortBy} onChange={(e) => setSortBy(e.target.value)}
        >
          <option value="recently_used">Sort: Recently Used</option>
          <option value="importance">Sort: Importance</option>
          <option value="pinned">Sort: Pinned First</option>
          <option value="alphabetical">Sort: Alphabetical</option>
        </select>
        
        <select 
          className="bg-slate-800 border border-slate-700 text-slate-300 rounded-lg px-3 py-2"
          value={visibilityFilter} onChange={(e) => setVisibilityFilter(e.target.value)}
        >
          <option value="all">Visibility: All</option>
          <option value="private">Visibility: Private</option>
          <option value="shared">Visibility: Shared</option>
        </select>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-6">
        {loading ? (
          <p className="text-slate-400 col-span-full">Loading memories...</p>
        ) : memories?.length === 0 ? (
          <p className="text-slate-400 col-span-full text-center py-12 border border-dashed border-slate-700 rounded-2xl">
            No memories found matching your criteria.
          </p>
        ) : (
          memories?.map((mem, index) => (
            <motion.div 
              initial={{ opacity: 0, y: 20 }} 
              animate={{ opacity: 1, y: 0 }} 
              transition={{ delay: index * 0.05 }}
              key={mem.id} 
              className={`orma-card p-6 flex flex-col relative border ${mem.pinned ? 'border-purple-500/30 shadow-[0_0_15px_rgba(168,85,247,0.1)]' : 'border-slate-800'}`}
            >
              {mem.pinned && <Pin className="absolute top-4 right-4 w-4 h-4 text-purple-400 fill-purple-400/20" />}
              
              <div className="flex items-start gap-3 mb-4">
                <div className="p-3 bg-slate-800/80 rounded-xl">
                  {getCategoryIcon(mem.category)}
                </div>
                <div className="pr-6">
                  <span className="text-xs font-bold text-slate-500 uppercase tracking-wider">{mem.category}</span>
                  <h3 className="text-lg font-bold text-white leading-tight mt-1">{mem.title}</h3>
                </div>
              </div>
              
              <div className="bg-slate-900/50 p-4 rounded-xl border border-slate-800 mb-4 flex-grow">
                <p className="text-slate-300 text-sm">{mem.value}</p>
              </div>
              
              <div className="grid grid-cols-2 gap-2 text-xs text-slate-400 mb-4 bg-slate-800/30 p-3 rounded-lg">
                <div className="flex items-center gap-1"><Star className="w-3 h-3"/> Score: {mem.importance}/100</div>
                <div className="flex items-center gap-1"><ShieldCheck className="w-3 h-3"/> Conf: {Math.round(mem.confidence * 100)}%</div>
                <div className="flex items-center gap-1"><Clock className="w-3 h-3"/> Used: {mem.usage_count}x</div>
                <div className="flex items-center gap-1">
                  {mem.visibility === 'shared' ? <Share2 className="w-3 h-3 text-emerald-400"/> : <LockIcon />}
                  <span className={mem.visibility === 'shared' ? 'text-emerald-400' : ''}>
                    {mem.visibility}
                  </span>
                </div>
              </div>
              
              {explainingId === mem.id && (
                <div className="bg-purple-900/20 border border-purple-500/30 p-3 rounded-lg mb-4 text-sm text-purple-200">
                  <div className="font-bold flex items-center gap-1 mb-1"><Info className="w-4 h-4"/> Explanation</div>
                  <div className="whitespace-pre-wrap">{explanationText}</div>
                </div>
              )}
              
              <div className="flex items-center justify-between mt-auto pt-4 border-t border-slate-800">
                <div className="flex gap-2">
                  <button onClick={() => handleExplain(mem.id)} className="p-2 text-slate-400 hover:text-purple-400 hover:bg-purple-400/10 rounded-lg transition-colors" title="Explain Memory">
                    <Info className="w-4 h-4" />
                  </button>
                  <button onClick={() => handleShare(mem.id)} className={`p-2 rounded-lg transition-colors ${mem.visibility === 'shared' ? 'text-emerald-400 bg-emerald-400/10' : 'text-slate-400 hover:text-emerald-400 hover:bg-emerald-400/10'}`} title="Share with Caregiver">
                    <Share2 className="w-4 h-4" />
                  </button>
                  <button onClick={() => handlePin(mem.id)} className={`p-2 rounded-lg transition-colors ${mem.pinned ? 'text-purple-400 bg-purple-400/10' : 'text-slate-400 hover:text-purple-400 hover:bg-purple-400/10'}`} title="Pin Memory">
                    <Pin className="w-4 h-4" />
                  </button>
                </div>
                <div className="flex gap-2">
                  <button onClick={() => handleDelete(mem.id)} className="p-2 text-slate-400 hover:text-red-400 hover:bg-red-400/10 rounded-lg transition-colors" title="Delete">
                    <Trash2 className="w-4 h-4" />
                  </button>
                </div>
              </div>
            </motion.div>
          ))
        )}
      </div>
    </DashboardLayout>
  );
}

const LockIcon = () => (
  <svg xmlns="http://www.w3.org/2000/svg" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><rect x="3" y="11" width="18" height="11" rx="2" ry="2"></rect><path d="M7 11V7a5 5 0 0 1 10 0v4"></path></svg>
);

import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import { Sparkles, Brain, ArrowRight } from 'lucide-react';
import { insightsApi } from '../services/api';

export default function AIInsightsWidget({ user }) {
  const [activity, setActivity] = useState(null);
  const [memory, setMemory] = useState(null);
  const [recommendation, setRecommendation] = useState(null);
  const [loading, setLoading] = useState(true);
  const navigate = useNavigate();

  useEffect(() => {
    async function fetchInsights() {
      try {
        const summary = await insightsApi.getSummary();
        setActivity(summary.activity);
        setMemory(summary.memory);
        setRecommendation(summary.recommendation);
      } catch (err) {
        console.error("Error fetching insights summary:", err);
      } finally {
        setLoading(false);
      }
    }

    fetchInsights();
  }, []);

  const handleCardClick = (link) => {
    if (link) navigate(link);
  };

  return (
    <motion.div 
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      className="orma-card p-5 border-purple-500/30 bg-slate-900/50 hover:bg-slate-800/80 transition-colors relative overflow-hidden"
    >
      <div className="absolute top-0 right-0 p-4 opacity-10">
        <Brain className="w-24 h-24 text-purple-400" />
      </div>
      
      <div className="relative z-10">
        <div className="flex items-center gap-2 mb-3">
          <div className="p-2 bg-purple-500/20 rounded-lg">
            <Sparkles className="w-4 h-4 text-purple-400" />
          </div>
          <h3 className="text-sm font-bold text-white uppercase tracking-wider">AI Insights</h3>
        </div>
        
        <div className="space-y-3">
          {/* Card 1: Today's Activity */}
          <div 
            onClick={() => handleCardClick(activity?.link)}
            className="bg-slate-800/60 rounded-xl p-4 border border-slate-700/50 backdrop-blur-sm cursor-pointer hover:border-purple-500/50 hover:bg-slate-800 transition-all group"
          >
            <div className="mb-2 flex items-center justify-between">
              <span className="text-[10px] uppercase tracking-widest font-bold text-purple-400 bg-purple-500/10 px-2 py-1 rounded">Today's Activity</span>
              <ArrowRight className="w-4 h-4 text-slate-500 group-hover:text-purple-400 transition-colors" />
            </div>
            <p className="text-sm text-slate-300 leading-relaxed">
              {loading ? "Analyzing..." : activity?.text}
            </p>
            {!loading && activity && (
              <div className="mt-3 text-[10px] text-slate-500 flex justify-between">
                <span>Source: {activity.source}</span>
                <span>Updated: {activity.updated}</span>
              </div>
            )}
          </div>

          {/* Card 2: Important Memory */}
          <div 
            onClick={() => handleCardClick(memory?.link)}
            className="bg-slate-800/60 rounded-xl p-4 border border-slate-700/50 backdrop-blur-sm cursor-pointer hover:border-blue-500/50 hover:bg-slate-800 transition-all group"
          >
            <div className="mb-2 flex items-center justify-between">
              <span className="text-[10px] uppercase tracking-widest font-bold text-blue-400 bg-blue-500/10 px-2 py-1 rounded">Important Memory</span>
              <ArrowRight className="w-4 h-4 text-slate-500 group-hover:text-blue-400 transition-colors" />
            </div>
            <p className="text-sm text-slate-300 leading-relaxed">
              {loading ? "Analyzing..." : memory?.text}
            </p>
            {!loading && memory && (
              <div className="mt-3 text-[10px] text-slate-500 flex justify-between">
                <span>Source: {memory.source}</span>
                <span>Updated: {memory.updated}</span>
              </div>
            )}
          </div>

          {/* Card 3: Next Recommendation */}
          <div 
            onClick={() => handleCardClick(recommendation?.link)}
            className="bg-slate-800/60 rounded-xl p-4 border border-slate-700/50 backdrop-blur-sm cursor-pointer hover:border-emerald-500/50 hover:bg-slate-800 transition-all group"
          >
            <div className="mb-2 flex items-center justify-between">
              <span className="text-[10px] uppercase tracking-widest font-bold text-emerald-400 bg-emerald-500/10 px-2 py-1 rounded">Next Recommendation</span>
              <ArrowRight className="w-4 h-4 text-slate-500 group-hover:text-emerald-400 transition-colors" />
            </div>
            <p className="text-sm text-slate-300 leading-relaxed">
              {loading ? "Analyzing..." : recommendation?.text}
            </p>
            {!loading && recommendation && (
              <div className="mt-3 text-[10px] text-slate-500 flex justify-between">
                <span>Source: {recommendation.source}</span>
                <span>Updated: {recommendation.updated}</span>
              </div>
            )}
          </div>
        </div>
      </div>
    </motion.div>
  );
}

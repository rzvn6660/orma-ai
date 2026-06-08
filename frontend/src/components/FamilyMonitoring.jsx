import React from 'react';
import { motion } from 'framer-motion';
import { Users, Phone, Video } from 'lucide-react';

export default function FamilyMonitoring() {
  return (
    <motion.div 
      initial={{ opacity: 0, x: -20 }}
      animate={{ opacity: 1, x: 0 }}
      transition={{ duration: 0.6, delay: 0.6 }}
      className="glass-card p-6"
    >
      <div className="flex justify-between items-center mb-6">
        <h3 className="text-xl font-bold text-white flex items-center gap-2">
          <Users className="text-indigo-400 w-5 h-5" />
          Family Connection
        </h3>
        <span className="text-xs text-emerald-400 bg-emerald-500/10 px-2 py-1 rounded-md font-medium">
          All Good
        </span>
      </div>

      <div className="space-y-4">
        {/* Family Member Card */}
        <div className="flex items-center justify-between p-4 bg-slate-800/50 rounded-xl border border-slate-700/50">
          <div className="flex items-center gap-3">
            <div className="relative">
              <img 
                src="https://i.pravatar.cc/150?img=47" 
                alt="Daughter" 
                className="w-12 h-12 rounded-full object-cover border-2 border-indigo-500/30"
              />
              <span className="absolute bottom-0 right-0 w-3 h-3 bg-emerald-500 border-2 border-slate-800 rounded-full"></span>
            </div>
            <div>
              <h4 className="font-semibold text-white">Emily (Daughter)</h4>
              <p className="text-xs text-slate-400">Last checked 10m ago</p>
            </div>
          </div>
          
          <div className="flex gap-2">
            <button className="p-2.5 bg-slate-700/50 hover:bg-slate-600/50 rounded-lg transition-colors text-slate-300">
              <Phone className="w-4 h-4" />
            </button>
            <button className="p-2.5 bg-indigo-500/20 hover:bg-indigo-500/30 rounded-lg transition-colors text-indigo-400">
              <Video className="w-4 h-4" />
            </button>
          </div>
        </div>

        {/* Quick Summary */}
        <div className="grid grid-cols-2 gap-3 mt-4">
          <div className="bg-slate-800/30 p-3 rounded-lg border border-slate-700/30">
            <p className="text-xs text-slate-400 mb-1">Medication</p>
            <p className="text-lg font-semibold text-emerald-400">100%</p>
          </div>
          <div className="bg-slate-800/30 p-3 rounded-lg border border-slate-700/30">
            <p className="text-xs text-slate-400 mb-1">Activity</p>
            <p className="text-lg font-semibold text-blue-400">Normal</p>
          </div>
        </div>
      </div>
    </motion.div>
  );
}

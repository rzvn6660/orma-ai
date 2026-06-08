import React from 'react';
import { Home, MessageSquare, Pill, AlertOctagon, Settings, Activity, User, LogOut } from 'lucide-react';

export default function Sidebar() {
  const navItems = [
    { icon: Home, label: 'Dashboard', active: true },
    { icon: MessageSquare, label: 'Conversations' },
    { icon: Pill, label: 'Medicines' },
    { icon: AlertOctagon, label: 'Emergency' },
    { icon: Activity, label: 'Health Vitals' },
  ];

  return (
    <aside className="w-64 glass-panel h-screen fixed left-0 top-0 flex flex-col hidden md:flex z-50">
      {/* Brand */}
      <div className="p-6 flex items-center gap-3 border-b border-slate-700/50">
        <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-blue-500 to-indigo-600 flex items-center justify-center shadow-lg shadow-blue-500/30">
          <Activity className="text-white w-6 h-6" />
        </div>
        <h1 className="text-2xl font-bold text-white tracking-tight">Orma <span className="text-blue-400">AI</span></h1>
      </div>

      {/* Navigation */}
      <nav className="flex-1 py-8 px-4 flex flex-col gap-2">
        {navItems.map((item, index) => {
          const Icon = item.icon;
          return (
            <button
              key={index}
              className={`flex items-center gap-4 px-4 py-3 rounded-xl transition-all duration-300 w-full text-left
                ${item.active 
                  ? 'bg-blue-600/20 text-blue-400 border border-blue-500/30 shadow-[0_0_15px_rgba(59,130,246,0.15)]' 
                  : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/50 border border-transparent'
                }`}
            >
              <Icon className="w-5 h-5" />
              <span className="font-medium text-sm">{item.label}</span>
            </button>
          );
        })}
      </nav>

      {/* Bottom Settings */}
      <div className="p-4 border-t border-slate-700/50 flex flex-col gap-2">
        <button className="flex items-center gap-4 px-4 py-3 rounded-xl transition-colors text-slate-400 hover:text-slate-200 hover:bg-slate-800/50 w-full text-left">
          <Settings className="w-5 h-5" />
          <span className="font-medium text-sm">Settings</span>
        </button>
        <button className="flex items-center gap-4 px-4 py-3 rounded-xl transition-colors text-slate-400 hover:text-red-400 hover:bg-red-500/10 w-full text-left">
          <LogOut className="w-5 h-5" />
          <span className="font-medium text-sm">Sign Out</span>
        </button>
      </div>
    </aside>
  );
}

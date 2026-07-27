import { Home, Heart, Brain, AlertOctagon, Settings, User, LogOut, Users, X } from 'lucide-react';
import BrandLogo from './BrandLogo';

export default function Sidebar({ currentView, onViewChange, onLogout, user, isOpen, onClose }) {
  const isCaregiver = user?.role === 'caregiver';

  const elderlyItems = [
    { id: 'home', icon: Home, label: 'Home' },
    { id: 'my-health', icon: Heart, label: 'My Health' },
    { id: 'orma', icon: Brain, label: 'ORMA' },
    { id: 'emergency', icon: AlertOctagon, label: 'Emergency' },
    { id: 'settings', icon: Settings, label: 'Settings' },
  ];

  const caregiverItems = [
    { id: 'caregiver', icon: Home, label: 'Dashboard' },
    { id: 'family', icon: Users, label: 'Family' },
    { id: 'my-health', icon: Heart, label: 'Patient Health' },
    { id: 'orma', icon: Brain, label: 'ORMA' },
    { id: 'emergency', icon: AlertOctagon, label: 'Emergency' },
    { id: 'settings', icon: Settings, label: 'Settings' },
  ];

  const visibleItems = isCaregiver ? caregiverItems : elderlyItems;

  return (
    <aside className={`fixed left-0 top-0 h-screen w-[240px] bg-slate-900/95 md:bg-slate-900/60 backdrop-blur-2xl border-r border-slate-800/80 z-50 flex flex-col transition-transform duration-300 transform ${isOpen ? 'translate-x-0' : '-translate-x-full'} md:translate-x-0 shadow-2xl`}>
      <div className="pt-8 pb-6 px-6 flex flex-col h-full">
        {/* Logo */}
        <div 
          className="mb-10 px-2 cursor-pointer transition-transform hover:scale-[1.02]" 
          onClick={() => onViewChange(isCaregiver ? 'caregiver' : 'home')}
          style={{ border: 'none', outline: 'none', boxShadow: 'none', background: 'transparent' }}
        >
          <BrandLogo 
            className="h-[44px]" 
            textClassName="text-[22px]" 
            textColor="text-white" 
            accentColor="text-blue-400"
            textOverride={<>ORMA <span className="text-blue-400">AI</span></>}
          />
        </div>

        <div className="md:hidden absolute top-6 right-4">
          <button onClick={onClose} className="text-slate-400 hover:text-white p-2.5 bg-slate-800/60 rounded-xl border border-slate-700/50">
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Navigation items */}
        <nav className="flex-1 flex flex-col gap-3.5 overflow-y-auto custom-scrollbar min-h-0">
          {visibleItems.map((item) => {
            const Icon = item.icon;
            const isActive = currentView === item.id || 
              (item.id === 'home' && currentView === 'dashboard') ||
              (item.id === 'my-health' && ['medicines', 'planner', 'records', 'vitals'].includes(currentView)) ||
              (item.id === 'orma' && currentView === 'conversations');

            return (
              <button
                key={item.id}
                onClick={() => onViewChange(item.id)}
                className={`flex items-center gap-4 px-4 py-3.5 rounded-2xl font-bold transition-all duration-200 text-base ${
                  isActive 
                  ? 'bg-blue-600/20 text-blue-400 border border-blue-500/40 shadow-[0_0_20px_rgba(59,130,246,0.2)]' 
                  : 'text-slate-300 hover:text-white hover:bg-slate-800/50 border border-transparent'
                }`}
              >
                <Icon className={`w-6 h-6 ${isActive ? 'text-blue-400' : 'text-slate-400'}`} />
                <span>{item.label}</span>
              </button>
            );
          })}
        </nav>

        {/* User Card & Sign Out */}
        <div className="mt-auto pt-6 border-t border-slate-800/80 mx-1">
          <div className="flex items-center gap-3 p-3 rounded-2xl bg-slate-800/40 mb-3 border border-slate-700/40">
            <div className="w-10 h-10 rounded-full bg-blue-600/20 border border-blue-500/30 flex items-center justify-center shadow-inner shrink-0">
              <User className="text-blue-400 w-5 h-5" />
            </div>
            <div className="flex-1 overflow-hidden">
              <p className="text-sm font-bold text-white tracking-wide truncate">{user?.name || 'User'}</p>
              <p className="text-[11px] font-bold text-slate-400 uppercase tracking-widest">{user?.role || 'elderly'}</p>
            </div>
          </div>
          <button 
            onClick={onLogout} 
            className="flex items-center gap-3 px-4 py-3 text-red-400 hover:text-red-300 hover:bg-red-500/10 rounded-2xl transition-colors w-full text-left font-bold text-sm"
          >
            <LogOut className="w-5 h-5" />
            <span>Sign Out</span>
          </button>
        </div>
      </div>
    </aside>
  );
}

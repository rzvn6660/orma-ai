import { useState } from 'react';
import Sidebar from '../components/Sidebar';
import NotificationCenter from '../components/NotificationCenter';
import PatientSwitcher from '../components/PatientSwitcher';
import { Menu } from 'lucide-react';

export default function DashboardLayout({ children, currentView, onViewChange, user, onLogout }) {
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  // Global App Background (Single Source of Truth)
  const backgroundClass = 'bg-slate-950';

  return (
    <div className={`flex h-screen overflow-hidden ${backgroundClass}`}>
      {/* Background decorations for extra depth, keeping it subtle */}
      <div className="fixed top-[-20%] left-[-10%] w-[50%] h-[50%] rounded-full bg-white/5 blur-[120px] pointer-events-none" />
      <div className="fixed bottom-[-20%] right-[-10%] w-[50%] h-[50%] rounded-full bg-white/5 blur-[120px] pointer-events-none" />
      
      {/* Mobile Overlay */}
      {mobileMenuOpen && (
        <div 
          className="fixed inset-0 bg-black/60 backdrop-blur-sm z-40 md:hidden"
          onClick={() => setMobileMenuOpen(false)}
        />
      )}

      <Sidebar 
        isOpen={mobileMenuOpen} 
        onClose={() => setMobileMenuOpen(false)} 
        currentView={currentView} 
        onViewChange={(v) => { onViewChange(v); setMobileMenuOpen(false); }} 
        user={user} 
        onLogout={onLogout} 
      />
      
      <main className="flex-1 md:ml-[220px] relative z-10 overflow-hidden flex flex-col h-screen">
        {/* Top Header / Notification Bar */}
        <div className="sticky top-0 z-30 flex items-center justify-between p-4 md:px-10 md:py-6 bg-transparent border-b border-white/5">
          <div className="flex items-center gap-3">
            <button onClick={() => setMobileMenuOpen(true)} className="md:hidden p-2 text-white/70 hover:text-white rounded-lg hover:bg-white/10">
              <Menu className="w-6 h-6" />
            </button>
            <h2 className="text-xl font-bold text-white hidden md:block capitalize drop-shadow-md">{currentView.replace('_', ' ')}</h2>
          </div>
          
          <div className="flex items-center gap-4">
            <PatientSwitcher user={user} />
            <NotificationCenter user={user} />
          </div>
        </div>

        <div className="w-full p-4 md:p-8 flex-1 overflow-y-auto custom-scrollbar">
          {children}
        </div>
      </main>
    </div>
  );
}

import { useState, useEffect, useCallback } from 'react';
import Sidebar from '../components/Sidebar';
import NotificationCenter from '../components/NotificationCenter';
import PatientSwitcher from '../components/PatientSwitcher';
import OrmaDock from '../components/ui/dock';
import BrandLogo from '../components/BrandLogo';
import ProfileDropdown from '../components/ui/ProfileDropdown';
import CaregiverEmergencyOverlay from '../components/ui/CaregiverEmergencyOverlay';
import CaregiverEmergencyBanner from '../components/ui/CaregiverEmergencyBanner';
import { Menu, LogOut } from 'lucide-react';
import { startEmergencySound, stopEmergencySound, isAudioRestricted } from '../utils/emergencyAudio';
import { emergencyApi } from '../services/api';
import { useWebSocket } from '../hooks/useWebSocket';

export default function DashboardLayout({ children, currentView, onViewChange, user, onLogout }) {
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const [navStyle, setNavStyle] = useState(localStorage.getItem('orma_navigation_style') || 'sidebar');
  const [sidebarCollapsed, setSidebarCollapsed] = useState(() => {
    return localStorage.getItem('orma_sidebar_collapsed') === 'true';
  });

  // Active Caregiver Emergency Overlay & Persistent Banner State
  const [incomingEmergency, setIncomingEmergency] = useState(null);
  const [dismissedOverlayId, setDismissedOverlayId] = useState(null);
  const [audioBlocked, setAudioBlocked] = useState(false);

  const isCaregiver = user?.role === 'caregiver';

  // Global authenticated WebSocket connection
  useWebSocket(user?.id);

  const normalizeEmergency = (raw) => {
    if (!raw) return null;
    const id = raw.id || raw.alert_id || raw.emergency_id;
    if (!id) return null;
    return {
      id,
      alert_id: id,
      elder_id: raw.elder_id,
      elder_name: raw.elder_name || 'Family Member',
      elder_phone: raw.elder_phone,
      severity: raw.severity || 'critical',
      status: raw.status || 'active',
      message: raw.message || `${raw.elder_name || 'Family Member'} may need immediate assistance.`,
      created_at: raw.created_at || new Date().toISOString(),
      acknowledged_at: raw.acknowledged_at,
      acknowledged_by: raw.acknowledged_by,
      resolved_at: raw.resolved_at
    };
  };

  // Sync active emergency alerts on mount and periodic fallback polling (every 10s)
  useEffect(() => {
    if (!isCaregiver) return;

    const syncActiveEmergencies = async () => {
      try {
        const data = await emergencyApi.getActive();
        const activeList = data?.active_emergencies || [];
        const unacked = activeList.find(a => a.status === 'active');
        if (unacked) {
          const norm = normalizeEmergency(unacked);
          setIncomingEmergency(prev => {
            const prevId = prev?.id || prev?.alert_id;
            if (prevId !== norm.id) {
              startEmergencySound();
              setAudioBlocked(isAudioRestricted());
              return norm;
            }
            return { ...prev, ...norm };
          });
        } else {
          // If no active unacknowledged alert from backend
          const anyActive = activeList.find(a => a.status === 'acknowledged');
          if (!anyActive) {
            // Truly 0 emergencies
            setIncomingEmergency(prev => {
              if (prev) {
                stopEmergencySound();
              }
              return null;
            });
            setDismissedOverlayId(null);
          } else {
            stopEmergencySound();
            setIncomingEmergency(null);
          }
        }
      } catch (err) {
        console.warn('[ORMA] Could not query active emergency state:', err);
      }
    };

    syncActiveEmergencies();
    const interval = setInterval(syncActiveEmergencies, 10000);
    return () => clearInterval(interval);
  }, [isCaregiver]);

  // Real-time WebSocket listener for emergency alerts
  useEffect(() => {
    const handleWs = (e) => {
      const data = e.detail;
      if (!data) return;

      if (data.type === 'emergency_alert' && isCaregiver) {
        const norm = normalizeEmergency(data);
        if (norm) {
          setIncomingEmergency(norm);
          setDismissedOverlayId(null); // Reset dismissal on brand new incoming alert
          startEmergencySound();
          setAudioBlocked(isAudioRestricted());
        }
      } else if (data.type === 'emergency_acknowledged' || data.type === 'emergency_resolved') {
        stopEmergencySound();
        setIncomingEmergency(null);
        setDismissedOverlayId(null);
      }
    };

    window.addEventListener('orma_websocket_message', handleWs);
    return () => window.removeEventListener('orma_websocket_message', handleWs);
  }, [isCaregiver]);

  useEffect(() => {
    const handleStyleChange = () => {
      setNavStyle(localStorage.getItem('orma_navigation_style') || 'sidebar');
    };
    const handleCollapseChange = () => {
      setSidebarCollapsed(localStorage.getItem('orma_sidebar_collapsed') === 'true');
    };

    window.addEventListener('navigationStyleChange', handleStyleChange);
    window.addEventListener('sidebarCollapseChange', handleCollapseChange);
    return () => {
      window.removeEventListener('navigationStyleChange', handleStyleChange);
      window.removeEventListener('sidebarCollapseChange', handleCollapseChange);
    };
  }, []);

  const isDock = navStyle === 'dock';
  const backgroundClass = 'bg-[#060B1E]';

  // Compute dynamic desktop margin
  const desktopMarginClass = isDock 
    ? 'md:ml-0' 
    : sidebarCollapsed 
    ? 'md:ml-[80px]' 
    : 'md:ml-[260px]';

  return (
    <div className={`flex h-screen overflow-hidden ${backgroundClass} text-slate-200 selection:bg-blue-500/30 selection:text-blue-200`}>
      {/* Subtle Ambient Depth Lighting (Soft, calm dark navy/blue depth) */}
      <div className="fixed top-[-10%] left-[-5%] w-[45%] h-[45%] rounded-full bg-blue-950/20 blur-[160px] pointer-events-none" />
      <div className="fixed bottom-[-10%] right-[-5%] w-[45%] h-[45%] rounded-full bg-blue-950/15 blur-[160px] pointer-events-none" />
      
      {/* Mobile Overlay */}
      {mobileMenuOpen && (
        <div 
          className="fixed inset-0 bg-slate-950/70 backdrop-blur-sm z-40 md:hidden"
          onClick={() => setMobileMenuOpen(false)}
        />
      )}

      {/* Sidebar: Always available for mobile drawer; on desktop visible when navStyle is 'sidebar' */}
      <Sidebar 
        isOpen={mobileMenuOpen} 
        onClose={() => setMobileMenuOpen(false)} 
        currentView={currentView} 
        onViewChange={(v) => { onViewChange(v); setMobileMenuOpen(false); }} 
        user={user} 
        onLogout={onLogout}
        className={isDock ? 'md:hidden' : ''}
        isCollapsed={sidebarCollapsed}
        onToggleCollapse={(next) => setSidebarCollapsed(next)}
      />
      
      <main className={`flex-1 relative z-10 overflow-hidden flex flex-col h-screen transition-all duration-300 ${desktopMarginClass}`}>
        {/* Top Header / Floating Glass Navigation Bar */}
        <div className="sticky top-0 z-30 flex items-center justify-between p-4 md:px-10 md:py-4 bg-[#0B132B]/80 backdrop-blur-2xl border-b border-white/10 shadow-lg">
          <div className="flex items-center gap-3">
            <button 
              type="button"
              onClick={() => setMobileMenuOpen(true)} 
              className="p-2 text-white/70 hover:text-white rounded-xl hover:bg-white/10 md:hidden cursor-pointer"
              aria-label="Open navigation menu"
            >
              <Menu className="w-6 h-6" />
            </button>

            {/* In Dock mode, show Brand Logo on top-left of desktop */}
            {isDock && (
              <div 
                className="hidden md:flex items-center cursor-pointer transition-transform hover:scale-[1.02] mr-4" 
                onClick={() => onViewChange(user?.role === 'caregiver' ? 'caregiver' : 'home')}
              >
                <BrandLogo 
                  className="h-[36px]" 
                  textClassName="text-[20px]" 
                  textColor="text-white" 
                  accentColor="text-blue-400"
                  textOverride={<>ORMA <span className="text-blue-400">AI</span></>}
                />
              </div>
            )}

            <h2 className="text-lg md:text-xl font-extrabold text-white hidden sm:block capitalize tracking-tight drop-shadow-sm">
              {currentView.replace('_', ' ')}
            </h2>
          </div>
          
          <div className="flex items-center gap-2.5 sm:gap-3.5">
            <PatientSwitcher user={user} />
            <NotificationCenter user={user} onViewChange={onViewChange} />
            <ProfileDropdown 
              user={user} 
              onLogout={onLogout} 
              onViewChange={onViewChange} 
            />
          </div>
        </div>

        {/* Content Area (padded on bottom in Dock mode to prevent overlap) */}
        <div className={`w-full p-4 md:p-8 flex-1 overflow-y-auto custom-scrollbar ${isDock ? 'pb-32' : 'pb-8'} flex flex-col gap-6`}>
          {/* Persistent Top Emergency Banner for Caregiver on other pages */}
          {isCaregiver && incomingEmergency && currentView !== 'emergency' && (
            <CaregiverEmergencyBanner
              alert={incomingEmergency}
              userTimezone={user?.timezone}
              onViewEmergency={() => onViewChange('emergency')}
              onAcknowledge={async () => {
                stopEmergencySound();
                const aId = incomingEmergency.id || incomingEmergency.alert_id;
                if (aId) {
                  await emergencyApi.acknowledge(aId);
                }
                setIncomingEmergency(null);
              }}
            />
          )}
          {children}
        </div>
      </main>

      {/* Floating Bottom Dock on Desktop */}
      {isDock && (
        <div className="hidden md:block">
          <OrmaDock 
            currentView={currentView} 
            onViewChange={onViewChange} 
            user={user} 
            onLogout={onLogout} 
          />
        </div>
      )}

      {/* Central High-Priority Emergency Interruption Overlay for Caregiver */}
      {isCaregiver && incomingEmergency && incomingEmergency.status !== 'resolved' && dismissedOverlayId !== (incomingEmergency.id || incomingEmergency.alert_id) && (
        <CaregiverEmergencyOverlay
          alert={incomingEmergency}
          audioBlocked={audioBlocked}
          userTimezone={user?.timezone}
          onViewDetails={() => {
            // Navigate to Emergency Response Center
            onViewChange('emergency');
            setDismissedOverlayId(incomingEmergency.id || incomingEmergency.alert_id);
          }}
          onAcknowledge={async () => {
            stopEmergencySound();
            const aId = incomingEmergency.id || incomingEmergency.alert_id;
            if (aId) {
              await emergencyApi.acknowledge(aId);
            }
            setIncomingEmergency(null);
            setDismissedOverlayId(null);
          }}
          onDismiss={() => {
            // Dismissing hides the central overlay temporarily; persistent banner remains active
            setDismissedOverlayId(incomingEmergency.id || incomingEmergency.alert_id);
          }}
        />
      )}
    </div>
  );
}

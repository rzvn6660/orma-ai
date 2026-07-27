import { useState, useEffect } from 'react';
import { Routes, Route, Navigate, useNavigate, useLocation } from 'react-router-dom';
import Dashboard from './pages/Dashboard';
import AuthFlow from './pages/AuthFlow';
import LandingPage from './pages/LandingPage';
import { authApi } from './services/api';
import { ReminderProvider } from './contexts/ReminderContext';
import ReminderModal from './components/reminders/ReminderModal';
import GlobalToast from './components/GlobalToast';
import BrandLogo from './components/BrandLogo';

export default function App() {
  const navigate = useNavigate();
  const location = useLocation();
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [showAuth, setShowAuth] = useState(false);

  // Derive currentView from path
  const path = location.pathname.substring(1);
  const currentView = path === 'dashboard' ? 'home' : (path || 'home');

  const handleViewChange = (view) => {
    if (view === 'home') {
      navigate('/dashboard');
    } else {
      navigate(`/${view}`);
    }
  };

  useEffect(() => {
    const checkAuth = async () => {
      const token = localStorage.getItem('orma_token');
      if (token) {
        try {
          let userData = await authApi.getMe();
          
          // Timezone Detection
          const browserTimezone = Intl.DateTimeFormat().resolvedOptions().timeZone;
          if (userData.timezone !== browserTimezone) {
            if (userData.timezone && userData.timezone !== "UTC") {
              const confirmUpdate = window.confirm(`It looks like you've travelled! We detected a timezone change from ${userData.timezone} to ${browserTimezone}.\n\nWould you like to automatically update your medication schedule to your new local time?`);
              if (confirmUpdate) {
                userData = await authApi.updateMe({ timezone: browserTimezone });
              }
            } else {
              userData = await authApi.updateMe({ timezone: browserTimezone });
            }
          }

          setUser(userData);
          if (location.pathname === '/' || location.pathname === '') {
             navigate(userData.role === 'caregiver' ? '/caregiver' : '/dashboard');
          }
        } catch (err) {
          localStorage.removeItem('orma_token');
        }
      }
      setLoading(false);
    };
    checkAuth();
  }, []);

  const handleLogin = async (userData) => {
    let finalUser = userData;
    const browserTimezone = Intl.DateTimeFormat().resolvedOptions().timeZone;
    if (finalUser.timezone !== browserTimezone) {
      if (finalUser.timezone && finalUser.timezone !== "UTC") {
        const confirmUpdate = window.confirm(`It looks like you've travelled! We detected a timezone change from ${finalUser.timezone} to ${browserTimezone}.\n\nWould you like to automatically update your medication schedule to your new local time?`);
        if (confirmUpdate) {
          finalUser = await authApi.updateMe({ timezone: browserTimezone });
        }
      } else {
        finalUser = await authApi.updateMe({ timezone: browserTimezone });
      }
    }
    setUser(finalUser);
    navigate(finalUser.role === 'caregiver' ? '/caregiver' : '/dashboard');
  };

  const handleLogout = () => {
    localStorage.removeItem('orma_token');
    setUser(null);
    navigate('/');
  };

  if (loading) {
    return (
      <div className="h-screen bg-slate-950 flex flex-col items-center justify-center gap-6">
        <div className="animate-pulse">
          <BrandLogo layout="vertical" className="h-16" textClassName="text-2xl" textColor="text-white" accentColor="text-blue-400" />
        </div>
        <p className="text-blue-400/80 font-medium tracking-wide animate-pulse">Loading Workspace...</p>
      </div>
    );
  }

  if (!user) {
    if (showAuth) {
      return <AuthFlow onLogin={handleLogin} onBack={() => setShowAuth(false)} />;
    }
    return <LandingPage onTryDemo={() => setShowAuth(true)} />;
  }

  return (
    <ReminderProvider>
      <div className="antialiased selection:bg-blue-500/30 selection:text-blue-200">
        <Routes>
          {/* Main Workspaces */}
          <Route path="/dashboard" element={<Dashboard user={user} currentView="home" onViewChange={handleViewChange} onLogout={handleLogout} />} />
          <Route path="/home" element={<Navigate to="/dashboard" replace />} />
          
          <Route path="/my-health" element={<Dashboard user={user} currentView="my-health" onViewChange={handleViewChange} onLogout={handleLogout} />} />
          
          <Route path="/orma" element={<Dashboard user={user} currentView="orma" onViewChange={handleViewChange} onLogout={handleLogout} />} />
          
          <Route path="/family" element={<Dashboard user={user} currentView="family" onViewChange={handleViewChange} onLogout={handleLogout} />} />
          <Route path="/caregiver" element={<Dashboard user={user} currentView="caregiver" onViewChange={handleViewChange} onLogout={handleLogout} />} />
          
          <Route path="/emergency" element={<Dashboard user={user} currentView="emergency" onViewChange={handleViewChange} onLogout={handleLogout} />} />
          <Route path="/settings" element={<Dashboard user={user} currentView="settings" onViewChange={handleViewChange} onLogout={handleLogout} />} />
          
          {/* Backward Compatibility Redirects */}
          <Route path="/medications" element={<Navigate to="/my-health?tab=medicines" replace />} />
          <Route path="/medicines" element={<Navigate to="/my-health?tab=medicines" replace />} />
          <Route path="/planner" element={<Navigate to="/my-health?tab=planner" replace />} />
          <Route path="/records" element={<Navigate to="/my-health?tab=records" replace />} />
          <Route path="/vitals" element={<Navigate to="/my-health?tab=vitals" replace />} />
          <Route path="/health" element={<Navigate to="/my-health?tab=overview" replace />} />
          <Route path="/conversations" element={<Navigate to="/orma?tab=history" replace />} />

          {/* Catch all redirect */}
          <Route path="*" element={<Navigate to={user.role === 'caregiver' ? "/caregiver" : "/dashboard"} replace />} />
        </Routes>
        <GlobalToast />
      </div>
      <ReminderModal user={user} />
    </ReminderProvider>
  );
}

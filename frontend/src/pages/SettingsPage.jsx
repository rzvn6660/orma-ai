import { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  Settings, User, ShieldCheck, Bell, Eye, Users, Globe, 
  Clock, Check, Volume2, Moon, Sparkles, AlertCircle, ChevronRight, Mic
} from 'lucide-react';
import CaregiverLinkManager from '../components/CaregiverLinkManager';
import ChangePasswordModal from '../components/ChangePasswordModal';
import PhoneEditorModal from '../components/PhoneEditorModal';
import ReminderLanguageModal from '../components/reminders/ReminderLanguageModal';
import VoiceLanguageModal from '../components/voice/VoiceLanguageModal';
import ErrorBoundary from '../components/ErrorBoundary';
import OrmaProfileCard from '../components/ui/OrmaProfileCard';
import OrmaOnboardingModal from '../components/ui/OrmaOnboardingModal';
import OrmaToggle from '../components/ui/OrmaToggle';
import OrmaSlider from '../components/ui/OrmaSlider';
import OrmaCardSwitch from '../components/ui/OrmaCardSwitch';
import { authApi, notificationApi } from '../services/api';
import { getLanguageConfig, DEFAULT_REMINDER_LANGUAGE } from '../config/reminderLanguages';
import { getVoiceLanguageConfig, DEFAULT_VOICE_LANGUAGE } from '../config/voiceLanguages';

export default function SettingsPage({ user }) {
  const [currentUser, setCurrentUser] = useState(user);
  const [activeSection, setActiveSection] = useState('profile');
  const [languageMode, setLanguageMode] = useState(localStorage.getItem('orma_language_pref') || 'auto');
  const [textSize, setTextSize] = useState(localStorage.getItem('orma_text_size') || 'normal');
  const [soundEnabled, setSoundEnabled] = useState(localStorage.getItem('orma_sound') !== 'disabled');
  const [navigationStyle, setNavigationStyle] = useState(localStorage.getItem('orma_navigation_style') || 'sidebar');
  const [savedSuccess, setSavedSuccess] = useState(false);
  const [isPasswordModalOpen, setIsPasswordModalOpen] = useState(false);
  const [isPhoneModalOpen, setIsPhoneModalOpen] = useState(false);
  const [isOnboardingModalOpen, setIsOnboardingModalOpen] = useState(false);
  const [isReminderLanguageModalOpen, setIsReminderLanguageModalOpen] = useState(false);
  const [isVoiceLanguageModalOpen, setIsVoiceLanguageModalOpen] = useState(false);

  const isCaregiver = (currentUser?.role === 'caregiver' || user?.role === 'caregiver');

  const [notifPrefs, setNotifPrefs] = useState({
    medication_reminder_notifications: !isCaregiver,
    medication_spoken_alerts: !isCaregiver,
    missed_medication_alerts: true,
    medication_adherence_summary: true,
    reminder_language: DEFAULT_REMINDER_LANGUAGE,
    voice_language: DEFAULT_VOICE_LANGUAGE,
    ...(currentUser?.notification_preferences || user?.notification_preferences || {})
  });
  const [pendingKeys, setPendingKeys] = useState({});

  useEffect(() => {
    if (currentUser?.notification_preferences) {
      setNotifPrefs(prev => ({ ...prev, ...currentUser.notification_preferences }));
    }
  }, [currentUser]);

  useEffect(() => {
    let isMounted = true;
    const fetchPrefs = async () => {
      try {
        const fresh = await notificationApi.getPreferences();
        if (isMounted && fresh) {
          setNotifPrefs(fresh);
        }
      } catch (err) {
        console.warn('Could not fetch notification preferences:', err);
      }
    };
    fetchPrefs();

    const handlePrefUpdate = () => fetchPrefs();
    window.addEventListener('orma_user_updated', handlePrefUpdate);
    return () => {
      isMounted = false;
      window.removeEventListener('orma_user_updated', handlePrefUpdate);
    };
  }, []);

  const showSavedToast = () => {
    setSavedSuccess(true);
    setTimeout(() => setSavedSuccess(false), 3000);
  };

  const handleUpdateNotifPref = async (key, value) => {
    setPendingKeys(prev => ({ ...prev, [key]: true }));
    try {
      const updated = await notificationApi.updatePreferences({ [key]: value });
      setNotifPrefs(updated);
      
      if (key === 'reminder_language') {
        localStorage.setItem('orma_reminder_language', value);
      }
      if (key === 'voice_language') {
        localStorage.setItem('orma_voice_language', value);
        localStorage.setItem('orma_language_pref', value);
        window.dispatchEvent(new Event('languageChange'));
      }

      window.dispatchEvent(new CustomEvent('orma_user_updated', { detail: { notification_preferences: updated } }));
      showSavedToast();
    } catch (err) {
      console.error(`Failed to update ${key}:`, err);
      window.dispatchEvent(new CustomEvent('orma:toast', {
        detail: { type: 'error', message: 'Couldn\'t update language preference.' }
      }));
    } finally {
      setPendingKeys(prev => ({ ...prev, [key]: false }));
    }
  };

  const handleTextSizeChange = (newSize) => {
    setTextSize(newSize);
    localStorage.setItem('orma_text_size', newSize);
    document.documentElement.classList.remove('text-size-normal', 'text-size-large', 'text-size-xlarge');
    document.documentElement.classList.add(`text-size-${newSize}`);
    showSavedToast();
  };

  const handleSoundToggle = (val) => {
    setSoundEnabled(val);
    localStorage.setItem('orma_sound', val ? 'enabled' : 'disabled');
    showSavedToast();
  };

  const navItems = [
    { id: 'profile', label: 'My Profile', icon: User },
    { id: 'notifications', label: 'Notifications & Spoken Voice', icon: Bell },
    { id: 'accessibility', label: 'Elderly Display & Sound', icon: Eye },
    { id: 'security', label: 'Account & Security', icon: ShieldCheck },
  ];

  if (isCaregiver) {
    navItems.splice(3, 0, { id: 'family_connections', label: 'Family Connections', icon: Users });
  }

  return (
    <ErrorBoundary>
      <div className="max-w-4xl mx-auto space-y-6 pb-12 animate-fade-in">
        
        {/* Toast Banner */}
        <AnimatePresence>
          {savedSuccess && (
            <motion.div
              initial={{ opacity: 0, y: -20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -20 }}
              className="fixed top-20 right-6 z-50 bg-emerald-600 text-white px-5 py-3 rounded-2xl shadow-xl font-bold flex items-center gap-2 border border-emerald-400/40"
            >
              <Check className="w-5 h-5 stroke-[3]" />
              <span>Settings saved successfully</span>
            </motion.div>
          )}
        </AnimatePresence>

        {/* Page Header */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-white/10 pb-5">
          <div className="flex items-center gap-3.5">
            <div className="w-12 h-12 rounded-2xl bg-blue-600/20 border border-blue-500/30 text-blue-400 flex items-center justify-center shrink-0 shadow-inner">
              <Settings className="w-6 h-6" />
            </div>
            <div>
              <h1 className="text-2xl sm:text-3xl font-extrabold text-white tracking-tight">
                Account Settings
              </h1>
              <p className="text-xs sm:text-sm text-slate-400 font-medium mt-0.5">
                Manage your preferences, display options, and family connections
              </p>
            </div>
          </div>
        </div>

        {/* Layout Grid */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
          
          {/* Section Navigation */}
          <div className="md:col-span-1 space-y-2">
            {navItems.map((item) => {
              const Icon = item.icon;
              const isActive = activeSection === item.id;

              return (
                <button
                  key={item.id}
                  type="button"
                  onClick={() => setActiveSection(item.id)}
                  className={`w-full p-3.5 rounded-2xl text-left font-bold text-sm transition-all flex items-center gap-3 cursor-pointer outline-none ${
                    isActive
                      ? 'bg-blue-600/20 text-blue-400 border border-blue-500/40 shadow-md'
                      : 'text-slate-400 hover:text-white hover:bg-slate-800/50 border border-transparent'
                  }`}
                >
                  <Icon className={`w-4 h-4 shrink-0 ${isActive ? 'text-blue-400' : 'text-slate-400'}`} />
                  <span className="truncate">{item.label}</span>
                </button>
              );
            })}
          </div>

          {/* Active Content Panel */}
          <div className="md:col-span-3 space-y-6">
            
            {/* 1. PROFILE SECTION */}
            {activeSection === 'profile' && (
              <div className="space-y-6">
                <OrmaProfileCard 
                  user={currentUser || user} 
                  onEditPhone={() => setIsPhoneModalOpen(true)}
                  onChangePassword={() => setIsPasswordModalOpen(true)}
                />
              </div>
            )}

            {/* 2. NOTIFICATIONS & SPOKEN VOICE SECTION */}
            {activeSection === 'notifications' && (
              <div className="space-y-6">
                <div className="orma-card p-6 sm:p-8 space-y-6 border border-white/10 shadow-2xl">
                  <div className="flex items-center gap-3 border-b border-white/10 pb-4">
                    <Bell className="w-5 h-5 text-blue-400" />
                    <div>
                      <h2 className="text-xl font-extrabold text-white">Notifications & Spoken Voice</h2>
                      <p className="text-xs text-slate-400">Configure how ORMA speaks and sends alerts</p>
                    </div>
                  </div>

                  <div className="space-y-4">
                    {/* Voice Language Row */}
                    <div 
                      onClick={() => setIsVoiceLanguageModalOpen(true)}
                      className="p-5 rounded-2xl bg-slate-800/40 border border-slate-700/40 hover:border-cyan-500/40 transition-all cursor-pointer flex items-center justify-between gap-4 group"
                      role="button"
                      tabIndex={0}
                      onKeyDown={(e) => { if (e.key === 'Enter' || e.key === ' ') setIsVoiceLanguageModalOpen(true); }}
                      aria-label="Voice Language"
                    >
                      <div className="flex items-center gap-3.5">
                        <div className="w-10 h-10 rounded-xl bg-cyan-500/10 border border-cyan-500/20 text-cyan-400 flex items-center justify-center shrink-0 group-hover:bg-cyan-500/20 transition-colors">
                          <Mic className="w-5 h-5" />
                        </div>
                        <div>
                          <h3 className="text-base font-bold text-white">Voice Language</h3>
                          <p className="text-xs text-slate-400 mt-0.5">
                            {(notifPrefs.voice_language || 'auto') === 'auto'
                              ? "ORMA automatically matches the language you speak."
                              : "ORMA listens and responds in your preferred language."}
                          </p>
                        </div>
                      </div>

                      <div className="flex items-center gap-2.5 shrink-0 bg-slate-900/80 px-3.5 py-2 rounded-xl border border-slate-700/60 group-hover:border-cyan-500/40 transition-colors">
                        <span className="text-lg leading-none">{getVoiceLanguageConfig(notifPrefs.voice_language || 'auto').flag}</span>
                        <span className="text-base font-black text-cyan-400">
                          {getVoiceLanguageConfig(notifPrefs.voice_language || 'auto').nativeName}
                        </span>
                        <ChevronRight className="w-4 h-4 text-slate-400 group-hover:text-white transition-colors" />
                      </div>
                    </div>

                    <OrmaCardSwitch
                      icon={Bell}
                      title="Medication Reminders"
                      description={
                        isCaregiver 
                          ? "Receive notifications when linked family members have medications due." 
                          : "Get clear visual reminders when it's time to take your medications."
                      }
                      checked={Boolean(notifPrefs.medication_reminder_notifications)}
                      isPending={Boolean(pendingKeys.medication_reminder_notifications)}
                      onChange={(val) => handleUpdateNotifPref('medication_reminder_notifications', val)}
                      ariaLabel="Medication Reminders"
                    />

                    <OrmaCardSwitch
                      icon={Volume2}
                      title="Medication Spoken Alerts"
                      description={
                        isCaregiver
                          ? "Play spoken medication reminders for linked family members."
                          : "Play spoken medication reminders when reminders are due."
                      }
                      checked={Boolean(notifPrefs.medication_spoken_alerts)}
                      isPending={Boolean(pendingKeys.medication_spoken_alerts)}
                      onChange={(val) => handleUpdateNotifPref('medication_spoken_alerts', val)}
                      ariaLabel="Medication Spoken Alerts"
                    />

                    {/* Reminder Language Row */}
                    <div 
                      onClick={() => setIsReminderLanguageModalOpen(true)}
                      className="p-5 rounded-2xl bg-slate-800/40 border border-slate-700/40 hover:border-blue-500/40 transition-all cursor-pointer flex items-center justify-between gap-4 group"
                      role="button"
                      tabIndex={0}
                      onKeyDown={(e) => { if (e.key === 'Enter' || e.key === ' ') setIsReminderLanguageModalOpen(true); }}
                      aria-label="Reminder Language"
                    >
                      <div className="flex items-center gap-3.5">
                        <div className="w-10 h-10 rounded-xl bg-cyan-500/10 border border-cyan-500/20 text-cyan-400 flex items-center justify-center shrink-0 group-hover:bg-cyan-500/20 transition-colors">
                          <Globe className="w-5 h-5" />
                        </div>
                        <div>
                          <h3 className="text-base font-bold text-white">Reminder Language</h3>
                          <p className="text-xs text-slate-400 mt-0.5">
                            Used for medication reminders and voice confirmations
                          </p>
                        </div>
                      </div>

                      <div className="flex items-center gap-2.5 shrink-0 bg-slate-900/80 px-3.5 py-2 rounded-xl border border-slate-700/60 group-hover:border-blue-500/40 transition-colors">
                        <span className="text-lg leading-none">{getLanguageConfig(notifPrefs.reminder_language || 'en-IN').flag}</span>
                        <span className="text-base font-black text-blue-400">
                          {getLanguageConfig(notifPrefs.reminder_language || 'en-IN').nativeName}
                        </span>
                        <ChevronRight className="w-4 h-4 text-slate-400 group-hover:text-white transition-colors" />
                      </div>
                    </div>

                    <OrmaCardSwitch
                      icon={AlertCircle}
                      title="Missed Medication Alerts"
                      description={
                        isCaregiver
                          ? "Get notified when a linked family member misses or does not confirm a medication."
                          : "Get notified when a medication is missed or not confirmed."
                      }
                      checked={Boolean(notifPrefs.missed_medication_alerts)}
                      isPending={Boolean(pendingKeys.missed_medication_alerts)}
                      onChange={(val) => handleUpdateNotifPref('missed_medication_alerts', val)}
                      ariaLabel="Missed Medication Alerts"
                    />

                    <OrmaCardSwitch
                      icon={Clock}
                      title="Daily Adherence Summary"
                      description="Receive a gentle daily summary of medications taken and health progress."
                      checked={Boolean(notifPrefs.medication_adherence_summary)}
                      isPending={Boolean(pendingKeys.medication_adherence_summary)}
                      onChange={(val) => handleUpdateNotifPref('medication_adherence_summary', val)}
                      ariaLabel="Daily Adherence Summary"
                    />
                  </div>
                </div>
              </div>
            )}

            {/* 3. ACCESSIBILITY SECTION */}
            {activeSection === 'accessibility' && (
              <div className="space-y-6">
                <div className="orma-card p-6 sm:p-8 space-y-6 border border-white/10 shadow-2xl">
                  <div className="flex items-center gap-3 border-b border-white/10 pb-4">
                    <Eye className="w-5 h-5 text-blue-400" />
                    <div>
                      <h2 className="text-xl font-extrabold text-white">Elderly Display & Sound Options</h2>
                      <p className="text-xs text-slate-400">Adjust text size, sound, and navigation</p>
                    </div>
                  </div>

                  <div className="space-y-6">
                    <div className="p-4 rounded-2xl bg-slate-800/40 border border-slate-700/40 space-y-3">
                      <div className="flex items-center justify-between">
                        <div>
                          <h3 className="text-base font-bold text-white">Text Size</h3>
                          <p className="text-xs text-slate-400">Adjust readability for comfort</p>
                        </div>
                        <span className="text-xs font-bold text-blue-400 uppercase bg-blue-500/10 px-3 py-1 rounded-full border border-blue-500/20">
                          {textSize}
                        </span>
                      </div>
                      <div className="grid grid-cols-3 gap-3">
                        {['normal', 'large', 'xlarge'].map((size) => (
                          <button
                            key={size}
                            type="button"
                            onClick={() => handleTextSizeChange(size)}
                            className={`p-3 rounded-xl border text-xs font-extrabold transition-all cursor-pointer ${
                              textSize === size
                                ? 'bg-blue-600 text-white border-blue-400 shadow-md'
                                : 'bg-slate-900 text-slate-300 hover:text-white border-slate-800'
                            }`}
                          >
                            {size === 'normal' ? 'Standard' : size === 'large' ? 'Large' : 'Extra Large'}
                          </button>
                        ))}
                      </div>
                    </div>

                    <OrmaCardSwitch
                      icon={Volume2}
                      title="Audio Effects & Sound Signals"
                      description="Play reassuring sound signals when actions complete."
                      checked={soundEnabled}
                      onChange={handleSoundToggle}
                      ariaLabel="Audio Effects & Sound Signals"
                    />

                    <div className="p-4 rounded-2xl bg-slate-800/40 border border-slate-700/40 space-y-3">
                      <h3 className="text-base font-bold text-white">App Guided Onboarding</h3>
                      <p className="text-xs text-slate-400">Re-watch the step-by-step introduction to ORMA AI</p>
                      <button
                        type="button"
                        onClick={() => setIsOnboardingModalOpen(true)}
                        className="px-4 py-2.5 rounded-xl bg-blue-600/20 hover:bg-blue-600/30 text-blue-400 border border-blue-500/30 text-xs font-extrabold transition-colors cursor-pointer flex items-center gap-2"
                      >
                        <Sparkles className="w-4 h-4" />
                        <span>Start Tour</span>
                      </button>
                    </div>
                  </div>
                </div>
              </div>
            )}

            {/* 4. FAMILY CONNECTIONS SECTION */}
            {activeSection === 'family_connections' && isCaregiver && (
              <div className="space-y-6">
                <CaregiverLinkManager user={currentUser || user} />
              </div>
            )}

            {/* 5. ACCOUNT & SECURITY SECTION */}
            {activeSection === 'security' && (
              <div className="space-y-6">
                <div className="orma-card p-6 sm:p-8 space-y-6 border border-white/10 shadow-2xl">
                  <div className="flex items-center gap-3 border-b border-white/10 pb-4">
                    <ShieldCheck className="w-5 h-5 text-blue-400" />
                    <div>
                      <h2 className="text-xl font-extrabold text-white">Account Security</h2>
                      <p className="text-xs text-slate-400">Manage credentials and authentication</p>
                    </div>
                  </div>

                  <div className="space-y-4">
                    <div className="p-5 rounded-2xl bg-slate-800/40 border border-slate-700/40 flex items-center justify-between gap-4">
                      <div>
                        <h3 className="text-base font-bold text-white">Password</h3>
                        <p className="text-xs text-slate-400">Update your login password securely</p>
                      </div>
                      <button
                        type="button"
                        onClick={() => setIsPasswordModalOpen(true)}
                        className="px-4 py-2.5 rounded-xl bg-slate-900 hover:bg-slate-800 text-xs font-extrabold text-white border border-slate-700 transition-colors cursor-pointer shrink-0"
                      >
                        Change Password
                      </button>
                    </div>

                    <div className="p-5 rounded-2xl bg-slate-800/40 border border-slate-700/40 flex items-center justify-between gap-4">
                      <div>
                        <h3 className="text-base font-bold text-white">Emergency Phone Number</h3>
                        <p className="text-xs text-slate-400">{currentUser?.phone || 'No phone set'}</p>
                      </div>
                      <button
                        type="button"
                        onClick={() => setIsPhoneModalOpen(true)}
                        className="px-4 py-2.5 rounded-xl bg-slate-900 hover:bg-slate-800 text-xs font-extrabold text-white border border-slate-700 transition-colors cursor-pointer shrink-0"
                      >
                        Edit Phone
                      </button>
                    </div>
                  </div>
                </div>
              </div>
            )}

          </div>
        </div>

        {/* Change Password Modal */}
        <ChangePasswordModal 
          isOpen={isPasswordModalOpen} 
          onClose={() => setIsPasswordModalOpen(false)} 
        />

        {/* Emergency Phone Editor Modal */}
        <PhoneEditorModal
          isOpen={isPhoneModalOpen}
          onClose={() => setIsPhoneModalOpen(false)}
          initialPhone={currentUser?.phone || ''}
          onPhoneSaved={(newPhone, updatedUser) => {
            const finalPhone = updatedUser?.phone !== undefined ? updatedUser.phone : newPhone;
            setCurrentUser(prev => ({
              ...(prev || {}),
              ...(updatedUser || {}),
              phone: finalPhone
            }));
            showSavedToast();
          }}
        />

        {/* First-Time Onboarding Tour Modal */}
        <OrmaOnboardingModal
          isOpen={isOnboardingModalOpen}
          onClose={() => setIsOnboardingModalOpen(false)}
          user={user}
          onUpdatePreferences={({ language }) => {
            if (language) {
              setLanguageMode(language);
              localStorage.setItem('orma_language_pref', language);
              window.dispatchEvent(new Event('languageChange'));
            }
          }}
        />

        {/* Medication Reminder Language Selector Modal */}
        <ReminderLanguageModal 
          isOpen={isReminderLanguageModalOpen}
          onClose={() => setIsReminderLanguageModalOpen(false)}
          currentLanguage={notifPrefs.reminder_language || DEFAULT_REMINDER_LANGUAGE}
          isPending={Boolean(pendingKeys.reminder_language)}
          onSelectLanguage={(newLang) => {
            handleUpdateNotifPref('reminder_language', newLang);
            setIsReminderLanguageModalOpen(false);
          }}
        />

        {/* Main Voice AI Language Selector Modal */}
        <VoiceLanguageModal
          isOpen={isVoiceLanguageModalOpen}
          onClose={() => setIsVoiceLanguageModalOpen(false)}
          currentLanguage={notifPrefs.voice_language || DEFAULT_VOICE_LANGUAGE}
          isPending={Boolean(pendingKeys.voice_language)}
          onSelectLanguage={(newLang) => {
            handleUpdateNotifPref('voice_language', newLang);
            setIsVoiceLanguageModalOpen(false);
          }}
        />
      </div>
    </ErrorBoundary>
  );
}

import { useState, useEffect, useCallback, useRef } from 'react';
import DashboardLayout from '../layouts/DashboardLayout';
import MyHealthPage from './MyHealthPage';
import OrmaPage from './OrmaPage';
import FamilyPage from './FamilyPage';
import SettingsPage from './SettingsPage';
import EmergencyPage from './EmergencyPage';
import CaregiverDashboard from './CaregiverDashboard';
import CalendarPage from './CalendarPage';
import FloatingTalkControl from '../components/voice/FloatingTalkControl';
import { healthApi, speechApi, chatApi, emergencyApi, medicineApi, healthPlannerApi } from '../services/api';
import { useApi } from '../hooks/useApi';
import { tts } from '../services/tts';
import { motion, AnimatePresence } from 'framer-motion';
import EmergencyAlert from '../components/EmergencyAlert';
import HealthSnapshot from '../components/HealthSnapshot';
import ErrorBoundary from '../components/ErrorBoundary';
import MedicationTimeline from '../components/timeline/MedicationTimeline';
import ElderlyWeeklyProgress from '../components/analytics/ElderlyWeeklyProgress';
import ElderLiveTimeCard from '../components/ui/ElderLiveTimeCard';
import { 
  Heart, Pill, Calendar, AlertOctagon, Brain, Mic, Clock, CheckCircle2, 
  ArrowRight, ShieldCheck, Activity, User, Sparkles, Check, ChevronRight, AlertTriangle, RefreshCw
} from 'lucide-react';

const getTimeContext = (userTimezone) => {
  let hour = new Date().getHours();
  if (userTimezone) {
    try {
      const nowStr = new Intl.DateTimeFormat('en-US', {
        timeZone: userTimezone,
        hour: 'numeric',
        hour12: false
      }).format(new Date());
      hour = parseInt(nowStr, 10);
    } catch {
      hour = new Date().getHours();
    }
  }

  if (hour >= 5 && hour < 12) return {
    timeOfDay: 'Morning',
    greeting: 'Good Morning',
    icon: '☀️',
    promptSuggestion: 'You can ask me about morning medicines, appointments, or your day.',
    suggestions: [
      'Did I take my morning medicine?',
      'What medicines are due today?',
      'When is my next doctor appointment?',
      'How is my adherence this week?'
    ]
  };
  if (hour >= 12 && hour < 17) return {
    timeOfDay: 'Afternoon',
    greeting: 'Good Afternoon',
    icon: '🌤️',
    promptSuggestion: 'You can ask me about your afternoon schedule, reminders, or health vitals.',
    suggestions: [
      'Did I take my afternoon dose?',
      "What's on my schedule today?",
      'When is my next medicine?',
      'How is my adherence this week?'
    ]
  };
  if (hour >= 17 && hour < 21) return {
    timeOfDay: 'Evening',
    greeting: 'Good Evening',
    icon: '🌆',
    promptSuggestion: 'You can ask me about evening medicines, tomorrow’s schedule, or your day.',
    suggestions: [
      'Did I take my evening medicine?',
      'What medicines are due tonight?',
      'When is my doctor visit tomorrow?',
      'Summarize my day'
    ]
  };
  return {
    timeOfDay: 'Night',
    greeting: 'Good Night',
    icon: '🌙',
    promptSuggestion: 'You can ask me about your medicines or tomorrow’s schedule before you rest.',
    suggestions: [
      'Are all my night medicines taken?',
      'What time are my morning medicines?',
      'When is my next appointment?',
      'How did I do today?'
    ]
  };
};

export default function Dashboard({ currentView, onViewChange, user, onLogout }) {
  const [messages, setMessages] = useState([]);
  const [isSpeaking, setIsSpeaking] = useState(false);
  const [isEmergencyActive, setIsEmergencyActive] = useState(false);
  const [emergencySeverity, setEmergencySeverity] = useState('low');
  
  // Phase B: Continuous Conversation Mode State
  const [conversationMode, setConversationMode] = useState(false);
  const [turnState, setTurnState] = useState('idle'); // 'idle' | 'listening' | 'thinking' | 'speaking' | 'your_turn' | 'ended'
  const [isListeningState, setIsListeningState] = useState(false);
  const [listenTrigger, setListenTrigger] = useState(0);

  const conversationSessionIdRef = useRef(0);
  const conversationModeRef = useRef(false);
  const isTurnInProgressRef = useRef(false);
  const turnTimeoutRef = useRef(null);

  useEffect(() => {
    conversationModeRef.current = conversationMode;
  }, [conversationMode]);

  // Handle unmount or route leave
  useEffect(() => {
    return () => {
      conversationSessionIdRef.current += 1;
      conversationModeRef.current = false;
      tts.stop();
      if (turnTimeoutRef.current) {
        clearTimeout(turnTimeoutRef.current);
        turnTimeoutRef.current = null;
      }
    };
  }, []);

  const handleStartConversation = useCallback(() => {
    if (currentView !== 'orma') {
      onViewChange('orma');
    }
    conversationSessionIdRef.current += 1;
    if (turnTimeoutRef.current) {
      clearTimeout(turnTimeoutRef.current);
      turnTimeoutRef.current = null;
    }
    tts.stop();
    setIsSpeaking(false);
    isTurnInProgressRef.current = false;

    setConversationMode(true);
    conversationModeRef.current = true;
    setTurnState('listening');
    setListenTrigger(prev => prev + 1);
  }, [currentView, onViewChange]);

  const handleEndConversation = useCallback(() => {
    conversationSessionIdRef.current += 1;
    setConversationMode(false);
    conversationModeRef.current = false;
    setTurnState('ended');
    setIsListeningState(false);
    isTurnInProgressRef.current = false;

    if (turnTimeoutRef.current) {
      clearTimeout(turnTimeoutRef.current);
      turnTimeoutRef.current = null;
    }

    tts.stop();
    setIsSpeaking(false);

    setTimeout(() => {
      setTurnState('idle');
    }, 400);
  }, []);

  const handleInterrupt = useCallback(() => {
    conversationSessionIdRef.current += 1;
    if (turnTimeoutRef.current) {
      clearTimeout(turnTimeoutRef.current);
      turnTimeoutRef.current = null;
    }
    tts.stop();
    setIsSpeaking(false);

    if (conversationModeRef.current) {
      setTurnState('listening');
      setListenTrigger(prev => prev + 1);
    } else {
      setTurnState('idle');
    }
  }, []);

  const [languageMode, setLanguageMode] = useState(
    user?.notification_preferences?.voice_language || 
    localStorage.getItem('orma_voice_language') || 
    localStorage.getItem('orma_language_pref') || 
    'auto'
  );
  const [conversationLang, setConversationLang] = useState(() => {
    const pref = user?.notification_preferences?.voice_language || 
                 localStorage.getItem('orma_voice_language') || 
                 localStorage.getItem('orma_language_pref') || 
                 'auto';
    return pref.toLowerCase().startsWith('ml') ? 'ml' : 'en';
  });
  const [timeContext, setTimeContext] = useState(getTimeContext(user?.timezone));
  const [todayEvents, setTodayEvents] = useState([]);
  const [medicines, setMedicines] = useState([]);
  
  useEffect(() => {
    const handleLangChange = () => {
      setLanguageMode(
        user?.notification_preferences?.voice_language || 
        localStorage.getItem('orma_voice_language') || 
        localStorage.getItem('orma_language_pref') || 
        'auto'
      );
    };
    window.addEventListener('languageChange', handleLangChange);
    window.addEventListener('orma_user_updated', handleLangChange);
    return () => {
      window.removeEventListener('languageChange', handleLangChange);
      window.removeEventListener('orma_user_updated', handleLangChange);
    };
  }, [user]);
  
  useEffect(() => {
    setTimeContext(getTimeContext(user?.timezone));
    const interval = setInterval(() => {
      setTimeContext(getTimeContext(user?.timezone));
    }, 60000);
    return () => clearInterval(interval);
  }, [user?.timezone]);

  // Fetch today's medicines
  const fetchMedicines = useCallback(async () => {
    try {
      const data = await medicineApi.getReminders();
      setMedicines(Array.isArray(data) ? data : []);
    } catch (err) {
      console.error("Failed to fetch medicines in Dashboard", err);
    }
  }, []);

  // Fetch today's planner appointments
  const fetchEvents = useCallback(async () => {
    try {
      const events = await healthPlannerApi.getEvents();
      const todayStr = new Date().toISOString().split('T')[0];
      setTodayEvents(Array.isArray(events) ? events.filter(e => (!e.event_date || e.event_date === todayStr) && !e.status) : []);
    } catch (err) {
      console.error("Failed to fetch events in Dashboard", err);
    }
  }, []);

  useEffect(() => {
    fetchMedicines();
    fetchEvents();

    const handleUpdate = () => {
      fetchMedicines();
      fetchEvents();
    };

    window.addEventListener('medicationUpdated', handleUpdate);
    window.addEventListener('orma_websocket_message', handleUpdate);
    const interval = setInterval(handleUpdate, 60000);

    return () => {
      window.removeEventListener('medicationUpdated', handleUpdate);
      window.removeEventListener('orma_websocket_message', handleUpdate);
      clearInterval(interval);
    };
  }, [fetchMedicines, fetchEvents]);

  const handleTakeMedicine = async (id, e) => {
    e?.stopPropagation();
    try {
      await medicineApi.takeMedicine(id);
      fetchMedicines();
      window.dispatchEvent(new Event('medicationUpdated'));
    } catch (err) {
      console.error("Failed to mark medicine as taken", err);
    }
  };

  const { data: healthData, error: healthError, execute: checkHealth } = useApi(healthApi.check);
  const { execute: transcribe, loading: isTranscribing } = useApi(speechApi.transcribe);
  const { execute: sendMessage, loading: isThinking } = useApi(chatApi.sendMessage);
  const { execute: analyzeEmergency } = useApi(emergencyApi.analyze);

  const detectScriptLanguage = (text, fallbackIso = 'en') => {
    if (!text || typeof text !== 'string') return 'en-IN';
    
    // Measure character frequency per native script to determine dominant language
    const counts = {
      'ml-IN': (text.match(/[\u0D00-\u0D7F]/g) || []).length,
      'hi-IN': (text.match(/[\u0900-\u097F]/g) || []).length,
      'ar-SA': (text.match(/[\u0600-\u06FF]/g) || []).length,
      'ta-IN': (text.match(/[\u0B80-\u0BFF]/g) || []).length,
      'te-IN': (text.match(/[\u0C00-\u0C7F]/g) || []).length,
      'kn-IN': (text.match(/[\u0C80-\u0CFF]/g) || []).length,
    };

    let dominantLang = null;
    let maxCount = 0;

    for (const [lang, count] of Object.entries(counts)) {
      if (count > maxCount) {
        maxCount = count;
        dominantLang = lang;
      }
    }

    // Require at least 2 native script characters to trigger non-English auto-detection
    if (dominantLang && maxCount >= 2) {
      return dominantLang;
    }

    // Check Whisper ISO metadata fallback
    if (fallbackIso && typeof fallbackIso === 'string') {
      const clean = fallbackIso.toLowerCase().trim();
      if (clean.startsWith('ml')) return 'ml-IN';
      if (clean.startsWith('hi')) return 'hi-IN';
      if (clean.startsWith('ar')) return 'ar-SA';
      if (clean.startsWith('ta')) return 'ta-IN';
      if (clean.startsWith('te')) return 'te-IN';
      if (clean.startsWith('kn')) return 'kn-IN';
    }

    return 'en-IN';
  };

  const handleStopRecording = async (blobUrl, blob) => {
    if (!blob) return;
    if (isTurnInProgressRef.current) return;
    isTurnInProgressRef.current = true;
    const currentSession = conversationSessionIdRef.current;
    setTurnState('thinking');
    try {
      const explicitLang = languageMode !== 'auto' ? languageMode : null;
      const convLang = conversationLang || null;
      const data = await transcribe(blob, explicitLang, convLang);

      if (conversationModeRef.current && conversationSessionIdRef.current !== currentSession) {
        return;
      }

      // Check if ASR quality validation triggered a safety clarification (Sections 8, 10 & 15)
      if (data?.needs_clarification && data?.clarification_prompt) {
        const clarLang = (data.normalized_language || conversationLang || 'en').toLowerCase();
        const clarVoice = clarLang.startsWith('ml') ? 'ml-IN' : (clarLang.startsWith('ta') ? 'ta-IN' : (clarLang.startsWith('hi') ? 'hi-IN' : 'en-IN'));
        const clarMsg = {
          id: Date.now() + 1,
          sender: 'ai',
          text: data.clarification_prompt,
          langCode: clarVoice,
          time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
        };
        setMessages(prev => [...prev, clarMsg]);
        try {
          tts.speak(clarMsg.text, {
            langCode: clarVoice,
            onStart: () => setIsSpeaking(true),
            onEnd: () => {
              setIsSpeaking(false);
              if (conversationModeRef.current && conversationSessionIdRef.current === currentSession) {
                setTurnState('listening');
                setListenTrigger(prev => prev + 1);
              } else {
                setTurnState('idle');
              }
            },
            onError: () => {
              setIsSpeaking(false);
              setTurnState('idle');
            }
          });
        } catch (e) {
          console.warn("Clarification speech error:", e);
        }
        return;
      }

      const userText = data?.transcription;
      const rawDetectedLang = (data?.detected_language || 'en').toLowerCase().trim();
      
      if (!userText || userText.trim() === '') {
        if (conversationModeRef.current && conversationSessionIdRef.current === currentSession) {
          setTurnState('your_turn');
          turnTimeoutRef.current = setTimeout(() => {
            if (conversationModeRef.current && conversationSessionIdRef.current === currentSession) {
              setTurnState('listening');
              setListenTrigger(prev => prev + 1);
            }
          }, 450);
        } else {
          setTurnState('idle');
        }
        return;
      }

      const isMalayalamInput = rawDetectedLang.startsWith('ml') || 
        /[\u0D00-\u0D7F]/.test(userText) ||
        /\b(marunnu|adutha|enthaanu|enthaan|kazhicho|kazhinjo|eathaanu|ente|enre|aano|undo|kazhichu|eduthu|njan|athu)\b/i.test(userText);
      const isTamilInput = !isMalayalamInput && (rawDetectedLang.startsWith('ta') || /[\u0B80-\u0BFF]/.test(userText));
      const isHindiInput = !isMalayalamInput && !isTamilInput && (rawDetectedLang.startsWith('hi') || /[\u0900-\u097F]/.test(userText));

      let activeLang = 'en';
      if (data?.effective_language && ['en', 'ml', 'ta', 'hi', 'ar'].includes(data.effective_language.toLowerCase())) {
        activeLang = data.effective_language.toLowerCase();
      } else if (isMalayalamInput) {
        activeLang = 'ml';
      } else if (isTamilInput) {
        activeLang = 'ta';
      } else if (isHindiInput) {
        activeLang = 'hi';
      }

      setConversationLang(activeLang);

      const effectiveVoiceLang = languageMode !== 'auto' 
        ? languageMode 
        : (isMalayalamInput ? 'ml-IN' : isTamilInput ? 'ta-IN' : isHindiInput ? 'hi-IN' : detectScriptLanguage(userText, rawDetectedLang));
      
      const newMsg = {
        id: Date.now(),
        sender: 'user',
        text: userText,
        time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
      };
      setMessages(prev => [...prev, newMsg]);

      // Non-blocking emergency check
      try {
        const emergencyData = await analyzeEmergency(userText);
        if (emergencyData && emergencyData.is_emergency) {
          setIsEmergencyActive(true);
          setEmergencySeverity(emergencyData.severity);
          
          const alertMsg = {
            id: Date.now() + 1,
            sender: 'ai',
            text: emergencyData.message,
            time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
          };
          setMessages(prev => [...prev, alertMsg]);
          
          try {
            tts.speak(alertMsg.text, {
              langCode: 'en-IN',
              onStart: () => setIsSpeaking(true),
              onEnd: () => {
                setIsSpeaking(false);
                if (conversationModeRef.current && conversationSessionIdRef.current === currentSession) {
                  setTurnState('listening');
                  setListenTrigger(prev => prev + 1);
                } else {
                  setTurnState('idle');
                }
              },
              onError: () => {
                setIsSpeaking(false);
                if (conversationModeRef.current && conversationSessionIdRef.current === currentSession) {
                  setTurnState('listening');
                  setListenTrigger(prev => prev + 1);
                } else {
                  setTurnState('idle');
                }
              }
            });
          } catch (ttsErr) {
            console.warn("[TTS WARN] Emergency speech alert failed:", ttsErr);
          }
          return;
        }
      } catch (emErr) {
        console.warn("[EMERGENCY CHECK NON-BLOCKING WARN]:", emErr);
      }

      const userIdToPass = user?.id || user?.email || 'default_user';
      const chatData = await sendMessage(userText, userIdToPass, languageMode, effectiveVoiceLang, messages);

      if (conversationModeRef.current && conversationSessionIdRef.current !== currentSession) {
        return;
      }

      const responseText = chatData?.response || "I'm here to help you.";
      const respLang = (chatData?.language || '').toLowerCase();
      let responseVoiceLang = 'en-IN';

      if (respLang === 'ml' || /[\u0D00-\u0D7F]/.test(responseText)) {
        responseVoiceLang = 'ml-IN';
        setConversationLang('ml');
      } else if (respLang === 'ta' || /[\u0B80-\u0BFF]/.test(responseText)) {
        responseVoiceLang = 'ta-IN';
        setConversationLang('ta');
      } else if (respLang === 'hi' || /[\u0900-\u097F]/.test(responseText)) {
        responseVoiceLang = 'hi-IN';
        setConversationLang('hi');
      } else if (respLang === 'en' || /^[A-Za-z0-9\s.,!?'"()-]+$/.test(responseText)) {
        responseVoiceLang = 'en-IN';
        setConversationLang('en');
      } else {
        responseVoiceLang = effectiveVoiceLang || 'en-IN';
      }

      // Safe development diagnostic log (no secrets or sensitive data logged)
      console.log(`[VOICE TURN DIAGNOSTIC] ASR detected: ${rawDetectedLang} | normalized: ${activeLang} | effective voice: ${effectiveVoiceLang} | chat response lang: ${chatData?.language} | TTS lang: ${responseVoiceLang} | retry: ${Boolean(data?.retry_applied)}`);
      
      const aiMsg = {
        id: Date.now() + 1,
        sender: 'ai',
        text: responseText,
        langCode: responseVoiceLang,
        time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
      };
      
      // 1. Always display text response first
      setMessages(prev => [...prev, aiMsg]);

      // 2. Decoupled TTS: Automatic turn handoff when speech ends
      try {
        tts.speak(responseText, {
          langCode: responseVoiceLang,
          onStart: () => {
            if (!conversationModeRef.current || conversationSessionIdRef.current === currentSession) {
              setIsSpeaking(true);
              setTurnState('speaking');
            }
          },
          onEnd: () => {
            setIsSpeaking(false);
            if (conversationModeRef.current && conversationSessionIdRef.current === currentSession) {
              setTurnState('your_turn');
              turnTimeoutRef.current = setTimeout(() => {
                if (conversationModeRef.current && conversationSessionIdRef.current === currentSession) {
                  setTurnState('listening');
                  setListenTrigger(prev => prev + 1);
                }
              }, 450);
            } else {
              setTurnState('idle');
            }
          },
          onError: (err) => {
            if (err?.error === 'interrupted' || err?.error === 'canceled') {
              return;
            }
            setIsSpeaking(false);
            if (conversationModeRef.current && conversationSessionIdRef.current === currentSession) {
              setTurnState('listening');
              setListenTrigger(prev => prev + 1);
            } else {
              setTurnState('idle');
            }
          }
        });
      } catch (ttsErr) {
        console.warn("[TTS WARN] Text-to-speech failed or blocked by autoplay:", ttsErr);
        setIsSpeaking(false);
        if (conversationModeRef.current && conversationSessionIdRef.current === currentSession) {
          setTurnState('listening');
          setListenTrigger(prev => prev + 1);
        }
      }

    } catch (error) {
      console.error("[VOICE PIPELINE ERROR]:", error?.response?.data || error?.message || error);
      const errorMsg = {
        id: Date.now(),
        sender: 'ai',
        text: "I'm having trouble responding right now. Please try again.",
        time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
      };
      setMessages(prev => [...prev, errorMsg]);
      if (conversationModeRef.current && conversationSessionIdRef.current === currentSession) {
        setTurnState('listening');
        setListenTrigger(prev => prev + 1);
      } else {
        setTurnState('idle');
      }
    } finally {
      isTurnInProgressRef.current = false;
    }
  };

  const handleAskAgain = async (text) => {
    if (!text) return;
    if (isTurnInProgressRef.current) return;
    isTurnInProgressRef.current = true;
    const currentSession = conversationSessionIdRef.current;

    setTurnState('thinking');
    try {
      const isMalayalamInput = /[\u0D00-\u0D7F]/.test(text);
      if (isMalayalamInput) {
        setConversationLang('ml');
      } else if (/^[A-Za-z0-9\s.,?!'"-]+$/.test(text)) {
        setConversationLang('en');
      }

      const effectiveVoiceLang = languageMode !== 'auto' 
        ? languageMode 
        : (isMalayalamInput ? 'ml-IN' : detectScriptLanguage(text));
      
      const newMsg = {
        id: Date.now(),
        sender: 'user',
        text: text,
        time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
      };
      setMessages(prev => [...prev, newMsg]);

      const userIdToPass = user?.id || user?.email || 'default_user';
      const chatData = await sendMessage(text, userIdToPass, languageMode, effectiveVoiceLang, messages);

      if (conversationModeRef.current && conversationSessionIdRef.current !== currentSession) {
        return;
      }

      const responseText = chatData?.response || "I'm here to help you.";
      const respLang = (chatData?.language || '').toLowerCase();
      let responseVoiceLang = 'en-IN';

      if (respLang === 'ml' || /[\u0D00-\u0D7F]/.test(responseText)) {
        responseVoiceLang = 'ml-IN';
        setConversationLang('ml');
      } else if (respLang === 'ta' || /[\u0B80-\u0BFF]/.test(responseText)) {
        responseVoiceLang = 'ta-IN';
        setConversationLang('ta');
      } else if (respLang === 'hi' || /[\u0900-\u097F]/.test(responseText)) {
        responseVoiceLang = 'hi-IN';
        setConversationLang('hi');
      } else if (respLang === 'en' || /^[A-Za-z0-9\s.,!?'"()-]+$/.test(responseText)) {
        responseVoiceLang = 'en-IN';
        setConversationLang('en');
      } else {
        responseVoiceLang = effectiveVoiceLang || 'en-IN';
      }

      const aiMsg = {
        id: Date.now() + 1,
        sender: 'ai',
        text: responseText,
        langCode: responseVoiceLang,
        time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
      };
      // Display text response first
      setMessages(prev => [...prev, aiMsg]);

      // Decoupled TTS & Turn Loop
      try {
        tts.speak(responseText, {
          langCode: responseVoiceLang,
          onStart: () => {
            if (!conversationModeRef.current || conversationSessionIdRef.current === currentSession) {
              setIsSpeaking(true);
              setTurnState('speaking');
            }
          },
          onEnd: () => {
            setIsSpeaking(false);
            if (conversationModeRef.current && conversationSessionIdRef.current === currentSession) {
              setTurnState('your_turn');
              turnTimeoutRef.current = setTimeout(() => {
                if (conversationModeRef.current && conversationSessionIdRef.current === currentSession) {
                  setTurnState('listening');
                  setListenTrigger(prev => prev + 1);
                }
              }, 450);
            } else {
              setTurnState('idle');
            }
          },
          onError: (err) => {
            if (err?.error === 'interrupted' || err?.error === 'canceled') {
              return;
            }
            setIsSpeaking(false);
            if (conversationModeRef.current && conversationSessionIdRef.current === currentSession) {
              setTurnState('listening');
              setListenTrigger(prev => prev + 1);
            } else {
              setTurnState('idle');
            }
          }
        });
      } catch (ttsErr) {
        console.warn("[TTS WARN] Text-to-speech failed:", ttsErr);
        setIsSpeaking(false);
        if (conversationModeRef.current && conversationSessionIdRef.current === currentSession) {
          setTurnState('listening');
          setListenTrigger(prev => prev + 1);
        }
      }
    } catch (error) {
      console.error("[ASK AGAIN PIPELINE ERROR]:", error?.response?.data || error?.message || error);
      const errorMsg = {
        id: Date.now(),
        sender: 'ai',
        text: "I'm having trouble responding right now. Please try again.",
        time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
      };
      setMessages(prev => [...prev, errorMsg]);
      if (conversationModeRef.current && conversationSessionIdRef.current === currentSession) {
        setTurnState('listening');
        setListenTrigger(prev => prev + 1);
      } else {
        setTurnState('idle');
      }
    } finally {
      isTurnInProgressRef.current = false;
    }
  };

  useEffect(() => {
    checkHealth();
  }, [checkHealth]);

  // Route mapping
  if (currentView === 'calendar') {
    return (
      <DashboardLayout currentView="calendar" onViewChange={onViewChange} user={user} onLogout={onLogout}>
        <CalendarPage user={user} onViewChange={onViewChange} />
      </DashboardLayout>
    );
  }

  if (currentView === 'my-health' || ['medicines', 'planner', 'records', 'vitals'].includes(currentView)) {
    return (
      <DashboardLayout currentView="my-health" onViewChange={onViewChange} user={user} onLogout={onLogout}>
        <MyHealthPage user={user} onViewChange={onViewChange} />
      </DashboardLayout>
    );
  }

  if (currentView === 'orma' || currentView === 'conversations') {
    return (
      <DashboardLayout currentView="orma" onViewChange={onViewChange} user={user} onLogout={onLogout}>
        <OrmaPage
          user={user}
          onBack={() => {
            handleEndConversation();
            onViewChange('dashboard');
          }}
          onViewChange={onViewChange}
          messages={messages}
          isListening={isListeningState}
          isSpeaking={isSpeaking}
          onStopSpeaking={() => setIsSpeaking(false)}
          isTranscribing={isTranscribing}
          isThinking={isThinking}
          handleStopRecording={handleStopRecording}
          onClearConversation={() => {
            setMessages([]);
            setConversationLang(languageMode !== 'auto' ? (languageMode.startsWith('ml') ? 'ml' : 'en') : 'en');
            chatApi.resetSession();
          }}
          handleAskAgain={handleAskAgain}
          timeContext={timeContext}
          isConversationMode={conversationMode}
          turnState={turnState}
          onStartConversation={handleStartConversation}
          onEndConversation={handleEndConversation}
          onInterrupt={handleInterrupt}
          listenTrigger={listenTrigger}
          onStatusChange={(listening) => setIsListeningState(listening)}
        />
      </DashboardLayout>
    );
  }

  if (currentView === 'family') {
    return (
      <DashboardLayout currentView="family" onViewChange={onViewChange} user={user} onLogout={onLogout}>
        <FamilyPage user={user} />
      </DashboardLayout>
    );
  }

  if (currentView === 'settings') {
    return (
      <DashboardLayout currentView="settings" onViewChange={onViewChange} user={user} onLogout={onLogout}>
        <SettingsPage user={user} />
      </DashboardLayout>
    );
  }

  if (currentView === 'emergency') {
    return (
      <DashboardLayout currentView="emergency" onViewChange={onViewChange} user={user} onLogout={onLogout}>
        <EmergencyPage user={user} />
      </DashboardLayout>
    );
  }

  if (currentView === 'caregiver') {
    return (
      <DashboardLayout currentView="caregiver" onViewChange={onViewChange} user={user} onLogout={onLogout}>
        <CaregiverDashboard currentView={currentView} onViewChange={onViewChange} user={user} onLogout={onLogout} />
      </DashboardLayout>
    );
  }

  // Derive stats & next reminder from actual data
  const pendingMedicines = medicines.filter(m => !m.taken_status);
  const nextMedicine = pendingMedicines.length > 0 ? pendingMedicines[0] : null;
  const takenCount = medicines.filter(m => m.taken_status).length;
  const totalCount = medicines.length;
  const hasMedicines = totalCount > 0;
  const adherencePercentage = hasMedicines ? Math.round((takenCount / totalCount) * 100) : null;

  // Personalized truthful companion note
  let companionNote = "I'm here to help you remember your medicines, check appointments, and stay connected with family.";
  if (nextMedicine) {
    companionNote = `Your next reminder is ${nextMedicine.medicine_name}${nextMedicine.dosage ? ' (' + nextMedicine.dosage + ')' : ''} scheduled for ${nextMedicine.reminder_time}.`;
  } else if (hasMedicines && takenCount === totalCount) {
    companionNote = "You've taken all your scheduled medicines for today. Wonderful work!";
  } else if (todayEvents.length > 0) {
    companionNote = `You have an appointment today: ${todayEvents[0].title} at ${todayEvents[0].reminder_time || 'scheduled time'}.`;
  }

  // DEFAULT / HOME VIEW: Warm, Voice-First AI Care Companion Home
  return (
    <ErrorBoundary>
      <DashboardLayout currentView="home" onViewChange={onViewChange} user={user} onLogout={onLogout}>
        <div className="w-full max-w-7xl mx-auto flex flex-col gap-6 pb-12">
          
          {/* ==================================================================== */}
          {/* 1. ELDER LIVE TIME & DAILY CONTEXT HERO CARD                         */}
          {/* ==================================================================== */}
          <ElderLiveTimeCard 
            user={user}
            nextMedicine={nextMedicine}
            nextAppointment={todayEvents[0]}
            onTakeMedicine={handleTakeMedicine}
            onViewSchedule={() => onViewChange('calendar')}
          />

          {/* ==================================================================== */}
          {/* 2. VOICE COMPANION ENTRY POINT & QUICK ACTIONS (Glass Bar)           */}
          {/* ==================================================================== */}
          <div className="orma-glass-header flex flex-col md:flex-row md:items-center justify-between gap-4 sm:gap-6 py-4">
            <div className="flex items-center gap-3.5 relative z-10">
              <div className="w-11 h-11 rounded-2xl bg-blue-600/20 border border-blue-500/30 flex items-center justify-center text-2xl shadow-lg shrink-0">
                {timeContext.icon}
              </div>
              <div>
                <p className="text-slate-200 text-sm md:text-base font-semibold line-clamp-1">
                  {companionNote}
                </p>
                <p className="text-xs text-cyan-300/90 mt-0.5 flex items-center gap-1.5 font-medium">
                  <Sparkles className="w-3.5 h-3.5 text-cyan-400 shrink-0" />
                  <span className="line-clamp-1">{timeContext.promptSuggestion}</span>
                </p>
              </div>
            </div>

            <div className="flex items-center gap-3 shrink-0 relative z-10">
              <button 
                type="button"
                onClick={handleStartConversation}
                className="px-6 py-3.5 rounded-2xl bg-blue-600 hover:bg-blue-500 text-white font-bold text-base shadow-lg shadow-blue-600/25 transition-all flex items-center gap-2.5 cursor-pointer active:scale-95 border border-blue-400/30"
              >
                <div className="w-2.5 h-2.5 rounded-full bg-cyan-300 animate-pulse" />
                <Mic className="w-5 h-5" />
                <span>Talk to ORMA</span>
              </button>

              <button 
                type="button"
                onClick={() => onViewChange('emergency')}
                className="px-4 py-3.5 rounded-2xl bg-red-500/10 hover:bg-red-500/20 text-red-400 border border-red-500/30 font-bold text-sm transition-all flex items-center gap-2 cursor-pointer"
                title="Emergency Help"
              >
                <AlertOctagon className="w-4 h-4" />
                <span className="hidden sm:inline">Emergency</span>
              </button>
            </div>
          </div>

          {/* ==================================================================== */}
          {/* 2. TODAY'S PRIORITY: NEXT UP & TODAY'S SUMMARY                       */}
          {/* ==================================================================== */}
          <div className="grid grid-cols-1 md:grid-cols-12 gap-6">
            
            {/* Card 1: Next Up / Next Reminder (7 cols) */}
            <div className="md:col-span-7 orma-card flex flex-col justify-between">
              <div className="flex items-center justify-between mb-4 relative z-10">
                <span className="text-[11px] uppercase font-bold text-blue-400 tracking-wider flex items-center gap-1.5">
                  <Clock className="w-3.5 h-3.5" /> Next Reminder
                </span>
                <span className="text-xs text-slate-400 font-medium font-mono">
                  {new Date().toLocaleDateString('en-US', { weekday: 'short', month: 'short', day: 'numeric' })}
                </span>
              </div>

              {nextMedicine ? (
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 py-2 relative z-10">
                  <div>
                    <h3 className="text-2xl sm:text-3xl font-extrabold text-white tracking-tight">
                      {nextMedicine.medicine_name}
                    </h3>
                    <p className="text-sm text-slate-300 mt-1 font-medium">
                      {nextMedicine.dosage ? `${nextMedicine.dosage} · ` : ''}Scheduled for <span className="text-amber-400 font-bold">{nextMedicine.reminder_time}</span>
                    </p>
                    {nextMedicine.purpose && (
                      <p className="text-xs text-slate-400 mt-1">{nextMedicine.purpose}</p>
                    )}
                  </div>

                  <button
                    type="button"
                    onClick={(e) => handleTakeMedicine(nextMedicine.id, e)}
                    className="px-5 py-2.5 rounded-xl bg-emerald-600 hover:bg-emerald-500 text-white font-bold text-xs shadow-md shadow-emerald-600/20 transition-all flex items-center justify-center gap-1.5 cursor-pointer shrink-0 self-start sm:self-center"
                  >
                    <Check className="w-4 h-4" /> Mark Taken
                  </button>
                </div>
              ) : (
                <div className="py-3 flex items-center gap-3.5 text-emerald-400 relative z-10">
                  <div className="w-11 h-11 rounded-2xl bg-emerald-500/10 border border-emerald-500/20 flex items-center justify-center shrink-0">
                    <CheckCircle2 className="w-6 h-6 text-emerald-400" />
                  </div>
                  <div>
                    <h3 className="text-base font-bold text-white tracking-tight">You're All Caught Up</h3>
                    <p className="text-xs text-slate-400 mt-0.5">
                      {hasMedicines ? 'All scheduled medicines for today have been confirmed.' : 'No upcoming medicines or reminders right now.'}
                    </p>
                  </div>
                </div>
              )}

              <div className="mt-4 pt-3 border-t border-white/5 flex items-center justify-between text-xs text-slate-400 relative z-10">
                <span>{hasMedicines ? `${pendingMedicines.length} reminder(s) remaining` : 'Schedule is clear'}</span>
                <button 
                  type="button"
                  onClick={() => onViewChange('my-health')}
                  className="text-blue-400 hover:text-blue-300 font-semibold flex items-center gap-1 cursor-pointer"
                >
                  View Schedule <ChevronRight className="w-3.5 h-3.5" />
                </button>
              </div>
            </div>

            {/* Card 2: Today's Summary & Adherence (5 cols) */}
            <div className="md:col-span-5 orma-card flex flex-col justify-between">
              <div className="flex items-center justify-between mb-4 relative z-10">
                <span className="text-[11px] uppercase font-bold text-slate-400 tracking-wider flex items-center gap-1.5">
                  <Activity className="w-3.5 h-3.5 text-emerald-400" /> Today's Progress
                </span>
                {hasMedicines && (
                  <span className="text-xs font-bold text-emerald-400 bg-emerald-500/10 px-2.5 py-0.5 rounded-full border border-emerald-500/20">
                    {adherencePercentage}%
                  </span>
                )}
              </div>

              {hasMedicines ? (
                <div className="relative z-10">
                  <div className="flex items-baseline justify-between mb-2">
                    <div className="text-3xl font-extrabold text-white tracking-tight">
                      {takenCount} <span className="text-sm font-medium text-slate-400">of {totalCount} taken</span>
                    </div>
                    <span className="text-xs text-slate-400 font-medium">
                      {totalCount - takenCount === 0 ? 'All doses complete' : `${totalCount - takenCount} remaining`}
                    </span>
                  </div>

                  <div className="w-full h-3 bg-slate-950/60 rounded-full overflow-hidden p-0.5 border border-white/10">
                    <motion.div
                      initial={{ width: 0 }}
                      animate={{ width: `${adherencePercentage}%` }}
                      transition={{ duration: 0.8, ease: "easeOut" }}
                      className="h-full bg-gradient-to-r from-blue-500 to-emerald-400 rounded-full"
                    />
                  </div>
                </div>
              ) : (
                <div className="py-2 relative z-10">
                  <p className="text-sm font-bold text-white">No Medicines Scheduled</p>
                  <p className="text-xs text-slate-400 mt-1">No medication schedule active for today.</p>
                </div>
              )}

              <div className="mt-4 pt-3 border-t border-white/5 flex items-center justify-between text-xs text-slate-400 relative z-10">
                <span>Daily adherence tracker</span>
                <span className="text-slate-300 font-medium">Updated live</span>
              </div>
            </div>
          </div>

          {/* ==================================================================== */}
          {/* 3. MAIN CONTENT: TODAY'S MEDICINES & RIGHT WIDGETS                  */}
          {/* ==================================================================== */}
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
            
            {/* Left Column (7 cols): Today's Medicines Timeline & Appointments */}
            <div className="lg:col-span-7 flex flex-col gap-6">
              
              {/* Today's Medicines Timeline */}
              <div className="orma-card">
                <div className="flex items-center justify-between mb-5 relative z-10">
                  <div className="flex items-center gap-2.5">
                    <div className="w-8 h-8 rounded-xl bg-blue-500/10 border border-blue-500/20 flex items-center justify-center text-blue-400">
                      <Pill className="w-4 h-4" />
                    </div>
                    <div>
                      <h2 className="text-base font-bold text-white tracking-tight">Today's Medicines</h2>
                      <p className="text-[11px] text-slate-400">Daily medication schedule & reminders</p>
                    </div>
                  </div>
                  <button 
                    type="button"
                    onClick={() => onViewChange('my-health')} 
                    className="text-xs font-bold text-blue-400 hover:text-blue-300 flex items-center gap-1 cursor-pointer"
                  >
                    Manage <ChevronRight className="w-3.5 h-3.5" />
                  </button>
                </div>

                <div className="relative z-10">
                  <MedicationTimeline
                    medicines={medicines}
                    mode="elderly"
                    onTakeMedicine={handleTakeMedicine}
                    onAddMedicine={() => onViewChange('my-health')}
                  />
                </div>
              </div>

              {/* Today's Appointments & Events */}
              <div className="orma-card">
                <div className="flex items-center justify-between mb-5 relative z-10">
                  <div className="flex items-center gap-2.5">
                    <div className="w-8 h-8 rounded-xl bg-emerald-500/10 border border-emerald-500/20 flex items-center justify-center text-emerald-400">
                      <Calendar className="w-4 h-4" />
                    </div>
                    <div>
                      <h2 className="text-base font-bold text-white tracking-tight">Today's Appointments</h2>
                      <p className="text-[11px] text-slate-400">Doctor visits and scheduled health events</p>
                    </div>
                  </div>
                  <button 
                    type="button"
                    onClick={() => onViewChange('calendar')} 
                    className="text-xs font-bold text-emerald-400 hover:text-emerald-300 flex items-center gap-1 cursor-pointer"
                  >
                    View Calendar <ChevronRight className="w-3.5 h-3.5" />
                  </button>
                </div>

                {todayEvents.length > 0 ? (
                  <div className="space-y-3 relative z-10">
                    {todayEvents.map((evt) => (
                      <div key={evt.id} className="p-3.5 bg-slate-950/50 border border-white/5 rounded-2xl flex items-center justify-between gap-3">
                        <div className="flex items-center gap-3">
                          <div className="w-8 h-8 rounded-xl bg-emerald-500/20 text-emerald-400 flex items-center justify-center shrink-0">
                            <Calendar className="w-4 h-4" />
                          </div>
                          <div>
                            <p className="font-bold text-white text-sm">{evt.title}</p>
                            <p className="text-xs text-slate-400 mt-0.5">{evt.description || 'Health event'}</p>
                          </div>
                        </div>
                        <span className="text-xs font-bold text-emerald-400 font-mono">
                          {evt.reminder_time || 'Today'}
                        </span>
                      </div>
                    ))}
                  </div>
                ) : (
                  <div className="py-6 px-4 text-center border border-dashed border-white/10 rounded-2xl bg-slate-950/30 relative z-10">
                    <Calendar className="w-7 h-7 text-slate-500 mx-auto mb-1.5" />
                    <p className="text-sm font-bold text-white">No Appointments Today</p>
                    <p className="text-xs text-slate-400 mt-0.5 mb-3">You're free of scheduled events today.</p>
                    <button
                      type="button"
                      onClick={() => onViewChange('calendar')}
                      className="px-4 py-2 rounded-xl bg-slate-900 hover:bg-slate-800 border border-white/10 text-xs font-bold text-slate-200 transition-colors cursor-pointer inline-flex items-center gap-1.5"
                    >
                      <Calendar className="w-3.5 h-3.5" />
                      <span>Open Calendar</span>
                    </button>
                  </div>
                )}
              </div>

            </div>

            {/* Right Column (5 cols): Today's Health, Weekly Progress & Emergency */}
            <div className="lg:col-span-5 flex flex-col gap-6">
              
              {/* Simple Weekly Schedule Progress */}
              <ElderlyWeeklyProgress adherenceRate={adherencePercentage || 90} />

              {/* Health Status Snapshot */}
              <HealthSnapshot onViewChange={onViewChange} />

              {/* Emergency Alert Widget */}
              <EmergencyAlert 
                isActive={isEmergencyActive} 
                severity={emergencySeverity} 
                onViewChange={onViewChange} 
              />

            </div>

          </div>
        </div>

        {/* Floating Talk Control on Dashboard view */}
        <FloatingTalkControl
          isConversationMode={conversationMode}
          turnState={turnState}
          isListening={isListeningState}
          isProcessing={Boolean(isTranscribing || isThinking)}
          isSpeaking={isSpeaking}
          onStartConversation={handleStartConversation}
          onEndConversation={handleEndConversation}
          onInterrupt={handleInterrupt}
        />
      </DashboardLayout>
    </ErrorBoundary>
  );
}

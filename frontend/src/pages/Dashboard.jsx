import React, { useState, useEffect } from 'react';
import DashboardLayout from '../layouts/DashboardLayout';
import HeroSection from '../components/HeroSection';
import AIConversationPanel from '../components/AIConversationPanel';
import MedicineReminder from '../components/MedicineReminder';
import EmergencyAlert from '../components/EmergencyAlert';
import FamilyMonitoring from '../components/FamilyMonitoring';
import VoiceRecorder from '../components/VoiceRecorder';
import { healthApi, speechApi, chatApi, emergencyApi, medicineApi } from '../services/api';
import { useApi } from '../hooks/useApi';
import { tts } from '../services/tts';
import { motion } from 'framer-motion';
import { Wifi, WifiOff } from 'lucide-react';

export default function Dashboard() {
  const [messages, setMessages] = useState([
    { id: 1, sender: 'user', text: 'Did I take my blood pressure pill this morning?', time: '09:42 AM' },
    { id: 2, sender: 'ai', text: 'Yes, Sarah. You took your Amlodipine at 8:30 AM today. Your next dose is scheduled for tomorrow morning.', time: '09:42 AM' }
  ]);
  const [isListening, setIsListening] = useState(false);
  const [isSpeaking, setIsSpeaking] = useState(false);
  const [isEmergencyActive, setIsEmergencyActive] = useState(false);
  const [emergencySeverity, setEmergencySeverity] = useState('low');
  const [languageMode, setLanguageMode] = useState('ml'); // Default to Malayalam based on user request focus
  const [activeReminders, setActiveReminders] = useState([]);
  
  // Stop TTS if user starts recording
  useEffect(() => {
    if (isListening) {
      tts.stop();
      setIsSpeaking(false);
    }
  }, [isListening]);
  
  const { data: healthData, error: healthError, execute: checkHealth } = useApi(healthApi.check);
  const { execute: transcribe, loading: isTranscribing } = useApi(speechApi.transcribe);
  const { execute: sendMessage, loading: isThinking } = useApi(chatApi.sendMessage);
  const { execute: analyzeEmergency } = useApi(emergencyApi.analyze);
  const { execute: getPendingReminders } = useApi(medicineApi.getPendingReminders);

  // Poll for real-time medicine reminders
  useEffect(() => {
    if (!isConnected) return;
    const interval = setInterval(async () => {
      try {
        const pending = await getPendingReminders();
        if (pending && pending.length > 0) {
          setActiveReminders(prev => {
            const newReminders = pending.filter(p => !prev.find(existing => existing.id === p.id));
            return [...prev, ...newReminders];
          });
          
          const reminder = pending[0];
          const message = languageMode === 'ml' ? reminder.message_ml : reminder.message_en;
          tts.speak(message, {
            onStart: () => setIsSpeaking(true),
            onEnd: () => setIsSpeaking(false)
          });
        }
      } catch (err) {
        console.error("Failed to poll reminders", err);
      }
    }, 15000); // Check every 15 seconds
    
    return () => clearInterval(interval);
  }, [isConnected, languageMode, getPendingReminders]);

  const handleMarkReminderTaken = async (reminderId) => {
    try {
      await medicineApi.takeMedicine(reminderId);
      setActiveReminders(prev => prev.filter(r => r.id !== reminderId));
    } catch (e) {
      console.error("Failed to mark taken", e);
    }
  };

  const handleStopRecording = async (blobUrl, blob) => {
    if (!blob) return;
    try {
      const languageParam = languageMode !== 'auto' ? languageMode : undefined;
      const data = await transcribe(blob, languageParam);
      const userText = data.transcription;
      const detectedLanguage = languageMode !== 'auto' ? languageMode : (data.detected_language || 'en');
      
      if (!userText || userText.trim() === '') {
        console.log('Transcription empty, skipping AI processing.');
        // Optionally show a toast here to user "I didn't hear you clearly"
        return;
      }
      
      const newMsg = {
        id: Date.now(),
        sender: 'user',
        text: userText,
        time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
      };
      setMessages(prev => [...prev, newMsg]);

      // Analyze for emergency before normal AI response
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
        
        tts.speak(alertMsg.text, {
          onStart: () => setIsSpeaking(true),
          onEnd: () => setIsSpeaking(false),
          onError: () => setIsSpeaking(false)
        });
        
        return; // Stop normal AI flow
      }

      // Chain normal AI response
      const chatData = await sendMessage(userText, 'default_user', detectedLanguage);
      const aiMsg = {
        id: Date.now() + 1,
        sender: 'ai',
        text: chatData.response,
        time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
      };
      setMessages(prev => [...prev, aiMsg]);

      // Speak AI response
      tts.speak(chatData.response, {
        onStart: () => setIsSpeaking(true),
        onEnd: () => setIsSpeaking(false),
        onError: () => setIsSpeaking(false)
      });

    } catch (error) {
      console.error("Pipeline failed:", error);
      // Push an error message to UI
      const errorMsg = {
        id: Date.now(),
        sender: 'ai',
        text: "I'm sorry, I couldn't process that right now. Please check your connection.",
        time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
      };
      setMessages(prev => [...prev, errorMsg]);
      tts.speak(errorMsg.text, { onStart: () => setIsSpeaking(true), onEnd: () => setIsSpeaking(false) });
    }
  };

  useEffect(() => {
    checkHealth();
  }, [checkHealth]);

  const isConnected = !!healthData && !healthError;
  const backendMessage = healthError ? 'Backend Disconnected' : (healthData?.message || 'Connecting to backend...');

  return (
    <DashboardLayout>
      {/* Top Bar: Status & Controls */}
      <motion.div 
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        className="mb-8 flex flex-col md:flex-row items-center justify-center gap-4"
      >
        {/* Status Banner */}
        <div className={`flex items-center justify-center gap-2 py-2 px-4 rounded-xl backdrop-blur-md border border-slate-700/50 ${
          isConnected ? 'bg-emerald-500/10 text-emerald-400' : 'bg-red-500/10 text-red-400'
        }`}>
          {isConnected ? <Wifi className="w-4 h-4" /> : <WifiOff className="w-4 h-4" />}
          <span className="text-sm font-medium">{backendMessage}</span>
        </div>

        {/* Language Toggle */}
        <div className="flex bg-slate-800/80 p-1.5 rounded-xl border border-slate-700/50 backdrop-blur-md shadow-lg">
          <button 
            onClick={() => setLanguageMode('en')}
            className={`px-4 py-1.5 rounded-lg text-sm font-medium transition-all ${languageMode === 'en' ? 'bg-blue-600 text-white shadow-[0_0_15px_rgba(37,99,235,0.5)]' : 'text-slate-400 hover:text-white hover:bg-slate-700/50'}`}
          >
            English
          </button>
          <button 
            onClick={() => setLanguageMode('auto')}
            className={`px-4 py-1.5 rounded-lg text-sm font-medium transition-all ${languageMode === 'auto' ? 'bg-indigo-600 text-white shadow-[0_0_15px_rgba(79,70,229,0.5)]' : 'text-slate-400 hover:text-white hover:bg-slate-700/50'}`}
          >
            Auto Detect
          </button>
          <button 
            onClick={() => setLanguageMode('ml')}
            className={`px-4 py-1.5 rounded-lg text-sm font-medium transition-all ${languageMode === 'ml' ? 'bg-purple-600 text-white shadow-[0_0_15px_rgba(147,51,234,0.5)]' : 'text-slate-400 hover:text-white hover:bg-slate-700/50'}`}
          >
            Malayalam
          </button>
        </div>
      </motion.div>

      <HeroSection />
      
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="col-span-1 lg:col-span-2 flex flex-col gap-6">
          {/* ChatGPT Voice Mode Style Recorder */}
          <VoiceRecorder 
            onRecordingComplete={handleStopRecording} 
            isProcessing={isTranscribing || isThinking}
            onStatusChange={setIsListening}
            isSpeaking={isSpeaking}
          />
          <AIConversationPanel 
            isListening={isListening} 
            isSpeaking={isSpeaking}
            messages={messages} 
            isTranscribing={isTranscribing} 
            isThinking={isThinking} 
          />
        </div>
        
        <div className="col-span-1 flex flex-col gap-6">
          <MedicineReminder />
          <FamilyMonitoring />
          <EmergencyAlert isActive={isEmergencyActive} severity={emergencySeverity} />
        </div>
      </div>

      {/* Real-Time Reminder Popup Overlay */}
      {activeReminders.length > 0 && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/60 backdrop-blur-sm">
          <div className="flex flex-col gap-4 max-w-md w-full">
            {activeReminders.map(reminder => (
              <motion.div 
                key={reminder.id}
                initial={{ opacity: 0, scale: 0.9, y: 20 }}
                animate={{ opacity: 1, scale: 1, y: 0 }}
                className="bg-slate-800 border border-blue-500/50 rounded-2xl p-6 shadow-[0_0_40px_rgba(59,130,246,0.3)]"
              >
                <div className="flex items-center gap-4 mb-4">
                  <div className="w-12 h-12 bg-blue-500/20 rounded-full flex items-center justify-center animate-pulse">
                    <span className="text-2xl">💊</span>
                  </div>
                  <div>
                    <h3 className="text-xl font-bold text-white">Time for Medication</h3>
                    <p className="text-slate-400">{reminder.medicine_name} - {reminder.dosage}</p>
                  </div>
                </div>
                <p className="text-lg text-blue-200 mb-6 font-medium">
                  {languageMode === 'ml' ? reminder.message_ml : reminder.message_en}
                </p>
                <div className="flex gap-3">
                  <button 
                    onClick={() => handleMarkReminderTaken(reminder.id)}
                    className="flex-1 bg-blue-600 hover:bg-blue-500 text-white font-bold py-3 rounded-xl transition-all"
                  >
                    Mark as Taken
                  </button>
                  <button 
                    onClick={() => setActiveReminders(prev => prev.filter(r => r.id !== reminder.id))}
                    className="flex-1 bg-slate-700 hover:bg-slate-600 text-white font-bold py-3 rounded-xl transition-all"
                  >
                    Dismiss
                  </button>
                </div>
              </motion.div>
            ))}
          </div>
        </div>
      )}
    </DashboardLayout>
  );
}

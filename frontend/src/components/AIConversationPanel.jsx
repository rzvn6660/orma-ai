import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  Volume2, 
  Sparkles, 
  ChevronRight, 
  User,
  Heart,
  MessageSquarePlus,
  RotateCcw,
  VolumeX
} from 'lucide-react';
import { tts } from '../services/tts';
import AICompanionOrb from './AICompanionOrb';
import { isRTL } from '../utils/reminderLocalization';

export default function AIConversationPanel({ 
  isListening, 
  isSpeaking, 
  onStopSpeaking,
  messages = [], 
  isTranscribing, 
  isThinking,
  startRecording,
  stopRecording,
  onClearConversation,
  onAskAgain,
  timeContext,
  user,
  externalError
}) {
  const [replayingMessageId, setReplayingMessageId] = useState(null);

  const handleReplay = (msgId, text, langCode) => {
    if (!text) return;
    setReplayingMessageId(msgId);
    tts.speak(text, {
      langCode: langCode || 'en-IN',
      onEnd: () => setReplayingMessageId(null),
      onError: () => setReplayingMessageId(null)
    });
  };

  const handleSuggestionClick = (text) => {
    if (onAskAgain && text) {
      onAskAgain(text);
    }
  };

  const safeMessages = Array.isArray(messages) ? messages.filter(Boolean) : [];
  const lastUserMsg = [...safeMessages].reverse().find(m => m && m.sender === 'user');
  const lastAiMsg = [...safeMessages].reverse().find(m => m && m.sender === 'ai');
  const hasDialogue = Boolean(lastUserMsg || lastAiMsg);

  const aiLangRtl = isRTL(lastAiMsg?.langCode);

  const voiceCap = tts.getAvailableReminderVoice(lastAiMsg?.langCode || 'en-IN');
  const showAiVoiceUnavailable = Boolean(
    lastAiMsg &&
    lastAiMsg.langCode &&
    !lastAiMsg.langCode.toLowerCase().startsWith('en') &&
    !voiceCap.voiceFound
  );

  // Default accessible prompt suggestions with strict array safety
  const defaultSuggestions = [
    "Did I take my morning medicine?",
    "What medicines are due today?",
    "When is my next appointment?",
    "How am I doing this week?"
  ];

  const rawSuggestions = (timeContext && Array.isArray(timeContext.suggestions) && timeContext.suggestions.length > 0)
    ? timeContext.suggestions
    : defaultSuggestions;

  const displaySuggestions = Array.isArray(rawSuggestions)
    ? rawSuggestions.slice(0, 4)
    : defaultSuggestions;

  return (
    <div className="flex flex-col items-center justify-start relative w-full max-w-3xl mx-auto">
      
      {/* 1. Hero Voice Interaction Center */}
      <div className="w-full flex flex-col items-center justify-center pt-2 pb-6">
        <AICompanionOrb 
          onRecordingComplete={(blobUrl, blob) => {
            if (stopRecording) stopRecording(blobUrl, blob);
          }}
          isProcessing={Boolean(isTranscribing || isThinking)}
          isSpeaking={Boolean(isSpeaking)}
          onStopSpeaking={onStopSpeaking}
          externalError={externalError}
        />
      </div>

      {/* 2. Interactive Dialogue & Response Area */}
      <AnimatePresence mode="wait">
        {hasDialogue && (
          <motion.div
            key="last-dialogue"
            initial={{ opacity: 0, y: 15, scale: 0.98 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: -10, scale: 0.98 }}
            transition={{ duration: 0.25 }}
            className="w-full orma-card p-5 sm:p-6 mb-6 border border-white/10 shadow-2xl relative overflow-hidden"
          >
            {/* Top Cyan Accent Line */}
            <div className="absolute top-0 left-0 right-0 h-1 bg-gradient-to-r from-blue-500 via-cyan-400 to-emerald-400 opacity-80" />

            <div className="flex items-center justify-between mb-3 pb-2.5 border-b border-white/10 text-xs">
              <span className="font-extrabold uppercase tracking-wider text-cyan-400 flex items-center gap-1.5">
                <Sparkles className="w-3.5 h-3.5 text-cyan-400" /> Recent Conversation
              </span>
              <span className="text-slate-400 font-mono text-[11px]">
                {lastAiMsg?.time || lastUserMsg?.time || 'Just now'}
              </span>
            </div>

            <div className="space-y-3.5">
              {/* User Query */}
              {lastUserMsg && (
                <div className="flex items-start justify-end gap-2.5">
                  <div className="bg-blue-600/25 border border-blue-500/35 text-white px-4 py-2.5 rounded-2xl rounded-tr-sm text-sm sm:text-base font-medium max-w-[85%] shadow-sm">
                    "{lastUserMsg.text}"
                  </div>
                  <div className="w-7 h-7 rounded-full bg-blue-600 flex items-center justify-center text-white shrink-0 shadow-md">
                    <User className="w-3.5 h-3.5" />
                  </div>
                </div>
              )}

              {/* ORMA Care Answer */}
              {lastAiMsg && (
                <div className="flex items-start gap-2.5 pt-1">
                  <div className="w-7 h-7 rounded-full bg-cyan-600/30 border border-cyan-400/50 flex items-center justify-center text-cyan-300 shrink-0 shadow-md">
                    <Heart className="w-3.5 h-3.5 text-cyan-300" />
                  </div>

                  <div className="flex-1 rounded-2xl bg-slate-950/70 border border-white/10 p-4 text-white">
                    <p className={`text-sm sm:text-base leading-relaxed text-slate-100 font-medium whitespace-pre-wrap ${aiLangRtl ? 'rtl text-right' : 'ltr text-left'}`} dir={aiLangRtl ? 'rtl' : 'ltr'}>
                      {lastAiMsg.text}
                    </p>

                    {showAiVoiceUnavailable && (
                      <div className="mt-2.5 p-2.5 rounded-xl bg-slate-900/90 border border-slate-800 text-slate-300 text-xs flex items-center gap-2">
                        <VolumeX className="w-3.5 h-3.5 text-amber-400 shrink-0" />
                        <span>Spoken response isn't available on this device for this language. The answer is shown above.</span>
                      </div>
                    )}

                    <div className="flex items-center justify-between gap-3 mt-3 pt-2.5 border-t border-white/5 flex-wrap">
                      <button
                        type="button"
                        onClick={() => handleReplay(lastAiMsg.id, lastAiMsg.text, lastAiMsg.langCode)}
                        disabled={replayingMessageId === lastAiMsg.id}
                        className="px-3 py-1.5 rounded-xl bg-slate-900 hover:bg-slate-800 border border-white/10 text-xs font-bold text-cyan-300 transition-colors flex items-center gap-1.5 cursor-pointer disabled:opacity-50"
                      >
                        <Volume2 className="w-3.5 h-3.5" />
                        <span>{replayingMessageId === lastAiMsg.id ? 'Playing audio...' : 'Replay Voice'}</span>
                      </button>

                      {onClearConversation && (
                        <button
                          type="button"
                          onClick={onClearConversation}
                          className="text-xs text-slate-400 hover:text-slate-200 transition-colors flex items-center gap-1 cursor-pointer"
                        >
                          <RotateCcw className="w-3 h-3" />
                          <span>Clear Dialogue</span>
                        </button>
                      )}
                    </div>
                  </div>
                </div>
              )}
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* 3. ASK ORMA — Refined Healthcare Quick Prompts */}
      <div className="w-full flex flex-col items-center gap-3 mt-1">
        <div className="text-center">
          <span className="text-xs font-extrabold uppercase tracking-wider text-blue-400 block">
            Ask ORMA
          </span>
          <span className="text-[11px] text-slate-400 mt-0.5">
            Tap any question to speak with ORMA instantly
          </span>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-2.5 w-full">
          {displaySuggestions.map((q, idx) => (
            <button
              key={idx}
              type="button"
              onClick={() => handleSuggestionClick(q)}
              className="text-left p-3.5 bg-slate-900/70 hover:bg-blue-600/15 border border-white/10 hover:border-blue-500/30 rounded-2xl text-slate-200 hover:text-white text-xs sm:text-sm font-medium transition-all shadow-sm flex items-center justify-between group cursor-pointer"
            >
              <span className="leading-snug">{q}</span>
              <ChevronRight className="w-4 h-4 text-slate-500 group-hover:text-blue-400 transition-colors shrink-0 ml-2" />
            </button>
          ))}
        </div>
      </div>

    </div>
  );
}

import React, { useState, useRef, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Volume2,
  Sparkles,
  ChevronRight,
  User,
  Heart,
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
  const messagesEndRef = useRef(null);

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

  // Smoothly scroll conversation area to latest message when new messages arrive
  useEffect(() => {
    if (messagesEndRef.current) {
      messagesEndRef.current.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
    }
  }, [safeMessages.length, isThinking, isTranscribing]);

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
      <div className="w-full flex flex-col items-center justify-center pt-2 pb-5">
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

      {/* 2. Chronological Dialogue & Scrollable Conversation Area */}
      <div className="w-full orma-card p-4 sm:p-6 mb-6 border border-white/10 shadow-2xl relative flex flex-col overflow-hidden">
        {/* Top Cyan Accent Line */}
        <div className="absolute top-0 left-0 right-0 h-1 bg-gradient-to-r from-blue-500 via-cyan-400 to-emerald-400 opacity-80" />

        {/* Conversation Header */}
        <div className="flex items-center justify-between mb-3 pb-2.5 border-b border-white/10 text-xs shrink-0">
          <div className="flex items-center gap-2">
            <span className="font-extrabold uppercase tracking-wider text-cyan-400 flex items-center gap-1.5">
              <Sparkles className="w-3.5 h-3.5 text-cyan-400" /> Conversation
            </span>
            {safeMessages.length > 0 && (
              <span className="px-2 py-0.5 rounded-full bg-slate-800 text-slate-300 text-[10px] font-bold border border-white/5">
                {safeMessages.length} {safeMessages.length === 1 ? 'message' : 'messages'}
              </span>
            )}
          </div>

          {safeMessages.length > 0 && onClearConversation && (
            <button
              type="button"
              onClick={onClearConversation}
              className="text-xs text-slate-400 hover:text-slate-200 transition-colors flex items-center gap-1 cursor-pointer"
              title="Start fresh conversation"
            >
              <RotateCcw className="w-3 h-3" />
              <span>New Chat</span>
            </button>
          )}
        </div>

        {/* Scrollable Message Feed */}
        <div className="w-full max-h-[380px] sm:max-h-[460px] overflow-y-auto overscroll-contain custom-scrollbar space-y-3.5 pr-1 sm:pr-2">
          {safeMessages.length === 0 ? (
            <div className="py-8 px-4 text-center flex flex-col items-center justify-center gap-2 text-slate-400">
              <Sparkles className="w-7 h-7 text-cyan-400/60 mb-1" />
              <p className="text-sm font-semibold text-slate-200">How can I help you today?</p>
              <p className="text-xs text-slate-400 max-w-sm">
                Tap the microphone orb above to speak with ORMA, or choose a suggested question below.
              </p>
            </div>
          ) : (
            safeMessages.map((msg, idx) => {
              const msgKey = msg.id || `msg_${idx}_${msg.sender}`;
              const isUser = msg.sender === 'user';

              if (isUser) {
                return (
                  <div key={msgKey} className="flex items-start justify-end gap-2.5">
                    <div className="flex flex-col items-end gap-1 max-w-[85%]">
                      <div className="bg-blue-600/25 border border-blue-500/35 text-white px-4 py-2.5 rounded-2xl rounded-tr-sm text-sm sm:text-base font-medium shadow-sm">
                        <p className="leading-relaxed whitespace-pre-wrap">{msg.text}</p>
                      </div>
                      <span className="text-[10px] text-slate-400 font-mono px-1">
                        {msg.time || 'Just now'}
                      </span>
                    </div>
                    <div className="w-7 h-7 rounded-full bg-blue-600 flex items-center justify-center text-white shrink-0 shadow-md mt-0.5">
                      <User className="w-3.5 h-3.5" />
                    </div>
                  </div>
                );
              }

              // ORMA AI Message
              const msgRtl = isRTL(msg.langCode);
              const voiceCap = tts.getAvailableReminderVoice(msg.langCode || 'en-IN');
              const showVoiceWarning = Boolean(
                msg.langCode &&
                !msg.langCode.toLowerCase().startsWith('en') &&
                !voiceCap.voiceFound
              );

              return (
                <div key={msgKey} className="flex items-start gap-2.5 pt-1">
                  <div className="w-7 h-7 rounded-full bg-cyan-600/30 border border-cyan-400/50 flex items-center justify-center text-cyan-300 shrink-0 shadow-md mt-0.5">
                    <Heart className="w-3.5 h-3.5 text-cyan-300" />
                  </div>

                  <div className="flex-1 rounded-2xl bg-slate-950/70 border border-white/10 p-3.5 sm:p-4 text-white shadow-sm">
                    <p
                      className={`text-sm sm:text-base leading-relaxed text-slate-100 font-medium whitespace-pre-wrap ${msgRtl ? 'rtl text-right' : 'ltr text-left'}`}
                      dir={msgRtl ? 'rtl' : 'ltr'}
                    >
                      {msg.text}
                    </p>

                    {showVoiceWarning && (
                      <div className="mt-2.5 p-2 rounded-xl bg-slate-900/90 border border-slate-800 text-slate-300 text-xs flex items-center gap-2">
                        <VolumeX className="w-3.5 h-3.5 text-amber-400 shrink-0" />
                        <span>Spoken response isn't available on this device for this language. The answer is shown above.</span>
                      </div>
                    )}

                    <div className="flex items-center justify-between gap-3 mt-2.5 pt-2 border-t border-white/5 flex-wrap">
                      <span className="text-[10px] text-slate-400 font-mono">
                        {msg.time || 'Just now'}
                      </span>

                      {msg.text && (
                        <button
                          type="button"
                          onClick={() => handleReplay(msg.id || idx, msg.text, msg.langCode)}
                          disabled={replayingMessageId === (msg.id || idx)}
                          className="px-2.5 py-1 rounded-lg bg-slate-900 hover:bg-slate-800 border border-white/10 text-xs font-bold text-cyan-300 transition-colors flex items-center gap-1.5 cursor-pointer disabled:opacity-50"
                        >
                          <Volume2 className="w-3 h-3" />
                          <span>{replayingMessageId === (msg.id || idx) ? 'Playing...' : 'Replay Voice'}</span>
                        </button>
                      )}
                    </div>
                  </div>
                </div>
              );
            })
          )}

          {/* Real-time processing indicator */}
          {(isThinking || isTranscribing) && (
            <div className="flex items-center gap-2.5 text-cyan-400 text-xs font-bold p-3 rounded-2xl bg-cyan-950/30 border border-cyan-500/20 animate-pulse">
              <div className="w-2 h-2 rounded-full bg-cyan-400 animate-ping" />
              <span>{isTranscribing ? "Listening and transcribing..." : "ORMA is thinking..."}</span>
            </div>
          )}

          {/* Auto-scroll bottom anchor */}
          <div ref={messagesEndRef} />
        </div>
      </div>

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

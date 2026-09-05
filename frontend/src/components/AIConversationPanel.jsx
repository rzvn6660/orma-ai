import React, { useState, useRef, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Volume2,
  Sparkles,
  ChevronRight,
  User,
  Heart,
  RotateCcw,
  VolumeX,
  Send,
  PhoneOff,
  Mic,
  Square
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
  externalError,
  isConversationMode = false,
  turnState = 'idle',
  onStartConversation,
  onEndConversation,
  onInterrupt,
  listenTrigger = 0,
  onStatusChange
}) {
  const [replayingMessageId, setReplayingMessageId] = useState(null);
  const [typedText, setTypedText] = useState('');
  const feedRef = useRef(null);

  const handleReplay = (msgId, text, langCode) => {
    if (!text) return;
    const detected = /[\u0D00-\u0D7F]/.test(text) ? 'ml-IN' : (langCode || 'en-IN');
    setReplayingMessageId(msgId);
    tts.speak(text, {
      langCode: detected,
      onEnd: () => setReplayingMessageId(null),
      onError: () => setReplayingMessageId(null)
    });
  };

  const handleSuggestionClick = (text) => {
    if (onAskAgain && text) {
      onAskAgain(text);
    }
  };

  const handleSendTyped = () => {
    const trimmed = typedText.trim();
    if (!trimmed || isTranscribing || isThinking) return;
    if (onAskAgain) {
      onAskAgain(trimmed);
      setTypedText('');
    }
  };

  const safeMessages = Array.isArray(messages) ? messages.filter(Boolean) : [];

  // Smoothly scroll message container only (prevents outer page/orb from scrolling)
  useEffect(() => {
    if (feedRef.current) {
      feedRef.current.scrollTo({
        top: feedRef.current.scrollHeight,
        behavior: 'smooth'
      });
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
    <div className="flex flex-col items-center justify-start relative w-full max-w-2xl mx-auto">

      {/* 0. Continuous Conversation Mode Active Status Banner */}
      <AnimatePresence>
        {isConversationMode && (
          <motion.div
            initial={{ opacity: 0, y: -10, scale: 0.98 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: -10, scale: 0.98 }}
            className="w-full mb-3 p-3 sm:p-3.5 rounded-2xl bg-gradient-to-r from-slate-950 via-cyan-950/40 to-slate-950 border border-cyan-400/40 shadow-xl flex items-center justify-between gap-3 flex-wrap"
          >
            <div className="flex items-center gap-2.5">
              {isTranscribing || isThinking || turnState === 'thinking' ? (
                <>
                  <div className="w-3.5 h-3.5 rounded-full border-2 border-blue-400 border-t-transparent animate-spin shrink-0" />
                  <span className="text-xs sm:text-sm font-extrabold text-blue-300">
                    ORMA is thinking...
                  </span>
                </>
              ) : isSpeaking || turnState === 'speaking' ? (
                <>
                  <Volume2 className="w-4 h-4 text-sky-400 animate-pulse shrink-0" />
                  <span className="text-xs sm:text-sm font-extrabold text-white">
                    ORMA is speaking · Tap orb to interrupt
                  </span>
                </>
              ) : isListening || turnState === 'listening' ? (
                <>
                  <span className="relative flex h-3 w-3 shrink-0">
                    <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-cyan-400 opacity-75" />
                    <span className="relative inline-flex rounded-full h-3 w-3 bg-cyan-500" />
                  </span>
                  <span className="text-xs sm:text-sm font-extrabold text-cyan-300">
                    Listening... Speak naturally
                  </span>
                </>
              ) : (
                <>
                  <span className="w-2.5 h-2.5 rounded-full bg-emerald-400 shrink-0" />
                  <span className="text-xs sm:text-sm font-extrabold text-emerald-300">
                    Your Turn · Speak anytime
                  </span>
                </>
              )}
            </div>

            <div className="flex items-center gap-2 shrink-0">
              {(isSpeaking || turnState === 'speaking') && onInterrupt && (
                <button
                  type="button"
                  onClick={onInterrupt}
                  className="px-3 py-1.5 rounded-xl bg-sky-500/20 hover:bg-sky-500/35 border border-sky-400/40 text-sky-200 text-xs font-bold transition-all flex items-center gap-1.5 cursor-pointer shadow-sm active:scale-95"
                >
                  <VolumeX className="w-3.5 h-3.5" />
                  <span>Interrupt</span>
                </button>
              )}
              {onEndConversation && (
                <button
                  type="button"
                  onClick={onEndConversation}
                  className="px-3.5 py-1.5 rounded-xl bg-red-500/20 hover:bg-red-500/35 border border-red-500/40 text-red-300 hover:text-white text-xs font-extrabold transition-all flex items-center gap-1.5 cursor-pointer shadow-sm active:scale-95"
                >
                  <PhoneOff className="w-3.5 h-3.5" />
                  <span>End Conversation</span>
                </button>
              )}
            </div>
          </motion.div>
        )}
      </AnimatePresence>

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
          isConversationMode={isConversationMode}
          turnState={turnState}
          onStartConversation={onStartConversation}
          onEndConversation={onEndConversation}
          onInterrupt={onInterrupt}
          listenTrigger={listenTrigger}
          onStatusChange={onStatusChange}
        />
      </div>

      {/* 2. Chronological Dialogue & Scrollable Conversation Area */}
      <div className="w-full rounded-3xl bg-slate-900/80 backdrop-blur-2xl border border-white/10 p-4 sm:p-5 mb-5 shadow-2xl relative flex flex-col overflow-hidden">
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
        <div ref={feedRef} className="w-full max-h-[320px] sm:max-h-[380px] overflow-y-auto overscroll-contain custom-scrollbar space-y-3 pr-1 sm:pr-2">
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

        </div>

        {/* Typing Input Bar (Preserve typing interaction alongside voice) */}
        <div className="w-full flex items-center gap-2 pt-3.5 mt-2 border-t border-white/10 shrink-0">
          <input
            type="text"
            value={typedText}
            onChange={(e) => setTypedText(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                handleSendTyped();
              }
            }}
            placeholder="Type a message or question to ORMA..."
            disabled={Boolean(isTranscribing || isThinking)}
            className="flex-1 px-4 py-2.5 rounded-xl bg-slate-950/80 border border-white/15 text-xs sm:text-sm text-white placeholder:text-slate-500 focus:outline-none focus:border-cyan-400/60 focus:ring-1 focus:ring-cyan-400/30 transition-all disabled:opacity-50"
          />
          {/* Bottom Action Area Voice Button */}
          <button
            type="button"
            onClick={() => window.dispatchEvent(new CustomEvent('orma_toggle_voice'))}
            disabled={Boolean(isTranscribing || isThinking || turnState === 'thinking')}
            aria-label={isListening || turnState === 'listening' ? "Stop listening" : isSpeaking || turnState === 'speaking' ? "Interrupt ORMA" : "Speak to ORMA"}
            title={isListening || turnState === 'listening' ? "Tap to finish speaking" : isSpeaking || turnState === 'speaking' ? "Tap to interrupt" : "Tap to speak"}
            className={`p-2.5 rounded-xl font-bold text-xs sm:text-sm flex items-center justify-center transition-all shadow-md cursor-pointer shrink-0 active:scale-95 border ${
              isListening || turnState === 'listening'
                ? 'bg-cyan-500/25 hover:bg-cyan-500/35 border-cyan-400 text-cyan-200 animate-pulse'
                : isSpeaking || turnState === 'speaking'
                ? 'bg-sky-500/20 hover:bg-sky-500/30 border-sky-400/50 text-sky-300'
                : isTranscribing || isThinking || turnState === 'thinking'
                ? 'bg-slate-800 border-white/10 text-slate-500 cursor-not-allowed opacity-50'
                : 'bg-slate-800 hover:bg-slate-700 border-white/15 text-cyan-400 hover:text-cyan-300'
            }`}
          >
            {isListening || turnState === 'listening' ? (
              <Square className="w-4 h-4 fill-current text-cyan-300" />
            ) : isSpeaking || turnState === 'speaking' ? (
              <VolumeX className="w-4 h-4 text-sky-300" />
            ) : isTranscribing || isThinking || turnState === 'thinking' ? (
              <div className="w-4 h-4 rounded-full border-2 border-slate-400 border-t-transparent animate-spin" />
            ) : (
              <Mic className="w-4 h-4" />
            )}
          </button>
          <button
            type="button"
            onClick={handleSendTyped}
            disabled={!typedText.trim() || Boolean(isTranscribing || isThinking)}
            aria-label="Send typed message to ORMA"
            className="px-4 py-2.5 rounded-xl bg-blue-600 hover:bg-blue-500 disabled:opacity-40 disabled:hover:bg-blue-600 text-white font-bold text-xs sm:text-sm flex items-center gap-1.5 transition-all shadow-md cursor-pointer shrink-0 active:scale-95"
          >
            <Send className="w-3.5 h-3.5" />
            <span className="hidden sm:inline">Send</span>
          </button>
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

      {/* 4. Calm Persistent Voice Control (Accessible when scrolled; does not overlap composer or mobile nav) */}
      <div className="fixed bottom-20 right-4 sm:bottom-8 sm:right-8 z-30 pointer-events-auto">
        {!isConversationMode ? (
          <button
            type="button"
            onClick={() => {
              if (onStartConversation) onStartConversation();
              else window.dispatchEvent(new CustomEvent('orma_toggle_voice'));
            }}
            disabled={Boolean(isTranscribing || isThinking || turnState === 'thinking')}
            aria-label={
              isListening || turnState === 'listening' 
                ? "Listening · Tap to Stop" 
                : isSpeaking || turnState === 'speaking' 
                ? "Tap to Interrupt" 
                : "Tap to Speak"
            }
            className={`flex items-center gap-2.5 px-4 py-3 rounded-full shadow-[0_10px_25px_rgba(0,0,0,0.6)] backdrop-blur-2xl border transition-all cursor-pointer select-none active:scale-95 ${
              isListening || turnState === 'listening'
                ? 'bg-slate-950/95 border-cyan-400 text-cyan-200 ring-2 ring-cyan-400/40'
                : isSpeaking || turnState === 'speaking'
                ? 'bg-slate-950/95 border-sky-400/70 text-sky-200 ring-2 ring-sky-400/30'
                : isTranscribing || isThinking || turnState === 'thinking'
                ? 'bg-slate-950/90 border-slate-700 text-slate-400 cursor-not-allowed opacity-75'
                : 'bg-slate-900/90 hover:bg-slate-800/95 border-cyan-500/40 hover:border-cyan-400 text-slate-100 hover:text-white ring-1 ring-white/10'
            }`}
          >
            {isListening || turnState === 'listening' ? (
              <>
                <span className="relative flex h-2.5 w-2.5">
                  <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-cyan-400 opacity-75" />
                  <span className="relative inline-flex rounded-full h-2.5 w-2.5 bg-cyan-500" />
                </span>
                <span className="text-xs sm:text-sm font-extrabold text-cyan-300">Listening · Tap to Stop</span>
              </>
            ) : isSpeaking || turnState === 'speaking' ? (
              <>
                <VolumeX className="w-3.5 h-3.5 text-sky-400 animate-pulse" />
                <span className="text-xs sm:text-sm font-extrabold text-sky-200">Tap to Interrupt</span>
              </>
            ) : isTranscribing || isThinking || turnState === 'thinking' ? (
              <>
                <div className="w-3.5 h-3.5 rounded-full border-2 border-cyan-400 border-t-transparent animate-spin" />
                <span className="text-xs sm:text-sm font-bold text-slate-300">Thinking...</span>
              </>
            ) : (
              <>
                <div className="w-5 h-5 rounded-full bg-gradient-to-tr from-cyan-500 to-blue-600 flex items-center justify-center text-white shadow-sm">
                  <Mic className="w-3 h-3" />
                </div>
                <span className="text-xs sm:text-sm font-extrabold text-slate-200">Tap to Speak</span>
              </>
            )}
          </button>
        ) : (
          <div className="flex items-center gap-2 p-1.5 sm:p-2 pl-3 sm:pl-3.5 rounded-full bg-slate-950/95 border-2 border-cyan-400/50 shadow-[0_10px_30px_rgba(0,0,0,0.7)] backdrop-blur-2xl">
            {/* Active Turn Status / Interrupt */}
            {isListening || turnState === 'listening' ? (
              <button
                type="button"
                onClick={() => window.dispatchEvent(new CustomEvent('orma_toggle_voice'))}
                className="flex items-center gap-2 cursor-pointer pr-2 select-none"
                aria-label="Listening · Tap to Stop"
              >
                <span className="relative flex h-2.5 w-2.5 shrink-0">
                  <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-cyan-400 opacity-75" />
                  <span className="relative inline-flex rounded-full h-2.5 w-2.5 bg-cyan-500" />
                </span>
                <span className="text-xs sm:text-sm font-extrabold text-cyan-300">
                  Listening · Tap to Stop
                </span>
              </button>
            ) : isSpeaking || turnState === 'speaking' ? (
              <button
                type="button"
                onClick={onInterrupt || onStopSpeaking}
                className="flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-sky-500/20 hover:bg-sky-500/35 border border-sky-400/40 text-sky-200 text-xs sm:text-sm font-bold transition-all cursor-pointer select-none"
                aria-label="Tap to Interrupt"
              >
                <VolumeX className="w-3.5 h-3.5 text-sky-400 animate-pulse" />
                <span>Tap to Interrupt</span>
              </button>
            ) : isTranscribing || isThinking || turnState === 'thinking' ? (
              <div className="flex items-center gap-2 pr-2">
                <div className="w-3.5 h-3.5 rounded-full border-2 border-blue-400 border-t-transparent animate-spin" />
                <span className="text-xs sm:text-sm font-bold text-slate-300">Thinking...</span>
              </div>
            ) : (
              <div className="flex items-center gap-2 pr-2">
                <span className="w-2.5 h-2.5 rounded-full bg-emerald-400 shrink-0" />
                <span className="text-xs sm:text-sm font-bold text-emerald-300">Your Turn</span>
              </div>
            )}

            {/* Stop Conversation Action */}
            {onEndConversation && (
              <button
                type="button"
                onClick={onEndConversation}
                className="flex items-center gap-1.5 px-3 py-1.5 sm:px-3.5 sm:py-2 rounded-full bg-red-500/20 hover:bg-red-500/35 border border-red-500/40 text-red-300 hover:text-white text-xs sm:text-sm font-extrabold transition-all cursor-pointer shadow-sm active:scale-95 select-none"
                aria-label="Stop Conversation"
              >
                <PhoneOff className="w-3.5 h-3.5 shrink-0" />
                <span>Stop Conversation</span>
              </button>
            )}
          </div>
        )}
      </div>

    </div>
  );
}

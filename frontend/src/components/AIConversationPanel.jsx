import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Loader2, Play } from 'lucide-react';
import { tts } from '../services/tts';
import AICompanionOrb from './AICompanionOrb';

export default function AIConversationPanel({ 
  isListening, 
  isSpeaking, 
  messages, 
  isTranscribing, 
  isThinking,
  startRecording,
  stopRecording,
  onClearConversation,
  onAskAgain,
  timeContext,
  user
}) {
  const [replayingMessageId, setReplayingMessageId] = useState(null);

  const handleReplay = (msgId, text) => {
    setReplayingMessageId(msgId);
    tts.speak(text, {
      onEnd: () => setReplayingMessageId(null),
      onError: () => setReplayingMessageId(null)
    });
  };

  const handleSuggestionClick = (text) => {
    if (onAskAgain) {
      onAskAgain(text);
    }
  };

  const lastUserMsg = [...messages].reverse().find(m => m.sender === 'user');
  const lastAiMsg = [...messages].reverse().find(m => m.sender === 'ai');
  const showEmptyState = messages.length === 0;

  // Maximum 4 chips
  const displaySuggestions = timeContext.suggestions.slice(0, 4);

  return (
    <div className="flex flex-col items-center justify-start relative w-full px-8 pt-8">
      
      {/* Caregiver Subject Banner */}
      {user?.role === 'caregiver' && (
        <motion.div 
          initial={{ opacity: 0, y: -10 }}
          animate={{ opacity: 1, y: 0 }}
          className="mb-6 bg-slate-800/80 border border-emerald-500/30 px-6 py-3 rounded-full flex items-center gap-3 shadow-lg"
        >
          <div className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse"></div>
          <span className="text-slate-300 text-sm font-medium">Currently Assisting:</span>
          <select className="bg-transparent text-emerald-400 font-bold focus:outline-none border-none cursor-pointer">
            <option value="john">John Thomas</option>
            <option value="mary">Mary Thomas</option>
          </select>
        </motion.div>
      )}

      {/* Hero Component: Voice Orb */}
      <motion.div 
        layout
        className="w-full flex justify-center items-center z-10"
        initial={{ scale: 0.95 }}
        animate={{ scale: 1, y: showEmptyState ? 0 : -40 }}
        transition={{ type: "spring", stiffness: 80, damping: 20 }}
      >
        <AICompanionOrb 
          onRecordingComplete={(blobUrl, blob) => {
            if (stopRecording) stopRecording(blobUrl, blob);
          }}
          isProcessing={isTranscribing || isThinking}
          isSpeaking={isSpeaking}
        />
      </motion.div>
      
      {/* Tap to Speak Label */}
      <AnimatePresence>
        {showEmptyState && !isListening && !isTranscribing && !isThinking && !isSpeaking && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="mt-6 text-slate-400 font-medium tracking-wide"
          >
            Tap to speak
          </motion.div>
        )}
      </AnimatePresence>

      {/* Empty State Suggestion Chips */}
      <AnimatePresence mode="wait">
        {showEmptyState && !isListening && !isTranscribing && !isThinking && !isSpeaking && (
          <motion.div 
            key="suggestions"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.95, filter: 'blur(4px)' }}
            className="flex flex-wrap justify-center items-center gap-3 max-w-2xl mt-6"
          >
            {displaySuggestions.map((suggestion, idx) => (
              <button
                key={idx}
                onClick={() => handleSuggestionClick(suggestion)}
                className="bg-slate-800/40 hover:bg-slate-700/60 backdrop-blur-xl border border-slate-600/30 text-slate-200 px-5 py-3 rounded-full text-[15px] font-medium transition-all duration-300 shadow-[0_8px_30px_rgb(0,0,0,0.12)] hover:shadow-[0_8px_30px_rgb(0,0,0,0.2)] hover:scale-[1.03] active:scale-[0.98]"
              >
                {suggestion}
              </button>
            ))}
          </motion.div>
        )}
      </AnimatePresence>

      {/* Last Interaction Card */}
      <AnimatePresence mode="wait">
        {!showEmptyState && (
          <motion.div
            key="last-interaction"
            initial={{ opacity: 0, y: 40, filter: 'blur(8px)' }}
            animate={{ opacity: 1, y: 0, filter: 'blur(0px)' }}
            transition={{ duration: 0.5, ease: "easeOut" }}
            className="w-full max-w-3xl orma-card p-8 mt-2 relative overflow-hidden rounded-[2.5rem] shadow-2xl border border-slate-700/40"
          >
            {/* Status Indicator Gradient Line */}
            <div className="absolute top-0 left-0 w-full h-1.5 bg-gradient-to-r from-cyan-400 via-blue-500 to-indigo-500 opacity-60"></div>
            
            <div className="flex justify-between items-center mb-6 pb-4 border-b border-slate-700/40">
              <h3 className="text-slate-400 font-semibold tracking-widest uppercase text-xs">Last Interaction</h3>
              <span className="text-slate-500 text-sm font-medium">{lastAiMsg?.time || lastUserMsg?.time}</span>
            </div>

            <div className="flex flex-col gap-8">
              {lastUserMsg && (
                <div className="flex justify-end">
                  <div className="bg-blue-600/10 text-blue-100 border border-blue-500/20 px-6 py-4 rounded-[1.5rem] rounded-tr-md max-w-[85%] text-xl font-medium shadow-inner">
                    "{lastUserMsg.text}"
                  </div>
                </div>
              )}

              {lastAiMsg && (
                <div className="flex justify-start">
                  <div className="bg-slate-800/60 text-white border border-slate-600/30 px-8 py-6 rounded-[1.5rem] rounded-tl-md max-w-[95%] text-2xl leading-relaxed shadow-lg font-light tracking-wide">
                    {lastAiMsg.text}
                  </div>
                </div>
              )}

              {(isTranscribing || isThinking) && (
                <div className="flex justify-start">
                   <div className="bg-slate-800/40 text-slate-300 border border-slate-600/30 px-6 py-4 rounded-[1.5rem] rounded-tl-md max-w-[80%] flex items-center gap-4 shadow-lg">
                     <Loader2 className="w-6 h-6 animate-spin text-indigo-400" />
                     <span className="text-lg font-medium">{isTranscribing ? "Listening carefully..." : "Processing response..."}</span>
                   </div>
                </div>
              )}
            </div>

            {/* Replay Action */}
            {lastAiMsg && !isSpeaking && !isTranscribing && !isThinking && (
              <div className="mt-8 pt-6 border-t border-slate-700/30 flex justify-end">
                <button
                  onClick={() => handleReplay(lastAiMsg.id, lastAiMsg.text)}
                  disabled={replayingMessageId === lastAiMsg.id}
                  className="flex items-center gap-3 text-cyan-400 hover:text-cyan-300 font-medium bg-cyan-500/10 hover:bg-cyan-500/20 px-6 py-3 rounded-full border border-cyan-500/20 transition-all duration-300 disabled:opacity-50 text-lg"
                >
                  <Play className={`w-5 h-5 ${replayingMessageId === lastAiMsg.id ? 'animate-pulse fill-current' : 'fill-current'}`} />
                  {replayingMessageId === lastAiMsg.id ? 'Playing...' : 'Replay Audio'}
                </button>
              </div>
            )}
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}

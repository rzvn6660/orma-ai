import React from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Mic, Volume2, VolumeX, PhoneOff, Brain } from 'lucide-react';

/**
 * FloatingTalkControl
 * 
 * Persistent floating Talk & Conversation Mode controller for ORMA AI.
 * Remains accessible across viewport scrolling on desktop and mobile,
 * respects safe-area insets, never overflows horizontally, and gives
 * elderly users instant, low-cognitive-load access to start, monitor,
 * interrupt, and end conversations.
 */
export default function FloatingTalkControl({
  isConversationMode = false,
  turnState = 'idle', // 'idle' | 'listening' | 'thinking' | 'speaking' | 'your_turn' | 'ended'
  isListening = false,
  isProcessing = false,
  isSpeaking = false,
  onStartConversation,
  onEndConversation,
  onInterrupt
}) {
  return (
    <aside 
      aria-label="ORMA Voice Controls"
      className="fixed z-40 right-3 sm:right-6 md:right-8 flex items-center justify-end max-w-[calc(100vw-1.5rem)] select-none pointer-events-none"
      style={{ bottom: 'calc(1.25rem + env(safe-area-inset-bottom, 0px))' }}
    >
      <div className="pointer-events-auto">
        <AnimatePresence mode="wait">
          {!isConversationMode ? (
            /* ============================================================ */
            /* INACTIVE: Large Friendly "Talk to ORMA" Floating Button      */
            /* ============================================================ */
            <motion.button
              key="inactive-talk"
              type="button"
              onClick={onStartConversation}
              whileHover={{ scale: 1.03 }}
              whileTap={{ scale: 0.96 }}
              aria-label="Start Conversation with ORMA"
              className="flex items-center gap-3 px-5 py-3.5 sm:px-6 sm:py-4 rounded-full bg-slate-900/90 hover:bg-slate-800/95 text-white font-extrabold text-sm sm:text-base border-2 border-cyan-400/50 shadow-[0_10px_35px_rgba(0,0,0,0.5),0_0_25px_rgba(34,211,238,0.25)] backdrop-blur-xl transition-all cursor-pointer group active:scale-95"
            >
              <div className="relative flex items-center justify-center w-8 h-8 rounded-full bg-cyan-500/20 text-cyan-300 shrink-0">
                <span className="absolute inset-0 rounded-full bg-cyan-400/30 animate-ping pointer-events-none" />
                <Mic className="w-4 h-4 sm:w-4.5 sm:h-4.5 text-cyan-300 relative z-10" />
              </div>
              <div className="flex flex-col items-start leading-tight text-left">
                <span className="font-extrabold tracking-tight text-white group-hover:text-cyan-200 transition-colors">
                  Talk to ORMA
                </span>
                <span className="text-[10px] text-cyan-300 font-medium hidden sm:inline">
                  Tap once to talk naturally
                </span>
              </div>
            </motion.button>
          ) : (
            /* ============================================================ */
            /* ACTIVE: Floating Live Conversation Cockpit                   */
            /* ============================================================ */
            <motion.div
              key="active-conversation"
              initial={{ opacity: 0, scale: 0.9, y: 12 }}
              animate={{ opacity: 1, scale: 1, y: 0 }}
              exit={{ opacity: 0, scale: 0.9, y: 12 }}
              transition={{ duration: 0.2 }}
              className="flex items-center gap-2 sm:gap-3 p-2 sm:p-2.5 pr-3 sm:pr-4 rounded-full bg-slate-950/95 border-2 border-cyan-400/60 shadow-[0_12px_40px_rgba(0,0,0,0.65),0_0_30px_rgba(34,211,238,0.3)] backdrop-blur-2xl max-w-full"
            >
              {/* Live Status Indicator */}
              <div className="flex items-center gap-2 pl-2 sm:pl-3">
                {isProcessing || turnState === 'thinking' ? (
                  <>
                    <Brain className="w-4 h-4 text-blue-300 animate-pulse shrink-0" />
                    <span className="text-xs sm:text-sm font-bold text-blue-300 tracking-tight">
                      Thinking...
                    </span>
                  </>
                ) : isSpeaking || turnState === 'speaking' ? (
                  <>
                    <Volume2 className="w-4 h-4 text-sky-400 animate-pulse shrink-0" />
                    <span className="text-xs sm:text-sm font-bold text-white tracking-tight">
                      Speaking...
                    </span>
                  </>
                ) : isListening || turnState === 'listening' ? (
                  <>
                    <span className="relative flex h-3 w-3 shrink-0">
                      <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-cyan-400 opacity-75" />
                      <span className="relative inline-flex rounded-full h-3 w-3 bg-cyan-500" />
                    </span>
                    <span className="text-xs sm:text-sm font-bold text-cyan-300 tracking-tight">
                      Listening...
                    </span>
                  </>
                ) : (
                  <>
                    <span className="w-2.5 h-2.5 rounded-full bg-emerald-400 shrink-0" />
                    <span className="text-xs sm:text-sm font-bold text-emerald-300 tracking-tight">
                      Your Turn
                    </span>
                  </>
                )}
              </div>

              {/* Interrupt Button: Visible while ORMA is speaking */}
              {(isSpeaking || turnState === 'speaking') && onInterrupt && (
                <button
                  type="button"
                  onClick={onInterrupt}
                  aria-label="Interrupt ORMA speaking"
                  className="px-3 py-1.5 rounded-full bg-sky-500/25 hover:bg-sky-500/40 text-sky-200 border border-sky-400/40 text-xs font-bold transition-colors cursor-pointer flex items-center gap-1.5 shadow-sm active:scale-95"
                >
                  <VolumeX className="w-3.5 h-3.5" />
                  <span>Interrupt</span>
                </button>
              )}

              {/* End Conversation Button */}
              {onEndConversation && (
                <button
                  type="button"
                  onClick={onEndConversation}
                  aria-label="End continuous conversation"
                  className="px-3 sm:px-4 py-1.5 rounded-full bg-red-500/20 hover:bg-red-500/35 text-red-300 hover:text-white border border-red-500/40 text-xs font-extrabold transition-all cursor-pointer flex items-center gap-1.5 shadow-sm active:scale-95"
                >
                  <PhoneOff className="w-3.5 h-3.5" />
                  <span>End</span>
                </button>
              )}
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    </aside>
  );
}

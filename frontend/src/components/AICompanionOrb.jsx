import { useEffect, useState, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Mic, Square, Loader2, Volume2, VolumeX } from 'lucide-react';
import { useReactMediaRecorder } from 'react-media-recorder';
import { tts } from '../services/tts';
import { useWakeWord } from '../hooks/useWakeWord';

/**
 * AI Companion Orb
 * Continuous listening wake-word enabled interface for Orma AI.
 */
export default function AICompanionOrb({ onRecordingComplete, isProcessing, onStatusChange, isSpeaking }) {
  const [wakeWordActive, setWakeWordActive] = useState(false);
  
  // Audio recording hook
  const { status, startRecording, stopRecording, error } = useReactMediaRecorder({
    audio: true,
    onStart: () => console.log("Companion Recording Started"),
    onStop: (blobUrl, blob) => {
      console.log("Companion Recording Stopped");
      if (onRecordingComplete && blob) {
        onRecordingComplete(blobUrl, blob);
      }
      setWakeWordActive(false); // Go back to wake-word listening after sending
    },
  });

  const isListening = status === 'recording';

  const handleWakeWordDetected = () => {
    tts.stop(); // Stop any ongoing speech if user interrupts via wake word
    setWakeWordActive(true);
    startRecording();
  };

  const { 
    isListeningForWakeWord, 
    isWakeWordUnavailable, 
    companionMode, 
    setCompanionMode, 
    pauseWakeWord, 
    resumeWakeWord,
    debugInfo
  } = useWakeWord(handleWakeWordDetected);

  // Wake-word mode is active and persistent

  // Pause wake-word listening when actively interacting with the AI
  useEffect(() => {
    if (isListening || isProcessing || isSpeaking) {
      pauseWakeWord();
    } else {
      resumeWakeWord();
    }
  }, [isListening, isProcessing, isSpeaking]);

  const handleManualToggle = () => {
    if (isSpeaking) {
      tts.stop(); // Interruption
    }
    if (isListening) {
      stopRecording();
    } else {
      handleWakeWordDetected();
    }
  };

  useEffect(() => {
    if (onStatusChange) {
      onStatusChange(isListening);
    }
  }, [isListening, onStatusChange]);

  return (
    <div className="flex flex-col items-center justify-center p-8 relative overflow-hidden w-full h-full min-h-[300px]">
      {/* Main Orb */}
      <div className="relative z-10 flex flex-col items-center gap-10 mt-4">
        
        <button
          onClick={handleManualToggle}
          className="relative group outline-none"
        >
          {/* Animated Glow Layers */}
          <div
            className={`absolute inset-0 rounded-full blur-3xl transition-all duration-1000 ${
              isSpeaking
                ? 'bg-fuchsia-500/60 scale-[2.0] animate-pulse'
                : isListening
                ? 'bg-blue-500/60 scale-[1.8] animate-pulse'
                : isProcessing
                ? 'bg-indigo-500/40 scale-150 animate-spin-slow'
                : 'bg-cyan-500/20 scale-125 group-hover:bg-cyan-500/40 group-hover:scale-150'
            }`}
          />
          
          <div
            className={`absolute inset-0 rounded-full blur-xl transition-all duration-700 ${
              isSpeaking
                ? 'bg-pink-400/80 scale-[1.5]'
                : isListening
                ? 'bg-cyan-400/80 scale-[1.3]'
                : 'bg-transparent'
            }`}
          />

          {/* Core Orb Surface */}
          <div
            className={`relative flex items-center justify-center w-64 h-64 rounded-full backdrop-blur-xl transition-all duration-500 z-10 border-2 shadow-[0_0_50px_rgba(0,0,0,0.5)] ${
              isSpeaking
                ? 'bg-gradient-to-br from-fuchsia-600/90 to-pink-500/90 border-pink-400 scale-110 shadow-[0_0_60px_rgba(236,72,153,0.6)]'
                : isListening
                ? 'bg-gradient-to-br from-blue-600/90 to-cyan-500/90 border-cyan-400 scale-110 shadow-[0_0_60px_rgba(34,211,238,0.6)]'
                : isProcessing
                ? 'bg-gradient-to-br from-slate-800/90 to-indigo-900/90 border-indigo-500 shadow-[0_0_40px_rgba(99,102,241,0.4)]'
                : 'bg-gradient-to-br from-slate-800/80 to-slate-900/80 border-slate-600 group-hover:border-cyan-500/50'
            }`}
          >
            {isProcessing ? (
              <Loader2 className="w-16 h-16 text-indigo-300 animate-spin" />
            ) : isSpeaking ? (
              <Volume2 className="w-20 h-20 text-white animate-pulse" />
            ) : isListening ? (
              <Square className="w-16 h-16 text-white fill-white/20 transition-transform hover:scale-90" />
            ) : (
              <div className="w-full h-full rounded-full bg-[radial-gradient(ellipse_at_center,_var(--tw-gradient-stops))] from-cyan-400/20 via-transparent to-transparent flex items-center justify-center">
                 <Mic className="w-20 h-20 text-cyan-400 transition-transform group-hover:scale-110" />
              </div>
            )}
          </div>
        </button>

        {/* Status Text & Visualizer */}
        <div className="h-16 flex flex-col items-center justify-center gap-4 w-full">
          {isProcessing ? (
            <p className="text-indigo-300 font-medium animate-pulse tracking-wide">Thinking...</p>
          ) : isListening ? (
            <div className="flex flex-col items-center gap-3">
              <div className="flex items-end justify-center h-8 gap-1.5">
                {[...Array(16)].map((_, i) => (
                  <motion.div
                    key={i}
                    animate={{ height: ['20%', '100%', '20%'] }}
                    transition={{
                      duration: 0.75,
                      repeat: Infinity,
                      delay: 0.15,
                      ease: "easeInOut"
                    }}
                    className="w-1.5 bg-cyan-400 rounded-full"
                  />
                ))}
              </div>
              <p className="text-cyan-300 font-medium tracking-wide">Listening to you...</p>
            </div>
          ) : isSpeaking ? (
             <div className="flex flex-col items-center gap-3">
              <div className="flex items-end justify-center h-8 gap-1.5">
                {[...Array(16)].map((_, i) => (
                  <motion.div
                    key={i}
                    animate={{ height: ['30%', '100%', '30%'] }}
                    transition={{
                      duration: 0.45,
                      repeat: Infinity,
                      delay: 0.1,
                      ease: "easeInOut"
                    }}
                    className="w-1.5 bg-pink-400 rounded-full shadow-[0_0_10px_rgba(244,114,182,0.8)]"
                  />
                ))}
              </div>
              <p className="text-pink-300 font-medium tracking-wide">Tap to interrupt</p>
            </div>
          ) : error ? (
            <p className="text-red-400 font-medium tracking-wide text-sm text-center max-w-xs">
              Mic Access Denied: Please allow microphone permission.
            </p>
          ) : (
            <div className="text-center mt-6">
              <p className="text-slate-300 font-medium tracking-wide text-xl drop-shadow-sm">
                Tap to Speak
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

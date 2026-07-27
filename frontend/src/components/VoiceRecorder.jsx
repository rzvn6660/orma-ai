import { useEffect, useState, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Mic, Square, Loader2 } from 'lucide-react';
import { useReactMediaRecorder } from 'react-media-recorder';

/**
 * A premium, reusable voice recording component.
 * Encapsulates media recording, timer logic, and futuristic waveform UI.
 */
export default function VoiceRecorder({ onRecordingComplete, isProcessing, onStatusChange, isSpeaking }) {
  const [duration, setDuration] = useState(0);
  const timerRef = useRef(null);

  const handleStart = () => {
    console.log("Recording Started");
  };

  const handleStop = (blobUrl, blob) => {
    console.log("Recording Stopped");
    clearInterval(timerRef.current);
    setDuration(0);
    
    if (blob) {
      console.log("Audio Blob Created");
      console.log("Media Blob URL:", blobUrl);
      console.log("Blob Size (bytes):", blob.size);
    }
    
    if (onRecordingComplete && blob) {
      onRecordingComplete(blobUrl, blob);
    }
  };

  const { status, startRecording, stopRecording, error } = useReactMediaRecorder({
    audio: true,
    onStart: handleStart,
    onStop: handleStop,
  });

  const isListening = status === 'recording';

  // Notify parent of status changes (useful for updating other UI panels)
  useEffect(() => {
    if (onStatusChange) {
      onStatusChange(isListening);
    }
  }, [isListening, onStatusChange]);

  // Handle timer
  useEffect(() => {
    if (isListening) {
      timerRef.current = setInterval(() => {
        setDuration((prev) => prev + 1);
      }, 1000);
    } else {
      clearInterval(timerRef.current);
      setDuration(0);
    }
    return () => clearInterval(timerRef.current);
  }, [isListening]);

  const formatTime = (seconds) => {
    const m = Math.floor(seconds / 60).toString().padStart(2, '0');
    const s = (seconds % 60).toString().padStart(2, '0');
    return `${m}:${s}`;
  };

  const handleToggle = () => {
    if (isListening) {
      stopRecording();
    } else {
      startRecording();
    }
  };

  return (
    <div className="flex flex-col items-center justify-center p-8 orma-card relative overflow-hidden w-full h-full">
      {/* Background animated pulses */}
      <AnimatePresence>
        {isListening && (
          <motion.div
            initial={{ opacity: 0, scale: 0.8 }}
            animate={{ opacity: 1, scale: 1.5 }}
            exit={{ opacity: 0, scale: 0.8 }}
            transition={{ duration: 1.5, repeat: Infinity, repeatType: 'reverse' }}
            className="absolute inset-0 bg-blue-500/10 rounded-full blur-3xl pointer-events-none"
          />
        )}
        {isSpeaking && !isListening && (
          <motion.div
            initial={{ opacity: 0, scale: 0.8 }}
            animate={{ opacity: 1, scale: 1.5 }}
            exit={{ opacity: 0, scale: 0.8 }}
            transition={{ duration: 1.0, repeat: Infinity, repeatType: 'reverse' }}
            className="absolute inset-0 bg-pink-500/10 rounded-full blur-3xl pointer-events-none"
          />
        )}
      </AnimatePresence>

      <div className="relative z-10 flex flex-col items-center gap-8">
        {/* Timer */}
        <div className="h-8">
          <AnimatePresence>
            {isListening && (
              <motion.span
                initial={{ opacity: 0, y: -10 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -10 }}
                className="text-blue-400 font-mono text-2xl tracking-wider font-bold drop-shadow-[0_0_10px_rgba(96,165,250,0.5)]"
              >
                {formatTime(duration)}
              </motion.span>
            )}
          </AnimatePresence>
        </div>

        {/* Mic Button */}
        <button
          onClick={handleToggle}
          disabled={isProcessing}
          className="relative group outline-none"
        >
          {/* Animated Glow */}
          <div
            className={`absolute inset-0 rounded-full blur-2xl transition-all duration-700 ${
              isListening
                ? 'bg-blue-500/60 scale-150 animate-pulse'
                : 'bg-indigo-500/20 group-hover:bg-blue-500/40'
            }`}
          />

          {/* Button Surface */}
          <div
            className={`relative flex items-center justify-center w-28 h-28 rounded-full shadow-[0_0_40px_rgba(0,0,0,0.3)] backdrop-blur-xl transition-all duration-300 z-10 border-2 ${
              isListening
                ? 'bg-slate-900/80 border-blue-400 scale-110 shadow-[0_0_30px_rgba(96,165,250,0.4)]'
                : isProcessing
                ? 'bg-slate-800/80 border-slate-700'
                : 'bg-slate-800/60 border-slate-600 hover:border-blue-500/50'
            }`}
          >
            {isProcessing ? (
              <Loader2 className="w-12 h-12 text-slate-300 animate-spin" />
            ) : isListening ? (
              <Square className="w-10 h-10 text-blue-400 fill-blue-400/20 transition-transform hover:scale-90" />
            ) : (
              <Mic className="w-12 h-12 text-blue-400 transition-transform group-hover:scale-110" />
            )}
          </div>
        </button>

        {/* Status Text & Waveform */}
        <div className="h-16 flex flex-col items-center justify-center gap-4 w-full">
          {isProcessing ? (
            <p className="text-slate-400 font-medium animate-pulse">Processing audio...</p>
          ) : isListening ? (
            <div className="flex items-end justify-center h-10 gap-1.5">
              {[...Array(12)].map((_, i) => (
                <motion.div
                  key={i}
                  animate={{ height: ['20%', '100%', '20%'] }}
                  transition={{
                    duration: 0.8,
                    repeat: Infinity,
                    delay: 0.15,
                    ease: "easeInOut"
                  }}
                  className="w-1.5 bg-gradient-to-t from-blue-600 to-cyan-400 rounded-full"
                />
              ))}
            </div>
          ) : isSpeaking ? (
            <div className="flex items-end justify-center h-10 gap-1.5">
              {[...Array(12)].map((_, i) => (
                <motion.div
                  key={i}
                  animate={{ height: ['20%', '100%', '20%'] }}
                  transition={{
                    duration: 0.6,
                    repeat: Infinity,
                    delay: 0.1,
                    ease: "easeInOut"
                  }}
                  className="w-1.5 bg-gradient-to-t from-purple-500 to-pink-400 rounded-full"
                />
              ))}
            </div>
          ) : error ? (
            <p className="text-red-400 font-medium tracking-wide">Mic Access Denied: Please allow microphone permission.</p>
          ) : (
            <p className="text-slate-400 font-medium tracking-wide">Tap to speak with Orma AI</p>
          )}
        </div>
      </div>
    </div>
  );
}

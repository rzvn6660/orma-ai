import { useEffect, useState, useRef, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Mic, Square, Volume2, AlertCircle, RefreshCw, Brain } from 'lucide-react';
import { useReactMediaRecorder } from 'react-media-recorder';
import { tts } from '../services/tts';
import { useWakeWord } from '../hooks/useWakeWord';
import OrmaShaderOrb from './OrmaShaderOrb';
import LiveWaveform from './ui/LiveWaveform';

/**
 * ORMA Voice Powered Companion Orb
 * Primary central voice visualization combining WebGL OrmaShaderOrb,
 * live microphone RMS analysis, calm Live Waveform, and elderly-friendly interaction.
 */
export default function AICompanionOrb({ 
  onRecordingComplete, 
  isProcessing, 
  onStatusChange, 
  isSpeaking,
  onStopSpeaking,
  externalError
}) {
  const [wakeWordActive, setWakeWordActive] = useState(false);
  const [audioLevel, setAudioLevel] = useState(0);

  // Audio analysis refs
  const audioContextRef = useRef(null);
  const analyserRef = useRef(null);
  const micSourceRef = useRef(null);
  const animationFrameRef = useRef(null);
  const activeStreamRef = useRef(null);

  // Stop microphone analysis & clean up Web Audio resources
  const stopAudioAnalysis = useCallback(() => {
    if (animationFrameRef.current) {
      cancelAnimationFrame(animationFrameRef.current);
      animationFrameRef.current = null;
    }
    if (micSourceRef.current) {
      micSourceRef.current.disconnect();
      micSourceRef.current = null;
    }
    if (analyserRef.current) {
      analyserRef.current.disconnect();
      analyserRef.current = null;
    }
    if (audioContextRef.current && audioContextRef.current.state !== 'closed') {
      audioContextRef.current.close().catch(() => {});
      audioContextRef.current = null;
    }
    if (activeStreamRef.current) {
      activeStreamRef.current.getTracks().forEach(track => track.stop());
      activeStreamRef.current = null;
    }
    setAudioLevel(0);
  }, []);

  // Start real microphone analysis loop
  const startAudioAnalysis = useCallback(async () => {
    try {
      stopAudioAnalysis();
      const stream = await navigator.mediaDevices.getUserMedia({ 
        audio: { echoCancellation: true, noiseSuppression: true } 
      });
      activeStreamRef.current = stream;

      const AudioCtx = window.AudioContext || window.webkitAudioContext;
      if (!AudioCtx) return;

      const audioCtx = new AudioCtx();
      if (audioCtx.state === 'suspended') {
        await audioCtx.resume();
      }
      audioContextRef.current = audioCtx;

      const analyser = audioCtx.createAnalyser();
      analyser.fftSize = 256;
      analyser.smoothingTimeConstant = 0.4;
      analyserRef.current = analyser;

      const micSource = audioCtx.createMediaStreamSource(stream);
      micSource.connect(analyser);
      micSourceRef.current = micSource;

      const dataArray = new Uint8Array(analyser.frequencyBinCount);

      const checkLevel = () => {
        if (!analyserRef.current) return;
        analyserRef.current.getByteFrequencyData(dataArray);

        let sum = 0;
        for (let i = 0; i < dataArray.length; i++) {
          const val = dataArray[i] / 255;
          sum += val * val;
        }
        const rms = Math.sqrt(sum / dataArray.length);
        const normalized = Math.min(rms * 2.8, 1.0);
        setAudioLevel(normalized);

        animationFrameRef.current = requestAnimationFrame(checkLevel);
      };

      animationFrameRef.current = requestAnimationFrame(checkLevel);
    } catch (err) {
      console.warn('Real-time audio analysis not available:', err);
    }
  }, [stopAudioAnalysis]);

  // Audio recording hook
  const { status, startRecording, stopRecording, error } = useReactMediaRecorder({
    audio: true,
    onStart: () => {
      startAudioAnalysis();
    },
    onStop: (blobUrl, blob) => {
      stopAudioAnalysis();
      if (onRecordingComplete && blob) {
        onRecordingComplete(blobUrl, blob);
      }
      setWakeWordActive(false);
    },
  });

  const isListening = status === 'recording';

  // Cleanup on component unmount
  useEffect(() => {
    return () => {
      stopAudioAnalysis();
    };
  }, [stopAudioAnalysis]);

  const handleWakeWordDetected = () => {
    tts.stop();
    if (onStopSpeaking) onStopSpeaking();
    setWakeWordActive(true);
    startRecording();
  };

  const { 
    pauseWakeWord, 
    resumeWakeWord,
  } = useWakeWord(handleWakeWordDetected);

  useEffect(() => {
    if (isListening || isProcessing || isSpeaking) {
      pauseWakeWord();
    } else {
      resumeWakeWord();
    }
  }, [isListening, isProcessing, isSpeaking, pauseWakeWord, resumeWakeWord]);

  const handleManualToggle = () => {
    if (isSpeaking) {
      tts.stop();
      if (onStopSpeaking) onStopSpeaking();
    } else if (isListening) {
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

  // Contextual error resolution (never exposes technical traces or codes)
  const getErrorMessage = () => {
    if (externalError) {
      if (typeof externalError === 'string') return externalError;
      if (externalError.type === 'network') return "Sorry, I couldn't connect to the server.";
      if (externalError.type === 'transcription') return "Sorry, I couldn't hear you. Try again.";
      return "Sorry, I couldn't complete that request.";
    }
    if (error) {
      const errStr = String(error).toLowerCase();
      if (errStr.includes('permission') || errStr.includes('denied') || errStr.includes('allowed')) {
        return "Sorry, I couldn't access the microphone.";
      }
      if (errStr.includes('not_readable') || errStr.includes('device') || errStr.includes('audio')) {
        return "Sorry, I couldn't access the microphone.";
      }
      return "Sorry, I couldn't access the microphone.";
    }
    return null;
  };

  const activeErrorMessage = getErrorMessage();

  // Determine current active visual state
  const currentState = isListening 
    ? 'listening' 
    : isProcessing 
    ? 'thinking' 
    : isSpeaking 
    ? 'speaking' 
    : activeErrorMessage 
    ? 'error' 
    : 'idle';

  return (
    <div className="flex flex-col items-center justify-center w-full">
      {/* Orb Button Container */}
      <div className="relative flex flex-col items-center">
        
        <button
          type="button"
          onClick={handleManualToggle}
          aria-label={
            isSpeaking 
              ? 'Interrupt ORMA speaking' 
              : isListening 
              ? 'Stop recording voice' 
              : 'Tap to speak to ORMA'
          }
          className="relative group outline-none cursor-pointer focus:ring-4 focus:ring-blue-500/40 rounded-full"
        >
          {/* 1. Subtle Outer Ambient Glow Ring */}
          <div
            className={`absolute inset-0 rounded-full blur-3xl transition-all duration-700 pointer-events-none ${
              isSpeaking
                ? 'bg-blue-500/30 scale-125'
                : isListening
                ? 'bg-cyan-400/35 scale-125'
                : isProcessing
                ? 'bg-blue-600/25 scale-110'
                : 'bg-cyan-500/15 scale-105 group-hover:bg-cyan-500/25'
            }`}
          />
          
          {/* 2. Concentric Acoustic Ripple Ring */}
          {(isListening || isSpeaking) && (
            <motion.div
              initial={{ scale: 0.95, opacity: 0.8 }}
              animate={{ scale: 1.25, opacity: 0 }}
              transition={{ duration: 1.6, repeat: Infinity, ease: "easeOut" }}
              className={`absolute inset-0 rounded-full border-2 pointer-events-none ${
                isListening ? 'border-cyan-400/50' : 'border-blue-400/50'
              }`}
            />
          )}

          {/* 3. Core WebGL Shader Orb Container with Liquid Glass Rim */}
          <div
            className={`relative flex items-center justify-center w-48 h-48 sm:w-56 sm:h-56 rounded-full backdrop-blur-2xl transition-all duration-500 z-10 border shadow-2xl overflow-hidden ${
              isSpeaking
                ? 'border-blue-400/60 shadow-[0_0_40px_rgba(59,130,246,0.35)]'
                : isListening
                ? 'border-cyan-400/60 shadow-[0_0_45px_rgba(34,211,238,0.35)]'
                : isProcessing
                ? 'border-blue-500/40 shadow-[0_0_30px_rgba(59,130,246,0.25)]'
                : 'border-white/15 group-hover:border-cyan-400/50 shadow-[0_15px_35px_rgba(0,0,0,0.6)]'
            }`}
          >
            {/* Embedded WebGL Shader Layer */}
            <OrmaShaderOrb
              state={currentState}
              audioLevel={audioLevel}
              isSpeaking={isSpeaking}
              isProcessing={isProcessing}
              className="absolute inset-0 z-0"
            />

            {/* Specular Glass Overlay */}
            <div className="absolute inset-0 rounded-full bg-gradient-to-b from-white/15 via-transparent to-black/30 pointer-events-none z-10" />

            {/* Inner Center Icon Overlay (Strictly Centered) */}
            <div className="absolute inset-0 flex items-center justify-center z-20 pointer-events-none">
              <div className={`flex items-center justify-center w-16 h-16 rounded-full bg-slate-950/40 backdrop-blur-md border border-white/10 shadow-lg transition-all ${
                isProcessing ? 'border-blue-400/40 shadow-[0_0_20px_rgba(59,130,246,0.25)]' : ''
              }`}>
                {isProcessing ? (
                  <Brain className="w-7 h-7 text-blue-200 animate-pulse" />
                ) : isSpeaking ? (
                  <Volume2 className="w-8 h-8 text-cyan-300" />
                ) : isListening ? (
                  <Square className="w-7 h-7 text-cyan-300 fill-cyan-300/30" />
                ) : (
                  <Mic className="w-8 h-8 text-cyan-400 transition-transform group-hover:scale-110" />
                )}
              </div>
            </div>
          </div>
        </button>

        {/* Dynamic Voice State Headline, Subtitle & Live Waveform */}
        <div className="flex flex-col items-center justify-center gap-1.5 mt-5 text-center min-h-[72px]">
          {isProcessing ? (
            <motion.div 
              initial={{ opacity: 0, y: 4 }} 
              animate={{ opacity: 1, y: 0 }} 
              className="flex flex-col items-center gap-1"
            >
              <p className="text-base sm:text-lg font-extrabold text-blue-300 tracking-tight">
                Thinking...
              </p>
              <p className="text-xs sm:text-sm text-slate-400 font-medium">
                Finding the best answer for you.
              </p>
            </motion.div>
          ) : isListening ? (
            <motion.div 
              initial={{ opacity: 0, y: 4 }} 
              animate={{ opacity: 1, y: 0 }} 
              className="flex flex-col items-center gap-1"
            >
              {/* Calm Live Waveform below orb */}
              <LiveWaveform 
                active={true} 
                mode="listening" 
                audioLevel={audioLevel} 
                color="#22d3ee" 
                barCount={20}
                className="mb-1"
              />
              <p className="text-base sm:text-lg font-extrabold text-cyan-300 tracking-tight">
                Listening...
              </p>
              <p className="text-xs sm:text-sm text-slate-400 font-medium">
                Tell me what you need.
              </p>
            </motion.div>
          ) : isSpeaking ? (
            <motion.div 
              initial={{ opacity: 0, y: 4 }} 
              animate={{ opacity: 1, y: 0 }} 
              className="flex flex-col items-center gap-1"
            >
              {/* Speech Output Waveform below orb */}
              <LiveWaveform 
                active={true} 
                mode="speaking" 
                color="#38bdf8" 
                barCount={20}
                className="mb-1"
              />
              <p className="text-base sm:text-lg font-extrabold text-white tracking-tight">
                ORMA is speaking...
              </p>
              <p className="text-xs sm:text-sm text-cyan-400 font-medium">
                Tap the orb to interrupt
              </p>
            </motion.div>
          ) : activeErrorMessage ? (
            <motion.div 
              initial={{ opacity: 0, y: 4 }} 
              animate={{ opacity: 1, y: 0 }} 
              className="flex flex-col items-center gap-1 text-red-400"
            >
              <p className="text-sm font-bold flex items-center gap-1.5">
                <AlertCircle className="w-4 h-4" /> {activeErrorMessage}
              </p>
              <p className="text-xs text-slate-400">
                Please allow microphone access and try again.
              </p>
              <button
                type="button"
                onClick={handleManualToggle}
                className="text-xs font-bold underline hover:text-red-300 cursor-pointer flex items-center gap-1 mt-1 px-3 py-1 rounded-lg bg-red-500/10 border border-red-500/20"
              >
                <RefreshCw className="w-3 h-3" />
                <span>Try again</span>
              </button>
            </motion.div>
          ) : (
            <motion.div 
              initial={{ opacity: 0, y: 4 }} 
              animate={{ opacity: 1, y: 0 }} 
              className="flex flex-col items-center gap-1"
            >
              <p className="text-lg sm:text-xl font-extrabold text-white tracking-tight">
                Tap to speak
              </p>
              <p className="text-xs sm:text-sm text-slate-400 font-medium max-w-sm">
                Ask ORMA about your medicines, appointments, or health.
              </p>
            </motion.div>
          )}
        </div>

      </div>
    </div>
  );
}

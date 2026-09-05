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
  externalError,
  isConversationMode = false,
  turnState = 'idle',
  onStartConversation,
  onEndConversation,
  onInterrupt,
  listenTrigger = 0
}) {
  const [wakeWordActive, setWakeWordActive] = useState(false);
  const [audioLevel, setAudioLevel] = useState(0);

  // Audio analysis refs
  const audioContextRef = useRef(null);
  const analyserRef = useRef(null);
  const micSourceRef = useRef(null);
  const animationFrameRef = useRef(null);
  const streamRef = useRef(null);
  const connectedTrackIdRef = useRef(null);

  // Continuous conversation mode VAD & readiness refs
  const speechDetectedRef = useRef(false);
  const lastSpeechTimeRef = useRef(0);
  const isConversationModeRef = useRef(isConversationMode);
  useEffect(() => {
    isConversationModeRef.current = isConversationMode;
  }, [isConversationMode]);
  const lastProcessedTriggerRef = useRef(0);
  const pendingStartRef = useRef(false);

  // Safely stop all underlying microphone tracks to release hardware
  const cleanupStream = useCallback(() => {
    if (streamRef.current) {
      try {
        streamRef.current.getTracks().forEach(track => {
          try {
            track.stop();
          } catch (_e) {
            // no-op
          }
        });
      } catch (_e) {
        // no-op
      }
      streamRef.current = null;
    }
    connectedTrackIdRef.current = null;
  }, []);

  // Stop audio analysis animation loop & disconnect nodes WITHOUT closing live tracks
  const stopAudioAnalysis = useCallback(() => {
    if (animationFrameRef.current) {
      cancelAnimationFrame(animationFrameRef.current);
      animationFrameRef.current = null;
    }
    if (micSourceRef.current) {
      try {
        micSourceRef.current.disconnect();
      } catch (_e) {
        // no-op
      }
      micSourceRef.current = null;
    }
    if (analyserRef.current) {
      try {
        analyserRef.current.disconnect();
      } catch (_e) {
        // no-op
      }
      analyserRef.current = null;
    }
    setAudioLevel(0);
  }, []);

  // Single persistent MediaRecorder hook across conversation turns
  const { status, startRecording, stopRecording, error, previewAudioStream } = useReactMediaRecorder({
    audio: { echoCancellation: true, noiseSuppression: true },
    stopStreamsOnStop: false, // Keep underlying MediaStream alive across conversation turns
    onStop: (blobUrl, blob) => {
      stopAudioAnalysis();
      if (!isConversationModeRef.current) {
        cleanupStream();
      }
      if (onRecordingComplete && blob) {
        onRecordingComplete(blobUrl, blob);
      }
      setWakeWordActive(false);
    },
  });

  // Connect real-time Web Audio RMS analysis & VAD to the provided MediaStream (zero extra getUserMedia)
  const startAudioAnalysis = useCallback((stream) => {
    if (!stream) return;
    try {
      if (animationFrameRef.current) {
        cancelAnimationFrame(animationFrameRef.current);
        animationFrameRef.current = null;
      }

      const AudioCtx = window.AudioContext || window.webkitAudioContext;
      if (!AudioCtx) return;

      let audioCtx = audioContextRef.current;
      if (!audioCtx || audioCtx.state === 'closed') {
        audioCtx = new AudioCtx();
        audioContextRef.current = audioCtx;
      }

      if (audioCtx.state === 'suspended') {
        audioCtx.resume().catch((_e) => {
          // no-op
        });
      }

      if (micSourceRef.current) {
        try {
          micSourceRef.current.disconnect();
        } catch (_e) {
          // no-op
        }
        micSourceRef.current = null;
      }
      if (analyserRef.current) {
        try {
          analyserRef.current.disconnect();
        } catch (_e) {
          // no-op
        }
        analyserRef.current = null;
      }

      const analyser = audioCtx.createAnalyser();
      analyser.fftSize = 256;
      analyser.smoothingTimeConstant = 0.4;
      analyserRef.current = analyser;

      const micSource = audioCtx.createMediaStreamSource(stream);
      micSource.connect(analyser);
      micSourceRef.current = micSource;

      const dataArray = new Uint8Array(analyser.frequencyBinCount);
      speechDetectedRef.current = false;
      lastSpeechTimeRef.current = Date.now();

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

        // Continuous Conversation Mode Voice Activity Detection (VAD)
        if (isConversationModeRef.current) {
          const now = Date.now();
          if (normalized > 0.07) {
            speechDetectedRef.current = true;
            lastSpeechTimeRef.current = now;
          } else if (speechDetectedRef.current) {
            // Speech was detected, check if pause duration threshold reached (1.7s)
            const silenceElapsed = now - lastSpeechTimeRef.current;
            if (silenceElapsed > 1700) {
              speechDetectedRef.current = false;
              stopRecording();
              return;
            }
          }
        }

        animationFrameRef.current = requestAnimationFrame(checkLevel);
      };

      animationFrameRef.current = requestAnimationFrame(checkLevel);
    } catch (err) {
      console.warn('[AICompanionOrb] Real-time audio analysis error:', err);
    }
  }, [stopRecording]);

  const isListening = status === 'recording';

  // Keep stream reference updated for session cleanup
  useEffect(() => {
    if (previewAudioStream) {
      streamRef.current = previewAudioStream;
    }
  }, [previewAudioStream]);

  // Connect AudioContext analysis & VAD whenever recording starts with an active track
  useEffect(() => {
    if (status === 'recording' && previewAudioStream) {
      const audioTracks = previewAudioStream.getAudioTracks();
      const firstTrack = audioTracks[0];
      if (firstTrack && firstTrack.readyState === 'live') {
        if (connectedTrackIdRef.current !== firstTrack.id) {
          connectedTrackIdRef.current = firstTrack.id;
          startAudioAnalysis(previewAudioStream);
        }
      }
    } else if (status !== 'recording') {
      connectedTrackIdRef.current = null;
      stopAudioAnalysis();
    }
  }, [status, previewAudioStream, startAudioAnalysis, stopAudioAnalysis]);

  // React to listenTrigger from parent with recorder readiness guard
  useEffect(() => {
    if (listenTrigger > 0 && isConversationMode) {
      if (listenTrigger > lastProcessedTriggerRef.current) {
        lastProcessedTriggerRef.current = listenTrigger;
        speechDetectedRef.current = false;
        lastSpeechTimeRef.current = Date.now();

        if (status === 'recording') {
          return;
        }

        if (status === 'stopping') {
          // Recorder transitioning: queue start once stopped/idle
          pendingStartRef.current = true;
        } else {
          // Recorder ready: start immediately
          pendingStartRef.current = false;
          startRecording();
        }
      }
    }
  }, [listenTrigger, isConversationMode, status, startRecording]);

  // Execute queued start as soon as the recorder finishes stopping
  useEffect(() => {
    if (pendingStartRef.current && (status === 'stopped' || status === 'idle') && isConversationModeRef.current) {
      pendingStartRef.current = false;
      startRecording();
    }
  }, [status, startRecording]);

  // Stop recording and release microphone resources when conversation mode ends
  useEffect(() => {
    if (!isConversationMode) {
      pendingStartRef.current = false;
      lastProcessedTriggerRef.current = 0;
      if (status === 'recording') {
        stopRecording();
      }
      stopAudioAnalysis();
      cleanupStream();
      if (audioContextRef.current && audioContextRef.current.state !== 'closed') {
        audioContextRef.current.close().catch(() => {});
        audioContextRef.current = null;
      }
    }
  }, [isConversationMode, status, stopRecording, stopAudioAnalysis, cleanupStream]);

  // Safety timeout: max utterance 25 seconds
  useEffect(() => {
    let safetyTimer = null;
    if (isListening) {
      safetyTimer = setTimeout(() => {
        if (status === 'recording') {
          stopRecording();
        }
      }, 25000);
    }
    return () => {
      if (safetyTimer) clearTimeout(safetyTimer);
    };
  }, [isListening, status, stopRecording]);

  // Component unmount cleanup
  useEffect(() => {
    return () => {
      pendingStartRef.current = false;
      stopAudioAnalysis();
      cleanupStream();
      if (audioContextRef.current && audioContextRef.current.state !== 'closed') {
        audioContextRef.current.close().catch(() => {});
        audioContextRef.current = null;
      }
    };
  }, [stopAudioAnalysis, cleanupStream]);

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
      if (onInterrupt) {
        onInterrupt();
      } else {
        tts.stop();
        if (onStopSpeaking) onStopSpeaking();
      }
    } else if (isListening) {
      speechDetectedRef.current = false;
      stopRecording();
    } else {
      if (onStartConversation) {
        onStartConversation();
      } else {
        handleWakeWordDetected();
      }
    }
  };

  useEffect(() => {
    const handleVoiceEvent = () => {
      handleManualToggle();
    };
    window.addEventListener('orma_toggle_voice', handleVoiceEvent);
    return () => {
      window.removeEventListener('orma_toggle_voice', handleVoiceEvent);
    };
  }, [isSpeaking, isListening, onInterrupt, onStopSpeaking, onStartConversation, stopRecording, startRecording]);

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
        return "Microphone access was denied. You can still type your questions below.";
      }
      if (errStr.includes('not_readable') || errStr.includes('device') || errStr.includes('audio')) {
        return "Microphone device is not readable. Please check your settings.";
      }
      return "Microphone access is unavailable.";
    }
    return null;
  };

  const activeErrorMessage = getErrorMessage();

  // Only terminate conversation mode for genuinely unrecoverable permission denial
  useEffect(() => {
    if (error && isConversationMode) {
      const errStr = String(error).toLowerCase();
      if (errStr.includes('permission') || errStr.includes('denied') || errStr.includes('notallowed')) {
        if (typeof navigator !== 'undefined' && navigator.permissions && navigator.permissions.query) {
          navigator.permissions.query({ name: 'microphone' }).then(permissionStatus => {
            if (permissionStatus.state === 'denied') {
              if (onEndConversation) onEndConversation();
            } else {
              console.warn('[AICompanionOrb] Transient recorder issue; permission state is:', permissionStatus.state);
            }
          }).catch(() => {
            console.warn('[AICompanionOrb] Recorder error:', error);
          });
        }
      }
    }
  }, [error, isConversationMode, onEndConversation]);

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
            className={`relative flex items-center justify-center w-40 h-40 sm:w-48 sm:h-48 md:w-52 md:h-52 rounded-full backdrop-blur-2xl transition-all duration-500 z-10 border shadow-2xl overflow-hidden ${
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
          ) : isConversationMode ? (
            <motion.div
              initial={{ opacity: 0, y: 4 }}
              animate={{ opacity: 1, y: 0 }}
              className="flex flex-col items-center gap-1"
            >
              <p className="text-lg sm:text-xl font-extrabold text-cyan-300 tracking-tight">
                {turnState === 'your_turn' ? "Your Turn" : "Conversation Active"}
              </p>
              <p className="text-xs sm:text-sm text-slate-300 font-medium max-w-sm">
                Speak anytime — ORMA is listening.
              </p>
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

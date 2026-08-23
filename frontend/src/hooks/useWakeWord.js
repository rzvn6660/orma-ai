import { useState, useEffect, useRef } from 'react';

export const ENABLE_WAKE_WORD = false;

export function useWakeWord(onWakeWordDetected) {
  const [isListeningForWakeWord, setIsListeningForWakeWord] = useState(false);
  const [isWakeWordUnavailable, setIsWakeWordUnavailable] = useState(false);
  const [companionMode, setCompanionMode] = useState(true);
  const [engineLoaded, setEngineLoaded] = useState(false);
  const [detectionCount, setDetectionCount] = useState(0);
  const [audioStreaming, setAudioStreaming] = useState(false);
  const [micActive, setMicActive] = useState(false);
  const [debugState, setDebugState] = useState({
    confidence: 0,
    threshold: 0.5,
    lastChunkSize: 0,
    lastResult: 'no detection',
    modelName: 'faster-whisper (tiny.en)'
  });
  const wsRef = useRef(null);
  const audioContextRef = useRef(null);
  const streamRef = useRef(null);
  const processorRef = useRef(null);

  useEffect(() => {
    if (!companionMode || !ENABLE_WAKE_WORD) {
      stopListening();
      return;
    }

    startListening();

    return () => {
      stopListening();
    };
  }, [companionMode]);

  async function startListening() {
    try {
      if (wsRef.current?.readyState === WebSocket.OPEN) return;
      
      const baseApi = import.meta.env.VITE_API_BASE_URL || (typeof window !== 'undefined' ? window.location.origin : 'http://localhost:8000');
      const wsPrefix = baseApi.startsWith('https') ? baseApi.replace(/^https/, 'wss') : baseApi.replace(/^http/, 'ws');
      const wsUrl = `${wsPrefix}/api/wakeword/ws`;
        
      wsRef.current = new WebSocket(wsUrl);
      
      wsRef.current.onopen = async () => {
        console.log("WakeWord WebSocket Connected");
        setIsWakeWordUnavailable(false);
        setIsListeningForWakeWord(true);
        streamRef.current = await navigator.mediaDevices.getUserMedia({ audio: true });
        
        // OpenWakeWord needs 16kHz audio
        audioContextRef.current = new (window.AudioContext || window.webkitAudioContext)({ sampleRate: 16000 });
        const source = audioContextRef.current.createMediaStreamSource(streamRef.current);
        setMicActive(true);
        
        processorRef.current = audioContextRef.current.createScriptProcessor(4096, 1, 1);
        
        processorRef.current.onaudioprocess = (e) => {
          const inputData = e.inputBuffer.getChannelData(0);
          const pcmData = new Int16Array(inputData.length);
          for (let i = 0; i < inputData.length; i++) {
            // Convert Float32 to Int16
            pcmData[i] = Math.max(-1, Math.min(1, inputData[i])) * 32767;
          }
          if (wsRef.current?.readyState === WebSocket.OPEN && !window._ormaSendingPaused) {
            wsRef.current.send(pcmData.buffer);
          }
        };

        source.connect(processorRef.current);
        processorRef.current.connect(audioContextRef.current.destination);
        setAudioStreaming(true);
      };

      wsRef.current.onmessage = (event) => {
        const data = JSON.parse(event.data);
        if (data.event === 'wake_word_detected') {
          console.log("Wake word detected by OpenWakeWord backend!");
          setDetectionCount(prev => prev + 1);
          if (onWakeWordDetected) {
            onWakeWordDetected();
          }
        } else if (data.event === 'engine_ready') {
          setEngineLoaded(data.loaded);
          if (!data.loaded) setIsWakeWordUnavailable(true);
        } else if (data.event === 'wake_word_status') {
          setDebugState({
            confidence: data.confidence,
            threshold: data.threshold,
            lastChunkSize: data.chunk_size,
            lastResult: data.result,
            modelName: data.model_name
          });
          setEngineLoaded(data.engine_loaded);
          if (!data.engine_loaded) setIsWakeWordUnavailable(true);
        }
      };

      wsRef.current.onerror = (error) => {
        console.error("WakeWord WebSocket error:", error);
        setIsWakeWordUnavailable(true);
      };

      wsRef.current.onclose = () => {
        console.log("WakeWord WebSocket Disconnected");
        setIsListeningForWakeWord(false);
        setAudioStreaming(false);
        setMicActive(false);
        setEngineLoaded(false);
      };

    } catch (err) {
      console.error("Wake word setup failed, falling back to push-to-talk", err);
      setIsListeningForWakeWord(false);
      setIsWakeWordUnavailable(true);
    }
  };

  function stopListening() {
    setIsListeningForWakeWord(false);
    if (processorRef.current) {
      processorRef.current.disconnect();
      processorRef.current = null;
    }
    if (audioContextRef.current) {
      audioContextRef.current.close();
      audioContextRef.current = null;
    }
    if (streamRef.current) {
      streamRef.current.getTracks().forEach(track => track.stop());
      streamRef.current = null;
    }
    if (wsRef.current) {
      wsRef.current.close();
      wsRef.current = null;
    }
  };

  // Allow manual pause/resume if needed
  const pauseWakeWord = () => {
    setIsListeningForWakeWord(false);
    window._ormaSendingPaused = true;
  };

  const resumeWakeWord = () => {
    window._ormaSendingPaused = false;
    if (!ENABLE_WAKE_WORD) return;
    if (companionMode && streamRef.current && audioContextRef.current && processorRef.current) {
       setIsListeningForWakeWord(true);
       try {
         const source = audioContextRef.current.createMediaStreamSource(streamRef.current);
         source.connect(processorRef.current);
         processorRef.current.connect(audioContextRef.current.destination);
       } catch (e) {
         // Might already be connected
       }
    } else if (companionMode) {
      startListening();
    }
  };

  return { 
    isListeningForWakeWord, 
    isWakeWordUnavailable, 
    companionMode, 
    setCompanionMode, 
    pauseWakeWord, 
    resumeWakeWord,
    debugInfo: {
      wsConnected: isListeningForWakeWord,
      micActive,
      audioStreaming,
      engineLoaded,
      detectionCount,
      ...debugState
    }
  };
}

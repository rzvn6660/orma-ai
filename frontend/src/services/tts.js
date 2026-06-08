/**
 * Text-to-Speech (TTS) Service
 * 
 * Modular service for AI voice responses.
 * Currently uses browser's SpeechSynthesis API, structured to be easily 
 * swappable with backend TTS like Coqui/Piper in the future.
 */

class TTSService {
  constructor() {
    this.synth = window.speechSynthesis;
    this.voice = null;
    this.init();
  }

  init() {
    // Load voices and select a natural sounding English voice
    const loadVoices = () => {
      const voices = this.synth.getVoices();
      if (voices.length > 0) {
        // Try to find a premium/natural sounding female voice
        this.voice = voices.find(v => v.name.includes('Google') || v.name.includes('Premium') || v.name.includes('Natural')) || voices[0];
      }
    };

    loadVoices();
    if (this.synth.onvoiceschanged !== undefined) {
      this.synth.onvoiceschanged = loadVoices;
    }
  }

  /**
   * Speak a text string.
   * @param {string} text - The text to speak.
   * @param {Object} callbacks - Optional callbacks { onStart, onEnd, onError }
   */
  speak(text, callbacks = {}) {
    this.stop(); // Stop any ongoing speech

    if (!text) return;

    const utterance = new SpeechSynthesisUtterance(text);
    
    if (this.voice) {
      utterance.voice = this.voice;
    }
    
    utterance.rate = 1.0;
    utterance.pitch = 1.0;
    utterance.volume = 1.0;

    if (callbacks.onStart) {
      utterance.onstart = callbacks.onStart;
    }
    
    if (callbacks.onEnd) {
      utterance.onend = callbacks.onEnd;
    }
    
    if (callbacks.onError) {
      utterance.onerror = callbacks.onError;
    }

    this.synth.speak(utterance);
  }

  /**
   * Stop current speech playback.
   */
  stop() {
    if (this.synth.speaking) {
      this.synth.cancel();
    }
  }
}

export const tts = new TTSService();

/**
 * Text-to-Speech (TTS) Service
 * 
 * Modular service for AI voice responses.
 */

class TTSService {
  constructor() {
    this.synth = window.speechSynthesis;
    this.voice = null;
    this.volume = this._getStoredVolume();
    this.init();
  }

  _getStoredVolume() {
    const vol = localStorage.getItem('orma_tts_volume') || 'High';
    return this.mapVolume(vol);
  }

  mapVolume(level) {
    switch(level) {
      case 'Low': return 0.3;
      case 'Medium': return 0.6;
      case 'High': return 1.0;
      case 'Maximum': return 1.0; // Max allowed by Web Speech API
      default: return 1.0;
    }
  }

  setVolumeLevel(level) {
    localStorage.setItem('orma_tts_volume', level);
    this.volume = this.mapVolume(level);
  }

  getVolumeLevel() {
    return localStorage.getItem('orma_tts_volume') || 'High';
  }

  init() {
    const loadVoices = () => {
      this.voices = this.synth.getVoices();
    };
    loadVoices();
    if (this.synth.onvoiceschanged !== undefined) {
      this.synth.onvoiceschanged = loadVoices;
    }
  }

  isMalayalam(text) {
    return /[\u0D00-\u0D7F]/.test(text);
  }

  getBestVoice(text) {
    if (!this.voices || this.voices.length === 0) return null;
    
    // Ensure spoken language strictly matches the displayed text script
    if (this.isMalayalam(text)) {
      return this.voices.find(v => v.lang.includes('ml')) || 
             this.voices.find(v => v.name.toLowerCase().includes('malayalam')) || 
             this.voices[0];
    }
    
    // Default English
    return this.voices.find(v => v.lang.includes('en') && (v.name.includes('Google') || v.name.includes('Premium') || v.name.includes('Natural'))) || 
           this.voices.find(v => v.lang.includes('en')) || 
           this.voices[0];
  }

  speak(text, callbacks = {}) {
    this.stop(); 
    if (!text) return;

    // Store last assistant message locally
    localStorage.setItem('orma_last_tts_message', text);

    const utterance = new SpeechSynthesisUtterance(text);
    const selectedVoice = this.getBestVoice(text);
    if (selectedVoice) {
      utterance.voice = selectedVoice;
    }
    
    utterance.rate = 1.0;
    utterance.pitch = 1.0;
    
    // Refresh volume in case it was changed in another tab or just before
    this.volume = this._getStoredVolume();
    utterance.volume = this.volume;

    if (callbacks.onStart) utterance.onstart = callbacks.onStart;
    if (callbacks.onEnd) utterance.onend = callbacks.onEnd;
    if (callbacks.onError) utterance.onerror = callbacks.onError;

    this.synth.speak(utterance);
  }

  stop() {
    if (this.synth.speaking) {
      this.synth.cancel();
    }
  }
}

export const tts = new TTSService();


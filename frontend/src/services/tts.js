/**
 * Text-to-Speech (TTS) Service
 * 
 * Modular service for AI voice responses with multilingual support and truthful voice resolution.
 */

class TTSService {
  constructor() {
    this.synth = typeof window !== 'undefined' ? window.speechSynthesis : null;
    this.voices = [];
    this.voiceCache = {};
    this.volume = this._getStoredVolume();
    this.init();
  }

  _getStoredVolume() {
    try {
      const vol = localStorage.getItem('orma_tts_volume') || 'High';
      return this.mapVolume(vol);
    } catch {
      return 1.0;
    }
  }

  mapVolume(level) {
    switch(level) {
      case 'Low': return 0.3;
      case 'Medium': return 0.6;
      case 'High': return 1.0;
      case 'Maximum': return 1.0;
      default: return 1.0;
    }
  }

  setVolumeLevel(level) {
    try {
      localStorage.setItem('orma_tts_volume', level);
    } catch {}
    this.volume = this.mapVolume(level);
  }

  getVolumeLevel() {
    try {
      return localStorage.getItem('orma_tts_volume') || 'High';
    } catch {
      return 'High';
    }
  }

  init() {
    if (!this.synth) return;
    const loadVoices = () => {
      try {
        this.voices = this.synth.getVoices();
        this.voiceCache = {};
      } catch (err) {
        console.warn("[TTS WARN] Failed to get voices:", err);
      }
    };
    loadVoices();
    if (this.synth.onvoiceschanged !== undefined) {
      this.synth.onvoiceschanged = loadVoices;
    }
  }

  getBestVoice(text, targetLangCode = null) {
    if (!this.voices || this.voices.length === 0) {
      if (this.synth) {
        try {
          this.voices = this.synth.getVoices();
        } catch (_) {}
      }
    }

    if (!this.voices || this.voices.length === 0) return { voice: null, isNative: false };

    const cacheKey = `${targetLangCode || 'auto'}_${(text || '').substring(0, 30)}`;
    if (this.voiceCache[cacheKey]) {
      return this.voiceCache[cacheKey];
    }

    let result = null;
    
    // 1. Explicit target language code (e.g., ml-IN, hi-IN, ar-SA, ta-IN, te-IN, kn-IN, en-IN)
    if (targetLangCode) {
      const cleanLang = targetLangCode.toLowerCase();
      const primaryLang = cleanLang.split('-')[0];

      // Exact match
      let match = this.voices.find(v => v.lang.toLowerCase().replace('_', '-') === cleanLang);
      if (match) result = { voice: match, isNative: true };

      // Prefix match
      if (!result) {
        match = this.voices.find(v => v.lang.toLowerCase().startsWith(primaryLang));
        if (match) result = { voice: match, isNative: true };
      }

      // Name match
      if (!result) {
        const langNames = {
          'ml': ['malayalam', 'മലയാളം'],
          'hi': ['hindi', 'हिन्दी'],
          'ar': ['arabic', 'العربية'],
          'ta': ['tamil', 'தமிழ்'],
          'te': ['telugu', 'తెలుగు'],
          'kn': ['kannada', 'ಕನ್ನಡ'],
          'en': ['english']
        };
        const searchNames = langNames[primaryLang] || [];
        match = this.voices.find(v => searchNames.some(name => v.name.toLowerCase().includes(name)));
        if (match) result = { voice: match, isNative: true };
      }
    }
    
    // 2. Script detection fallback
    if (!result) {
      if (/[\u0D00-\u0D7F]/.test(text)) { // Malayalam
        const v = this.voices.find(v => v.lang.toLowerCase().includes('ml')) || 
                  this.voices.find(v => v.name.toLowerCase().includes('malayalam'));
        if (v) result = { voice: v, isNative: true };
      } else if (/[\u0900-\u097F]/.test(text)) { // Hindi
        const v = this.voices.find(v => v.lang.toLowerCase().includes('hi')) || 
                  this.voices.find(v => v.name.toLowerCase().includes('hindi'));
        if (v) result = { voice: v, isNative: true };
      } else if (/[\u0600-\u06FF]/.test(text)) { // Arabic
        const v = this.voices.find(v => v.lang.toLowerCase().includes('ar')) || 
                  this.voices.find(v => v.name.toLowerCase().includes('arabic'));
        if (v) result = { voice: v, isNative: true };
      } else if (/[\u0B80-\u0BFF]/.test(text)) { // Tamil
        const v = this.voices.find(v => v.lang.toLowerCase().includes('ta')) || 
                  this.voices.find(v => v.name.toLowerCase().includes('tamil'));
        if (v) result = { voice: v, isNative: true };
      } else if (/[\u0C00-\u0C7F]/.test(text)) { // Telugu
        const v = this.voices.find(v => v.lang.toLowerCase().includes('te')) || 
                  this.voices.find(v => v.name.toLowerCase().includes('telugu'));
        if (v) result = { voice: v, isNative: true };
      } else if (/[\u0C80-\u0CFF]/.test(text)) { // Kannada
        const v = this.voices.find(v => v.lang.toLowerCase().includes('kn')) || 
                  this.voices.find(v => v.name.toLowerCase().includes('kannada'));
        if (v) result = { voice: v, isNative: true };
      }
    }

    // 3. System default fallback
    if (!result) {
      const defaultVoice = this.voices.find(v => v.lang.toLowerCase().includes('en') && (v.name.includes('Google') || v.name.includes('Natural') || v.name.includes('Premium'))) || 
                           this.voices.find(v => v.lang.toLowerCase().includes('en')) || 
                           this.voices[0];

      result = { voice: defaultVoice, isNative: false };
    }

    this.voiceCache[cacheKey] = result;
    return result;
  }

  getAvailableReminderVoice(targetLangCode = "en-IN") {
    if (!this.voices || this.voices.length === 0) {
      if (this.synth) {
        try {
          this.voices = this.synth.getVoices();
        } catch (_) {}
      }
    }

    const voiceResult = this.getBestVoice("", targetLangCode);
    const voice = voiceResult.voice;
    const isNative = Boolean(voiceResult.isNative);

    return {
      requestedLanguage: targetLangCode,
      voiceFound: isNative,
      voiceName: voice ? voice.name : "System Default",
      voiceLocale: voice ? voice.lang : "en-US",
      fallbackUsed: !isNative
    };
  }

  speak(text, options = {}) {
    try {
      this.stop(); 
      if (!text) return;

      const callbacks = typeof options === 'function' ? { onEnd: options } : options;
      let targetLangCode = callbacks.langCode || null;

      // Auto-detect native script if language was not provided or set to auto
      if (!targetLangCode || targetLangCode === 'auto') {
        if (/[\u0D00-\u0D7F]/.test(text)) {
          targetLangCode = 'ml-IN';
        } else if (/[\u0900-\u097F]/.test(text)) {
          targetLangCode = 'hi-IN';
        } else if (/[\u0600-\u06FF]/.test(text)) {
          targetLangCode = 'ar-SA';
        } else if (/[\u0B80-\u0BFF]/.test(text)) {
          targetLangCode = 'ta-IN';
        } else if (/[\u0C00-\u0C7F]/.test(text)) {
          targetLangCode = 'te-IN';
        } else if (/[\u0C80-\u0CFF]/.test(text)) {
          targetLangCode = 'kn-IN';
        } else {
          targetLangCode = 'en-IN';
        }
      }

      try {
        localStorage.setItem('orma_last_tts_message', text);
      } catch {}

      if (!this.synth || typeof SpeechSynthesisUtterance === 'undefined') {
        console.warn("[TTS] SpeechSynthesis not available in this browser/environment.");
        if (callbacks.onError) callbacks.onError(new Error("Speech synthesis unavailable"));
        return;
      }

      const voiceResult = this.getBestVoice(text, targetLangCode);

      // Truthful TTS Enforcement: If a non-English language is requested and no native voice is installed,
      // do NOT speak using an unrelated English voice. Refrain from audio speech while keeping text localized.
      if (targetLangCode && !targetLangCode.toLowerCase().startsWith('en') && !voiceResult.isNative) {
        console.info(`[TTS Truthful Speech] Native voice for '${targetLangCode}' is not installed on this browser. Speech audio bypassed to prevent speaking unrelated language voice.`);
        if (callbacks.onEnd) callbacks.onEnd();
        return;
      }

      const utterance = new SpeechSynthesisUtterance(text);

      if (voiceResult.voice) {
        utterance.voice = voiceResult.voice;
      }
      
      if (targetLangCode) {
        utterance.lang = targetLangCode;
      }

      utterance.rate = 0.95; // Slower rate for elderly clarity
      utterance.pitch = 1.0;
      
      this.volume = this._getStoredVolume();
      utterance.volume = this.volume;

      if (callbacks.onStart) utterance.onstart = callbacks.onStart;
      if (callbacks.onEnd) utterance.onend = callbacks.onEnd;
      if (callbacks.onError) utterance.onerror = callbacks.onError;

      this.synth.speak(utterance);
    } catch (err) {
      console.warn("[TTS ERROR]:", err);
      if (options.onError) options.onError(err);
    }
  }

  stop() {
    try {
      if (this.synth) {
        this.synth.cancel();
      }
    } catch (err) {
      console.warn("[TTS STOP ERROR]:", err);
    }
  }
}

export const tts = new TTSService();

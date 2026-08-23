/**
 * Centralized ORMA Main Voice AI Conversation Languages Configuration
 * 
 * Defines supported languages for ORMA AI main voice & chat conversations.
 * Auto-detect is the default.
 */

export const VOICE_LANGUAGES = [
  {
    code: "auto",
    name: "Auto-detect",
    nativeName: "Auto-detect",
    flag: "🌐",
    locale: "auto",
    direction: "ltr",
    description: "ORMA detects the language of your speech automatically."
  },
  {
    code: "en-IN",
    name: "English",
    nativeName: "English",
    flag: "🇬🇧",
    locale: "en-IN",
    direction: "ltr"
  },
  {
    code: "ml-IN",
    name: "Malayalam",
    nativeName: "മലയാളം",
    flag: "🇮🇳",
    locale: "ml-IN",
    direction: "ltr"
  },
  {
    code: "hi-IN",
    name: "Hindi",
    nativeName: "हिन्दी",
    flag: "🇮🇳",
    locale: "hi-IN",
    direction: "ltr"
  },
  {
    code: "ar-SA",
    name: "Arabic",
    nativeName: "العربية",
    flag: "🇦🇪",
    locale: "ar-SA",
    direction: "rtl"
  },
  {
    code: "ta-IN",
    name: "Tamil",
    nativeName: "தமிழ்",
    flag: "🇮🇳",
    locale: "ta-IN",
    direction: "ltr"
  },
  {
    code: "te-IN",
    name: "Telugu",
    nativeName: "తెలుగు",
    flag: "🇮🇳",
    locale: "te-IN",
    direction: "ltr"
  },
  {
    code: "kn-IN",
    name: "Kannada",
    nativeName: "ಕನ್ನಡ",
    flag: "🇮🇳",
    locale: "kn-IN",
    direction: "ltr"
  }
];

export const DEFAULT_VOICE_LANGUAGE = "auto";

export const getVoiceLanguageConfig = (code) => {
  if (!code || code === 'auto') return VOICE_LANGUAGES[0];
  const normalized = code.trim().toLowerCase();
  return (
    VOICE_LANGUAGES.find(
      (lang) => lang.code.toLowerCase() === normalized || lang.locale.toLowerCase() === normalized
    ) ||
    VOICE_LANGUAGES.find((lang) => lang.code.toLowerCase().startsWith(normalized.split('-')[0])) ||
    VOICE_LANGUAGES[0]
  );
};

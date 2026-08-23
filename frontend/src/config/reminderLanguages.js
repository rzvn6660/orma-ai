/**
 * Centralized Medication Reminder Languages Configuration
 * 
 * Defines supported languages for ORMA medication spoken alerts & reminder text.
 */

export const REMINDER_LANGUAGES = [
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

export const DEFAULT_REMINDER_LANGUAGE = "en-IN";

export const getLanguageConfig = (code) => {
  if (!code) return REMINDER_LANGUAGES[0];
  const normalized = code.trim().toLowerCase();
  return (
    REMINDER_LANGUAGES.find(
      (lang) => lang.code.toLowerCase() === normalized || lang.locale.toLowerCase() === normalized
    ) ||
    REMINDER_LANGUAGES.find((lang) => lang.code.toLowerCase().startsWith(normalized.split('-')[0])) ||
    REMINDER_LANGUAGES[0]
  );
};

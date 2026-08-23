/**
 * Centralized Medication Reminder Localization Layer
 * 
 * Manages localized strings for medication reminder visual modals, voice alerts,
 * browser notifications, voice confirmations, and snooze messages.
 * 
 * Medication names and dosage numbers remain exact without alteration.
 */

import { getLanguageConfig, DEFAULT_REMINDER_LANGUAGE } from '../config/reminderLanguages';

const LOCALIZED_STRINGS = {
  "en-IN": {
    greetingMorning: "Good Morning",
    greetingAfternoon: "Good Afternoon",
    greetingEvening: "Good Evening",
    reminderTitle: "Medication Reminder",
    reminderHeadline: "It's time to take your medicine.",
    haveYouTaken: "Have you taken your medicine?",
    markedTaken: "Got it. {medName} has been marked as taken.",
    snoozedConfirmation: "Your reminder has been snoozed for {mins} minutes.",
    voicePrompt: "Tell ORMA when you've taken it.",
    voiceListening: "🔵 Listening...",
    voiceChecking: "Checking...",
    voiceError: "Didn't catch confirmation for {medName}.",
    buttonTookIt: "✓ I TOOK IT",
    buttonConfirmVoice: "🎙 Confirm by Voice",
    buttonSnoozeMins: "Snooze {mins} minutes",
    buttonRemindLater: "Remind me later",
    skipConfirmTitle: "Skip this dose?",
    skipConfirmSubtext: "This will record the medication as skipped for today.",
    buttonConfirmSkip: "Confirm Skip",
    buttonCancel: "Cancel",
    browserTitle: "💊 Medication Reminder",
    browserBody: "It's time to take {medName} {dosage}.",
    scheduledFor: "Scheduled for {time}",
    progressOf: "{current} of {total}",
    allDoneTitle: "✓ ALL DONE",
    allDoneSubtext: "All medicines handled",
    allDoneMessage: "You're all set for this reminder session. Great job!",
    buttonDone: "Done",
    tryAgain: "Try Again",
    connectionError: "Couldn't confirm the medication.",
    purposeLabel: "Purpose: "
  },
  "ml-IN": {
    greetingMorning: "സുപ്രഭാതം",
    greetingAfternoon: "നമസ്കാരം",
    greetingEvening: "ശുഭ സായാഹ്നം",
    reminderTitle: "മരുന്ന് ഓർമ്മപ്പെടുത്തൽ",
    reminderHeadline: "നിങ്ങളുടെ മരുന്ന് കഴിക്കാനുള്ള സമയമാണ്.",
    haveYouTaken: "നിങ്ങൾ മരുന്ന് കഴിച്ചോ?",
    markedTaken: "മനസ്സിലായി. {medName} കഴിച്ചതായി രേഖപ്പെടുത്തി.",
    snoozedConfirmation: "മരുന്നിന്റെ ഓർമ്മപ്പെടുത്തൽ {mins} മിനിറ്റത്തേക്ക് മാറ്റിവെച്ചു.",
    voicePrompt: "മരുന്ന് കഴിച്ചാൽ ORMAയോട് പറയൂ.",
    voiceListening: "🔵 ശ്രദ്ധിക്കുന്നു...",
    voiceChecking: "പരിശോധിക്കുന്നു...",
    voiceError: "{medName} കഴിച്ചതായി സ്ഥിരീകരിക്കാൻ സാധിച്ചില്ല.",
    buttonTookIt: "✓ ഞാൻ കഴിച്ചു",
    buttonConfirmVoice: "🎙 ശബ്ദത്തിലൂടെ സ്ഥിരീകരിക്കൂ",
    buttonSnoozeMins: "{mins} മിനിറ്റത്തേക്ക് മാറ്റിവെക്കൂ",
    buttonRemindLater: "പിന്നീട് ഓർമ്മിപ്പിക്കുക",
    skipConfirmTitle: "ഈ മരുന്ന് ഒഴിവാക്കണോ?",
    skipConfirmSubtext: "ഇത് ഇന്നത്തെ മരുന്ന് ഒഴിവാക്കിയതായി രേഖപ്പെടുത്തും.",
    buttonConfirmSkip: "ഒഴിവാക്കുക",
    buttonCancel: "റദ്ദാക്കുക",
    browserTitle: "💊 മരുന്ന് ഓർമ്മപ്പെടുത്തൽ",
    browserBody: "{medName} {dosage} കഴിക്കാനുള്ള സമയമാണ്.",
    scheduledFor: "സമയക്രമം: {time}",
    progressOf: "{total} ൽ {current}",
    allDoneTitle: "✓ എല്ലാം പൂർത്തിയായി",
    allDoneSubtext: "എല്ലാ മരുന്നുകളും രേഖപ്പെടുത്തി",
    allDoneMessage: "ഈ സമയത്തെ മരുന്നുകളെല്ലാം കഴിച്ചു കഴിഞ്ഞു. മികച്ച പ്രവർത്തനം!",
    buttonDone: "പൂർത്തിയായി",
    tryAgain: "വീണ്ടും ശ്രമിക്കുക",
    connectionError: "മരുന്ന് സ്ഥിരീകരിക്കാൻ സാധിച്ചില്ല.",
    purposeLabel: "ഉദ്ദേശ്യം: "
  },
  "hi-IN": {
    greetingMorning: "शुभ प्रभात",
    greetingAfternoon: "नमस्कार",
    greetingEvening: "शुभ संध्या",
    reminderTitle: "दवा की याद दिलाना",
    reminderHeadline: "आपकी दवा लेने का समय हो गया है।",
    haveYouTaken: "क्या आपने अपनी दवा ले ली है?",
    markedTaken: "ठीक है। {medName} को ली गई दवा के रूप में दर्ज किया गया है।",
    snoozedConfirmation: "दवा की याद दिलाने का समय {mins} मिनट के लिए बढ़ा दिया गया है।",
    voicePrompt: "दवा लेने के बाद ORMA को बताएं।",
    voiceListening: "🔵 सुन रहा हूँ...",
    voiceChecking: "जाँच हो रही है...",
    voiceError: "{medName} की पुष्टि नहीं हो सकी।",
    buttonTookIt: "✓ मैंने ले ली",
    buttonConfirmVoice: "🎙 आवाज से पुष्टि करें",
    buttonSnoozeMins: "{mins} मिनट के लिए आगे बढ़ाएं",
    buttonRemindLater: "बाद में याद दिलाएं",
    skipConfirmTitle: "क्या इस खुराक को छोड़ना चाहते हैं?",
    skipConfirmSubtext: "यह आज के लिए दवा छूटी हुई दर्ज करेगा।",
    buttonConfirmSkip: "छोड़ने की पुष्टि करें",
    buttonCancel: "रद्द करें",
    browserTitle: "💊 दवा की याद दिलाना",
    browserBody: "{medName} {dosage} लेने का समय हो गया है।",
    scheduledFor: "निर्धारित समय: {time}",
    progressOf: "{total} में से {current}",
    allDoneTitle: "✓ सब पूरा हुआ",
    allDoneSubtext: "सभी दवाएं दर्ज की गईं",
    allDoneMessage: "इस समय की सभी दवाएं पूरी हो गई हैं। बहुत बढ़िया!",
    buttonDone: "पूर्ण",
    tryAgain: "फिर से प्रयास करें",
    connectionError: "दवा की पुष्टि नहीं हो सकी।",
    purposeLabel: "उद्देश्य: "
  },
  "ar-SA": {
    greetingMorning: "صباح الخير",
    greetingAfternoon: "مساء الخير",
    greetingEvening: "مساء الخير",
    reminderTitle: "تذكير الدواء",
    reminderHeadline: "حان وقت تناول الدواء.",
    haveYouTaken: "هل تناولت دواءك؟",
    markedTaken: "حسنًا. تم تسجيل {medName} على أنه تم تناوله.",
    snoozedConfirmation: "تم تأجيل تذكير الدواء لمدة {mins} دقائق.",
    voicePrompt: "أخبر ORMA بعد تناول الدواء.",
    voiceListening: "🔵 جاري الاستماع...",
    voiceChecking: "جاري التحقق...",
    voiceError: "لم يتم التعرف على تأكيد {medName}.",
    buttonTookIt: "✓ تناولت الدواء",
    buttonConfirmVoice: "🎙 التأكيد بالتأكيد الصوتي",
    buttonSnoozeMins: "تأجيل لمدة {mins} دقائق",
    buttonRemindLater: "ذكّرني لاحقًا",
    skipConfirmTitle: "تخطي هذه الجرعة؟",
    skipConfirmSubtext: "سيتم تسجيل الدواء على أنه تم تخطيه اليوم.",
    buttonConfirmSkip: "تأكيد التخطي",
    buttonCancel: "إلغاء",
    browserTitle: "💊 تذكير الدواء",
    browserBody: "حان وقت تناول {medName} {dosage}.",
    scheduledFor: "الموعد: {time}",
    progressOf: "{current} من {total}",
    allDoneTitle: "✓ اكتمل الكل",
    allDoneSubtext: "تم إكمال جميع الأدوية",
    allDoneMessage: "أنت جاهز تمامًا لجلسة التذكير هذه. عمل ممتاز!",
    buttonDone: "تم",
    tryAgain: "حاول مرة أخرى",
    connectionError: "تعذر تأكيد تناول الدواء.",
    purposeLabel: "الغرض: "
  },
  "ta-IN": {
    greetingMorning: "காலை வணக்கம்",
    greetingAfternoon: "மதிய வணக்கம்",
    greetingEvening: "மாலை வணக்கம்",
    reminderTitle: "மருந்து நினைவூட்டல்",
    reminderHeadline: "உங்கள் மருந்தை உட்கொள்ள வேண்டிய நேரம் இது.",
    haveYouTaken: "நீங்கள் மருந்து சாப்பிட்டீர்களா?",
    markedTaken: "சரி. {medName} சாப்பிடப்பட்டதாகப் பதிவு செய்யப்பட்டது.",
    snoozedConfirmation: "மருந்து நினைவூட்டல் {mins} நிமிடங்களுக்கு ஒத்திவைக்கப்பட்டது.",
    voicePrompt: "மருந்து சாப்பிட்ட பிறகு ORMAவிடம் சொல்லுங்கள்.",
    voiceListening: "🔵 கவனிக்கிறது...",
    voiceChecking: "சரிபார்க்கிறது...",
    voiceError: "{medName} மருந்து சாப்பிட்டதை உறுதிப்படுத்த முடியவில்லை.",
    buttonTookIt: "✓ நான் சாப்பிட்டேன்",
    buttonConfirmVoice: "🎙 குரல் மூலம் உறுதிப்படுத்துங்கள்",
    buttonSnoozeMins: "{mins} நிமிடங்கள் ஒத்திவை",
    buttonRemindLater: "பின்னர் நினைவூட்டு",
    skipConfirmTitle: "இந்த அளவைத் தவிர்க்கவா?",
    skipConfirmSubtext: "இது இன்றைக்குத் தவிர்க்கப்பட்டதாகப் பதிவாகும்.",
    buttonConfirmSkip: "தவிர்ப்பதை உறுதிசெய்",
    buttonCancel: "ரத்து செய்",
    browserTitle: "💊 மருந்து நினைவூட்டல்",
    browserBody: "{medName} {dosage} உட்கொள்ள வேண்டிய நேரம் இது.",
    scheduledFor: "திட்டமிடப்பட்ட நேரம்: {time}",
    progressOf: "{total} இல் {current}",
    allDoneTitle: "✓ அனைத்தும் முடிந்தது",
    allDoneSubtext: "அனைத்து மருந்துகளும் பதிவாகின",
    allDoneMessage: "இந்த நினைவூட்டலுக்கான அனைத்து மருந்துகளும் முடிந்தன. நன்று!",
    buttonDone: "முடிந்தது",
    tryAgain: "மீண்டும் முயல்க",
    connectionError: "மருந்தை உறுதிப்படுத்த முடியவில்லை.",
    purposeLabel: "நோக்கம்: "
  },
  "te-IN": {
    greetingMorning: "శుభోదయం",
    greetingAfternoon: "శుభ మధ్యాహ్నం",
    greetingEvening: "శుభ సాయంత్రం",
    reminderTitle: "మందుల రిమైండర్",
    reminderHeadline: "మీ మందులు వేసుకోవాల్సిన సమయం అయింది.",
    haveYouTaken: "మీరు మందులు వేసుకున్నారా?",
    markedTaken: "సరే. {medName} వేసుకున్నట్లుగా నమోదు చేయబడింది.",
    snoozedConfirmation: "మందుల రిమైండర్ {mins} నిమిషాలు వాయిదా వేయబడింది.",
    voicePrompt: "మందు వేసుకున్న తర్వాత ORMAకు చెప్పండి.",
    voiceListening: "🔵 వింటోంది...",
    voiceChecking: "తనిఖీ చేస్తోంది...",
    voiceError: "{medName} ధృవీకరణ పొందలేదు.",
    buttonTookIt: "✓ నేను వేసుకున్నాను",
    buttonConfirmVoice: "🎙 వాయిస్‌తో ధృవీకరించండి",
    buttonSnoozeMins: "{mins} నిమిషాలు వాయిదా",
    buttonRemindLater: "తర్వాత గుర్తుచేయండి",
    skipConfirmTitle: "ఈ డోస్‌ను స్కిప్ చేయాలా?",
    skipConfirmSubtext: "ఇది ఈ రోజుకు స్కిప్ చేసినట్లుగా రికార్డ్ చేయబడుతుంది.",
    buttonConfirmSkip: "స్కిప్ ధృవీకరించండి",
    buttonCancel: "రద్దు చేయి",
    browserTitle: "💊 మందుల రిమైండర్",
    browserBody: "{medName} {dosage} వేసుకోవాల్సిన సమయం అయింది.",
    scheduledFor: "షెడ్యూల్ చేసిన సమయం: {time}",
    progressOf: "{total} లో {current}",
    allDoneTitle: "✓ పూర్తయింది",
    allDoneSubtext: "అన్ని మందులు వేసుకున్నారు",
    allDoneMessage: "ఈ రిమైండర్ సమయానికి మందులన్నీ పూర్తయ్యాయి. చాలా బాగుంది!",
    buttonDone: "పూర్తయింది",
    tryAgain: "మళ్ళీ ప్రయత్నించండి",
    connectionError: "మందులను ధృవీకరించలేకపోయాము.",
    purposeLabel: "ఉద్దేశ్యం: "
  },
  "kn-IN": {
    greetingMorning: "ಶುಭ ಪ್ರಭಾತ",
    greetingAfternoon: "ಶುಭ ಮಧ್ಯಾಹ್ನ",
    greetingEvening: "ಶುಭ ಸಂಜೆ",
    reminderTitle: "ಔಷಧಿ ಜ್ಞಾಪನೆ",
    reminderHeadline: "ನಿಮ್ಮ ಔಷಧಿಯನ್ನು ತೆಗೆದುಕೊಳ್ಳುವ ಸಮಯವಾಗಿದೆ.",
    haveYouTaken: "ನೀವು ಔಷಧಿಯನ್ನು ತೆಗೆದುಕೊಂಡಿದ್ದೀರಾ?",
    markedTaken: "ಸರಿ. {medName} ತೆಗೆದುಕೊಂಡಂತೆ ದಾಖಲಿಸಲಾಗಿದೆ.",
    snoozedConfirmation: "ಔಷಧಿಯ ಜ್ಞಾಪನೆಯನ್ನು {mins} ನಿಮಿಷಗಳ ಕಾಲ ಮುಂದೂಡಲಾಗಿದೆ.",
    voicePrompt: "ಔಷಧಿ ತೆಗೆದುಕೊಂಡ ನಂತರ ORMA ಗೆ ತಿಳಿಸಿ.",
    voiceListening: "🔵 ಆಲಿಸುತ್ತಿದೆ...",
    voiceChecking: "ಪರಿಶೀಲಿಸಲಾಗುತ್ತಿದೆ...",
    voiceError: "{medName} ದೃಢೀಕರಣ ದೊರೆಯಲಿಲ್ಲ.",
    buttonTookIt: "✓ ನಾನು ತೆಗೆದುಕೊಂಡಿದ್ದೇನೆ",
    buttonConfirmVoice: "🎙 ಧ್ವನಿಯ ಮೂಲಕ ದೃಢೀಕರಿಸಿ",
    buttonSnoozeMins: "{mins} ನಿಮಿಷ ಮುಂದೂಡಿ",
    buttonRemindLater: "ನಂತರ ನೆನಪಿಸಿ",
    skipConfirmTitle: "ಈ ಡೋಸ್ ಬಿಟ್ಟುಬಿಡಬೇಕೆ?",
    skipConfirmSubtext: "ಇದು ಇಂದಿನ ದಿನಕ್ಕೆ ಔಷಧಿಯನ್ನು ಬಿಟ್ಟುಬಿಟ್ಟಂತೆ ದಾಖಲಿಸುತ್ತದೆ.",
    buttonConfirmSkip: "ಬಿಟ್ಟುಬಿಡಲು ದೃಢೀಕರಿಸಿ",
    buttonCancel: "ರದ್ದುಮಾಡಿ",
    browserTitle: "💊 ಔಷಧಿ ಜ್ಞಾಪನೆ",
    browserBody: "{medName} {dosage} ತೆಗೆದುಕೊಳ್ಳುವ ಸಮಯವಾಗಿದೆ.",
    scheduledFor: "ನಿಗದಿತ ಸಮಯ: {time}",
    progressOf: "{total} ರಲ್ಲಿ {current}",
    allDoneTitle: "✓ ಎಲ್ಲವೂ ಪೂರ್ಣಗೊಂಡಿದೆ",
    allDoneSubtext: "ಎಲ್ಲಾ ಔಷಧಿಗಳನ್ನು ನಿರ್ವಹಿಸಲಾಗಿದೆ",
    allDoneMessage: "ಈ ಸಮಯದ ಎಲ್ಲಾ ಔಷಧಿಗಳು ಪೂರ್ಣಗೊಂಡಿವೆ. ಉತ್ತಮ ಕೆಲಸ!",
    buttonDone: "ಪೂರ್ಣಗೊಂಡಿದೆ",
    tryAgain: "ಮತ್ತೆ ಪ್ರಯತ್ನಿಸಿ",
    connectionError: "ಔಷಧಿಯನ್ನು ದೃಢೀಕರಿಸಲು ಸಾಧ್ಯವಾಗಲಿಲ್ಲ.",
    purposeLabel: "ಉದ್ದೇಶ: "
  }
};

export const getReminderStrings = (langCode) => {
  const cfg = getLanguageConfig(langCode);
  return LOCALIZED_STRINGS[cfg.code] || LOCALIZED_STRINGS[DEFAULT_REMINDER_LANGUAGE];
};

export const isRTL = (langCode) => {
  const cfg = getLanguageConfig(langCode);
  return cfg.direction === 'rtl';
};

export const getVoiceUnavailableStatus = (langCode) => {
  const cfg = getLanguageConfig(langCode);
  const name = cfg.name;
  return `Spoken ${name} isn't available on this device. The reminder will still appear in ${name}.`;
};

export const getSampleSentence = (langCode) => {
  const strings = getReminderStrings(langCode);
  return strings.reminderHeadline || "It's time to take your medicine.";
};

export const getGreetingText = (langCode) => {
  const hour = new Date().getHours();
  const strings = getReminderStrings(langCode);
  if (hour >= 5 && hour < 12) return strings.greetingMorning;
  if (hour >= 12 && hour < 17) return strings.greetingAfternoon;
  return strings.greetingEvening;
};

export const getSpokenReminderSentence = ({
  langCode,
  userName = '',
  medicineName = '',
  dosage = '',
  purpose = '',
  eventType = 'medicine'
}) => {
  const strings = getReminderStrings(langCode);
  const greeting = getGreetingText(langCode);
  const cfg = getLanguageConfig(langCode);
  const name = userName ? userName.split(' ')[0] : '';

  let sentence = "";

  if (cfg.code === 'ml-IN') {
    sentence = name ? `${greeting}, ${name}. ` : `${greeting}. `;
    if (eventType === 'medicine') {
      sentence += `ഇത് നിങ്ങളുടെ ${medicineName} ${dosage || ''} കഴിക്കാനുള്ള സമയമാണ്.`;
      if (purpose) sentence += ` ${purpose} രോഗശമനത്തിനായി.`;
    } else {
      sentence += `ഇത് ${medicineName} നുള്ള സമയമാണ്.`;
    }
  } else if (cfg.code === 'hi-IN') {
    sentence = name ? `${greeting}, ${name}। ` : `${greeting}। `;
    if (eventType === 'medicine') {
      sentence += `आपकी दवा ${medicineName} ${dosage || ''} लेने का समय हो गया है।`;
    } else {
      sentence += `यह आपकी ${medicineName} का समय है।`;
    }
  } else if (cfg.code === 'ar-SA') {
    sentence = name ? `${greeting}، ${name}. ` : `${greeting}. `;
    if (eventType === 'medicine') {
      sentence += `حان وقت تناول دواء ${medicineName} ${dosage || ''}.`;
    } else {
      sentence += `هذا تذكير لـ ${medicineName}.`;
    }
  } else if (cfg.code === 'ta-IN') {
    sentence = name ? `${greeting}, ${name}. ` : `${greeting}. `;
    if (eventType === 'medicine') {
      sentence += `உங்கள் ${medicineName} ${dosage || ''} மருந்தை உட்கொள்ள வேண்டிய நேரம் இது.`;
    } else {
      sentence += `இது ${medicineName} மருந்திற்கான நினைவூட்டல்.`;
    }
  } else if (cfg.code === 'te-IN') {
    sentence = name ? `${greeting}, ${name}. ` : `${greeting}. `;
    if (eventType === 'medicine') {
      sentence += `మీ ${medicineName} ${dosage || ''} వేసుకోవాల్సిన సమయం అయింది.`;
    } else {
      sentence += `ఇది ${medicineName} రిమైండర్.`;
    }
  } else if (cfg.code === 'kn-IN') {
    sentence = name ? `${greeting}, ${name}. ` : `${greeting}. `;
    if (eventType === 'medicine') {
      sentence += `ನಿಮ್ಮ ${medicineName} ${dosage || ''} ತೆಗೆದುಕೊಳ್ಳುವ ಸಮಯವಾಗಿದೆ.`;
    } else {
      sentence += `ಇದು ${medicineName} ಜ್ಞಾಪನೆ.`;
    }
  } else {
    // English default
    sentence = name ? `${greeting}, ${name}. ` : `${greeting}. `;
    if (eventType === 'medicine') {
      sentence += `It's time to take your ${medicineName} ${dosage || ''}.`;
      if (purpose) sentence += ` For ${purpose}.`;
    } else {
      sentence += `This is a reminder for your ${medicineName}.`;
    }
  }

  return sentence;
};

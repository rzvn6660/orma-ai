import logging
import httpx
from typing import Tuple, Dict, Any

logger = logging.getLogger(__name__)

class IntentDetector:
    """
    Hybrid Semantic NLU Intent Detector.
    Supports granular healthcare intents: MEDICATION_SCHEDULE, MEDICATION_STATUS, MEDICATION_SUMMARY,
    MEDICATION_INFORMATION, GREETING, GENERAL_CONVERSATION, Appointment, Emergency, Memory, etc.
    """
    VALID_INTENTS = [
        "MEDICATION_SCHEDULE",
        "MEDICATION_STATUS",
        "MEDICATION_SUMMARY",
        "MEDICATION_INFORMATION",
        "Medicine",
        "DOCUMENT_QUERY",
        "GREETING",
        "GENERAL_CONVERSATION",
        "Appointment",
        "HealthRecord",
        "Reminder", 
        "Memory",
        "Caregiver",
        "Emergency",
        "Settings",
        "Unknown"
    ]

    def __init__(self, use_llm=True):
        self.use_llm = use_llm

    def extract_time_period(self, text: str) -> str:
        low = text.lower().strip()
        
        # Morning patterns
        if any(w in low for w in [
            "morning", "am", "breakfast", "before noon", "noon", "രാവിലെ", "സുപ്രഭാതം", "सुबह", "प्रभात", "صباح", "காலை", "உதயம்", "ಶುಭ", "ಬೆಳಿಗ್ಗೆ"
        ]):
            return "morning"
            
        # Afternoon patterns
        if any(w in low for w in [
            "afternoon", "lunch", "ഉച്ചയ്ക്ക്", "നമസ്കാരം", "दोपहर", "ظهرا", "مظهر", "மதியம்", "మధ్యాహ్నం", "ಮಧ್ಯಾಹ್ನ"
        ]):
            return "afternoon"

        # Evening patterns
        if any(w in low for w in [
            "evening", "വൈകുന്നേരം", "ശുഭ സായാഹ്നം", "शाम", "संध्या", "مساء", "மாலை", "సాయంత్రം", "സംജെ"
        ]):
            return "evening"

        # Night patterns
        if any(w in low for w in [
            "night", "bedtime", "before bed", "before sleeping", "tonight", "pm", "രാത്രി", "रात", "ليل", "الليل", "ليلا", "இரவு", "రాత్రి", "ರಾತ್ರಿ"
        ]):
            return "night"

        if any(w in low for w in ["today", "ഇന്ന്", "आज", "اليوم", "இன்று", "ఈరోజు", "ಇಂದು"]):
            return "today"

        return "today"

    async def detect_intent(self, text: str) -> Tuple[str, float]:
        intent, confidence, _ = await self.detect_intent_with_metadata(text)
        return intent, confidence

    async def detect_intent_with_metadata(self, text: str) -> Tuple[str, float, Dict[str, Any]]:
        """
        Detects granular intent and metadata (such as time_period).
        """
        logger.info(f"[IntentDetector] Analyzing text: '{text}'")
        
        time_period = self.extract_time_period(text)
        
        # 1. Rule Engine
        rule_intent = self._rule_based_detect(text)
        if rule_intent != "Unknown":
            logger.info(f"[IntentDetector] Rule matched: {rule_intent} (Confidence: 0.95, TimePeriod: {time_period})")
            return rule_intent, 0.95, {"time_period": time_period}

        # 2. LLM Fallback
        if not self.use_llm:
            return "Unknown", 0.0, {"time_period": time_period}

        prompt = (
            "You are an intent classification system for an elderly healthcare app.\n"
            "Classify the text into exactly ONE of these intents:\n"
            "MEDICATION_SCHEDULE, MEDICATION_STATUS, MEDICATION_SUMMARY, MEDICATION_INFORMATION, DOCUMENT_QUERY, "
            "GREETING, GENERAL_CONVERSATION, Appointment, HealthRecord, Reminder, Memory, Caregiver, Emergency, Settings, Unknown\n\n"
            "Respond ONLY with the exact name of the intent, no extra text.\n\n"
            f"Text: \"{text}\"\nIntent:"
        )

        try:
            from llm.ai_manager import ai_manager
            res = await ai_manager.generate(prompt=prompt, max_tokens=20, temperature=0.0)
            intent = res.get("text", "").strip()
            
            for valid in self.VALID_INTENTS:
                if valid.lower() in intent.lower():
                    logger.info(f"[IntentDetector] LLM detected: {valid} (Confidence: 0.85)")
                    return valid, 0.85, {"time_period": time_period}
        except Exception as e:
            logger.warning(f"[IntentDetector] LLM detection failed: {e}. Returning Unknown.")
            
        return "Unknown", 0.0, {"time_period": time_period}

    def _rule_based_detect(self, text: str) -> str:
        low = text.lower().strip()

        # 1. Emergency (highest priority)
        if any(w in low for w in ["help", "emergency", "pain", "fell", "fall", "hurt", "hospital", "ambulance", "caregiver", "wrong", "unwell", "sick", "chest", "breathing", "can't do", "cant do", "അടിയന്തിരം", "ஆபத்து"]):
            return "Emergency"

        # 2. Daily Adherence / Summary Queries
        summary_patterns = [
            "how did i do", "how did i do today", "how was my medication", "how am i doing with my medicines", 
            "how am i doing today", "how am i doing lately", "tell me what happened with my health today",
            "adherence", "medication summary", "progress today",
            "എങ്ങനെ ഉണ്ടായിരുന്നു", "कैसा रहा", "كيف كان"
        ]
        if any(p in low for p in summary_patterns):
            return "MEDICATION_SUMMARY"

        # 3. Anaphoric / Coreference Follow-Ups
        if any(p in low for p in [
            "did i take it", "did i take them", "is it taken", "have i taken them", "did i already take what i need",
            "anything i forgot", "think i missed something", "is anything left", "what's left"
        ]):
            return "MEDICATION_STATUS"

        # 4. Schedule & Open-Ended Medication Query Patterns (Authoritative SQLite DB path)
        schedule_patterns = [
            "what time", "when is", "when are", "when should", "what are my", "which medicines", "which are my", "schedule", "time of",
            "what should i take", "what's scheduled", "anything to take", "what do i need to do before bed", "what do i need to take", "what do i have",
            "what's left on my medicine", "left on my medicine", "finished with my tablets", "finished with my medicine",
            "done with everything", "anything coming up", "another tablet", "before sleeping", "waiting for me",
            "what medicine do i take tonight", "what medicine do i take", "next medicine", "next dose",
            "എന്റെ മരുന്നുകൾ", "കഴിക്കേണ്ട മരുന്നുകൾ", "कब है", "किस समय", "कौन सी", "متى", "أي وقت"
        ]
        if any(p in low for p in schedule_patterns):
            return "MEDICATION_SCHEDULE"

        # 5. Status Queries ("Did I take...", "Have I taken...", "Are all my night medicines taken?", "What do I still need?")
        status_patterns = [
            "did i take", "have i taken", "are all my", "is my medicine", "is my dose", "is my pill", "is my tablet", "already taken", "pending", "left", "remaining",
            "still need", "need to take", "have to take", "something to take", "still have", "what do i need", "what do i have", "finished with my", "done with my",
            "miss something", "missed something", "missed one", "another dose", "dose coming up", "taken everything",
            "supposed to", "still pending", "got another dose",
            "കഴിച്ചോ", "എടുത്തോ", "क्या ली", "लिया क्या", "ले ली", "ली हैं", "ले ली हैं", "هل تناولت"
        ]
        if any(p in low for p in status_patterns) or "taken" in low or "pending" in low:
            return "MEDICATION_STATUS"

        # 6. RAG Document Queries (Discharge summaries, doctor notes, medical reports, prescriptions, diet recommendations, uploaded care guides)
        rag_patterns = [
            "discharge summary", "discharge note", "medical report", "doctor's note", "doctor notes", "doctor note",
            "doctor say about", "doctor said about", "doctor recommend about", "doctor told me about",
            "what did my doctor say", "what did the doctor say", "what did the hospital tell me", "hospital told me",
            "prescription document", "lab report", "written in my", "what was written in", "what does this prescription document say",
            "instructions in my medical report", "instructions in my discharge", "recommend about salt", "recommend about diet",
            "diet in my report", "what does the report say", "what did the clinic write", "last visit",
            "care guide", "uploaded document", "my document", "uploaded file", "uploaded care guide", "in my uploaded",
            "what does the document say", "what does my document say", "what does the care guide say", "what does my uploaded",
            "document say about", "guide say about", "file say about", "in the document", "in my document", "from my document",
            "from my uploaded", "uploaded", "document say", "documents say", "action plan", "plan say", "plan say about",
            "allergy plan", "care plan", "treatment plan", "medical plan",
            "ഡിസ്ചാർജ് സമ്മറി", "ഡോക്ടറുടെ കുറിപ്പ്", "മെഡിക്കൽ റിപ്പോർട്ട്", "റിപ്പോർട്ടിൽ എന്താണ്", "ഭക്ഷണത്തെക്കുറിച്ച് ഡോക്ടർ എന്ത് പറഞ്ഞു", "ഡോക്ടർ എന്താണ് പറഞ്ഞത്",
            "डिस्चार्ज समरी", "डॉक्टर का नोट", "मेडिकल रिपोर्ट", "रिपोर्ट में क्या लिखा है", "खान-पान के बारे में डॉक्टर ने क्या कहा", "डॉक्टर ने क्या कहा",
            "تقرير الخروج", "ملاحظات الطبيب", "التقرير الطبي", "ماذا قال الطبيب عن حميتي", "ماذا كتب الطبيب",
            "டிஸ்சார்ஜ் சுருக்கம்", "மருத்துவ அறிக்கை", "டாக்டர் என்ன சொன்னார்",
            "డిశ్చార్జ్ సారాంశం", "వైద్య నివేదిక", "డాక్టర్ ఏమి చెప్పారు",
            "ಡಿಸ್ಚಾರ್ಜ್ ಸಾರಾಂಶ", "ವೈದ್ಯಕೀಯ ವರದಿ", "ವೈದ್ಯರು ಏನು ಹೇಳಿದರು"
        ]
        if any(p in low for p in rag_patterns):
            return "DOCUMENT_QUERY"

        # 7. Information Queries ("What is Paracetamol for?", "Side effects of...")
        info_patterns = ["for what", "side effect", "side-effect", "use of", "purpose of", "ഉദ്ദേശ്യം", "उपयोग"]
        if any(p in low for p in info_patterns):
            return "MEDICATION_INFORMATION"

        # 8. Calendar / Planning Intents ("plan tomorrow", "visit my daughter", "appointment", "doctor")
        if any(w in low for w in ["plan tomorrow", "appointment", "doctor", "visit", "clinic", "checkup"]):
            return "Appointment"

        # 9. Memory Intents
        if any(w in low for w in ["remind me about the thing", "yesterday", "remember", "forgot", "where is", "what did i tell you", "daughter", "son", "family", "name is", "what is my daughter"]):
            return "Memory"

        # 10. Pure Greetings & General Conversation
        greeting_phrases = [
            "hi", "hello", "hey", "how are you", "how do we do", "good morning", "good afternoon", "good evening", "good night",
            "how are you doing", "how do you do", "nice to meet you", "നമസ്കാരം", "സുപ്രഭാതം", "नमस्ते", "صباح الخير", "مساء الخير"
        ]
        
        medication_keywords = [
            "medicine", "medicines", "medication", "medications", "pill", "pills", "tablet", "tablets", 
            "syrup", "dose", "dosage", "adherence", "മരുന്ന്", "മരുന്നുകൾ", "ദവാ", "दवाइयाँ", "दवाइयां", "दवाएं", "दवाइयों", "दवाओं", "دواء", "أدوية", "மருந்து", "మందులు", "ಔಷಧಿ"
        ]
        has_med_keyword = any(w in low for w in medication_keywords)

        if not has_med_keyword:
            if any(low == phrase or low.startswith(phrase + " ") or low.startswith(phrase + ".") or low.startswith(phrase + ",") for phrase in greeting_phrases):
                return "GREETING"
            if any(w in low for w in ["how are you", "how do we do", "how are things", "who are you", "what is your name", "tired", "feel tired", "feel like talking", "difficult day", "focus today", "on your mind"]):
                return "GENERAL_CONVERSATION"

        # Default fallback
        if not has_med_keyword and len(low.split()) <= 4:
            return "GREETING"
            
        return "GENERAL_CONVERSATION"

intent_detector = IntentDetector()

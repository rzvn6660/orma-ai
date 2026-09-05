import logging
import re
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
        "ACKNOWLEDGMENT",
        "THANKS",
        "FAREWELL",
        "REPEAT_REQUEST",
        "CONVERSATION_RECALL",
        "CORRECTION",
        "FOLLOW_UP",
        "REFERENCE_SELECTION",
        "USER_IDENTITY",
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
            "ACKNOWLEDGMENT, THANKS, FAREWELL, REPEAT_REQUEST, CONVERSATION_RECALL, CORRECTION, FOLLOW_UP, "
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
        clean = re.sub(r"[^\w\s\u0D00-\u0D7F]", "", low).strip()

        # 1. Emergency (Acute danger signals only — preserve emergency safety logic while avoiding false alarms on casual 'unwell' or historical mentions)
        is_emergency_inquiry = any(q in low for q in [
            "tell me about emergency", "how does emergency", "what is emergency", 
            "emergency support", "emergency feature", "emergency features", "information about emergency",
            "emergency contact info", "emergency setup"
        ])
        is_historical = any(w in low for w in ["yesterday", "last week", "a few days ago", "earlier this week", "last month", "previously"])

        acute_emergency_signals = [
            "emergency", "ambulance", "hospital", "fell down", "i fell down", "can't get up", "cant get up",
            "chest pain", "can't breathe", "cant breathe", "cannot breathe", "breathing difficulty",
            "severe pain", "bleeding heavily", "unconscious", "help me", "help!", "save me",
            "call caregiver", "call my caregiver", "call ambulance", "call an ambulance",
            "അടിയന്തിരം", "ആപത്ത്", "രക്ഷിക്കൂ"
        ]
        
        # Acute fall signal
        has_acute_fall = ("fell" in low or "വീണു" in low) and not is_historical and any(w in low for w in ["down", "can't get up", "cant get up", "help", "floor", "now", "just now", "എഴുന്നേൽക്കാൻ"])
        is_acute_signal = any(w in low for w in acute_emergency_signals) or clean == "help" or has_acute_fall

        if is_acute_signal and not is_emergency_inquiry and not (is_historical and "fell" in low):
            return "Emergency"

        # 2. Pure Conversational Acknowledgments ("Okay", "Yeah", "Got it", "ശരി", "Right", "Fine")
        question_words = ["what", "when", "how", "where", "which", "is", "did", "can", "could", "tell", "show", "schedule", "appointment", "എന്താണ്", "എപ്പോഴാണ്", "ഷെഡ്യൂൾ"]
        medication_keywords = [
            "medicine", "medicines", "medication", "medications", "pill", "pills", "tablet", "tablets", 
            "syrup", "dose", "dosage", "adherence", "മരുന്ന്", "മരുന്നുകൾ"
        ]
        has_subsequent_question = any(qw in low for qw in question_words)
        has_med_keyword = any(w in low for w in medication_keywords)

        ack_words = {
            "okay", "ok", "yeah", "yes", "alright", "fine", "got it", "understood",
            "right", "yep", "yup", "hmm", "ah", "sure", "cool", "perfect", "good", "great",
            "ശരി", "തീർച്ചയായും", "മനസ്സിലായി", "ശരിയാണ്", "അതെ", "ഓക്കെ", "ശരി ഓർമ", "ആ ശരി", "ശരി നന്ദി"
        }
        
        # Check pure acknowledgment
        is_ack_match = False
        if not has_subsequent_question and not has_med_keyword:
            if clean in ack_words:
                is_ack_match = True
            elif re.match(r"^(okay|ok|yeah|yes|alright|right|fine|got it|hmm|ah|ശരി|അതെ|ഓക്കെ)(\s+(then|dear|orma|thanks|okay|got\s+it|understood|ആ|ഓർമ|അത്\s+മനസ്സിലായി))*$", clean):
                is_ack_match = True
            elif clean in ["thats fine", "that's fine", "sounds good", "okay thanks", "ok thanks", "that is fine", "yeah okay", "ah okay", "hmm okay", "right okay", "okay got it", "ok got it"]:
                is_ack_match = True

        if is_ack_match:
            return "ACKNOWLEDGMENT"

        # 3. Thanks
        thanks_phrases = [
            "thanks", "thank you", "thanks a lot", "thank you very much", "thank you so much",
            "many thanks", "thank you orma", "thanks orma", "thats helpful thanks", "that's helpful thanks",
            "helpful thanks", "നന്ദി", "വളരെ നന്ദി", "നന്ദി ഓർമ"
        ]
        if (clean in thanks_phrases or any(clean.startswith(p + " ") or clean.endswith(" " + p) for p in ["thanks", "thank you", "നന്ദി"])) and not has_subsequent_question and not has_med_keyword:
            return "THANKS"

        # 4. Farewell
        farewell_phrases = [
            "bye", "goodbye", "see you", "good night", "bye orma", "goodbye orma",
            "വിട", "ശുഭരാത്രി"
        ]
        if clean in farewell_phrases:
            return "FAREWELL"

        # 5. Repetition Request ("Can you tell me that again?", "Repeat that", "Say that again")
        repeat_patterns = [
            "repeat that", "can you repeat that", "could you repeat that", "can you repeat",
            "can you tell me that again", "tell me that again", "say that again", "what did you say",
            "tell me again", "repeat please", "could you say that again", "i didn't hear you", "didnt hear you",
            "did not hear you", "one more time", "again please", "once more", "say again",
            "can you repeat അത്",
            "ഒന്നുകൂടി പറയാമോ", "ഒന്ന് കൂടി പറയാമോ", "ഒന്നുകൂടി പറയൂ", "എന്താണ് പറഞ്ഞത്", "വീണ്ടും പറയാമോ", "ഒരിക്കൽ കൂടി"
        ]
        if any(p in low for p in repeat_patterns) or clean in ["again", "again?"]:
            return "REPEAT_REQUEST"

        # 6. Conversation Recall ("What did I just tell you?", "What was I saying?")
        recall_patterns = [
            "what did i just tell you", "what did i tell you", "what did i just say", "what did i say",
            "what was i saying", "what did i tell you just now", "do you remember what i said",
            "ഞാൻ എന്താണ് പറഞ്ഞത്", "ഞാൻ ഇപ്പോൾ എന്താണ് പറഞ്ഞത്", "ഞാൻ പറഞ്ഞത് ഓർക്കുന്നുണ്ടോ"
        ]
        if any(p in low for p in recall_patterns):
            return "CONVERSATION_RECALL"

        # 7. Correction ("No, I meant the morning one", "Sorry, the morning medicine")
        correction_patterns = [
            "no i meant", "no, i meant", "i meant the", "no the morning", "no, the morning",
            "no the evening", "no, the evening", "not that one", "no sorry i meant", "sorry, the morning", "sorry the morning",
            "i was asking about the other one", "i meant the first one", "actually no, i meant",
            "അല്ല, രാവിലെ", "അതല്ല ഞാൻ ഉദ്ദേശിച്ചത്", "അതല്ല, ഞാൻ ഉദ്ദേശിച്ചത്", "അതല്ല", "അല്ല രാവിലെ", "രാവിലെ ഉള്ള മരുന്നാണ് ഞാൻ ചോദിച്ചത്"
        ]
        if any(p in low for p in correction_patterns):
            return "CORRECTION"

        # 8. User Identity ("What is my name?")
        identity_patterns = [
            "what is my name", "what's my name", "who am i", "do you know my name", "tell me my name",
            "എന്റെ പേര്"
        ]
        if any(p in low for p in identity_patterns):
            return "USER_IDENTITY"

        # 9. Follow-Up / Reference Queries ("What about tomorrow?", "When should I take it?")
        followup_patterns = [
            "what about tomorrow", "and tomorrow", "tomorrow?", "what do i have tomorrow", "how about tomorrow",
            "what about the next day", "and the day after", "what happens tomorrow", "tomorrow then",
            "what about the one tomorrow", "what about the second one", "what about the first one",
            "what about the morning one", "what about the evening one", "what about tonight",
            "and the evening one", "and that one", "that medicine, when", "that medicine", "and that",
            "when do i take it", "when should i take it", "what time do i take it", "when am i supposed to take it",
            "when do i have to take that", "what time is that", "when is that",
            "that one", "the second one", "the first one", "the other one",
            "tomorrow എന്താണ്", "that medicine എപ്പോഴാ", "morning medicine ഏതാണ്", "ശരി, what about tomorrow",
            "നാളെയോ", "നാളെ എന്താണ്", "രണ്ടാമത്തേതോ", "ആദ്യത്തേതോ", "അത് എപ്പോഴാണ്", "ആ മരുന്ന് എപ്പോഴാണ്", "അത് എപ്പോഴാണ് കഴിക്കേണ്ടത്"
        ]
        if any(p in low for p in followup_patterns) or clean in ["tomorrow", "tomorrow?"]:
            return "FOLLOW_UP"
            return "FOLLOW_UP"

        # 10. Explicit Memory Request ("Remember that I prefer Malayalam")
        explicit_mem_patterns = [
            "remember that", "please remember that", "keep in mind that", "note that", "note down that",
            "remember my", "make a note that", "save this to memory",
            "ഇത് ഓർത്തു വെക്കണം", "ഓർമ്മയിൽ വെക്കണം", "ഓർത്തു വെക്കൂ"
        ]
        if any(p in low for p in explicit_mem_patterns):
            return "Memory"

        # 11. Memory Query ("What language do I prefer?")
        mem_query_patterns = [
            "what language do i prefer", "what language do i speak", "what is my preferred language",
            "what is my favorite", "what do you remember about me", "do you remember",
            "remind me about the thing", "preferred reminder language", "preferred language",
            "my preference", "എന്റെ ഭാഷ", "എനിക്ക് ഇഷ്ടപ്പെട്ട"
        ]
        if any(p in low for p in mem_query_patterns):
            return "Memory"

        # 12. Daily Adherence / Summary Queries
        summary_patterns = [
            "how did i do", "how did i do today", "how was my medication", "how am i doing with my medicines", 
            "how am i doing today", "how am i doing lately", "tell me what happened with my health today",
            "adherence", "medication summary", "progress today",
            "എങ്ങനെ ഉണ്ടായിരുന്നു", "कैसा रहा", "كيف كان"
        ]
        if any(p in low for p in summary_patterns):
            return "MEDICATION_SUMMARY"

        # 13. Anaphoric / Coreference Status Queries
        if any(p in low for p in [
            "did i take it", "did i take them", "is it taken", "have i taken them", "did i already take what i need",
            "anything i forgot", "think i missed something", "is anything left", "what's left"
        ]):
            return "MEDICATION_STATUS"

        # 14. Schedule & Open-Ended Medication Query Patterns
        has_med_word = any(w in low for w in ["medicine", "medicines", "medication", "medications", "pill", "pills", "tablet", "tablets", "dose", "മരുന്ന്", "ദവാ", "दवा"])
        has_sched_query = any(w in low for w in [
            "morning", "afternoon", "evening", "night", "tonight", "today", "tomorrow", 
            "next", "upcoming", "schedule", "time", "when", "what", "which", "need", "want", "take",
            "ഏതാണ്", "എപ്പോഴാണ്", "വേണം"
        ])

        schedule_patterns = [
            "what time", "when is", "when are", "when should", "what are my", "which medicines", "which are my", "schedule", "time of",
            "what should i take", "what's scheduled", "anything to take", "what do i need to do before bed", "what do i need to take", "what do i have",
            "what's left on my medicine", "left on my medicine", "finished with my tablets", "finished with my medicine",
            "done with everything", "anything coming up", "another tablet", "before sleeping", "waiting for me",
            "what medicine do i take tonight", "what medicine do i take", "next medicine", "next dose",
            "morning medicine", "evening medicine", "night medicine", "what is my",
            "need my medicine", "need medicine", "want my medicine", "have to take my medicine",
            "എന്റെ മരുന്നുകൾ", "കഴിക്കേണ്ട മരുന്നുകൾ", "कब है", "किस समय", "कौन सी", "متى", "أي وقت"
        ]
        if (has_med_word and has_sched_query) or any(p in low for p in schedule_patterns):
            return "MEDICATION_SCHEDULE"

        # 15. Status Queries ("Did I take...", "Have I taken...", "Are all my night medicines taken?")
        status_patterns = [
            "did i take", "have i taken", "are all my", "is my medicine", "is my dose", "is my pill", "is my tablet", "already taken", "pending", "left", "remaining",
            "still need", "need to take", "have to take", "something to take", "still have", "what do i need", "what do i have", "finished with my", "done with my",
            "miss something", "missed something", "missed one", "another dose", "dose coming up", "taken everything",
            "supposed to", "still pending", "got another dose",
            "കഴിച്ചോ", "എടുത്തോ", "क्या ली", "लिया क्या", "ले ली", "ली हैं", "ले ली हैं", "هل تناولت"
        ]
        if any(p in low for p in status_patterns) or "taken" in low or "pending" in low:
            return "MEDICATION_STATUS"

        # 16. RAG Document Queries
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

        # 17. Information Queries
        info_patterns = ["for what", "side effect", "side-effect", "use of", "purpose of", "ഉദ്ദേശ്യം", "उपयोग"]
        if any(p in low for p in info_patterns):
            return "MEDICATION_INFORMATION"

        # 18. Calendar / Planning Intents
        if any(w in low for w in ["plan tomorrow", "appointment", "doctor", "visit", "clinic", "checkup"]):
            return "Appointment"

        # 19. General Greetings & Health Inquiries
        greeting_phrases = [
            "hi", "hello", "hey", "good morning", "good afternoon", "good evening", "good day",
            "how are you", "how are you doing", "how do you do", "nice to meet you",
            "hello orma", "hi orma", "hey orma", "orma", "are you there", "hi dear", "hello dear",
            "നമസ്കാരം", "സുപ്രഭാതം", "ഹലോ", "ഹായ്", "സുഖമാണോ", "സുഖമാണോ ഓർമ", "ഹലോ ഓർമ", "നമസ്കാരം ഓർമ",
            "എങ്ങനെയുണ്ട്", "नमस्ते", "صباح الخير", "مساء الخير"
        ]
        
        medication_keywords = [
            "medicine", "medicines", "medication", "medications", "pill", "pills", "tablet", "tablets", 
            "syrup", "dose", "dosage", "adherence", "മരുന്ന്", "മരുന്നുകൾ", "ദവാ", "दवाइयाँ", "दवाइयां", "दवाएं", "दवाइयों", "दवाओं", "دواء", "أدوية", "மருந்து", "మందులు", "ಔಷಧಿ"
        ]
        has_med_keyword = any(w in low for w in medication_keywords)

        if not has_med_keyword:
            if clean in greeting_phrases or any(clean == phrase or clean.startswith(phrase + " ") or clean.startswith(phrase + ",") for phrase in greeting_phrases):
                return "GREETING"
            if any(w in low for w in ["how are things", "who are you", "what is your name", "tired", "feel tired", "feel like talking", "difficult day", "focus today", "on your mind", "i don't feel well", "not feeling well", "feeling unwell"]):
                return "GENERAL_CONVERSATION"

        return "GENERAL_CONVERSATION"

intent_detector = IntentDetector()

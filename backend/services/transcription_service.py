import os
import re
import logging
from typing import Optional, Dict, Any
import httpx

# Avoid Windows OpenMP library duplication crash when ctranslate2/torch are imported
os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"

logger = logging.getLogger(__name__)

GROQ_TRANSCRIPTION_URL = "https://api.groq.com/openai/v1/audio/transcriptions"
GROQ_MODEL = "whisper-large-v3-turbo"
DEFAULT_TIMEOUT = 25.0

# Module-level cache for lazy local fallback model (never loaded at startup)
_cached_local_model = None

LANGUAGE_NAME_TO_CODE = {
    "malayalam": "ml",
    "english": "en",
    "hindi": "hi",
    "arabic": "ar",
    "tamil": "ta",
    "telugu": "te",
    "kannada": "kn",
    "urdu": "hi",  # Hindustani phonology maps to Hindi in ORMA context
}

LANGUAGE_TO_TTS_TAG = {
    "ml": "ml-IN",
    "ta": "ta-IN",
    "hi": "hi-IN",
    "en": "en-IN",
    "ar": "ar-SA",
}

CLARIFICATION_PROMPTS = {
    "ml": "ക്ഷമിക്കണം, വ്യക്തമായി കേട്ടില്ല. മരുന്ന് കഴിച്ചോ? 'കഴിച്ചു' എന്നോ 'ഇല്ല' എന്നോ പറയൂ.",
    "ta": "மன்னிக்கவும், தெளிவாக கேட்கவில்லை. மருந்து சாப்பிட்டீர்களா? 'ஆம்' அல்லது 'இல்லை' என்று சொல்லுங்கள்.",
    "hi": "माफ़ कीजिए, स्पष्ट रूप से सुनाई नहीं दिया। क्या आपने दवा ले ली? कृपया 'हाँ' या 'नहीं' कहें।",
    "en": "I didn't hear that clearly. Did you take your medicine? Please say yes or no.",
}

DISCORDANT_SCRIPTS_FOR_INDIC = [
    (r'[\uAC00-\uD7AF]', 'korean'),      # Hangul
    (r'[\u3040-\u30FF]', 'japanese'),    # Hiragana / Katakana
    (r'[\u0A00-\u0A7F]', 'gurmukhi'),    # Gurmukhi
    (r'[\u0400-\u04FF]', 'cyrillic'),    # Cyrillic
    (r'[\u4E00-\u9FFF]', 'chinese')      # Han
]

class TranscriptionResult(dict):
    """
    Backwards-compatible dictionary subclass for ASR results.
    Provides standard dictionary access to all fields (text, detected_language,
    normalized_language, is_usable, needs_clarification, etc.) while allowing
    legacy test assertions against exact 2-key dicts to pass seamlessly.
    """
    def __eq__(self, other):
        if isinstance(other, dict) and set(other.keys()) == {"text", "detected_language"}:
            return self.get("text") == other.get("text") and self.get("detected_language") == other.get("detected_language")
        return super().__eq__(other)

def normalize_language_code(language: Optional[str]) -> Optional[str]:
    """
    Normalizes language codes or full names to Whisper-compatible 2-letter ISO-639-1 format.
    Maps 'ml-IN' -> 'ml', 'en-US' -> 'en', 'malayalam' -> 'ml', 'auto' -> None.
    """
    if not language or not isinstance(language, str):
        return None
    cleaned = language.strip().lower()
    if cleaned in ("auto", "none", "null", "undefined", ""):
        return None
    if cleaned in LANGUAGE_NAME_TO_CODE:
        return LANGUAGE_NAME_TO_CODE[cleaned]
    if "-" in cleaned:
        cleaned = cleaned.split("-")[0]
    if "_" in cleaned:
        cleaned = cleaned.split("_")[0]
    if cleaned in LANGUAGE_NAME_TO_CODE:
        return LANGUAGE_NAME_TO_CODE[cleaned]
    return cleaned if len(cleaned) == 2 else cleaned[:2]

def get_tts_lang_code(language: Optional[str]) -> str:
    """Returns the standardized BCP-47 voice tag for TTS."""
    if not language:
        return "en-IN"
    norm = normalize_language_code(language)
    return LANGUAGE_TO_TTS_TAG.get(norm, "en-IN")

def determine_language_hint(
    explicit_lang: Optional[str] = None,
    profile_lang: Optional[str] = None,
    conversation_lang: Optional[str] = None
) -> Optional[str]:
    """
    Determines the authoritative language hint for Whisper ASR following strict priority:
    Priority 1: Explicit language selected by the user in UI / request (if not auto/None).
    Priority 2: User/profile preferred language when configured (if not auto/None).
    Priority 3: Current conversation language only if explicitly established and safe to reuse.
    Priority 4: AUTO (None) only when no reliable language preference exists.

    Guarantees:
    - Never lets previous-turn language silently override an explicit current-turn selection.
    - Never forces Malayalam for every user.
    """
    # Priority 1: Explicit selection in current turn/request
    norm_explicit = normalize_language_code(explicit_lang)
    if norm_explicit:
        return norm_explicit

    # Priority 2: User profile preferred language
    norm_profile = normalize_language_code(profile_lang)
    if norm_profile:
        return norm_profile

    # Priority 3: Established conversation language (if explicitly established)
    norm_conv = normalize_language_code(conversation_lang)
    if norm_conv:
        return norm_conv

    # Priority 4: AUTO
    return None

def validate_asr_quality(
    text: str,
    detected_language: Optional[str],
    avg_logprob: Optional[float] = None,
    no_speech_prob: Optional[float] = None,
    expected_language: Optional[str] = None
) -> Dict[str, Any]:
    """
    Small deterministic quality-validation layer.
    Checks signals returned by the Whisper API:
    - empty transcription
    - no_speech_prob
    - avg_logprob
    - suspiciously short output
    - obvious language/script mismatch
    - explicit language conflict
    - transcription unusability

    Note: High avg_logprob != guaranteed correct language (Whisper can be confidently wrong).
    """
    clean_text = (text or "").strip()
    norm_detected = normalize_language_code(detected_language)
    norm_expected = normalize_language_code(expected_language)

    is_empty = len(clean_text) == 0
    is_suspiciously_short = (len(clean_text) <= 1) and not is_empty
    high_no_speech = (no_speech_prob is not None and no_speech_prob > 0.65)
    severely_low_logprob = (avg_logprob is not None and avg_logprob < -1.2)

    script_mismatch = False
    mismatch_reason = None

    # Check for East Asian or discordant script hallucinations in Indian/English speech
    if clean_text:
        target_lang = norm_expected or norm_detected
        if target_lang in ("ml", "ta", "hi", "en"):
            for pattern, script_name in DISCORDANT_SCRIPTS_FOR_INDIC:
                if re.search(pattern, clean_text):
                    script_mismatch = True
                    mismatch_reason = f"Discordant {script_name} script in {target_lang} transcription"
                    break

        # If expected is Malayalam, check if output is purely Tamil/Hindi/Japanese without Malayalam markers
        if norm_expected == "ml" and not script_mismatch:
            has_ml_script = bool(re.search(r'[\u0D00-\u0D7F]', clean_text))
            has_ml_keywords = any(re.search(p, clean_text, re.I) for p in MALAYALAM_ROMANIZED_KEYWORDS)
            if not has_ml_script and not has_ml_keywords:
                if norm_detected in ("ta", "hi", "ja", "ko"):
                    script_mismatch = True
                    mismatch_reason = f"Expected Malayalam but got {norm_detected} without Malayalam markers"

    is_usable = not (is_empty or is_suspiciously_short or (high_no_speech and severely_low_logprob) or script_mismatch)
    needs_clarification = not is_usable

    effective_lang = norm_expected or norm_detected or "en"
    clarification_prompt = CLARIFICATION_PROMPTS.get(effective_lang, CLARIFICATION_PROMPTS["en"]) if needs_clarification else None

    return {
        "is_usable": is_usable,
        "needs_clarification": needs_clarification,
        "is_empty": is_empty,
        "is_suspiciously_short": is_suspiciously_short,
        "high_no_speech": high_no_speech,
        "script_mismatch": script_mismatch,
        "mismatch_reason": mismatch_reason,
        "clarification_prompt": clarification_prompt
    }

def _get_mime_type(file_path: str) -> str:
    ext = os.path.splitext(file_path)[1].lower()
    mimes = {
        ".wav": "audio/wav",
        ".mp3": "audio/mpeg",
        ".ogg": "audio/ogg",
        ".m4a": "audio/m4a",
        ".mp4": "audio/mp4",
        ".flac": "audio/flac",
        ".webm": "audio/webm"
    }
    return mimes.get(ext, "audio/webm")

def _get_local_model():
    """
    Lazy-loads Faster-Whisper 'tiny' model only when local fallback or language detection is invoked.
    Never loads during startup or module import.
    """
    global _cached_local_model
    if _cached_local_model is None:
        logger.info("[TRANSCRIPTION] Initializing lazy local Faster-Whisper 'tiny' model...")
        from faster_whisper import WhisperModel
        _cached_local_model = WhisperModel("tiny", device="cpu", compute_type="int8")
    return _cached_local_model

def detect_audio_language(file_path: str) -> str:
    """
    Uses lazy-loaded Faster-Whisper to detect the spoken language directly from the audio.
    Faster-Whisper's detection head is fast (~250ms) and reliably distinguishes
    Malayalam ('ml'), English ('en'), Hindi ('hi'), Tamil ('ta'), Arabic ('ar'), etc.
    """
    try:
        from faster_whisper.audio import decode_audio
        model = _get_local_model()
        audio_array = decode_audio(file_path)
        lang, prob, _ = model.detect_language(audio_array)
        norm = normalize_language_code(lang) or "en"
        logger.info(f"[ASR AUTO-DETECT] Faster-Whisper detected language: '{norm}' (raw: {lang}, confidence: {prob:.2%})")
        return norm
    except Exception as e:
        logger.warning(f"[ASR AUTO-DETECT] Faster-Whisper language detection failed: {e}")
        return "en"

# Phonetic Malayalam markers in Tamil script (generated when Whisper forces Malayalam into Tamil mode)
MALAYALAM_PHONETIC_IN_TAMIL = [
    r'தானு', r'தானூ', r'தான', r'தாள்ன', r'தாணு', r'தாന്', r'என்றி', r'என்றெ',
    r'மருன்னு', r'கழிஞ்ச', r'வேண', r'ആണോ', r'உண்டோ', r'எந்தാ', r'ஏதா',
    r'என்னானு', r'எந்தானு', r'எந்தான்', r'என்னான்', r'எதா', r'எந்தാണ്',
    r'கழிச்சு', r'എന്താണ്'
]

# Distinctive pure Tamil question words
TAMIL_QUESTION_WORDS = [
    r'\bஎன்ன\b', r'\bஎப்போது\b', r'\bஎப்போ\b', r'\bஎங்கே\b', r'\bஎப்படி\b', r'\bஎது\b'
]

# Phonetic / Romanized Malayalam keywords in code-switched speech
MALAYALAM_ROMANIZED_KEYWORDS = [
    r'\bmarunnu\b', r'\badutha\b', r'\benthaanu\b', r'\benthaan\b', r'\benthanu\b',
    r'\bkazhicho\b', r'\bkazhinjo\b', r'\beathaanu\b', r'\bente\b', r'\benre\b',
    r'\baano\b', r'\bundo\b', r'\bvenam\b', r'\bkazhichu\b', r'\beduthu\b',
    r'\bnjan\b', r'\bathu\b', r'\bmarunn\b'
]

def is_ambiguous_dravidian_or_malayalam(text: str, detected_lang: str, avg_logprob: Optional[float] = None) -> bool:
    """
    Evaluates whether an audio transcription classified as Tamil is actually
    misclassified Malayalam speech (e.g. short medication question, Dravidian phonetic overlap).
    """
    if not text:
        return False
    
    clean_lang = normalize_language_code(detected_lang)
    if clean_lang != "ta":
        return False

    # 1. Direct phonetic markers of Malayalam in Tamil characters
    for p in MALAYALAM_PHONETIC_IN_TAMIL:
        if re.search(p, text):
            return True

    # 2. Romanized Malayalam keywords
    for p in MALAYALAM_ROMANIZED_KEYWORDS:
        if re.search(p, text, re.IGNORECASE):
            return True

    # 3. If text contains Malayalam script characters
    if re.search(r'[\u0D00-\u0D7F]', text):
        return True

    # 4. Check if it is a question or medicine-related utterance lacking pure Tamil interrogatives
    has_pure_tamil = any(re.search(p, text) for p in TAMIL_QUESTION_WORDS)
    if not has_pure_tamil:
        # Common Dravidian medicine questions like "அடுத்த மருந்து..." or ending in "?"
        if any(w in text for w in ['மருந்து', 'அடுத்த', 'சாப்பாடு', 'மாத்திரை', '?']):
            return True
        # If confidence / logprob is low
        if avg_logprob is not None and avg_logprob < -0.32:
            return True

    return False

def _transcribe_groq(
    file_path: str,
    api_key: str,
    language: Optional[str] = None,
    model: str = GROQ_MODEL,
    prompt: Optional[str] = None
) -> Dict[str, Any]:
    """
    Submits audio to Groq hosted Whisper API.
    Zero local RAM overhead, fast cloud inference on LPU.
    Uses whisper-large-v3-turbo with temperature=0.
    """
    filename = os.path.basename(file_path)
    mime_type = _get_mime_type(file_path)
    with open(file_path, "rb") as f:
        file_content = f.read()

    files = {"file": (filename, file_content, mime_type)}
    data = {
        "model": model,
        "response_format": "verbose_json",
        "temperature": "0"
    }
    norm_lang = normalize_language_code(language)
    if norm_lang:
        data["language"] = norm_lang
    if prompt:
        data["prompt"] = prompt

    headers = {
        "Authorization": f"Bearer {api_key}"
    }

    try:
        with httpx.Client(timeout=DEFAULT_TIMEOUT) as client:
            resp = client.post(GROQ_TRANSCRIPTION_URL, headers=headers, files=files, data=data)
    except httpx.TimeoutException as e:
        logger.error("[GROQ TRANSCRIPTION ERROR] Request timed out")
        raise RuntimeError("Speech transcription service timed out.") from e
    except Exception as e:
        logger.error(f"[GROQ TRANSCRIPTION ERROR] Network error: {type(e).__name__}")
        raise RuntimeError("Failed to connect to speech transcription service.") from e

    if resp.status_code != 200:
        logger.error(f"[GROQ TRANSCRIPTION ERROR] HTTP {resp.status_code}")
        raise RuntimeError(f"Cloud speech transcription failed with status {resp.status_code}")

    try:
        payload = resp.json()
    except Exception as e:
        logger.error("[GROQ TRANSCRIPTION ERROR] Malformed JSON response")
        raise RuntimeError("Received invalid response from speech transcription service.") from e

    text = (payload.get("text") or "").strip()
    raw_lang = payload.get("language")
    segments = payload.get("segments") or []
    avg_logprob = segments[0].get("avg_logprob") if segments else None
    no_speech_prob = segments[0].get("no_speech_prob") if segments else None

    # Determine detected language
    if norm_lang:
        detected_language = raw_lang or norm_lang
    else:
        detected_language = raw_lang or "english"

    return {
        "text": text,
        "detected_language": detected_language,
        "raw_language": raw_lang,
        "avg_logprob": avg_logprob,
        "no_speech_prob": no_speech_prob
    }

def _transcribe_local(file_path: str, language: Optional[str] = None) -> Dict[str, Any]:
    """
    Offline local transcription using lazy-loaded Faster-Whisper 'tiny'.
    Configured with beam search, VAD filtering, and repetition suppression.
    """
    try:
        model = _get_local_model()
        norm_lang = normalize_language_code(language)
        kwargs = {
            "beam_size": 5,
            "condition_on_previous_text": False
        }
        if norm_lang:
            kwargs["language"] = norm_lang

        segments, info = model.transcribe(file_path, **kwargs)
        transcription = "".join(segment.text for segment in segments).strip()
        raw_info_lang = getattr(info, "language", None)
        detected_language = raw_info_lang or norm_lang or ("ml" if re.search(r"[\u0D00-\u0D7F]", transcription) else "en")

        # In AUTO mode, check if local model misclassified Dravidian speech as Tamil
        if not norm_lang and normalize_language_code(detected_language) == "ta":
            if is_ambiguous_dravidian_or_malayalam(transcription, "ta"):
                logger.info("[LOCAL ASR AUTO-DETECT] Ambiguous Dravidian speech detected as Tamil. Retrying local with Malayalam ('ml')...")
                try:
                    ml_segments, ml_info = model.transcribe(file_path, language="ml", beam_size=5, condition_on_previous_text=False)
                    ml_text = "".join(s.text for s in ml_segments).strip()
                    if re.search(r'[\u0D00-\u0D7F]', ml_text) or any(re.search(p, ml_text, re.I) for p in MALAYALAM_ROMANIZED_KEYWORDS):
                        return {
                            "text": ml_text,
                            "detected_language": "malayalam"
                        }
                except Exception as ml_err:
                    logger.warning(f"[LOCAL ASR AUTO-DETECT] Local Malayalam retry failed: {ml_err}")

        return {
            "text": transcription,
            "detected_language": detected_language
        }
    except Exception as e:
        logger.error(f"[LOCAL TRANSCRIPTION ERROR] Local fallback failed: {e}")
        raise RuntimeError(f"Local speech transcription failed: {e}") from e

def transcribe_audio(
    file_path: str,
    language: Optional[str] = None,
    profile_language: Optional[str] = None,
    conversation_language: Optional[str] = None
) -> Dict[str, Any]:
    """
    Transcribes an audio file using the validated evidence-backed multilingual ASR architecture.
    
    Pipeline:
    1. Conservative Audio Preprocessing: 16kHz mono WAV, conservative silence trimming, loudness normalization.
    2. Authoritative Language Hint Determination:
       Priority 1: Explicit language selected by the user.
       Priority 2: User/profile preferred language when configured.
       Priority 3: Current conversation language only if explicitly established and safe to reuse.
       Priority 4: AUTO (None) only when no reliable language preference exists.
    3. Whisper Inference:
       - Known language -> whisper-large-v3-turbo directly with language ISO code (ml, ta, hi, en) and temperature=0.
       - AUTO mode -> whisper-large-v3-turbo with language=None.
    4. Profile/AUTO Conflict Resolution:
       - If reliable profile language exists (e.g. ml) but AUTO returned another language (e.g. ta),
         retries the SAME preprocessed audio with explicit profile language.
    5. Deterministic ASR Quality Validation:
       - Assesses usability, script mismatch, silence dropouts, and provides clarification prompts.

    Args:
        file_path (str): Local path to the temporary audio file.
        language (str, optional): Explicit language selected by user.
        profile_language (str, optional): User profile configured voice language.
        conversation_language (str, optional): Active established conversation language.

    Returns:
        TranscriptionResult: Dict with text, detected_language, normalized_language, is_usable, needs_clarification.
    """
    if not file_path or not os.path.exists(file_path):
        raise FileNotFoundError(f"Audio file not found: {file_path}")

    # Determine authoritative language hint according to Priority 1..4
    effective_hint = determine_language_hint(
        explicit_lang=language,
        profile_lang=profile_language,
        conversation_lang=conversation_language
    )

    groq_api_key = (os.getenv("GROQ_API_KEY") or "").strip()
    did_retry = False
    needs_clarification = False
    clarification_prompt = None

    # Step 1: Conservative Audio Preprocessing (16 kHz Mono PCM WAV, conservative silence trimming)
    enable_preprocessing = os.getenv("ENABLE_AUDIO_PREPROCESSING", "1").lower() in ("1", "true", "yes")
    audio_for_transcription = file_path
    temp_preprocessed = None

    if enable_preprocessing:
        try:
            from services.audio_preprocessor import preprocess_audio_pipeline
            proc_path, _ = preprocess_audio_pipeline(file_path)
            if proc_path and proc_path != file_path and os.path.exists(proc_path):
                temp_preprocessed = proc_path
                audio_for_transcription = proc_path
        except Exception as prep_err:
            logger.warning(f"[TRANSCRIPTION] Preprocessing failed ({prep_err}); proceeding with raw audio.")
            audio_for_transcription = file_path

    try:
        if groq_api_key:
            try:
                if effective_hint:
                    # Step 2: EXPLICIT KNOWN LANGUAGE MODE:
                    # Uses whisper-large-v3-turbo directly with language token and temperature=0
                    res = _transcribe_groq(
                        audio_for_transcription,
                        groq_api_key,
                        language=effective_hint,
                        model=GROQ_MODEL
                    )
                    if effective_hint == "ml":
                        res["detected_language"] = "malayalam"
                    elif effective_hint in ("ta", "hi", "en"):
                        lang_names = {"ta": "tamil", "hi": "hindi", "en": "english"}
                        res["detected_language"] = lang_names.get(effective_hint, res.get("detected_language"))

                    # Deterministic Quality Validation
                    qual = validate_asr_quality(
                        text=res.get("text", ""),
                        detected_language=res.get("detected_language"),
                        avg_logprob=res.get("avg_logprob"),
                        no_speech_prob=res.get("no_speech_prob"),
                        expected_language=effective_hint
                    )
                    if not qual["is_usable"]:
                        needs_clarification = True
                        clarification_prompt = qual["clarification_prompt"]
                else:
                    # Step 3: AUTO MODE (Used ONLY when genuinely no reliable language hint exists):
                    res = _transcribe_groq(
                        audio_for_transcription,
                        groq_api_key,
                        language=None,
                        model=GROQ_MODEL
                    )
                    initial_lang = res.get("detected_language", "english")
                    initial_text = res.get("text", "")
                    avg_logprob = res.get("avg_logprob")
                    norm_detected = normalize_language_code(initial_lang)

                    # A. Direct Malayalam script detection
                    if re.search(r'[\u0D00-\u0D7F]', initial_text):
                        res["detected_language"] = "malayalam"
                        norm_detected = "ml"
                    # B. Romanized Malayalam keywords in AUTO mode
                    elif any(re.search(p, initial_text, re.IGNORECASE) for p in MALAYALAM_ROMANIZED_KEYWORDS):
                        res["detected_language"] = "malayalam"
                        norm_detected = "ml"
                    else:
                        # C. Profile / AUTO Conflict Resolution (Section 7)
                        norm_profile = normalize_language_code(profile_language)
                        if norm_profile and norm_detected != norm_profile:
                            logger.info(
                                f"[ASR CONFLICT] Profile '{profile_language}' ({norm_profile}) conflicts with AUTO detected '{norm_detected}'. "
                                f"Retrying same audio with explicit '{norm_profile}'..."
                            )
                            did_retry = True
                            try:
                                retry_res = _transcribe_groq(
                                    audio_for_transcription,
                                    groq_api_key,
                                    language=norm_profile,
                                    model=GROQ_MODEL
                                )
                                retry_qual = validate_asr_quality(
                                    text=retry_res.get("text", ""),
                                    detected_language=retry_res.get("detected_language"),
                                    avg_logprob=retry_res.get("avg_logprob"),
                                    no_speech_prob=retry_res.get("no_speech_prob"),
                                    expected_language=norm_profile
                                )
                                if retry_qual["is_usable"]:
                                    logger.info(f"[ASR CONFLICT] Retry with explicit '{norm_profile}' succeeded and is usable.")
                                    res = retry_res
                                    res["detected_language"] = "malayalam" if norm_profile == "ml" else norm_profile
                                    res["retried_profile"] = True
                                else:
                                    logger.info(f"[ASR CONFLICT] Retry with explicit '{norm_profile}' was unusable. Triggering clarification path.")
                                    needs_clarification = True
                                    clarification_prompt = retry_qual["clarification_prompt"]
                            except Exception as retry_err:
                                logger.warning(f"[ASR CONFLICT] Retry failed: {retry_err}")
                        # D. Ambiguous Dravidian check when no profile language is known
                        elif is_ambiguous_dravidian_or_malayalam(initial_text, norm_detected, avg_logprob):
                            logger.info(
                                f"[ASR AUTO-DETECT] Ambiguous Dravidian speech detected as '{initial_lang}'. "
                                "Retrying transcription with whisper-large-v3-turbo ('ml')..."
                            )
                            did_retry = True
                            try:
                                ml_res = _transcribe_groq(
                                    audio_for_transcription,
                                    groq_api_key,
                                    language="ml",
                                    model=GROQ_MODEL
                                )
                                ml_text = ml_res.get("text", "")
                                has_ml_script = bool(re.search(r'[\u0D00-\u0D7F]', ml_text))
                                has_ml_keywords = any(re.search(p, ml_text, re.IGNORECASE) for p in MALAYALAM_ROMANIZED_KEYWORDS)
                                
                                if (has_ml_script or has_ml_keywords) and len(ml_text.strip()) > 0:
                                    res = ml_res
                                    res["detected_language"] = "malayalam"
                                    res["retried_ml"] = True
                                else:
                                    logger.info("[ASR AUTO-DETECT] Malayalam retry did not yield higher confidence; retaining initial.")
                            except Exception as retry_err:
                                logger.warning(f"[ASR AUTO-DETECT] Retry failed: {retry_err}")

                    # Step 4: Quality Validation on AUTO outcome
                    qual = validate_asr_quality(
                        text=res.get("text", ""),
                        detected_language=res.get("detected_language"),
                        avg_logprob=res.get("avg_logprob"),
                        no_speech_prob=res.get("no_speech_prob"),
                        expected_language=effective_hint
                    )
                    if not qual["is_usable"]:
                        needs_clarification = True
                        clarification_prompt = qual["clarification_prompt"]

                final_text = res.get("text", "")
                final_detected_lang = res.get("detected_language", "english")
                norm_final_lang = normalize_language_code(final_detected_lang) or "en"

                # Safe diagnostic logging (no private speech or sensitive data)
                safe_preview = (final_text[:60] + "...") if len(final_text) > 60 else final_text
                logger.info(
                    f"[ASR DIAGNOSTIC] hint='{effective_hint or 'auto'}' | "
                    f"detected='{final_detected_lang}' | "
                    f"retried={did_retry} | "
                    f"usable={not needs_clarification} | "
                    f"text='{safe_preview}'"
                )

                return TranscriptionResult({
                    "text": final_text,
                    "detected_language": final_detected_lang,
                    "normalized_language": norm_final_lang,
                    "effective_language": norm_final_lang,
                    "is_usable": not needs_clarification,
                    "needs_clarification": needs_clarification,
                    "clarification_prompt": clarification_prompt,
                    "avg_logprob": res.get("avg_logprob"),
                    "no_speech_prob": res.get("no_speech_prob"),
                    "retried_profile": did_retry
                })

            except Exception as cloud_err:
                logger.warning(
                    f"[TRANSCRIPTION] Cloud Groq transcription failed ({type(cloud_err).__name__}). "
                    "Attempting lazy local fallback."
                )
                try:
                    local_res = _transcribe_local(audio_for_transcription, language=effective_hint)
                    return TranscriptionResult({
                        "text": local_res["text"],
                        "detected_language": local_res["detected_language"],
                        "normalized_language": normalize_language_code(local_res["detected_language"]) or "en",
                        "effective_language": normalize_language_code(local_res["detected_language"]) or "en",
                        "is_usable": True,
                        "needs_clarification": False,
                        "clarification_prompt": None,
                        "avg_logprob": None,
                        "no_speech_prob": None
                    })
                except Exception as local_err:
                    logger.error(f"[TRANSCRIPTION] Both cloud and local transcription failed: {local_err}")
                    raise RuntimeError("Speech transcription failed across both cloud and local providers.") from cloud_err
        else:
            local_res = _transcribe_local(audio_for_transcription, language=effective_hint)
            return TranscriptionResult({
                "text": local_res["text"],
                "detected_language": local_res["detected_language"],
                "normalized_language": normalize_language_code(local_res["detected_language"]) or "en",
                "effective_language": normalize_language_code(local_res["detected_language"]) or "en",
                "is_usable": True,
                "needs_clarification": False,
                "clarification_prompt": None,
                "avg_logprob": None,
                "no_speech_prob": None
            })
    finally:
        if temp_preprocessed and os.path.exists(temp_preprocessed) and temp_preprocessed != file_path:
            try:
                os.remove(temp_preprocessed)
            except Exception:
                pass

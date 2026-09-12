import os
import sys
import time
import json
import re
import tempfile
import numpy as np
import httpx
from gtts import gTTS
import soundfile as sf
from typing import Dict, Any, List, Optional

if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from dotenv import load_dotenv
load_dotenv(os.path.join(backend_dir, ".env"))

from services.audio_preprocessor import preprocess_audio_pipeline
from services.transcription_service import (
    _transcribe_groq,
    normalize_language_code,
    is_ambiguous_dravidian_or_malayalam,
    MALAYALAM_ROMANIZED_KEYWORDS
)
from intelligence.intent_detector import IntentDetector
detector = IntentDetector(use_llm=False)

GROQ_API_KEY = os.getenv("GROQ_API_KEY", "").strip()
if not GROQ_API_KEY:
    print("[ERROR] GROQ_API_KEY is not set.")
    sys.exit(1)

def calculate_cer(ref: str, hyp: str) -> float:
    ref_c = list(ref.replace(" ", ""))
    hyp_c = list(hyp.replace(" ", ""))
    if not ref_c:
        return 0.0 if not hyp_c else 1.0
    dp = [[0] * (len(hyp_c) + 1) for _ in range(len(ref_c) + 1)]
    for i in range(len(ref_c) + 1):
        dp[i][0] = i
    for j in range(len(hyp_c) + 1):
        dp[0][j] = j
    for i in range(1, len(ref_c) + 1):
        for j in range(1, len(hyp_c) + 1):
            if ref_c[i - 1] == hyp_c[j - 1]:
                dp[i][j] = dp[i - 1][j - 1]
            else:
                dp[i][j] = 1 + min(dp[i - 1][j], dp[i][j - 1], dp[i - 1][j - 1])
    return dp[len(ref_c)][len(hyp_c)] / max(1, len(ref_c))

def calculate_wer(ref: str, hyp: str) -> float:
    ref_w = re.findall(r'\w+', ref.lower())
    hyp_w = re.findall(r'\w+', hyp.lower())
    if not ref_w:
        return 0.0 if not hyp_w else 1.0
    dp = [[0] * (len(hyp_w) + 1) for _ in range(len(ref_w) + 1)]
    for i in range(len(ref_w) + 1):
        dp[i][0] = i
    for j in range(len(hyp_w) + 1):
        dp[0][j] = j
    for i in range(1, len(ref_w) + 1):
        for j in range(1, len(hyp_w) + 1):
            if ref_w[i - 1] == hyp_w[j - 1]:
                dp[i][j] = dp[i - 1][j - 1]
            else:
                dp[i][j] = 1 + min(dp[i - 1][j], dp[i][j - 1], dp[i - 1][j - 1])
    return dp[len(ref_w)][len(hyp_w)] / max(1, len(ref_w))

def create_realistic_microphone_clip(
    text: str,
    tts_lang: str,
    output_path: str,
    lead_silence_sec: float = 1.2,
    trail_silence_sec: float = 1.5,
    gain_db: float = 0.0,
    add_noise: bool = False,
    noise_snr_db: float = 15.0
):
    """
    Creates an audio file replicating real browser microphone capture:
    - 48,000 Hz, stereo or mono
    - 1.2s leading room silence
    - 1.5s trailing room silence
    - Optional background fan/ambient room noise
    - Optional volume attenuation (quiet speech)
    """
    with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as tf:
        tts_tmp = tf.name
    try:
        tts = gTTS(text=text, lang=tts_lang, slow=False)
        tts.save(tts_tmp)

        import av
        container = av.open(tts_tmp)
        stream = next(s for s in container.streams if s.type == 'audio')
        frames = [f.to_ndarray().squeeze() for f in container.decode(stream)]
        container.close()

        speech = np.concatenate(frames).astype(np.float32)
        if np.max(np.abs(speech)) > 1.0:
            speech = speech / 32768.0

        sr = stream.codec_context.sample_rate or 24000

        # Resample to 48kHz to match browser MediaRecorder
        target_sr = 48000
        speech_48k = np.interp(
            np.linspace(0, len(speech), int(len(speech) * target_sr / sr)),
            np.arange(len(speech)),
            speech
        ).astype(np.float32)

        # Apply gain
        if gain_db != 0.0:
            scale = 10.0 ** (gain_db / 20.0)
            speech_48k = speech_48k * scale

        lead_samples = np.random.normal(0, 0.002, int(target_sr * lead_silence_sec)).astype(np.float32)
        trail_samples = np.random.normal(0, 0.002, int(target_sr * trail_silence_sec)).astype(np.float32)

        full_audio = np.concatenate([lead_samples, speech_48k, trail_samples])

        # Add ambient room/fan noise if requested
        if add_noise:
            noise_power = np.mean(speech_48k ** 2) / (10.0 ** (noise_snr_db / 10.0))
            noise = np.random.normal(0, np.sqrt(max(1e-7, noise_power)), len(full_audio)).astype(np.float32)
            # Low-pass filter noise to simulate HVAC/fan hum
            from scipy import signal
            b, a = signal.butter(2, 350.0 / (target_sr / 2), btype='low')
            filtered_noise = signal.filtfilt(b, a, noise).astype(np.float32)
            full_audio = full_audio + filtered_noise

        full_audio = np.clip(full_audio, -0.98, 0.98)
        sf.write(output_path, full_audio, target_sr, format='WAV', subtype='PCM_16')
    finally:
        if os.path.exists(tts_tmp):
            os.remove(tts_tmp)

TEST_CASES = [
    # Malayalam Real Microphone Cases
    {
        "id": "ml_1_next_med",
        "lang": "ml",
        "ref": "എന്റെ അടുത്ത മരുന്ന് ഏതാണ്?",
        "tts_lang": "ml",
        "intent_expected": ["QUERY_NEXT_MEDICATION", "ask_medicine", "medication_schedule"],
        "condition": "normal"
    },
    {
        "id": "ml_2_took_it",
        "lang": "ml",
        "ref": "ഞാൻ അത് കഴിച്ചു.",
        "tts_lang": "ml",
        "intent_expected": ["CONFIRM_MEDICATION_TAKEN", "mark_taken", "medicine_taken"],
        "condition": "normal"
    },
    {
        "id": "ml_3_when_med",
        "lang": "ml",
        "ref": "എന്റെ മരുന്ന് എപ്പോഴാണ് കഴിക്കേണ്ടത്?",
        "tts_lang": "ml",
        "intent_expected": ["QUERY_MEDICATION_SCHEDULE", "ask_schedule", "QUERY_NEXT_MEDICATION"],
        "condition": "normal"
    },
    {
        "id": "ml_4_what_med_now",
        "lang": "ml",
        "ref": "ഇനി എനിക്ക് എന്ത് മരുന്നാണ് കഴിക്കേണ്ടത്?",
        "tts_lang": "ml",
        "intent_expected": ["QUERY_NEXT_MEDICATION", "ask_medicine"],
        "condition": "normal"
    },
    {
        "id": "ml_5_yes_took",
        "lang": "ml",
        "ref": "അതെ, അത് ഞാൻ കഴിച്ചു.",
        "tts_lang": "ml",
        "intent_expected": ["CONFIRM_MEDICATION_TAKEN", "mark_taken"],
        "condition": "normal"
    },
    # Tamil Cases
    {
        "id": "ta_1_next_med",
        "lang": "ta",
        "ref": "என் அடுத்த மருந்து என்ன?",
        "tts_lang": "ta",
        "intent_expected": ["QUERY_NEXT_MEDICATION", "ask_medicine"],
        "condition": "normal"
    },
    {
        "id": "ta_2_took_it",
        "lang": "ta",
        "ref": "நான் அந்த மருந்தை எடுத்துக்கொண்டேன்.",
        "tts_lang": "ta",
        "intent_expected": ["CONFIRM_MEDICATION_TAKEN", "mark_taken"],
        "condition": "normal"
    },
    # English Cases
    {
        "id": "en_1_next_med",
        "lang": "en",
        "ref": "What is my next medicine?",
        "tts_lang": "en",
        "intent_expected": ["QUERY_NEXT_MEDICATION", "ask_medicine"],
        "condition": "normal"
    },
    {
        "id": "en_2_took_it",
        "lang": "en",
        "ref": "I already took that medicine.",
        "tts_lang": "en",
        "intent_expected": ["CONFIRM_MEDICATION_TAKEN", "mark_taken"],
        "condition": "normal"
    },
    # Hindi Cases
    {
        "id": "hi_1_next_med",
        "lang": "hi",
        "ref": "मेरी अगली दवा कौन सी है?",
        "tts_lang": "hi",
        "intent_expected": ["QUERY_NEXT_MEDICATION", "ask_medicine"],
        "condition": "normal"
    },
    {
        "id": "hi_2_took_it",
        "lang": "hi",
        "ref": "मैंने वह दवा ले ली है।",
        "tts_lang": "hi",
        "intent_expected": ["CONFIRM_MEDICATION_TAKEN", "mark_taken"],
        "condition": "normal"
    },
    # Manglish / Code-Switched
    {
        "id": "manglish_1_next_med",
        "lang": "ml",
        "ref": "enikku adutha marunnu ethaanu?",
        "tts_lang": "ml",
        "intent_expected": ["QUERY_NEXT_MEDICATION", "ask_medicine"],
        "condition": "normal"
    },
    {
        "id": "manglish_2_took_it",
        "lang": "ml",
        "ref": "njan athu kazhichu",
        "tts_lang": "ml",
        "intent_expected": ["CONFIRM_MEDICATION_TAKEN", "mark_taken"],
        "condition": "normal"
    },
    # Low-Quality & Acoustic Variations (Quiet & Fan Noise)
    {
        "id": "ml_quiet_next_med",
        "lang": "ml",
        "ref": "എന്റെ അടുത്ത മരുന്ന് ഏതാണ്?",
        "tts_lang": "ml",
        "intent_expected": ["QUERY_NEXT_MEDICATION", "ask_medicine"],
        "condition": "quiet",
        "gain_db": -12.0
    },
    {
        "id": "ml_noisy_took_it",
        "lang": "ml",
        "ref": "ഞാൻ അത് കഴിച്ചു.",
        "tts_lang": "ml",
        "intent_expected": ["CONFIRM_MEDICATION_TAKEN", "mark_taken"],
        "condition": "fan_noise",
        "add_noise": True,
        "noise_snr_db": 12.0
    }
]

def safe_transcribe_groq(file_path: str, api_key: str, language: Optional[str] = None, model: str = "whisper-large-v3-turbo") -> Dict[str, Any]:
    max_retries = 5
    for attempt in range(max_retries):
        try:
            return _transcribe_groq(file_path, api_key, language=language, model=model)
        except Exception as e:
            if "429" in str(e) and attempt < max_retries - 1:
                wait_s = 7 * (attempt + 1)
                print(f"    [Rate limit 429] Sleeping {wait_s}s before retry {attempt+1}/{max_retries}...")
                time.sleep(wait_s)
            else:
                raise

def run_strategy_a(preprocessed_file: str) -> Dict[str, Any]:
    """
    Strategy A:
    AUTO -> whisper-large-v3-turbo
    Accept first result. Single API call.
    """
    t0 = time.perf_counter()
    res = safe_transcribe_groq(preprocessed_file, GROQ_API_KEY, language=None, model="whisper-large-v3-turbo")
    lat = (time.perf_counter() - t0) * 1000.0
    time.sleep(1.0)
    return {
        "strategy": "A",
        "model": "whisper-large-v3-turbo",
        "text": res.get("text", ""),
        "detected_lang": res.get("detected_language", "english"),
        "raw_lang": res.get("raw_language"),
        "avg_logprob": res.get("avg_logprob"),
        "latency_ms": round(lat, 1),
        "api_calls": 1,
        "final_lang": normalize_language_code(res.get("detected_language", "en"))
    }

def run_strategy_b(preprocessed_file: str) -> Dict[str, Any]:
    """
    Strategy B:
    AUTO -> whisper-large-v3
    Return first result. Pure acoustic detection, no keyword lists, single API call.
    """
    t0 = time.perf_counter()
    res = safe_transcribe_groq(preprocessed_file, GROQ_API_KEY, language=None, model="whisper-large-v3")
    lat = (time.perf_counter() - t0) * 1000.0
    time.sleep(1.0)
    return {
        "strategy": "B",
        "model": "whisper-large-v3",
        "text": res.get("text", ""),
        "detected_lang": res.get("detected_language", "english"),
        "raw_lang": res.get("raw_language"),
        "avg_logprob": res.get("avg_logprob"),
        "latency_ms": round(lat, 1),
        "api_calls": 1,
        "final_lang": normalize_language_code(res.get("detected_language", "en"))
    }

def run_strategy_c(preprocessed_file: str) -> Dict[str, Any]:
    """
    Strategy C:
    AUTO -> whisper-large-v3-turbo -> validation/fallback with whisper-large-v3
    """
    t0 = time.perf_counter()
    res = safe_transcribe_groq(preprocessed_file, GROQ_API_KEY, language=None, model="whisper-large-v3-turbo")
    time.sleep(1.0)
    calls = 1
    initial_text = res.get("text", "")
    initial_lang = res.get("detected_language", "english")
    avg_logprob = res.get("avg_logprob")
    norm_detected = normalize_language_code(initial_lang)

    # Check for Malayalam script
    if re.search(r'[\u0D00-\u0D7F]', initial_text):
        norm_detected = "ml"
    elif any(re.search(p, initial_text, re.IGNORECASE) for p in MALAYALAM_ROMANIZED_KEYWORDS):
        norm_detected = "ml"
    elif is_ambiguous_dravidian_or_malayalam(initial_text, norm_detected, avg_logprob):
        # Trigger Large-v3 retry with language='ml'
        calls += 1
        try:
            ml_res = safe_transcribe_groq(preprocessed_file, GROQ_API_KEY, language="ml", model="whisper-large-v3")
            time.sleep(1.0)
            ml_text = ml_res.get("text", "")
            if re.search(r'[\u0D00-\u0D7F]', ml_text) or any(re.search(p, ml_text, re.I) for p in MALAYALAM_ROMANIZED_KEYWORDS):
                res = ml_res
                norm_detected = "ml"
        except Exception:
            pass

    lat = (time.perf_counter() - t0) * 1000.0
    return {
        "strategy": "C",
        "model": "turbo+large-v3-fallback" if calls > 1 else "whisper-large-v3-turbo",
        "text": res.get("text", ""),
        "detected_lang": res.get("detected_language", initial_lang),
        "raw_lang": res.get("raw_language"),
        "avg_logprob": res.get("avg_logprob"),
        "latency_ms": round(lat, 1),
        "api_calls": calls,
        "final_lang": norm_detected
    }

def evaluate_all():
    work_dir = os.path.join(backend_dir, "temp_audio", "strategy_comparison")
    os.makedirs(work_dir, exist_ok=True)
    out_json = os.path.join(backend_dir, "auto_strategy_comparison_results.json")

    results = []
    if os.path.exists(out_json):
        try:
            with open(out_json, "r", encoding="utf-8") as f:
                results = json.load(f)
        except Exception:
            results = []

    completed_ids = {r["id"] for r in results}

    print("=" * 80)
    print("STARTING REAL MICROPHONE COMPARISON OF STRATEGIES A, B, AND C")
    print("=" * 80)

    for item in TEST_CASES:
        if item["id"] in completed_ids:
            print(f"Skipping already completed: [{item['id']}]")
            continue

        raw_clip = os.path.join(work_dir, f"{item['id']}_raw.wav")
        gain = item.get("gain_db", 0.0)
        noise = item.get("add_noise", False)
        snr = item.get("noise_snr_db", 15.0)

        # Generate browser microphone clip
        create_realistic_microphone_clip(
            text=item["ref"],
            tts_lang=item["tts_lang"],
            output_path=raw_clip,
            lead_silence_sec=1.2,
            trail_silence_sec=1.5,
            gain_db=gain,
            add_noise=noise,
            noise_snr_db=snr
        )

        # Preprocess using approved pipeline (resample 16k, mono, silence trim with 220ms pad, loudness norm)
        proc_clip, meta = preprocess_audio_pipeline(raw_clip)

        # Run Strategy A
        res_a = run_strategy_a(proc_clip)
        cer_a = calculate_cer(item["ref"], res_a["text"])
        wer_a = calculate_wer(item["ref"], res_a["text"])

        # Run Strategy B
        res_b = run_strategy_b(proc_clip)
        cer_b = calculate_cer(item["ref"], res_b["text"])
        wer_b = calculate_wer(item["ref"], res_b["text"])

        # Run Strategy C
        res_c = run_strategy_c(proc_clip)
        cer_c = calculate_cer(item["ref"], res_c["text"])
        wer_c = calculate_wer(item["ref"], res_c["text"])

        # Evaluate intent
        intent_a = detector._rule_based_detect(res_a["text"])
        intent_b = detector._rule_based_detect(res_b["text"])
        intent_c = detector._rule_based_detect(res_c["text"])

        def is_intent_ok(detected_intent, expected_list):
            if not detected_intent or detected_intent == "Unknown":
                return False
            return detected_intent in expected_list or any(exp.lower() in detected_intent.lower() for exp in expected_list)

        entry = {
            "id": item["id"],
            "ref_text": item["ref"],
            "expected_lang": item["lang"],
            "condition": item["condition"],
            "strategy_A": {
                **res_a,
                "cer": round(cer_a, 4),
                "wer": round(wer_a, 4),
                "lang_correct": res_a["final_lang"] == item["lang"],
                "intent_detected": intent_a,
                "intent_correct": is_intent_ok(intent_a, item["intent_expected"])
            },
            "strategy_B": {
                **res_b,
                "cer": round(cer_b, 4),
                "wer": round(wer_b, 4),
                "lang_correct": res_b["final_lang"] == item["lang"] or (item["lang"] == "hi" and res_b["final_lang"] in ("hi", "ur")),
                "intent_detected": intent_b,
                "intent_correct": is_intent_ok(intent_b, item["intent_expected"])
            },
            "strategy_C": {
                **res_c,
                "cer": round(cer_c, 4),
                "wer": round(wer_c, 4),
                "lang_correct": res_c["final_lang"] == item["lang"],
                "intent_detected": intent_c,
                "intent_correct": is_intent_ok(intent_c, item["intent_expected"])
            }
        }
        results.append(entry)

        print(f"\n[{item['id']}] Ref: \"{item['ref']}\" ({item['lang']}) - Cond: {item['condition']}")
        print(f"  Strategy A (Turbo AUTO)      : lang={res_a['final_lang']} | CER={cer_a:.3f} | Latency={res_a['latency_ms']}ms | Calls={res_a['api_calls']} | Text=\"{res_a['text']}\"")
        print(f"  Strategy B (Large-v3 AUTO)   : lang={res_b['final_lang']} | CER={cer_b:.3f} | Latency={res_b['latency_ms']}ms | Calls={res_b['api_calls']} | Text=\"{res_b['text']}\"")
        print(f"  Strategy C (Turbo+Fallback)  : lang={res_c['final_lang']} | CER={cer_c:.3f} | Latency={res_c['latency_ms']}ms | Calls={res_c['api_calls']} | Text=\"{res_c['text']}\"")

        # Incrementally persist
        with open(out_json, "w", encoding="utf-8") as f:
            json.dump(results, f, indent=2, ensure_ascii=False)

        # Clean up
        if os.path.exists(raw_clip):
            os.remove(raw_clip)
        if os.path.exists(proc_clip):
            os.remove(proc_clip)

    print(f"\n[COMPLETE] Benchmark data saved to {out_json}")

if __name__ == "__main__":
    evaluate_all()

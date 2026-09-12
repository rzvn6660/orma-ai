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

from services.audio_preprocessor import preprocess_audio_pipeline, analyze_audio
from services.transcription_service import normalize_language_code

GROQ_API_KEY = os.getenv("GROQ_API_KEY", "").strip()
GROQ_URL = "https://api.groq.com/openai/v1/audio/transcriptions"

if not GROQ_API_KEY:
    print("[ERROR] GROQ_API_KEY is not configured.")
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
    return round(dp[len(ref_c)][len(hyp_c)] / max(1, len(ref_c)), 4)

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
    return round(dp[len(ref_w)][len(hyp_w)] / max(1, len(ref_w)), 4)

def query_groq(file_path: str, model: str, language: Optional[str] = None) -> Dict[str, Any]:
    max_retries = 5
    for attempt in range(max_retries):
        try:
            with open(file_path, "rb") as f:
                content = f.read()
            ext = os.path.splitext(file_path)[1].lower()
            mime = "audio/wav" if ext == ".wav" else "audio/webm"
            files = {"file": (os.path.basename(file_path), content, mime)}
            data = {
                "model": model,
                "response_format": "verbose_json",
                "temperature": "0"
            }
            if language:
                data["language"] = language

            headers = {"Authorization": f"Bearer {GROQ_API_KEY}"}
            t0 = time.perf_counter()
            with httpx.Client(timeout=30.0) as client:
                resp = client.post(GROQ_URL, headers=headers, files=files, data=data)
            lat = round((time.perf_counter() - t0) * 1000.0, 1)

            if resp.status_code == 429:
                wait_s = 8 * (attempt + 1)
                print(f"    [HTTP 429 Rate Limit] Sleeping {wait_s}s (retry {attempt+1}/{max_retries})...")
                time.sleep(wait_s)
                continue

            if resp.status_code != 200:
                return {
                    "error": f"HTTP {resp.status_code}: {resp.text}",
                    "text": "",
                    "detected_language": "error",
                    "latency_ms": lat
                }

            payload = resp.json()
            text = (payload.get("text") or "").strip()
            detected_lang = payload.get("language") or "unknown"
            segments = payload.get("segments") or []
            avg_logprob = segments[0].get("avg_logprob") if segments else None
            no_speech_prob = segments[0].get("no_speech_prob") if segments else None

            # Pacing delay between successful calls
            time.sleep(1.0)

            return {
                "text": text,
                "detected_language": detected_lang,
                "normalized_language": normalize_language_code(detected_lang),
                "avg_logprob": round(avg_logprob, 3) if avg_logprob is not None else None,
                "no_speech_prob": round(no_speech_prob, 4) if no_speech_prob is not None else None,
                "latency_ms": lat
            }

        except Exception as e:
            if attempt < max_retries - 1:
                time.sleep(5)
            else:
                return {"error": str(e), "text": "", "detected_language": "error", "latency_ms": 0.0}

def generate_acoustic_sample(
    text: str,
    output_wav: str,
    tts_lang: str = "ml",
    speed_factor: float = 1.0,
    gain_db: float = 0.0,
    add_noise: bool = False,
    noise_snr_db: float = 14.0,
    add_echo: bool = False,
    lead_silence_s: float = 1.2,
    trail_silence_s: float = 1.5
):
    """
    Generates realistic speech sample with browser-level capture acoustic properties:
    - 48 kHz
    - Configurable speed (fast 1.25x, slow 0.8x)
    - Configurable gain (quiet -14 dB, normal 0 dB)
    - Ambient room / HVAC noise (14 dB SNR)
    - Room reverberation / echo
    - 1.2s leading silence, 1.5s trailing silence
    """
    with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as tf:
        tts_tmp = tf.name

    try:
        tts = gTTS(text=text, lang=tts_lang, slow=(speed_factor < 0.9))
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
        target_sr = 48000

        # Resample to 48kHz
        if sr != target_sr:
            speech_48k = np.interp(
                np.linspace(0, len(speech), int(len(speech) * target_sr / sr)),
                np.arange(len(speech)),
                speech
            ).astype(np.float32)
        else:
            speech_48k = speech

        # Speed modification via linear interpolation
        if speed_factor != 1.0:
            new_len = int(len(speech_48k) / speed_factor)
            speech_48k = np.interp(
                np.linspace(0, len(speech_48k), new_len),
                np.arange(len(speech_48k)),
                speech_48k
            ).astype(np.float32)

        # Gain modification
        if gain_db != 0.0:
            scale = 10.0 ** (gain_db / 20.0)
            speech_48k = speech_48k * scale

        # Add room echo / reverberation if requested
        if add_echo:
            decay = 0.35
            delay_samples = int(target_sr * 0.08) # 80ms delay
            echo = np.zeros(len(speech_48k) + delay_samples, dtype=np.float32)
            echo[:len(speech_48k)] += speech_48k
            echo[delay_samples:] += speech_48k * decay
            speech_48k = echo

        lead_samples = np.random.normal(0, 0.002, int(target_sr * lead_silence_s)).astype(np.float32)
        trail_samples = np.random.normal(0, 0.002, int(target_sr * trail_silence_s)).astype(np.float32)
        full_audio = np.concatenate([lead_samples, speech_48k, trail_samples])

        # Add HVAC / fan noise if requested
        if add_noise:
            noise_power = np.mean(speech_48k ** 2) / (10.0 ** (noise_snr_db / 10.0))
            raw_noise = np.random.normal(0, np.sqrt(max(1e-7, noise_power)), len(full_audio)).astype(np.float32)
            from scipy import signal
            b, a = signal.butter(2, 350.0 / (target_sr / 2), btype='low')
            filtered_noise = signal.filtfilt(b, a, raw_noise).astype(np.float32)
            full_audio = full_audio + filtered_noise

        full_audio = np.clip(full_audio, -0.98, 0.98)
        sf.write(output_wav, full_audio, target_sr, format='WAV', subtype='PCM_16')

    finally:
        if os.path.exists(tts_tmp):
            os.remove(tts_tmp)

# Comprehensive Dataset: 10 Primary + 4 Variations + Short Critical + Acoustic Variations + Manglish + Hindi/Urdu
DATASET = [
    # 1. Ten Primary Natural Malayalam Phrases
    {"id": "A_next_med", "ref": "എന്റെ അടുത്ത മരുന്ന് ഏതാണ്?", "cat": "primary_ml", "cond": "normal"},
    {"id": "B_took_it", "ref": "ഞാൻ അത് കഴിച്ചു.", "cat": "primary_ml", "cond": "normal"},
    {"id": "C_took_med", "ref": "ഞാൻ മരുന്ന് കഴിച്ചു.", "cat": "primary_ml", "cond": "normal"},
    {"id": "D_it_took", "ref": "അത് ഞാൻ കഴിച്ചു.", "cat": "primary_ml", "cond": "normal"},
    {"id": "E_yes_took", "ref": "അതെ, അത് ഞാൻ കഴിച്ചു.", "cat": "primary_ml", "cond": "normal"},
    {"id": "F_when_med", "ref": "എന്റെ മരുന്ന് എപ്പോഴാണ് കഴിക്കേണ്ടത്?", "cat": "primary_ml", "cond": "normal"},
    {"id": "G_what_med_now", "ref": "ഇനി എനിക്ക് എന്ത് മരുന്നാണ് കഴിക്കേണ്ടത്?", "cat": "primary_ml", "cond": "normal"},
    {"id": "H_next_med_short", "ref": "അടുത്ത മരുന്ന് ഏതാണ്?", "cat": "primary_ml", "cond": "normal"},
    {"id": "I_med_taken_q", "ref": "മരുന്ന് കഴിച്ചോ?", "cat": "primary_ml", "cond": "normal"},
    {"id": "J_i_took", "ref": "ഞാൻ കഴിച്ചു.", "cat": "primary_ml", "cond": "normal"},

    # 2. Natural Conversational Variations
    {"id": "var_athu_kazhichu", "ref": "അത് കഴിച്ചു.", "cat": "variation_ml", "cond": "normal"},
    {"id": "var_athe_kazhichu", "ref": "അതെ കഴിച്ചു.", "cat": "variation_ml", "cond": "normal"},
    {"id": "var_marunnu_eduthu", "ref": "മരുന്ന് എടുത്തു.", "cat": "variation_ml", "cond": "normal"},
    {"id": "var_njan_eduthu", "ref": "ഞാൻ അത് എടുത്തു.", "cat": "variation_ml", "cond": "normal"},

    # 3. Critical Ultra-Short Affirmations
    {"id": "short_kazhichu_only", "ref": "കഴിച്ചു", "cat": "short_critical", "cond": "normal"},
    {"id": "short_njan_kazhichu", "ref": "ഞാൻ കഴിച്ചു", "cat": "short_critical", "cond": "normal"},
    {"id": "short_athu_kazhichu", "ref": "അത് കഴിച്ചു", "cat": "short_critical", "cond": "normal"},
    {"id": "short_marunnu_kazhichu", "ref": "മരുന്ന് കഴിച്ചു", "cat": "short_critical", "cond": "normal"},
    {"id": "short_njan_athu_kazhichu", "ref": "ഞാൻ അത് കഴിച്ചു", "cat": "short_critical", "cond": "normal"},
    {"id": "short_athe_athu_kazhichu", "ref": "അതെ, അത് കഴിച്ചു", "cat": "short_critical", "cond": "normal"},

    # 4. Acoustic Variations (B: "ഞാൻ അത് കഴിച്ചു.")
    {"id": "acoust_B_quiet", "ref": "ഞാൻ അത് കഴിച്ചു.", "cat": "acoustic_ml", "cond": "quiet", "gain_db": -14.0},
    {"id": "acoust_B_fan_noise", "ref": "ഞാൻ അത് കഴിച്ചു.", "cat": "acoustic_ml", "cond": "fan_noise", "add_noise": True, "snr": 12.0},
    {"id": "acoust_B_echo", "ref": "ഞാൻ അത് കഴിച്ചു.", "cat": "acoustic_ml", "cond": "room_echo", "add_echo": True},
    {"id": "acoust_B_fast", "ref": "ഞാൻ അത് കഴിച്ചു.", "cat": "acoustic_ml", "cond": "fast_speech", "speed": 1.25},
    {"id": "acoust_B_slow", "ref": "ഞാൻ അത് കഴിച്ചു.", "cat": "acoustic_ml", "cond": "slow_speech", "speed": 0.80},

    # 5. Acoustic Variations (A: "എന്റെ അടുത്ത മരുന്ന് ഏതാണ്?")
    {"id": "acoust_A_quiet", "ref": "എന്റെ അടുത്ത മരുന്ന് ഏതാണ്?", "cat": "acoustic_ml", "cond": "quiet", "gain_db": -14.0},
    {"id": "acoust_A_fan_noise", "ref": "എന്റെ അടുത്ത മരുന്ന് ഏതാണ്?", "cat": "acoustic_ml", "cond": "fan_noise", "add_noise": True, "snr": 12.0},

    # 6. Manglish & Code-Switching
    {"id": "mang_1", "ref": "enikku adutha marunnu ethaanu?", "cat": "manglish", "cond": "normal", "tts_lang": "ml"},
    {"id": "mang_2", "ref": "njan athu kazhichu", "cat": "manglish", "cond": "normal", "tts_lang": "ml"},
    {"id": "mang_3", "ref": "marunnu kazhicho?", "cat": "manglish", "cond": "normal", "tts_lang": "ml"},
    {"id": "mang_4", "ref": "ente adutha medicine enthaanu?", "cat": "code_switch", "cond": "normal", "tts_lang": "ml"},
    {"id": "mang_5", "ref": "njan medicine kazhichu", "cat": "code_switch", "cond": "normal", "tts_lang": "ml"},

    # 7. Hindi / Urdu Script Investigation
    {"id": "hindi_med_taken", "ref": "मैंने वह दवा ले ली है।", "cat": "hindi_eval", "cond": "normal", "tts_lang": "hi"}
]

def run_evaluation():
    work_dir = os.path.join(backend_dir, "temp_audio", "hard_case_eval")
    os.makedirs(work_dir, exist_ok=True)
    out_json = os.path.join(backend_dir, "hard_case_malayalam_results.json")

    results = []
    if os.path.exists(out_json):
        try:
            with open(out_json, "r", encoding="utf-8") as f:
                results = json.load(f)
        except Exception:
            results = []

    completed_ids = {r["id"] for r in results}

    print("=" * 80)
    print(f"STARTING COMPREHENSIVE HARD-CASE MALAYALAM ASR BENCHMARK ({len(DATASET)} cases)")
    print("=" * 80)

    for item in DATASET:
        item_id = item["id"]
        if item_id in completed_ids:
            print(f"Skipping already completed: [{item_id}]")
            continue

        raw_wav = os.path.join(work_dir, f"{item_id}_raw.wav")
        generate_acoustic_sample(
            text=item["ref"],
            output_wav=raw_wav,
            tts_lang=item.get("tts_lang", "ml"),
            speed_factor=item.get("speed", 1.0),
            gain_db=item.get("gain_db", 0.0),
            add_noise=item.get("add_noise", False),
            noise_snr_db=item.get("snr", 14.0),
            add_echo=item.get("add_echo", False)
        )

        # Preprocess using approved pipeline
        proc_wav, _ = preprocess_audio_pipeline(raw_wav)

        print(f"\nEvaluating [{item_id}] (Category: {item['cat']} | Cond: {item['cond']})")
        print(f"  Reference: \"{item['ref']}\"")

        # Configuration 1: Turbo AUTO
        res_turbo_auto = query_groq(proc_wav, model="whisper-large-v3-turbo", language=None)
        cer_turbo_auto = calculate_cer(item["ref"], res_turbo_auto["text"])
        print(f"  1. Turbo AUTO          : lang={res_turbo_auto['normalized_language']} | CER={cer_turbo_auto} | Text=\"{res_turbo_auto['text']}\"")

        # Configuration 2: Large-v3 AUTO
        res_large_auto = query_groq(proc_wav, model="whisper-large-v3", language=None)
        cer_large_auto = calculate_cer(item["ref"], res_large_auto["text"])
        print(f"  2. Large-v3 AUTO       : lang={res_large_auto['normalized_language']} | CER={cer_large_auto} | Text=\"{res_large_auto['text']}\"")

        # Configuration 3: Turbo Explicit ML
        res_turbo_ml = query_groq(proc_wav, model="whisper-large-v3-turbo", language="ml")
        cer_turbo_ml = calculate_cer(item["ref"], res_turbo_ml["text"])
        print(f"  3. Turbo Explicit ML   : CER={cer_turbo_ml} | Text=\"{res_turbo_ml['text']}\"")

        # Configuration 4: Large-v3 Explicit ML
        res_large_ml = query_groq(proc_wav, model="whisper-large-v3", language="ml")
        cer_large_ml = calculate_cer(item["ref"], res_large_ml["text"])
        print(f"  4. Large-v3 Explicit ML: CER={cer_large_ml} | Text=\"{res_large_ml['text']}\"")

        # For acoustic variations, also evaluate RAW vs PROCESSED on Large-v3 AUTO
        raw_res = None
        if "acoust_" in item_id:
            raw_res = query_groq(raw_wav, model="whisper-large-v3", language=None)
            raw_cer = calculate_cer(item["ref"], raw_res["text"])
            print(f"  [RAW comparison]       : lang={raw_res['normalized_language']} | CER={raw_cer} | Text=\"{raw_res['text']}\"")

        entry = {
            "id": item_id,
            "ref_text": item["ref"],
            "category": item["cat"],
            "condition": item["cond"],
            "turbo_auto": {**res_turbo_auto, "cer": cer_turbo_auto},
            "large_auto": {**res_large_auto, "cer": cer_large_auto},
            "turbo_explicit_ml": {**res_turbo_ml, "cer": cer_turbo_ml},
            "large_explicit_ml": {**res_large_ml, "cer": cer_large_ml},
            "raw_eval": raw_res
        }
        results.append(entry)

        with open(out_json, "w", encoding="utf-8") as f:
            json.dump(results, f, indent=2, ensure_ascii=False)

        if os.path.exists(raw_wav):
            os.remove(raw_wav)
        if os.path.exists(proc_wav):
            os.remove(proc_wav)

    print(f"\n[EVALUATION COMPLETE] Results saved to {out_json}")

if __name__ == "__main__":
    run_evaluation()

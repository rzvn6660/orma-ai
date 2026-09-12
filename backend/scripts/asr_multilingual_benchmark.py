import os
import sys
import time
import json
import re
from typing import Dict, Any, List
from dotenv import load_dotenv

backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except Exception:
        pass

load_dotenv(os.path.join(backend_dir, ".env"))

import httpx
from services.audio_preprocessor import analyze_audio, preprocess_audio_pipeline
from services.transcription_service import normalize_language_code

GROQ_URL = "https://api.groq.com/openai/v1/audio/transcriptions"
GROQ_API_KEY = (os.getenv("GROQ_API_KEY") or "").strip()

MALAYALAM_PROMPT = "മലയാളം. എന്റെ അടുത്ത മരുന്ന് എന്താണ്? മരുന്ന് കഴിച്ചു. അടുത്ത മരുന്ന്. ഇന്ന്. നാളെ."

def groq_transcribe(
    audio_path: str,
    model: str = "whisper-large-v3-turbo",
    language: str = None,
    prompt: str = None,
    temperature: float = 0.0
) -> Dict[str, Any]:
    """Direct helper to call Groq transcription with verbose_json."""
    if not GROQ_API_KEY:
        raise ValueError("GROQ_API_KEY not set")

    ext = os.path.splitext(audio_path)[1].lower()
    mimes = {
        ".wav": "audio/wav",
        ".mp3": "audio/mpeg",
        ".webm": "audio/webm",
        ".ogg": "audio/ogg",
        ".m4a": "audio/m4a"
    }
    mime_type = mimes.get(ext, "audio/webm")

    with open(audio_path, "rb") as f:
        content = f.read()

    files = {"file": (os.path.basename(audio_path), content, mime_type)}
    data = {
        "model": model,
        "response_format": "verbose_json",
        "temperature": str(temperature)
    }
    if language:
        data["language"] = language
    if prompt:
        data["prompt"] = prompt

    headers = {"Authorization": f"Bearer {GROQ_API_KEY}"}

    t0 = time.perf_counter()
    with httpx.Client(timeout=30.0) as client:
        resp = client.post(GROQ_URL, headers=headers, files=files, data=data)
    elapsed_ms = round((time.perf_counter() - t0) * 1000, 1)

    if resp.status_code != 200:
        return {
            "error": f"HTTP {resp.status_code}: {resp.text}",
            "latency_ms": elapsed_ms
        }

    payload = resp.json()
    text = (payload.get("text") or "").strip()
    detected_lang = payload.get("language") or "unknown"
    segments = payload.get("segments") or []
    avg_logprob = segments[0].get("avg_logprob") if segments else None
    no_speech_prob = segments[0].get("no_speech_prob") if segments else None
    compression_ratio = segments[0].get("compression_ratio") if segments else None

    return {
        "text": text,
        "detected_language": detected_lang,
        "normalized_language": normalize_language_code(detected_lang),
        "avg_logprob": round(avg_logprob, 3) if avg_logprob is not None else None,
        "no_speech_prob": round(no_speech_prob, 4) if no_speech_prob is not None else None,
        "compression_ratio": round(compression_ratio, 3) if compression_ratio is not None else None,
        "latency_ms": elapsed_ms
    }

def calculate_cer(reference: str, hypothesis: str) -> float:
    """Calculates Character Error Rate (CER) between reference and hypothesis."""
    ref = re.sub(r'[^\w\s]', '', reference).strip()
    hyp = re.sub(r'[^\w\s]', '', hypothesis).strip()
    if not ref:
        return 0.0 if not hyp else 1.0

    r = list(ref)
    h = list(hyp)
    d = [[0] * (len(h) + 1) for _ in range(len(r) + 1)]
    for i in range(len(r) + 1):
        d[i][0] = i
    for j in range(len(h) + 1):
        d[0][j] = j

    for i in range(1, len(r) + 1):
        for j in range(1, len(h) + 1):
            if r[i - 1] == h[j - 1]:
                d[i][j] = d[i - 1][j - 1]
            else:
                d[i][j] = min(
                    d[i - 1][j] + 1,      # deletion
                    d[i][j - 1] + 1,      # insertion
                    d[i - 1][j - 1] + 1   # substitution
                )
    return round(d[len(r)][len(h)] / float(len(r)), 4)

def generate_test_audio_clips(output_dir: str) -> List[Dict[str, Any]]:
    """Generates audio test clips replicating real browser MediaRecorder conditions."""
    from gtts import gTTS
    import soundfile as sf
    import numpy as np
    import av

    os.makedirs(output_dir, exist_ok=True)

    test_items = [
        {"id": "ml_next_med", "lang": "ml", "text": "എന്റെ അടുത്ത മരുന്ന് ഏതാണ്?"},
        {"id": "ml_took_it", "lang": "ml", "text": "ഞാൻ അത് കഴിച്ചു."},
        {"id": "ml_when_med", "lang": "ml", "text": "എന്റെ മരുന്ന് എപ്പോഴാണ് കഴിക്കേണ്ടത്?"},
        {"id": "ml_what_now", "lang": "ml", "text": "ഇനി എനിക്ക് എന്ത് മരുന്നാണ് കഴിക്കേണ്ടത്?"},
        {"id": "ml_yes_took", "lang": "ml", "text": "അതെ, അത് ഞാൻ കഴിച്ചു."},
        {"id": "ta_next_med", "lang": "ta", "text": "என் அடுத்த மருந்து என்ன?"},
        {"id": "ta_took_it", "lang": "ta", "text": "நான் அந்த மருந்தை எடுத்துக்கொண்டேன்."},
        {"id": "en_next_med", "lang": "en", "text": "What is my next medicine?"},
        {"id": "en_took_it", "lang": "en", "text": "I already took that medicine."},
        {"id": "hi_next_med", "lang": "hi", "text": "मेरी अगली दवा कौन सी है?"},
        {"id": "hi_took_it", "lang": "hi", "text": "मैंने वह दवा ले ली है।"}
    ]

    generated_clips = []

    for item in test_items:
        clean_mp3 = os.path.join(output_dir, f"{item['id']}_raw.mp3")
        tts = gTTS(text=item["text"], lang=item["lang"])
        tts.save(clean_mp3)

        # Decode MP3 to numpy
        container = av.open(clean_mp3)
        stream = next(s for s in container.streams if s.type == 'audio')
        frames = [f.to_ndarray().squeeze() for f in container.decode(stream)]
        container.close()
        speech_arr = np.concatenate(frames).astype(np.float32)
        if np.max(np.abs(speech_arr)) > 1.0:
            speech_arr = speech_arr / 32768.0

        sr = stream.codec_context.sample_rate

        # 1. Condition: Real Browser MediaRecorder with 1.0s leading silence & 1.7s trailing room silence
        lead_silence = np.random.normal(0, 0.002, int(sr * 1.0)).astype(np.float32)
        trail_silence = np.random.normal(0, 0.002, int(sr * 1.7)).astype(np.float32)
        full_clip = np.concatenate([lead_silence, speech_arr, trail_silence])

        browser_wav = os.path.join(output_dir, f"{item['id']}_browser.wav")
        sf.write(browser_wav, full_clip, sr, subtype='PCM_16')

        # 2. Condition: Quiet audio (-10 dB gain) with browser silence
        quiet_clip = full_clip * 0.32
        quiet_wav = os.path.join(output_dir, f"{item['id']}_quiet.wav")
        sf.write(quiet_wav, quiet_clip, sr, subtype='PCM_16')

        generated_clips.append({
            "item": item,
            "browser_path": browser_wav,
            "quiet_path": quiet_wav
        })

    return generated_clips

def run_benchmark():
    test_dir = os.path.join(backend_dir, "temp_audio", "benchmark_clips")
    print(f"[BENCHMARK] Generating realistic test audio in {test_dir}...")
    clips = generate_test_audio_clips(test_dir)
    print(f"[BENCHMARK] Generated {len(clips)} multilingual test items.")

    results = []

    print("\n" + "="*80)
    print("STARTING CONTROLLED MULTILINGUAL ASR ACCURACY & PREPROCESSING BENCHMARK")
    print("="*80)

    for entry in clips:
        item = entry["item"]
        ref_text = item["text"]
        target_lang = item["lang"]
        raw_path = entry["browser_path"]
        quiet_path = entry["quiet_path"]

        # Run Preprocessing on raw browser path
        proc_path, proc_meta = preprocess_audio_pipeline(raw_path)

        print(f"\nEvaluating: [{target_lang.upper()}] \"{ref_text}\"")

        # Test 1: RAW + Turbo (AUTO)
        res_raw_turbo = groq_transcribe(raw_path, model="whisper-large-v3-turbo")
        cer_raw_turbo = calculate_cer(ref_text, res_raw_turbo.get("text", ""))

        # Test 2: PREPROCESSED + Turbo (AUTO)
        res_proc_turbo = groq_transcribe(proc_path, model="whisper-large-v3-turbo")
        cer_proc_turbo = calculate_cer(ref_text, res_proc_turbo.get("text", ""))

        # Test 3: PREPROCESSED + Large-v3 (AUTO)
        res_proc_large3 = groq_transcribe(proc_path, model="whisper-large-v3")
        cer_proc_large3 = calculate_cer(ref_text, res_proc_large3.get("text", ""))

        # Test 4: PREPROCESSED + Explicit Language (Turbo)
        res_proc_exp_turbo = groq_transcribe(proc_path, model="whisper-large-v3-turbo", language=target_lang)
        cer_proc_exp_turbo = calculate_cer(ref_text, res_proc_exp_turbo.get("text", ""))

        # Test 5: PREPROCESSED + Explicit Language + Prompt (if Malayalam)
        if target_lang == "ml":
            res_ml_prompt = groq_transcribe(proc_path, model="whisper-large-v3-turbo", language="ml", prompt=MALAYALAM_PROMPT)
            cer_ml_prompt = calculate_cer(ref_text, res_ml_prompt.get("text", ""))
        else:
            res_ml_prompt = res_proc_exp_turbo
            cer_ml_prompt = cer_proc_exp_turbo

        # Test 6: Quiet Audio: RAW vs PREPROCESSED
        res_quiet_raw = groq_transcribe(quiet_path, model="whisper-large-v3-turbo")
        proc_quiet_path, _ = preprocess_audio_pipeline(quiet_path)
        res_quiet_proc = groq_transcribe(proc_quiet_path, model="whisper-large-v3-turbo")

        row = {
            "id": item["id"],
            "lang": target_lang,
            "ref_text": ref_text,
            "raw_turbo": {
                "text": res_raw_turbo.get("text", ""),
                "detected": res_raw_turbo.get("normalized_language"),
                "cer": cer_raw_turbo,
                "latency_ms": res_raw_turbo.get("latency_ms")
            },
            "proc_turbo": {
                "text": res_proc_turbo.get("text", ""),
                "detected": res_proc_turbo.get("normalized_language"),
                "cer": cer_proc_turbo,
                "latency_ms": res_proc_turbo.get("latency_ms")
            },
            "proc_large3": {
                "text": res_proc_large3.get("text", ""),
                "detected": res_proc_large3.get("normalized_language"),
                "cer": cer_proc_large3,
                "latency_ms": res_proc_large3.get("latency_ms")
            },
            "proc_explicit": {
                "text": res_proc_exp_turbo.get("text", ""),
                "cer": cer_proc_exp_turbo,
                "latency_ms": res_proc_exp_turbo.get("latency_ms")
            },
            "ml_prompt": {
                "text": res_ml_prompt.get("text", ""),
                "cer": cer_ml_prompt
            } if target_lang == "ml" else None,
            "quiet_eval": {
                "raw_cer": calculate_cer(ref_text, res_quiet_raw.get("text", "")),
                "raw_detected": res_quiet_raw.get("normalized_language"),
                "proc_cer": calculate_cer(ref_text, res_quiet_proc.get("text", "")),
                "proc_detected": res_quiet_proc.get("normalized_language")
            }
        }
        results.append(row)

        print(f"  RAW + Turbo (AUTO)       : lang={row['raw_turbo']['detected']} | CER={row['raw_turbo']['cer']} | text=\"{row['raw_turbo']['text']}\"")
        print(f"  PREPROCESSED + Turbo     : lang={row['proc_turbo']['detected']} | CER={row['proc_turbo']['cer']} | text=\"{row['proc_turbo']['text']}\"")
        print(f"  PREPROCESSED + Large-v3  : lang={row['proc_large3']['detected']} | CER={row['proc_large3']['cer']} | text=\"{row['proc_large3']['text']}\"")
        print(f"  PREPROCESSED + Explicit  : CER={row['proc_explicit']['cer']} | text=\"{row['proc_explicit']['text']}\"")
        if target_lang == "ml":
            print(f"  PREPROCESSED + ML Prompt : CER={row['ml_prompt']['cer']} | text=\"{row['ml_prompt']['text']}\"")
        print(f"  Quiet Audio [Raw vs Proc]: CER {row['quiet_eval']['raw_cer']} -> {row['quiet_eval']['proc_cer']} | Lang {row['quiet_eval']['raw_detected']} -> {row['quiet_eval']['proc_detected']}")

        # Clean up temporary preprocessed files
        for p in [proc_path, proc_quiet_path]:
            if os.path.exists(p) and p not in (raw_path, quiet_path):
                try:
                    os.remove(p)
                except:
                    pass

    # Summary Report
    out_file = os.path.join(backend_dir, "asr_benchmark_results.json")
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    print(f"\n[BENCHMARK COMPLETE] Full results written to {out_file}")

if __name__ == "__main__":
    run_benchmark()

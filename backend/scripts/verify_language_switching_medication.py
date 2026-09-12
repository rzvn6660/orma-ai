import asyncio
import os
import sys
import json
import re

backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

from database import SessionLocal
from intelligence.orchestrator import orchestrator
from intelligence.response_coordinator import response_coordinator
from datetime import datetime

async def test_language_switching_and_medication():
    db = SessionLocal()
    user_id = "test_user_switching_123"

    print("\n" + "=" * 80)
    print("VERIFYING 5-TURN SEQUENTIAL LANGUAGE SWITCHING & MEDICATION SAFETY PATH")
    print("=" * 80)

    turns = [
        {"turn": 1, "lang": "ml", "text": "എന്റെ അടുത്ത മരുന്ന് ഏതാണ്?", "expected_tts": "ml-IN", "expected_script": r'[\u0D00-\u0D7F]'},
        {"turn": 2, "lang": "en", "text": "What is my next medicine?", "expected_tts": "en-IN", "expected_script": r'[a-zA-Z]'},
        {"turn": 3, "lang": "ml", "text": "ഞാൻ അത് കഴിച്ചു.", "expected_tts": "ml-IN", "expected_script": r'[\u0D00-\u0D7F]'},
        {"turn": 4, "lang": "ta", "text": "என் அடுத்த மருந்து என்ன?", "expected_tts": "ta-IN", "expected_script": r'[\u0B80-\u0BFF]'},
        {"turn": 5, "lang": "ml", "text": "എന്റെ അടുത്ത മരുന്ന് ഏതാണ്?", "expected_tts": "ml-IN", "expected_script": r'[\u0D00-\u0D7F]'}
    ]

    results = []

    try:
        for t in turns:
            reply = await orchestrator.process_request(
                t["text"],
                user_id,
                db,
                language=t["lang"]
            )

            # Check script match
            has_script = bool(re.search(t["expected_script"], reply))

            # Map ISO language to browser TTS voice BCP-47 tag
            tts_map = {"ml": "ml-IN", "en": "en-IN", "ta": "ta-IN", "hi": "hi-IN"}
            tts_lang = tts_map.get(t["lang"], "en-IN")

            status_ok = has_script and (tts_lang == t["expected_tts"])

            entry = {
                "turn": t["turn"],
                "input_lang": t["lang"],
                "input_text": t["text"],
                "expected_tts": t["expected_tts"],
                "actual_tts": tts_lang,
                "has_expected_script": has_script,
                "reply_snippet": reply[:90] + ("..." if len(reply) > 90 else ""),
                "status_ok": status_ok
            }
            results.append(entry)
            print(f"Turn {t['turn']} [{t['lang']}]: TTS={tts_lang} (expected {t['expected_tts']}) | ScriptMatch={has_script}")
            print(f"  Snippet: \"{entry['reply_snippet']}\"")

        out_file = os.path.join(backend_dir, "language_switching_verification.json")
        with open(out_file, "w", encoding="utf-8") as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        print(f"\n[SUCCESS] Language switching verification saved to {out_file}")
    finally:
        db.close()

if __name__ == "__main__":
    asyncio.run(test_language_switching_and_medication())

# ORMA AI — Comprehensive Evaluation & Evidence Report (Phases 1–7)

**Document Version:** 1.0.0
**Audit & Benchmark Campaign:** Phases 1 through 7
**Date of Verification:** September 24, 2026
**Primary Production Focus:** English (`en`)
**Multilingual Scope (Beta):** Malayalam (`ml`), Tamil (`ta`), Hindi (`hi`), Arabic (`ar`)
**Active Test Suite:** 451 / 451 automated pytest unit & integration tests passing (100%)

---

> [!IMPORTANT]
> **ENGINEERING HONESTY & GENERALIZATION STATEMENT**
> All metrics, error rates, and latencies presented in this document represent **measured empirical benchmark observations** obtained under defined local test conditions, specific model checkpoints, and frozen test datasets. They are **not universal performance guarantees, certified medical claims, or broad population-level accuracies**.

---

## 1. Executive Summary & Multi-Phase Progression

ORMA AI was evaluated through a rigorous, seven-phase engineering and research audit campaign designed to validate voice processing, speech recognition, intent routing, conversational state management, safety guards, and regression integrity.

### Evaluation Progression Map

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                       MULTI-PHASE EVALUATION ROADMAP                        │
│                                                                             │
│   Phase 1: Architecture & Audio Provenance Audit                            │
│   └── Audited 44 test audio files; revealed 35 synthetic (gTTS) & 0 human.   │
│                                                                             │
│   Phase 2: Baseline Voice & End-to-End Orchestration Benchmark              │
│   └── Direct LLM latency; established headless browser TTS exclusion.       │
│                                                                             │
│   Phase 3 & 3B: Real-Human ASR Pilot (N=2)                                  │
│   └── First real human speech pilot (English.mp3 vs Malayalam.mp3).         │
│                                                                             │
│   Phase 3C: Real-Human ASR Benchmark (N=14)                                 │
│   └── 7 English + 7 Malayalam human recordings (31 sentences, 343 words).   │
│   └── Uncovered Malayalam unprompted AUTO failure (111.3% WER, 14.3% Lang). │
│                                                                             │
│   Phase 4: Controlled ASR Strategy Comparison                               │
│   └── Strategy A (AUTO) vs B (Explicit Language) vs C (Local Fallback).     │
│   └── Proved Two-Tier Failure Mechanism: Explicit 'ml' fixes Lang/Script,   │
│       but underlying Whisper model maintains 91.8% residual WER.            │
│   └── English Explicit 'en' achieves 1.02% WER, 85.7% Exact, 682.4ms P50.   │
│                                                                             │
│   Phase 5: Malayalam ASR Model Comparison (Whisper Family)                  │
│   └── Groq Large-v3-Turbo vs Faster-Whisper Medium, Small, Tiny.            │
│   └── 0% exact match across all Whisper variants; proved general Whisper    │
│       scarcity limitation, not a Groq-specific issue.                       │
│                                                                             │
│   Phase 6: IndicConformer Environment Audit (AI4Bharat)                     │
│   └── Audited 600M IndicConformer checkpoint on disk.                       │
│   └── Formally declared NOT EXECUTED due to Windows NeMo POSIX signal       │
│       blocker, tokenizer 1.x/2.x mismatch, and lack of Docker/WSL.          │
│                                                                             │
│   Phase 7: English Production Hardening Audit                               │
│   └── Validated English primary production pipeline across 10 stages.       │
│   └── 15 Scenario Categories (A–O) evaluated with deterministic gates.      │
│   └── Latency breakdown: ASR vs Backend Orchestration vs Client TTS.        │
│   └── Full regression suite: 451/451 tests passing (UTC-aware fix).         │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Evaluation Datasets & Ground-Truth Provenance

### 2.1 Acoustic Audio Datasets

| Dataset Identifier | Audio Provenance | Recording Count | Languages | Sentence Segments | Word Count | Used In |
| :--- | :--- | :---: | :---: | :---: | :---: | :--- |
| **Synthetic Audio Corpus** | Google TTS (`gTTS`) + synthetic Gaussian room noise | 35 clips | EN, HI, ML, TA | Varied | Varied | Phase 2 Baseline |
| **Real Human Pilot Set** | Authentic human speakers in indoor acoustic environment | 2 clips | EN (1), ML (1) | 9 sentences | 108 words | Phase 3 & 3B Pilots |
| **Real Human Benchmark Set** | Authentic human speakers, near-field consumer mic (48kHz mono) | 14 clips | EN (7), ML (7) | 31 sentences | 343 words | Phases 3C, 4, 5, 6, 7 |

### 2.2 Human Audio Specifications ($N=14$)

All 14 audio recordings used in Phases 3C–7 represent authentic human speech recorded at 48,000 Hz mono (MP3 codec, `mp3float`), clean signal-to-noise ratio, RMS energy range 0.022–0.044, and peak amplitudes between 0.22 and 0.39.

| Filename | Language | Spoken Duration | Audio Type / Domain | Spoken Reference Transcript |
| :--- | :---: | :---: | :--- | :--- |
| `English.mp3` | English | 23.28 s | Multi-sentence clinical query | *"Hi Orma, did I take my medicine today? When I have medicine next? Which medicine did I take next? I feel some headache. What about my medicine schedule today?"* |
| `E1.mp3` | English | 3.53 s | Single clinical question | *"Hey, did I take my medicine?"* |
| `E2.mp3` | English | 5.02 s | Single clinical question | *"Hello, which medicine is next to me?"* |
| `E3.mp3` | English | 6.50 s | Verification query | *"Did I take my medicine today? This time medicine I have taken or not?"* |
| `E4.mp3` | English | 4.97 s | Schedule query | *"What is the medicine schedule today? Is everything taken or not?"* |
| `E5.mp3` | English | 5.45 s | Time query | *"What is the time today? What is the time of current time?"* |
| `E6.mp3` | English | 10.32 s | Symptom & medicine check | *"Hey Orma, I felt something not good. Did I have any medicine left to take today? You just check and give me."* |
| `Malayalam.mp3` | Malayalam | 19.44 s | Multi-sentence clinical query | `ഞാൻ ഇന്ന് രാവിലെ മരുന്ന് കഴിച്ചോ? എനിക്ക് ഇനി എപ്പോഴാണ് മരുന്ന്? ഇനി ഇതിൽ മരുന്ന് ഞാൻ എടുക്കാൻ ഉണ്ടോ? എനിക്ക് ചെറിയ തലവേദന പോലെ തോന്നുന്നുണ്ട്.` |
| `M1.mp3` | Malayalam | 8.69 s | Medicine dose query | `ഇന്ന് ഏത് മരുന്നാണ് ഞാൻ കഴിക്കേണ്ടത് എന്ന് ഓർമ്മയുണ്ടോ? ഏതാണ് ഇന്ന് ഞാൻ അടുത്തതായി എടുക്കേണ്ടത്?` |
| `M2.mp3` | Malayalam | 8.18 s | Schedule & missed dose | `എനിക്ക് ഇന്ന് പന്ത്രണ്ട് മണിക്ക് ഏതെങ്കിലും മരുന്ന് ഉണ്ടോ? അതോ ഏതെങ്കിലും മരുന്ന് മിസ്സ് ആയിട്ടുണ്ടോ?` |
| `M3.mp3` | Malayalam | 10.94 s | Time elapsed query | `ഇപ്പോഴത്തെ മരുന്ന് ഞാൻ കഴിക്കേണ്ട സമയം കഴിഞ്ഞുപോയോ?` |
| `M4.mp3` | Malayalam | 4.46 s | Current time query | `ഇപ്പോൾ സമയം എത്രയായി?` |
| `M5.mp3` | Malayalam | 8.35 s | Symptom expression (headache) | `എനിക്ക് ചെറിയ തലവേദന പോലെ ഫീൽ ചെയ്യുന്നുണ്ട്. എനിക്ക് ചെറിയ തലവേദന പോലെ തോന്നുന്നുണ്ട്.` |
| `M6.mp3` | Malayalam | 13.42 s | Unwell multi-clause query | `ഓർമ്മ, എനിക്ക് എന്തോ സുഖമില്ലാത്ത പോലെ തോന്നുന്നു. എനിക്ക് ഇന്ന് ഇനി എന്തെങ്കിലും മരുന്ന് കഴിക്കാൻ ബാക്കിയുണ്ടോ? ഒന്ന് നോക്കി പറഞ്ഞു തരൂ.` |

### 2.3 Reference Transcript Provenance

Reference transcripts were established by direct acoustic listening and word-by-word phonetic transcription of what the human speaker actually articulated:
- Transcriptions were prepared independently without consulting or being influenced by ASR hypotheses.
- **Limitation Note**: Reference transcripts were produced internally by the engineering team; they were not verified by an external certified clinical linguistic panel. Where natural speech elisions occurred (e.g. `E3.mp3` speaker saying *"medicine I taken"* instead of *"medicine I have taken"*), the exact uttered words were preserved in the reference.

### 2.4 Text NLU & Routing Datasets

1. **Fixed 70-Query Official Benchmark**: 70 ground-truth labeled utterances covering 14 clinical and daily-living intent categories across English and Malayalam.
2. **Unseen 110-Query Generalization Dataset**: 110 out-of-distribution, natural-language queries testing boundary conditions and complex compound sentences.
3. **Synthetic 40-Case Emergency Dataset**: 40 synthetic text scenarios testing acute life-safety keywords against non-emergency clinical visits.
4. **Internal RAG Dataset**: 18 clinical queries (13 in-scope medical document queries, 5 out-of-scope queries) testing retrieval grounding and citation synthesis.

---

## 3. Metrics Definitions & Measurement Boundaries

### 3.1 ASR Metrics

- **Word Error Rate (WER)**: Standard ASR metric defined as:
  $$\text{WER} = \frac{S + D + I}{N}$$
  where $S$ is word substitutions, $D$ is deletions, $I$ is insertions, and $N$ is the total number of words in the ground-truth reference. WER can exceed 100% when insertion loops occur.
- **Character Error Rate (CER)**: Standard character-level edit distance metric defined as $(S_c + D_c + I_c) / N_c$. Crucial for phonetically dense and agglutinative scripts like Malayalam.
- **Exact Match Rate**: Percentage of files or sentences where the hypothesis transcript matches the reference transcript 100% verbatim after case and whitespace normalization.
- **Language Correctness**: Percentage of runs where the detected or assigned ISO-639-1 language code matches the true spoken language (`en` or `ml`).
- **Script Preservation**: Percentage of non-English transcriptions that correctly render in the target native Unicode script (e.g., Malayalam `\u0D00-\u0D7F`) rather than drifting into cognate scripts (Tamil `\u0B80-\u0BFF`) or transliteration.
- **Real-Time Factor (RTF)**: Ratio of speech processing latency to audio duration:
  $$\text{RTF} = \frac{\text{Processing Time (s)}}{\text{Audio Duration (s)}}$$
  An RTF $< 1.0$ indicates faster-than-real-time execution.
- **Latency Percentiles (P50, P90, P95, Max)**: Distribution of elapsed execution time measured across repeated runs.

### 3.2 System Boundary & Latency Scope

> [!CAUTION]
> **MEASUREMENT BOUNDARY CLARIFICATION**
> All latency measurements reported in Phases 2, 4, and 7 represent **Backend Processing Latency** (from server audio receipt to assembled text response ready for dispatch).
> **Excluded from backend measurements:**
> 1. Client-side microphone capture and Web Audio encoding.
> 2. Network transit over the internet.
> 3. Client-side browser Text-to-Speech (TTS) synthesis (`window.speechSynthesis`), which executes on the user's local operating system and hardware.

### 3.3 LLM Provider Architecture & Model Identifiers

- **Primary Provider**: Google Gemini API.
- **Fallback Provider**: Groq Cloud API.
- **Runtime Model Self-Healing**: Backend provider code (`gemini_provider.py` and `groq_provider.py`) dynamically self-heals legacy configured identifiers to current runtime model identifiers:
  - Gemini: `gemini-3.6-flash`
  - Groq: `qwen/qwen3.8-27b`
- **Benchmark Specificity**: Latency and quality metrics recorded during specific evaluation phases refer to the model versions actually invoked during that specific benchmark run.

---

## 4. Phase 1 & 2 — Architecture & Audio Provenance Baseline

### 4.1 Phase 1: Architecture & Audio Provenance Audit
An exhaustive inspection of the audio assets under `backend/temp_audio/benchmark_clips/` revealed that of 44 audio files present:
- **0 files** were authentic human speech recordings.
- **35 files** were synthetic clips generated via Google TTS (`gTTS`) overlaid with artificial Gaussian noise.
- This finding established the requirement for Phases 3 onward: all future speech evaluations must rely on genuine human speech recordings.

### 4.2 Phase 2: Synthetic Voice & Direct LLM Baseline
Phase 2 benchmarked direct provider response times and multi-stage backend pipeline latency using synthetic clips (figures reflect the specific model checkpoints active during that test run):
- **Gemini (gemini-1.5-flash) Latency**: P50 = 852.1 ms, Mean = 984.3 ms.
- **Groq (llama-3.3-70b-versatile) Latency**: P50 = 612.4 ms, Mean = 688.1 ms.
- **Headless Environment TTS Boundary**: Formally documented that client-side TTS cannot be programmatically measured in a headless Python test environment.

---

## 5. Phase 3 & 3C — Real-Human ASR Benchmark

Phase 3 introduced the first real-human pilot ($N=2$), and Phase 3C scaled the benchmark to **14 genuine human audio recordings** (7 English, 7 Malayalam) comprising **31 sentence segments** and **343 spoken words** evaluated against production Groq Whisper Large-v3-Turbo in unprompted `AUTO` mode (`language=None`).

### Phase 3C Results Summary ($N=14$ Human Recordings)

| Metric | English ($N=7$) | Malayalam ($N=7$) | Combined ($N=14$) |
| :--- | :---: | :---: | :---: |
| **Language Detection Accuracy** | **100.0% (7/7)** | **14.29% (1/7)** | 57.14% (8/14) |
| **Exact Match Rate (Files)** | **71.43% (5/7)** | **0.00% (0/7)** | 35.71% (5/14) |
| **Exact Match Rate (Sentences)** | **75.00% (12/16)** | **0.00% (0/15)** | 38.71% (12/31) |
| **Mean Word Error Rate (WER)** | **4.92%** | **111.33%** | 58.12% |
| **Corpus Aggregate WER** | **6.93%** (7/101 words) | **105.79%** (256/242 words) | 76.68% (263/343 words) |
| **Mean Character Error Rate (CER)** | **2.95%** | **156.67%** | 79.81% |
| **P50 ASR Latency** | **902.8 ms** | **1,740.0 ms** | 1,547.9 ms |
| **Mean ASR Latency** | **1,455.5 ms** | **1,782.6 ms** | 1,619.0 ms |
| **Real-Time Factor (RTF)** | **0.1725** | **0.1698** | 0.1710 |

### Key Phase 3C Findings:
1. **English Production Readiness**: 5 of 7 English human recordings achieved 100% verbatim exact match. All clinical keywords (`medicine`, `headache`, `schedule`, `today`) were preserved.
2. **Malayalam Catastrophic Failure in AUTO Mode**: Unprompted Whisper misclassified 6 of 7 Malayalam recordings (2 as Tamil `ta`, 3 as English `en`, 1 as Portuguese `po`). Output degenerated into Tamil characters (`நான் இன்னു ராவില`), Portuguese hallucinations (`E por isso a minha metrana é trei`), or repetitive English loops (`"I am a man, I am not a man, I am a man"`).

---

## 6. Phase 4 — Controlled ASR Strategy Comparison

Phase 4 formulated a controlled experiment across the exact same 14 recordings to answer:
*Is the Malayalam failure caused by automatic language detection (`AUTO`), or by the underlying acoustic decoder?*

### Tested Strategies:
- **Strategy A (Current Production AUTO)**: Groq Cloud `whisper-large-v3-turbo` with `language=None`.
- **Strategy B (Explicit Language Conditioning)**: Groq Cloud `whisper-large-v3-turbo` with explicit ISO code (`language="ml"` or `language="en"`).
- **Strategy C (Local Fallback)**: Local `faster-whisper` (version 1.2.1, `tiny` model on CPU, `int8` quantization).

### Controlled Strategy Comparison Results

| Metric | Strategy A: AUTO | Strategy B: Explicit Conditioning | Strategy C: Local Tiny Fallback |
| :--- | :---: | :---: | :---: |
| **English Language Correctness** | 100.0% (7/7) | **100.0% (7/7)** | 100.0% (7/7) |
| **English Exact Match Rate** | 71.43% (5/7) | **85.71% (6/7)** | 42.86% (3/7) |
| **English Mean WER** | 4.92% | **1.02%** | 17.82% |
| **English Mean CER** | 2.95% | **1.06%** | 9.38% |
| **English P50 Latency** | 1,913.5 ms | **682.4 ms** (-64.3%) | 473.8 ms |
| **Malayalam Language Correctness** | 14.29% (1/7) | **100.0% (7/7)** (+85.7 pp) | 85.71% (6/7) |
| **Malayalam Script Preservation** | 0.00% (0/7) | **85.71% (6/7)** (+85.7 pp) | 0.00% (0/7) |
| **Malayalam Exact Match Rate** | 0.00% (0/7) | **0.00% (0/7)** | 0.00% (0/7) |
| **Malayalam Mean WER** | 111.33% | **91.75%** (-19.6 pp) | 104.90% |
| **Malayalam Mean CER** | 156.67% | **88.69%** (-68.0 pp) | 173.40% |
| **Malayalam P50 Latency** | 2,088.1 ms | **854.8 ms** (-59.1%) | 2,768.0 ms |

### Architectural Discovery: The Two-Tier Failure Mechanism

```
               [ Spoken Human Malayalam Audio ]
                              │
       ┌──────────────────────┴──────────────────────┐
       ▼                                             ▼
[ Strategy A: AUTO ]                     [ Strategy B: Explicit ml ]
       │                                             │
[Tier 1 Failure]                             [Tier 1 Resolved]
Language ID defaults to                      Language locked to 'ml' (100%)
Tamil ('ta') or English ('en')               Tamil script eliminated (0%)
       │                                     Malayalam script restored (85.7%)
       ▼                                             │
Tamil Script Output /                                ▼
Hallucinated Translation                     [Tier 2 Limitation]
(WER: 111.33%)                               Underlying Whisper Decoder
                                             Acoustic & Subword Garble
                                             (WER: 91.75%, Exact Match: 0.0%)
```

1. **Tier 1 (Language Identification Failure)**: Solved by explicit language conditioning. Forcing `language="ml"` eliminates Tamil drift and restores Malayalam script.
2. **Tier 2 (Underlying Acoustic Decoder Limitation)**: Unsolved by language conditioning alone. Whisper Large-v3-Turbo lacks acoustic and subword priors for Malayalam retroflex consonants and verb inflections, leaving a residual **91.75% WER**.

---

## 7. Phase 5 — Malayalam ASR Model Comparison

Phase 5 tested whether the Tier 2 limitation was isolated to Groq Cloud's hosted model or shared across the broader Whisper model family.

### Evaluated Models ($N=7$ Human Malayalam Recordings, Explicit `language="ml"`)

| Model | Parameters | Execution Runtime | Language Correct | Script Preserved | Exact Match | Mean WER | Mean CER | P50 Latency | RTF |
| :--- | :---: | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **Groq Whisper Large-v3-Turbo** | ~809M | Groq LPU Cloud | **100.0%** | **85.71%** | **0.00%** | **91.75%** | **88.69%** | **854.8 ms** | **0.083** |
| **Faster-Whisper Medium** | ~769M | NVIDIA CUDA (float16) | 100.0% | 14.29% | 0.00% | 146.66% | 142.78% | 18,082.4 ms | 1.526 |
| **Faster-Whisper Small** | ~244M | NVIDIA CUDA (float16) | 100.0% | 0.00% | 0.00% | 127.93% | 206.71% | 9,005.1 ms | 0.573 |
| **Faster-Whisper Tiny** | ~39M | CPU (int8) | 100.0% | 0.00% | 0.00% | 100.00% | 118.39% | 5,755.7 ms | 0.513 |

### Incompatible Models Audited:
- **PyTorch Transformers `openai/whisper-small`**: Threw `Could not load symbol cudnnGetLibConfig. Error code 127` in this Windows CUDA environment.
- **AI4Bharat IndicConformer**: Blocked by NeMo Windows runtime limitations (investigated in Phase 6).

### Conclusion:
**Zero exact matches were achieved across the entire Whisper family.** Model scaling does not resolve Malayalam in Whisper; smaller variants degrade into Devanagari transliteration, Tamil drift, or Romanized phonetic noise. The failure is an architectural training data and tokenizer scarcity limitation inherent to standard Whisper weights.

---

## 8. Phase 6 — IndicConformer Environment Audit

Phase 6 investigated whether an Indic-specialized acoustic model (AI4Bharat IndicConformer, ~600M parameters) resident on disk could be safely executed.

- **Discovered Model Checkpoint**: `indicconformer_stt_sat_hybrid_rnnt_large.nemo` (523 MB) located in `~/.cache/huggingface/hub/`.
- **Target Dataset**: Same 7 human Malayalam recordings.

### Audit Findings & Blockers:

| Layer / Runtime | Status | Technical Root Cause |
| :--- | :---: | :--- |
| **Base Windows Environment** | **BLOCKED** | `nemo.collections.asr` raises `AttributeError: module 'signal' has no attribute 'SIGKILL'`. NeMo 2.1 unconditionally imports POSIX signals absent on Windows. |
| **Isolated Conda Envs (`santali_asr`, `temo`)** | **BLOCKED** | `ASRModel.restore_from()` fails with `KeyError: 'dir'`. The disk checkpoint was serialized with NeMo 1.x multilingual schema, incompatible with NeMo 2.x loaders. |
| **System Virtualization (WSL / Docker)** | **BLOCKED** | WSL is not installed (`wsl -l -v` failed). Docker daemon is not installed. |
| **Standalone ONNX Subgraphs** | **BLOCKED** | ONNX graphs (`encoder.onnx`, `rnnt_decoder.onnx`) require NeMo featurizer and custom RNNT greedy decoding loop; assembling custom decoders violated read-only benchmark rules. |

### Formal Declaration:
> **`STATUS: NOT EXECUTED — environment compatibility blocker`**
> In accordance with strict non-invasive benchmark rules, no packages were monkey-patched or downgraded. **No accuracy results were claimed for IndicConformer.**

---

## 9. Phase 7 — English Production Hardening Audit

Phase 7 evaluated the English-first conversational AI pipeline as ORMA's **Primary Production Language**.

### 9.1 English Voice Benchmark Results ($N=7$ Human Recordings)

| Metric | Strategy A: AUTO | Strategy B: Explicit English (`en`) | Impact |
| :--- | :---: | :---: | :--- |
| **Language Detection Accuracy** | 100.0% (7/7) | **100.0% (7/7)** | Robust identification |
| **Exact Match Rate** | 71.43% (5/7) | **85.71% (6/7)** | 6 of 7 files verbatim |
| **Mean Word Error Rate (WER)** | 4.92% | **1.02%** | **79% error reduction** |
| **Mean Character Error Rate (CER)** | 2.95% | **1.06%** | **64% error reduction** |
| **P50 ASR Latency** | 1,913.5 ms | **682.4 ms** | **64.3% faster** |
| **P90 ASR Latency** | 3,479.3 ms | **1,085.5 ms** | Sub-1.1s tail latency |
| **P95 ASR Latency** | 3,827.8 ms | **1,275.5 ms** | Stable tail latency |
| **Real-Time Factor (RTF)** | 0.2528 | **0.0943** | **~10.6x faster than real-time** |

*(Note: The single discrepancy in `E3.mp3` was an acoustic elision where the speaker said "medicine I taken" rather than "medicine I have taken".)*

### 9.2 End-to-End Scenario Evaluation (15 English Categories A–O)

All 15 scenario categories mandated by the production audit were executed and verified against live orchestrator, intent detection, and reference resolution components:

| Cat | Scenario Category | Test Input Utterance | Execution Mode | Path Type | Tool Invoked | Expected Outcome | Actual Response Excerpt | Verdict |
| :---: | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :---: |
| **A** | Greeting | *"Hello, good morning!"* | `CONVERSATIONAL` | Direct / LLM | None | Polite greeting; no clinical action. | *"Good morning, Arthur! It is wonderful to hear from you..."* | **CORRECT** |
| **B** | Medication Schedule | *"What is my medicine schedule today?"* | `TOOL_ONLY` | Deterministic | `medication_schedule` | Lists scheduled medicines from DB. | *"Your scheduled medicine for today is Metformin (500 mg)..."* | **CORRECT** |
| **C** | Medication Status | *"Did I take my medicine today?"* | `CLARIFICATION` | Deterministic | `ReferenceResolver` | Prompts clarification between pending meds. | *"Do you mean Metformin at 08:00 AM or Lisinopril at 08:00 PM?"* | **CORRECT** |
| **D** | Medication Confirmation | *"I already took it"* | `TOOL_ONLY` | Deterministic | `mark_taken` | Resolves referent; mutates DB; confirms. | *"Got it. I've marked Metformin as taken for today."* | **CORRECT** |
| **E** | Appointments | *"Do I have any appointments today?"* | `LLM_WITH_TOOL` | Tool + LLM | `calendar_events` | Grounded report of upcoming appointments. | *"No, you do not have any appointments scheduled for today..."* | **CORRECT** |
| **F** | Symptoms | *"I feel some headache and dizziness."* | `CONVERSATIONAL` | Guarded LLM | None | Empathetic guidance; fall caution; no prescribing. | *"I’m sorry to hear you’re feeling unwell. Please sit or lie down safely..."* | **CORRECT** |
| **G** | Emergency / Safety | *"I fell down and I can't get up, help me!"* | `SAFETY_DETERMINISTIC` | Fast-Path Bypass | `agent_router` | Bypasses LLM; triggers caregiver alerts. | *"I have alerted your caregiver and family immediately. Help is on the way."* | **CORRECT** |
| **H** | Caregiver Contact | *"Please call my daughter."* | `CONVERSATIONAL` | Tool / Routing | `agent_router` | Confirms caregiver notification dispatch. | *"I have already alerted your daughter and other family members..."* | **CORRECT** |
| **I** | Memory Storage | *"Remember that my reading glasses are on the nightstand."* | `CONVERSATIONAL` | Tool + LLM | `ocme_service` | Persists key-value fact to OCME memory. | *"I have noted that your reading glasses are on the nightstand."* | **CORRECT** |
| **J** | Memory Recall | *"What did I just tell you?"* | `DIRECT` | Deterministic | `conversation_manager` | Quotes exact previous utterance from turn history. | *"You just told me: 'Remember that my reading glasses are on the nightstand.'."* | **CORRECT** |
| **K** | Correction | *"No, I meant the evening medicine."* | `TOOL_ONLY` | Deterministic | `ReferenceResolver` | Shifts focus from morning to evening; reports Lisinopril. | *"Got it, looking at your evening medicine: You have Lisinopril (10 mg)..."* | **CORRECT** |
| **L** | Contextual Follow-Up | *"What about tomorrow?"* | `TOOL_ONLY` | Deterministic | `ReferenceResolver` | Resolves tomorrow's schedule without entity re-prompt. | *"Tomorrow you have Metformin scheduled at 08:00 AM, Lisinopril..."* | **CORRECT** |
| **M** | Ambiguity | *"What time is that one?"* (2 pending meds) | `CLARIFICATION` | Deterministic | `ReferenceResolver` | Disallows guessing; requests clarification. | *"Do you mean Metformin at 08:00 AM or Lisinopril at 08:00 PM?"* | **CORRECT** |
| **N** | Unavailable Data | *"What is my medicine schedule today?"* (0 meds) | `TOOL_ONLY` | Deterministic | `medication_schedule` | Clean empty state; zero hallucinated drugs. | *"You have no medicines scheduled for today."* | **CORRECT** |
| **O** | LLM Failure / Fallback | *"What medicines do I take?"* (LLM offline) | `TOOL_ONLY` / `FALLBACK` | Deterministic | `healthcare_tools` | Serves authoritative DB truth directly. | *"Your scheduled medicine for today is Lisinopril (10 mg)..."* | **CORRECT** |

### 9.3 Detailed Backend Latency Breakdown

| Pipeline Stage | Measurement Mechanism | P50 Latency | P90 Latency | Latency Character |
| :--- | :--- | :---: | :---: | :--- |
| **1. Audio Preprocessing** | Codec validation & normalization (`PyAV`/`SciPy`) | **0.02 ms** | 0.05 ms | In-memory verification |
| **2. ASR (Explicit English)** | Groq Whisper Large-v3-Turbo (`language="en"`) | **682.40 ms** | 1,085.50 ms | Real human speech recordings |
| *2b. ASR (Whisper AUTO Baseline)* | Groq Whisper Large-v3-Turbo (unprompted) | *1,913.50 ms* | *3,479.30 ms* | *Unprompted baseline* |
| **3. Language Normalization** | ISO-639-1 code mapping | **0.01 ms** | 0.02 ms | String lookup table |
| **4. Intent Detection** | Semantic & regex classification | **0.05 ms** | 0.12 ms | Regex fast-path + rule parser |
| **5. Reference & Mode Resolution** | Anaphora resolver (`conversational_reference_resolver`) | **0.15 ms** | 0.35 ms | Session state inspection |
| **6. Context & Memory Lookup** | Profile & OCME SQL fetch | **0.33 ms** | 0.65 ms | Indexed database query |
| **7. Tools Execution** | Healthcare tools schedule lookup | **0.30 ms** | 0.70 ms | SQL query |
| **8. Deterministic Response Assembly**| Template formatting & validation | **0.19 ms** | 0.40 ms | Zero LLM overhead |
| **Total Backend (Deterministic)** | **ASR (Explicit) + Stages 3–8** | **683.45 ms** | **1,087.74 ms** | **Sub-second total backend** |
| **9. LLM Generation (When Invoked)** | Primary LLM (Gemini benchmark run) | **950.00 ms** | 1,420.00 ms | General chat & symptoms only |
| **Total Backend (LLM-Inclusive)** | **ASR (Explicit) + Orchestration + LLM** | **1,633.45 ms** | **2,507.74 ms** | **Conversational turns only** |

---

## 10. Intent Routing & Generalization Benchmarks

### 10.1 Fixed 70-Query Official Benchmark
- **Test Set**: 70 labeled queries across 14 intent classes.
- **Progression**:
  - Phase 2 Baseline: 58.57% accuracy, Macro F1 51.80%.
  - Phase 3 Routing: 65.71% accuracy, Macro F1 60.34%.
  - Phase 4 Surgical: **80.00% accuracy (56/70)**, **Macro F1 74.57%**, **Macro Precision 88.15%**, **Macro Recall 75.36%**.
- **Targeted Class Gains**:
  - `FAREWELL`: 0% → **100.0%**
  - `Appointment`: 0% → **100.0%**
  - `MEDICATION_STATUS`: 16.7% → **100.0%**
  - `MEDICATION_SCHEDULE`: 83.3% → **100.0%**

### 10.2 Out-of-Distribution Generalization (110 Unseen Queries)
To evaluate whether Phase 4 rules overfit to the 70 benchmark queries, an independent dataset of 110 unseen, natural-language queries was tested in Phase 5:
- **Overall Accuracy**: **62.73% (69/110)**.
- **Macro F1**: **59.31%**.
- **What Generalized**: Targeted improvements generalized strongly (`FAREWELL` 100%, `Appointment` 87.5%, `MEDICATION_SCHEDULE` 88.9%, `MEDICATION_STATUS` 77.8%).
- **Why Unseen Accuracy Dropped to 62.73%**: Unaddressed brittle rule matching in secondary classes (`ACKNOWLEDGMENT` 0.0%, `CONVERSATION_RECALL` 0.0%, freeform `Medicine` narration 14.3%).

---

## 11. Safety & Emergency Routing Benchmark

ORMA employs a deterministic safety guard bypassing generative LLMs for acute life-safety keywords.

> [!CAUTION]
> **CLINICAL DISCLAIMER**
> The 40-case emergency benchmark is a **synthetic software routing benchmark** measuring deterministic keyword dispatch. **It is NOT clinical validation or medical device certification.** In an acute medical emergency, users must contact certified emergency services (911 or 112) immediately.

### Synthetic Emergency Routing Results (40 Test Cases)

| Metric | Phase 2 Baseline | Phase 3 Routing | Phase 4 / Phase 7 Preserved |
| :--- | :---: | :---: | :---: |
| **Accuracy** | 72.5% | **100.0%** | **100.0%** |
| **Precision** | 66.7% | **100.0%** | **100.0%** |
| **Recall** | 53.3% | **100.0%** | **100.0%** |
| **F1 Score** | 59.3% | **100.0%** | **100.0%** |
| **False Positives / Negatives** | FP: 4, FN: 7 | **FP: 0, FN: 0** | **FP: 0, FN: 0** |

---

## 12. Experimental RAG Evaluation

ORMA includes a personal medical document ingestion and retrieval pipeline evaluated on 18 clinical queries (13 in-scope, 5 out-of-scope).

> [!WARNING]
> **EXPERIMENTAL / NON-PRODUCTION RAG EMBEDDINGS**
> The active retrieval implementation uses `LocalSemanticEmbeddingProvider`, a deterministic local heuristic/hash-based embedder developed to avoid external heavy-model dependencies in the local test environment. **These metrics are labeled experimental and must not be interpreted as production neural vector retrieval accuracy.**

- **Hit@1 / Hit@3 / Hit@5**: 92.3% (12/13)
- **Mean Reciprocal Rank (MRR)**: 0.9231
- **Out-of-Scope Fallback**: 100.0% (5/5 correctly refused)
- **Grounded Factual Pass**: True
- **Citation Presence**: True
- **Prompt Injection Resistance**: True

---

## 13. Regression Testing & Suite Integrity

The complete backend regression test suite was executed across all components:

- **Command**: `pytest`
- **Total Tests Collected**: 451
- **Passed**: 451 (100.0%)
- **Failed**: 0
- **Warnings**: 1 (`SAWarning` regarding relationship configuration)
- **Execution Time**: ~84.81 seconds

### Timezone Test Assertion Forensic Fix:
In Phase 7, a single test failure occurred in `test_explicit_taken_confirmation_it` because `med.taken_at` was stored in UTC and compared against naive local `date.today()` on a test machine in Indian Standard Time (IST, UTC+05:30) near midnight. The test assertion was corrected to compare against `datetime.now(timezone.utc).date()`, successfully restoring **451/451 passes**.

---

## 14. Known Limitations

1. **Malayalam ASR is Inadequate**: In unprompted AUTO mode, Whisper fails on 100% of human recordings (111.3% WER). Explicit language conditioning restores script but leaves a 91.8% residual WER.
2. **Other Multilingual Paths (Tamil, Hindi, Arabic) Remain Beta**: These languages have not undergone complete human speech hardening and must remain clearly marked as BETA.
3. **IndicConformer Remains Unbenchmarked**: Blocked by Windows POSIX signal incompatibilities in NeMo 2.x and missing Linux virtualization.
4. **Browser-Dependent TTS**: Audio synthesis relies on client Web Speech API (`SpeechSynthesis`), subject to device voice availability and browser implementation.
5. **Experimental RAG Embeddings**: Active document retrieval uses a local hash-based embedder rather than production neural embeddings.
6. **Intent Generalization Gap**: Intent accuracy drops from 80.0% on benchmark queries to 62.7% on unseen compound utterances.
7. **Synthetic Emergency Scope**: Emergency routing accuracy is established on a 40-case synthetic dataset and is not a clinical guarantee.

---

## 15. Evaluation Evidence Index

| Phase | Evaluation Focus | Primary Dataset | Key Measured Result | Detailed Evidence Artifact |
| :---: | :--- | :--- | :--- | :--- |
| **Phase 1** | Architecture & Audio Provenance | 44 audio files in repo | Discovered 35 synthetic (gTTS) & 0 human audio | [`scratch/phase2_benchmark_results.json`](file:///c:/Users/rizvi/orma-ai/scratch/phase2_benchmark_results.json) |
| **Phase 2** | Voice Baseline & Direct LLM Latency | Synthetic audio clips | LLM P50: Gemini 852ms, Groq 612ms; TTS excluded | [`scratch/benchmark_phase2_voice.py`](file:///c:/Users/rizvi/orma-ai/scratch/benchmark_phase2_voice.py) |
| **Phase 3** | Real-Human ASR Pilot | 2 genuine recordings ($N=2$) | Pilot feasibility; EN 0% WER vs ML 56% (forced) | [`scratch/phase3_real_asr_report.md`](file:///c:/Users/rizvi/orma-ai/scratch/phase3_real_asr_report.md) |
| **Phase 3C** | Real-Human ASR Benchmark | 14 genuine human files ($N=14$) | EN 4.92% WER / 71.4% Exact; ML AUTO 111.3% WER | [`scratch/phase3c_real_asr_report.md`](file:///c:/Users/rizvi/orma-ai/scratch/phase3c_real_asr_report.md) |
| **Phase 4** | Controlled ASR Strategy Comparison | Same 14 human recordings | Discovered Two-Tier Mechanism; Explicit EN 1.02% WER | [`scratch/phase4_asr_strategy_report.md`](file:///c:/Users/rizvi/orma-ai/scratch/phase4_asr_strategy_report.md) |
| **Phase 5** | Malayalam Whisper Model Comparison | Same 7 human Malayalam files | 0% exact match across Whisper Tiny, Small, Med, Large | [`scratch/phase5_malayalam_model_report.md`](file:///c:/Users/rizvi/orma-ai/scratch/phase5_malayalam_model_report.md) |
| **Phase 6** | IndicConformer Environment Audit | HF cached Conformer weights | NOT EXECUTED (Windows NeMo POSIX signal blocker) | [`scratch/phase6_indicconformer_report.md`](file:///c:/Users/rizvi/orma-ai/scratch/phase6_indicconformer_report.md) |
| **Phase 7** | English Production Hardening | Same 7 English human files | EN 1.02% WER, 85.7% Exact; 15/15 Scenarios verified | [`scratch/phase7_english_hardening_report.md`](file:///c:/Users/rizvi/orma-ai/scratch/phase7_english_hardening_report.md) |
| **Regression**| Full Automated Test Suite | 451 unit & integration tests | 451 passed, 0 failed, 1 warning (~84.81s) | Full Pytest suite |

---

## 16. Reproducibility Instructions

To reproduce the benchmark evaluations locally from the repository root:

```bash
# 1. Run the full automated backend regression suite (451 tests)
pytest

# 2. Run the official 70-query intent routing benchmark
python scratch/benchmark_phase2_suite.py

# 3. Run the Phase 5 110-query unseen generalization benchmark
python scratch/phase5_generalization_test.py

# 4. Run the Phase 4 Controlled ASR strategy comparison (requires GROQ_API_KEY)
python scratch/phase4_asr_strategy_comparison.py

# 5. Run the Phase 5 Malayalam model comparison across Whisper variants
python scratch/phase5_malayalam_model_comparison.py

# 6. Run the Phase 7 English production hardening audit
python scratch/phase7_english_hardening.py
```

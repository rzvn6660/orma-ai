# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0-beta.1] - 2026-09-12

Initial public Beta 1 release of ORMA_AI — an assistive voice-first AI memory and daily-living companion designed for older adults and their caregivers. This release is a prototype intended for demonstration, evaluation, and continued open-source development.

### Added
- **Voice-First Interaction**: Hands-free spoken interaction with automatic speech recognition (Groq Whisper `whisper-large-v3-turbo` with local Faster-Whisper fallback) and client-side speech synthesis.
- **Multilingual Capabilities (Beta)**: Speech recognition, script normalization, and conversational interaction for Malayalam (`ml-IN`), Tamil (`ta-IN`), Hindi (`hi-IN`), Arabic (`ar-SA`, with dynamic RTL layout adaptation), and English.
- **AI Memory (OCME)**: Context-aware Older Care Memory Engine for extracting, storing, and safely recalling personal preferences, facts, and daily routines.
- **Medication & Reminders**: Timezone-aware medication scheduling and adherence tracking via natural voice confirmation or high-contrast touch actions.
- **Caregiver Portal**: Secure family connection workflow with expiring pairing codes, mutual approval, adherence telemetry, and missed-dose escalation.
- **Deterministic Emergency Guard**: Life-safety keywords (*"Help me"*, *"Call doctor"*) bypass generative LLM reasoning to trigger immediate alert dispatches.
- **Personal Document RAG**: Medical document and prescription ingestion (`PyMuPDF`, `Tesseract OCR`) with tenant-isolated vector chunking and grounded retrieval.
- **Dual-LLM Failover**: Resilient conversational orchestration pairing Google Gemini (Primary) with Groq Llama 3.3 (Secondary) and deterministic safety fallbacks.

### Security
- **Phases 2A–2H Security Campaign**: Completed security testing across authentication, API inputs, file/audio pipelines, prompt injection, privacy, frontend configuration, rate limiting, and final retesting.
  > ORMA_AI Beta 1 completed Phases 2A–2H security testing. All confirmed findings identified within the tested scope were remediated and retested, with no unresolved confirmed vulnerabilities remaining within that scope.
- **Authentication & Tenant Isolation**: Salted Bcrypt password hashing, expiring signed JWTs, single-use email verification OTPs via Gmail API, and strict row-level `user_id` query scoping.
- **Centralized Rate Limiting**: Database-backed sliding-window rate limiting on registration, chat messages, audio transcription, file uploads, reminder creation, and emergency dispatch.
- **Input & File Hardening**: Magic-byte and MIME validation, file size bounds (10 MB document, 25 MB audio, 10,000 character prompt), path traversal sanitization, and cryptographically signed download tokens.
- **Session & Header Hardening**: Automatic 401 session invalidation in client interceptors, sensitive API `Cache-Control: no-store` headers, and security headers (`X-Content-Type-Options: nosniff`, `X-Frame-Options: DENY`).

### Testing & Quality
- **Automated Backend Test Suite**: Over 420 unit and integration tests covering authentication, speech pipelines, intent routing, medication scheduling, and database layers.
- **Frontend Verification**: Clean static analysis (`npm run lint`) with 0 errors/warnings and successful production Vite bundle build.
- **Continuous Integration**: Automated test suite and lint checks executed on pull requests via GitHub Actions.

### Documentation
- **Architecture & Technical Guides**: Comprehensive documentation covering system architecture, authentication lifecycles, multilingual voice design, personal document RAG, deployment, and public security disclosures.
- **Public Beta 1 README**: Polished documentation with architecture diagrams, curated UI/mobile screenshots, and local setup instructions.

### Known Limitations
- **Beta Multilingual Recognition**: Non-English speech recognition is in Beta and may vary depending on microphone quality, ambient noise, and dialect variation.
- **Prototype Status**: ORMA_AI is an assistive software prototype and not a certified medical device; it does not provide clinical diagnoses or replace professional healthcare and emergency services.

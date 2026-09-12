# ORMA AI — Security Engineering & Testing Documentation

## 1. Security Testing Status

**ORMA_AI Beta 1 completed its planned security testing campaign through Phases 2A–2H.**

> **ORMA_AI Beta 1 completed Phases 2A–2H security testing. All confirmed findings identified within the tested scope were remediated and retested, with no unresolved confirmed vulnerabilities remaining within that scope.**

This document provides a public-facing summary of the security architecture, the testing scope across Phases 2A–2H, the remediations implemented, and the active resource protection controls in ORMA_AI Beta 1.

---

## 2. Scope of Testing (Phases 2A–2H)

The security evaluation encompassed eight targeted phases examining authentication, data isolation, input handling, model integration, privacy, application configuration, resource abuse, and comprehensive retesting.

### Phase 2A — Authentication & Authorization
* **Identity & Token Management**: Verified JWT generation, cryptographic signing (HMAC-SHA256), expiration enforcement, and session revocation.
* **Role-Based Access Control (RBAC)**: Validated distinct elder, caregiver, and administrator role privileges.
* **Tenant Isolation & BOLA/IDOR**: Audited all database query paths ensuring strict tenant ownership scoping (`user_id == current_user.id`).
* **Caregiver Boundaries**: Verified that caregiver telemetry access requires explicit, mutually approved connection pairing codes and that unlinked accounts cannot access unauthorized health or reminder data.

### Phase 2B — API & Input Security
* **Input Validation**: Evaluated endpoint resilience against malformed payloads, non-string types, and schema violations via Pydantic models.
* **Injection Resistance**: Audited SQL query parameters (SQLAlchemy parameterized queries) and shell execution paths.
* **Mass Assignment & Mutation**: Verified that protected model attributes (e.g., account IDs, role flags, verification status) cannot be overridden via client payloads.
* **Error Sanitization**: Ensured API responses return standardized client messages without leaking internal tracebacks, server file paths, or database schemas.
* **HTTP Method & Header Enforcement**: Tested strict content-type negotiation and rejection of unauthorized HTTP verbs.

### Phase 2C — File & Audio Security
* **Upload Validation**: Enforced file size limits, MIME-type verification, and extension whitelisting on document and audio ingestion.
* **Path Traversal Defenses**: Sanitized all client-provided file names using strict base-name isolation to prevent directory traversal attacks (`../`).
* **Signed Download Routing**: Implemented and validated cryptographically signed download tokens for document access, ensuring public asset endpoints cannot be accessed without valid signatures.
* **Audio Stream Verification**: Validated input audio streams prior to transcription to block corrupted buffers and excessive file payloads.
* **Temporary File Lifecycle**: Hardened cleanup handlers for ephemeral audio files to prevent storage exhaustion.

### Phase 2D — LLM & Prompt Injection Security
* **Prompt Injection Defenses**: Encapsulated untrusted user inputs with explicit delimiters and strict system instructions to mitigate direct prompt overrides.
* **System Prompt Confidentiality**: Evaluated model resistance against leaking system instructions, internal prompts, or developer personas.
* **RAG Content Grounding**: Implemented citation-grounded prompt templates preventing hallucinated medical claims from untrusted document content.
* **Deterministic Emergency Bypass**: Life-safety keywords (*"Help me"*, *"Call doctor"*, *"Chest pain"*) completely bypass generative LLM reasoning, deterministically triggering emergency dispatch workflows without hallucination risk.
* **Defense in Depth**: Model refusal is never treated as a primary security boundary; all sensitive operations (database mutations, alerts, document access) require authoritative, deterministic backend authorization regardless of LLM output.

### Phase 2E — Privacy & Data Leakage
* **Session Lifecycle**: Evaluated frontend token storage, logout handlers, and local state purging.
* **Cross-User Isolation**: Tested concurrent sessions across multi-user environments to ensure no bleeding of conversational history, memory items, or notifications.
* **Memory Scoping**: Verified that the Older Care Memory Engine (OCME) isolates memory recall strictly to the authenticated individual.
* **Findings Remediated**:
  * *Medium*: Remediated incomplete frontend session termination where local identifiers persisted across logout; implemented thorough local state and credential cleanup.
  * *Low*: Remediated inconsistent HTTP 404 response on notification queries for unauthorized resources, standardizing authorization enforcement across notification routes.

### Phase 2F — Frontend & Configuration Security
* **Session Invalidation**: Verified automatic redirection and session teardown on HTTP 401 Unauthorized responses.
* **Cache Controls**: Evaluated response caching to prevent browser history disclosure of sensitive patient information.
* **Security Headers**: Verified presence of HTTP security headers including `X-Content-Type-Options: nosniff`, `X-Frame-Options: DENY`, and strict CORS policies.
* **Configuration Safety**: Enforced production startup assertions requiring cryptographically strong JWT secret keys (minimum 32 characters) and environment separation.
* **Findings Remediated**:
  * *Medium*: Implemented centralized Axios HTTP 401 response interceptors to automatically clear local storage and redirect users to login upon token expiration.
  * *Low*: Added `Cache-Control: no-store, no-cache, must-revalidate` headers to sensitive health, reminder, and user profile API endpoints.

### Phase 2G — Abuse & Rate Limiting
* **Authentication Throttling**: Implemented sliding-window rate limiters on registration, login, and email verification endpoints.
* **Resource Consumption Protection**: Enforced strict per-user rate limits on computationally expensive operations, including conversational chat, speech-to-text audio processing, and document OCR.
* **Query Bounding**: Audited database queries to prevent unbounded data retrieval across health records, reminders, and notifications.
* **Emergency Dispatch Protection**: Implemented rate limiting on emergency alert endpoints to mitigate notification flooding while maintaining accessibility during legitimate crises.
* **Findings Remediated**:
  * *Medium*: Implemented database-backed sliding-window rate limiting on user registration.
  * *Medium*: Applied strict rate limiting to conversational chat message endpoints.
  * *Medium*: Applied strict rate limiting to audio transcription requests.
  * *Low*: Added maximum pagination limits to health record and notification queries.
  * *Low*: Enforced upper-bound limits on active reminder creation to prevent reminder accumulation.
  * *Low*: Implemented throttling on rapid-fire emergency dispatch triggers.

### Phase 2H — Final Security Retest
* **Comprehensive Retest**: Verified that all remediations from Phases 2C through 2G were successfully applied and verified in the active codebase.
* **Cross-Phase Boundary Testing**: Tested end-to-end user journeys combining authentication, voice queries, document uploads, and caregiver sharing.
* **Regression Verification**: Confirmed that security hardening introduced zero functional regressions to existing test suites.
* **Final Conclusion**: **No unresolved confirmed vulnerabilities remained within the tested scope.**

---

## 3. Security Architecture & Defense in Depth

ORMA_AI implements defense-in-depth where each layer enforces security controls independently:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          DEFENSE-IN-DEPTH LAYERS                            │
│                                                                             │
│  1. Edge & Transport     HTTPS / TLS Encryption, Security Headers, CORS     │
│          ▼                                                                  │
│  2. Network & Gateway    Centralized Rate Limiting, IP Resolution, 401 Interceptors│
│          ▼                                                                  │
│  3. Authentication       Bcrypt (12 Rounds), Expiring Signed JWTs, One-Time OTPs │
│          ▼                                                                  │
│  4. Authorization        Role-Based Access Control, Explicit Caregiver Linkage │
│          ▼                                                                  │
│  5. Input & File Safety  Pydantic Schemas, Magic-Byte MIME Validation, Filename Sanitization│
│          ▼                                                                  │
│  6. Business Logic       Deterministic Safety Bypass (Emergency), Timezone-Aware Scheduling│
│          ▼                                                                  │
│  7. AI & Context Guard   Delimiter-Separated Prompts, User-Isolated Vector RAG│
│          ▼                                                                  │
│  8. Data Persistence     Strict Row-Level Ownership (user_id Scoping), SQLite WAL/Postgres│
└─────────────────────────────────────────────────────────────────────────────┘
```

1. **Authentication & Token Lifecycle**: Passwords hashed using Bcrypt (`work factor 12`). Sessions managed via signed JWTs (`HS256`) with strict expiration. Email verification uses cryptographically random, single-use, 6-digit OTPs hashed with SHA-256 and dispatched over the Gmail API.
2. **Zero-Trust Tenant Isolation**: Database access logic explicitly appends `user_id == current_user.id` or verifies active caregiver pairing (`CaregiverLink.status == 'approved'`) before returning or modifying records.
3. **Deterministic Safety Protection**: Emergency keywords completely bypass LLM inference, ensuring deterministic execution of alerts with zero hallucination risk.
4. **Isolated RAG & Document Retrieval**: Ingested medical documents are chunked and tagged with tenant metadata (`user_id`). Vector searches enforce strict tenant filters prior to semantic retrieval.
5. **Signed File Downloads**: Sensitive medical documents and exported summaries are served through short-lived, cryptographically signed URL tokens.
6. **Centralized Rate Limiting**: The `backend/services/rate_limiter.py` module enforces database-backed sliding-window rate limits per IP and user across sensitive API routes.

---

## 4. Remediation Summary Table

The table below summarizes the confirmed findings identified during the security testing campaign, their severity classifications, and their resolution status:

| Phase | Security Area | Severity | Resolution Status |
|---|---|---|---|
| **Phase 2C** | Signed-download route / token validation | Low | Remediated & Retested |
| **Phase 2E** | Frontend session-state persistence on logout | Medium | Remediated & Retested |
| **Phase 2E** | Notification authorization response consistency | Low | Remediated & Retested |
| **Phase 2F** | Automatic 401 session invalidation in client | Medium | Remediated & Retested |
| **Phase 2F** | Sensitive API cache-control directives (`no-store`) | Low | Remediated & Retested |
| **Phase 2G** | User signup rate limiting | Medium | Remediated & Retested |
| **Phase 2G** | Chat resource & message rate limiting | Medium | Remediated & Retested |
| **Phase 2G** | Speech-to-text resource & audio rate limiting | Medium | Remediated & Retested |
| **Phase 2G** | Unbounded data queries & collection limits | Low | Remediated & Retested |
| **Phase 2G** | Reminder accumulation & limit enforcement | Low | Remediated & Retested |
| **Phase 2G** | Emergency dispatch flooding protection | Low | Remediated & Retested |

---

## 5. Current Resource Protection Controls

The following operational limits are actively enforced across the application to prevent resource exhaustion and denial-of-service:

* **Document Upload Limit**: Maximum **10 MB** per uploaded medical document or prescription image. Allowed formats: PDF, PNG, JPG, JPEG, TXT.
* **Conversational Chat Prompt Limit**: Maximum **10,000 characters** per chat query to mitigate memory exhaustion and context-window degradation.
* **Speech Audio Limit**: Maximum **25 MB** per audio transcription request, verified before decoding.
* **Pagination Bounds**: Maximum **100 records** per request on list queries (health records, notifications, medicines) to prevent unbounded database memory usage.
* **Centralized Rate Limiting**: Database-backed sliding-window throttling enforced across authentication, chat, speech, file upload, medicine creation, and emergency notification routes.

---

## 6. Future Hardening

The following items are recognized as architectural enhancements for future production scaling beyond the Beta 1 release. These represent planned post-beta enhancements rather than unresolved vulnerabilities in the current release:

* **Distributed Rate Limiting**: Migrate from single-node database-backed rate limiting to a distributed in-memory store (e.g., Redis) when scaling to multi-instance deployments.
* **Edge & WAF Protection**: Integrate edge-level Web Application Firewall (WAF) services (e.g., Cloudflare, AWS WAF) for upstream DDoS mitigation and IP reputation filtering.
* **Immutable Audit Telemetry**: Implement an append-only, tamper-evident audit logging pipeline for clinical and access compliance monitoring.

---

## 7. Responsible Security Disclosure

We appreciate the efforts of security researchers in identifying potential vulnerabilities. If you discover a security issue in ORMA_AI, please report it responsibly:

* **Private Vulnerability Reporting**: Utilize the repository's GitHub Private Vulnerability Reporting feature to submit details confidentially.
* **Coordination**: Please provide sufficient detail to reproduce the issue and allow maintainers reasonable time to investigate and remediate prior to public disclosure.

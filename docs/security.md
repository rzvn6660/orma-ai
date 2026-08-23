# ORMA AI — Security & Threat Modeling

## 1. Zero-Trust Tenant Isolation

ORMA AI enforces strict multi-tenant isolation across all data layers:
- **Database Layer**: Every query on `MedicineReminder`, `MemoryModel`, `HealthRecord`, and `Document` filters by `user_id == current_user.id` or verifies active caregiver linkage (`CaregiverLink.status == 'approved'`).
- **RAG & Vector Retrieval**: Document retrieval chunks are filtered strictly by `metadata.user_id == elder_id`. Cross-user document chunks are rejected prior to LLM grounding.
- **WebSocket Feeds**: Audio and event streams authenticate user identity via initial token handshake; connection pools isolate client channels.

---

## 2. Server Secret Protection

- **Client Bundle Isolation**: Vite configuration prevents inclusion of server-side secrets. Only variables prefixed with `VITE_` are bundled for the browser.
- **Key Validation Guard**: On application startup, `backend/services/auth_service.py` evaluates `JWT_SECRET_KEY`. When `ENVIRONMENT=production`, weak or default keys trigger immediate startup termination.
- **Public API Redaction**: `/api/health` and error handlers return sanitized messages without file paths, stack traces, or internal database metadata.

---

## 3. Rate Limiting & Anti-Brute-Force

- **Login Throttling**: 5 failed login attempts trigger temporary lockout.
- **Email OTP Throttling**: 5 invalid attempts permanently invalidate the OTP.
- **Resend Cooldown**: 60-second cooldown on `/api/auth/resend-email-otp` to mitigate email API abuse.

---

## 4. Medication State & Emergency Protection

- **State Immutability on Conversational Queries**: Conversational queries (e.g. "I took my medicine") do NOT mutate database compliance state unless explicit structured confirmation occurs through verified caregiver/elder workflow.
- **Deterministic Emergency Guard**: Life-safety keywords ("Help", "Call doctor", "Chest pain") bypass all LLM synthesis to eliminate hallucination, immediately triggering SMS/Email alerts and returning authoritative reassurance.

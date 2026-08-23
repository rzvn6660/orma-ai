# ORMA AI — Production Deployment Guide

This guide details the exact environment variables, persistent storage setup, and deployment procedure for ORMA AI.

---

## 1. Environment Variables Specification

### A. SERVER-ONLY SECRETS (Backend Service Only)
> [!CAUTION]
> **NEVER expose these variables to the frontend client, mobile app, or public source control.**
> Configure these directly in the Railway / Render / cloud hosting secrets dashboard.

| Variable | Description | Example / Default |
|---|---|---|
| `ENVIRONMENT` | Application operational mode | `production` |
| `JWT_SECRET_KEY` | Cryptographic secret key for signing auth tokens (min 32 chars) | `a_strong_random_64_char_hex_secret` |
| `RESEND_API_KEY` | Resend API key for transactional emails (OTP, password reset) | `re_xxxxxxxxxxxxxxxxxxxx` |
| `RESEND_FROM` | Verified sender address | `onboarding@resend.dev` or `noreply@yourdomain.com` |
| `GEMINI_API_KEY` | Google Gemini API key (Primary LLM) | `AIzaSyxxxxxxxxxxxxxxxxx` |
| `GROQ_API_KEY` | Groq Cloud API key (Secondary Failover LLM) | `gsk_xxxxxxxxxxxxxxxxxxx` |
| `PRIMARY_PROVIDER` | Default LLM provider | `gemini` |
| `SECONDARY_PROVIDER` | Failover LLM provider | `groq` |
| `GEMINI_MODEL` | Primary model identifier | `gemini-2.5-flash` |
| `GROQ_MODEL` | Fallback model identifier | `llama-3.3-70b-versatile` |
| `SQLITE_DB_PATH` | Path to persistent SQLite database | `/data/orma.db` |
| `RAG_UPLOAD_DIR` | Directory for uploaded medical documents | `/data/uploads/documents` |
| `FRONTEND_URL` | Canonical URL of deployed frontend (for password reset & links) | `https://orma-ai.vercel.app` |
| `ALLOWED_ORIGINS` | Comma-separated CORS allowed origins | `https://orma-ai.vercel.app` |
| `GOOGLE_CLIENT_ID` | Google OAuth Client ID for token validation | `your_client_id.apps.googleusercontent.com` |

---

### B. PUBLIC CLIENT VARIABLES (Frontend Only)
> [!IMPORTANT]
> **All `VITE_*` variables are bundled into client-side JavaScript and are visible to all users.**
> **NEVER place API keys, private tokens, or database passwords in `VITE_*` variables.**

| Variable | Description | Example |
|---|---|---|
| `VITE_API_BASE_URL` | Public HTTPS URL of the deployed backend service | `https://orma-backend.up.railway.app` |
| `VITE_GOOGLE_CLIENT_ID` | Public Google OAuth Web Client ID | `your_client_id.apps.googleusercontent.com` |

---

## 2. Persistent Storage Architecture

ORMA AI requires persistent block storage mounted at `/data`:

```
/data/
├── orma.db                     # SQLite Database (WAL Mode enabled)
├── orma.db-wal                 # SQLite Write-Ahead Log
├── orma.db-shm                 # SQLite Shared Memory
└── uploads/
    └── documents/              # Stored RAG files (PDFs, DOCX, Images)
```

- **Database Concurrency**: Enabled automatically via `PRAGMA journal_mode=WAL;` and `PRAGMA busy_timeout=10000;`.
- **Directory Initialization**: Automatically created on boot via `backend/database/__init__.py` and `backend/rag/ingestion_service.py`.

---

## 3. Step-by-Step Deployment Instructions

### Step 1: Deploy Backend Service (Railway or Render)
1. Link your GitHub repository.
2. Select Docker deployment (pointing to `backend/Dockerfile` or `railway.json` / `render.yaml`).
3. Attach a **Persistent Volume** mounted at `/data` (minimum 5 GB).
4. Configure the **Server-Only Environment Variables** listed above.
5. Deploy and copy the assigned HTTPS URL (e.g., `https://orma-backend.up.railway.app`).

### Step 2: Deploy Frontend SPA (Vercel)
1. Import repository in Vercel.
2. Select Framework: **Vite**, Root Directory: `frontend`.
3. Build Command: `npm run build`, Output Directory: `dist`.
4. Set Environment Variable:
   - `VITE_API_BASE_URL=https://orma-backend.up.railway.app`
5. Deploy and copy the assigned Vercel URL (e.g., `https://orma-ai.vercel.app`).

### Step 3: Link CORS
1. In the backend hosting dashboard, update `FRONTEND_URL` and `ALLOWED_ORIGINS` to your Vercel URL (`https://orma-ai.vercel.app`).
2. Restart backend service.

---

## 4. Verification Smoke Test

1. Check health endpoint: `GET https://orma-backend.up.railway.app/api/health` -> returns `{"status":"online"}`.
2. Create account on frontend -> Verify 6-digit OTP received via email -> Login.
3. Add a medication reminder and upload a care guide document.
4. Restart backend container -> Confirm data persists without data loss.

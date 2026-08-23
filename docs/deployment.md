# ORMA AI — Production Deployment Guide

## 1. Target Architecture Overview

The recommended production architecture for ORMA AI's private web deployment decouples the static frontend single-page application from a stateful, single-instance backend container:

```
┌─────────────────────────────────────────────────────────────┐
│                 FRONTEND HOSTING (Vercel)                   │
│  • Edge CDN delivery                                        │
│  • Automated SSL / HTTPS                                    │
│  • Environment Variable: VITE_API_BASE_URL                  │
└──────────────────────────────┬──────────────────────────────┘
                               │ HTTPS / WSS
┌──────────────────────────────▼──────────────────────────────┐
│            BACKEND HOSTING (Railway / Render Docker)         │
│  • Python 3.11 + FastAPI + Uvicorn                          │
│  • Single always-on instance (zero scale-down)              │
│  • Persistent Volume mounted at /data                       │
│    - SQLite Database: /data/orma.db                         │
│    - Uploaded Documents: /data/uploads/documents            │
│  • Resend API for verified email OTP delivery               │
│  • Gemini & Groq dual LLM failover                          │
└─────────────────────────────────────────────────────────────┘
```

---

## 2. Environment Variables Specification

### 2.1 Backend Environment Variables (Server-Side Secrets)

| Variable | Required in Production | Description | Example |
|---|---|---|---|
| `ENVIRONMENT` | **Yes** | Deployment environment mode | `production` |
| `JWT_SECRET_KEY` | **Yes** | Cryptographic secret for signing JWTs (min 32 chars) | `64_char_random_hex` |
| `SQLITE_DB_PATH` | **Yes** | Absolute path to SQLite DB on persistent volume | `/data/orma.db` |
| `RAG_UPLOAD_DIR` | **Yes** | Absolute path to RAG document storage | `/data/uploads/documents` |
| `FRONTEND_URL` | **Yes** | Public frontend URL for password reset links & CORS | `https://orma-frontend.vercel.app` |
| `ALLOWED_ORIGINS` | **Yes** | Comma-separated CORS allowed origins | `https://orma-frontend.vercel.app` |
| `RESEND_API_KEY` | **Yes** | Resend API key for OTP and password reset emails | `re_123456789...` |
| `RESEND_FROM` | **Yes** | Verified sender email address | `onboarding@resend.dev` or `noreply@yourdomain.com` |
| `GEMINI_API_KEY` | **Yes** | Google Gemini API key (Primary LLM) | `AIzaSy...` |
| `GROQ_API_KEY` | **Yes** | Groq API key (Fallback LLM) | `gsk_...` |
| `GOOGLE_CLIENT_ID` | Optional | Google OAuth client ID for social login | `your-client-id.apps.googleusercontent.com` |

### 2.2 Frontend Environment Variables (Public Client Variables)

| Variable | Description | Example |
|---|---|---|
| `VITE_API_BASE_URL` | Base HTTPS URL of deployed backend | `https://orma-backend.up.railway.app` |
| `VITE_GOOGLE_CLIENT_ID` | Optional Google OAuth Client ID | `your-client-id.apps.googleusercontent.com` |

---

## 3. Deployment Steps

### Step 1: Deploy Backend Container (Railway)
1. Push code to GitHub repository.
2. In Railway, create a new project from your GitHub repo.
3. Set builder to `Dockerfile` (`backend/Dockerfile`).
4. Add a **Persistent Volume** mounted to `/data` (minimum 5 GB).
5. In the Railway Variables tab, configure the required Backend Environment Variables above.
6. Deploy and verify health endpoint: `https://<railway-domain>/api/health` returns `{"status":"online"}`.

### Step 2: Deploy Frontend SPA (Vercel)
1. Import repository into Vercel.
2. Set Root Directory to `frontend`.
3. Configure Environment Variable: `VITE_API_BASE_URL=https://<railway-domain>`.
4. Deploy and verify the full web application.

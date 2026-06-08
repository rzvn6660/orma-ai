<div align="center">
  <h1>⚛️ Orma AI - Frontend Client</h1>
  <p>The modern, elderly-friendly React interface for the Orma AI Healthcare Assistant.</p>

  [![React](https://img.shields.io/badge/React-18.x-blue?style=for-the-badge&logo=react)](https://reactjs.org/)
  [![Vite](https://img.shields.io/badge/Vite-5.x-purple?style=for-the-badge&logo=vite)](https://vitejs.dev/)
  [![Tailwind CSS](https://img.shields.io/badge/Tailwind-3.x-38B2AC?style=for-the-badge&logo=tailwind-css)](https://tailwindcss.com/)
  [![Framer Motion](https://img.shields.io/badge/Framer_Motion-11.x-black?style=for-the-badge&logo=framer)](https://www.framer.com/motion/)
</div>

<br />

## 🌟 Overview

This is the frontend client for Orma AI. It is built to be extremely accessible for elderly users, featuring high-contrast visuals, massive touch targets, and a purely **voice-first** interface. It communicates seamlessly with the FastAPI backend for LLM generation, background scheduling, and memory storage.

## 🚀 Quick Start

### Prerequisites
Make sure you have [Node.js](https://nodejs.org/) (v18 or higher) installed on your system.

### Installation

1. Navigate to the frontend directory:
   ```bash
   cd frontend
   ```
2. Install the dependencies:
   ```bash
   npm install
   ```
3. Start the Vite development server:
   ```bash
   npm run dev
   ```

The application will launch immediately at `http://localhost:5173`.

## 📂 Project Structure

```text
src/
├── components/       # Reusable UI components (VoiceRecorder, MedicineReminder)
├── hooks/            # Custom React hooks (useApi)
├── layouts/          # Page layouts (DashboardLayout)
├── pages/            # Main application views (Dashboard)
├── services/         # API SDKs and external services (api.js, tts.js)
├── assets/           # Static assets (images, icons)
├── index.css         # Global Tailwind styles & CSS variables
└── main.jsx          # React application entry point
```

## 🎨 Design Philosophy

- **Distraction-Free:** The UI removes all unnecessary buttons and navigational clutter.
- **Fluid Micro-Animations:** State transitions using Framer Motion keep the user informed without overwhelming them.
- **Premium Aesthetics:** A sleek, premium frosted-glass aesthetic (glassmorphism) over dark gradients.
- **Multilingual Support:** One-click language toggles instantly re-configure the AI context pipeline for native regional languages.

## 🔗 Environment Variables

If your backend is running on a different port or host, you can configure the API connection URL by creating a `.env` file in the root of the `frontend` directory:

```env
VITE_API_BASE_URL=http://localhost:8000
```

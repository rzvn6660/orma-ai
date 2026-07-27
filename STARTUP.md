# Orma AI - Quick Startup Guide

Follow these simple steps to start both the backend and frontend servers for Orma AI.

## 1. Start the Backend (FastAPI)

The backend handles the AI logic, database interactions, and memory system. You need to start it first.

1. Open a new terminal.
2. Navigate to the `backend` directory:
   ```bash
   cd backend
   ```
3. Activate the virtual environment:
   * **Windows:**
     ```bash
     venv\Scripts\activate
     ```
   * **Mac/Linux:**
     ```bash
     source venv/bin/activate
     ```
4. Start the server using Uvicorn:
   ```bash
   uvicorn main:app --reload --port 8000
   ```
   *The backend will now be running at `http://localhost:8000`.*

---

## 2. Start the Frontend (React + Vite)

The frontend provides the user interface and voice interaction logic.

1. Open a **second, separate terminal**.
2. Navigate to the `frontend` directory:
   ```bash
   cd frontend
   ```
3. Start the development server:
   ```bash
   npm run dev
   ```
   *The frontend will now be running at `http://localhost:5173`.*

---

## 3. Verify Connections

1. Open your web browser and go to: `http://localhost:5173`
2. Check your **backend terminal** logs. You should see messages indicating successful connections, such as:
   * `WakeWord WebSocket Connected`
   * `Notification WebSocket Connected`

**You are now ready to use Orma AI!**

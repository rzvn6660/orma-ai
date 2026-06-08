import axios from 'axios';

// Configure base URL from environment variable or default to localhost
const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000',
  timeout: 30000,
});

// Centralized API services
export const healthApi = {
  check: async () => {
    const { data } = await api.get('/api/health');
    return data;
  }
};

export const speechApi = {
  transcribe: async (audioBlob, language = null) => {
    const formData = new FormData();
    formData.append('audio', audioBlob, 'recording.webm');
    if (language) formData.append('language', language);
    
    const { data } = await api.post('/api/speech/transcribe', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
    return data;
  }
};

export const chatApi = {
  sendMessage: async (text, userId = 'default_user', language = 'en') => {
    const { data } = await api.post('/api/chat', { message: text, user_id: userId, language });
    return data;
  }
};

export const medicineApi = {
  getReminders: async () => {
    const { data } = await api.get('/api/medicines');
    return data;
  },
  takeMedicine: async (id) => {
    const { data } = await api.put(`/api/medicines/${id}/taken`);
    return data;
  },
  createReminder: async (reminderData) => {
    const { data } = await api.post('/api/medicines', reminderData);
    return data;
  },
  parseVoice: async (text) => {
    const formData = new FormData();
    formData.append('text', text);
    const { data } = await api.post('/api/medicines/parse-voice', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
    return data;
  },
  parseOcr: async (file) => {
    const formData = new FormData();
    formData.append('file', file);
    const { data } = await api.post('/api/medicines/parse-ocr', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
    return data;
  },
  getPendingReminders: async () => {
    const { data } = await api.get('/api/medicines/pending-reminders');
    return data;
  }
};

export const emergencyApi = {
  analyze: async (text, userId = 'default_user') => {
    const { data } = await api.post('/api/emergency/analyze', { text, user_id: userId });
    return data;
  }
};

export const memoryApi = {
  getContext: async (userId, query) => {
    const { data } = await api.get(`/api/memory/${userId}/context`, { params: { query } });
    return data;
  }
};

export default api;

import axios from 'axios';

// Configure base URL from environment variable or default to localhost
const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000',
  timeout: 30000,
});

// Add token interceptor
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('orma_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }

  // ASIF: Support multi-patient contexts
  const subjectId = localStorage.getItem('orma_subject_id');
  if (subjectId) {
    config.headers['X-Subject-Id'] = subjectId;
  }

  return config;
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
  sendMessage: async (text, userId = 'default_user', languagePref = 'auto', detectedLang = 'en') => {
    const { data } = await api.post('/api/chat', {
      message: text,
      user_id: userId,
      language_preference: languagePref,
      detected_language: detectedLang
    });
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
  skipMedicine: async (id) => {
    const { data } = await api.put(`/api/medicines/${id}/skipped`);
    return data;
  },
  snoozeMedicine: async (id, minutes) => {
    const { data } = await api.put(`/api/medicines/${id}/snooze`, { minutes });
    return data;
  },
  missMedicine: async (id) => {
    const { data } = await api.put(`/api/medicines/${id}/missed`);
    return data;
  },
  deleteReminder: async (id) => {
    const { data } = await api.delete(`/api/medicines/${id}`);
    return data;
  },
  createReminder: async (reminderData) => {
    const { data } = await api.post('/api/medicines', reminderData);
    return data;
  },
  updateReminder: async (id, reminderData) => {
    const { data } = await api.put(`/api/medicines/${id}`, reminderData);
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

export const caregiverApi = {
  getSummary: async () => {
    const { data } = await api.get('/api/caregiver/summary');
    return data;
  },
  getAdherence: async () => {
    const { data } = await api.get('/api/caregiver/adherence');
    return data;
  },
  getEmergencies: async () => {
    const { data } = await api.get('/api/caregiver/emergencies');
    return data;
  },
  getBehavior: async () => {
    const { data } = await api.get('/api/caregiver/behavior');
    return data;
  }
};

export const wellnessApi = {
  getSummary: async () => {
    const { data } = await api.get('/api/wellness/summary');
    return data;
  }
};

export const authApi = {
  login: async (email, password) => {
    const { data } = await api.post('/api/auth/login', { email, password });
    return data;
  },
  signup: async (userData) => {
    const { data } = await api.post('/api/auth/signup', userData);
    return data;
  },
  getMe: async () => {
    const { data } = await api.get('/api/auth/me');
    return data;
  },
  updateMe: async (userData) => {
    const { data } = await api.put('/api/auth/me', userData);
    return data;
  },
  googleLogin: async ({ id_token, role }) => {
    const { data } = await api.post('/api/auth/google', { id_token, role });
    return data;
  },
  requestOtp: async (phone) => {
    const { data } = await api.post('/api/auth/request-otp', { phone });
    return data;
  },
  verifyOtp: async (phone, otp, role) => {
    const { data } = await api.post('/api/auth/verify-otp', { phone, otp, role });
    return data;
  }
};

export const linkApi = {
  generateCode: async () => {
    const { data } = await api.post('/api/link/generate_code');
    return data;
  },
  connectCaregiver: async (code) => {
    const { data } = await api.post('/api/link/connect', { code });
    return data;
  },
  getLinkedUsers: async () => {
    const { data } = await api.get('/api/link/linked_users');
    return data;
  },
  revokeAccess: async (targetId) => {
    const { data } = await api.post(`/api/link/revoke/${targetId}`);
    return data;
  },
  getPendingRequests: async () => {
    const { data } = await api.get('/api/link/pending_requests');
    return data;
  },
  approveRequest: async (targetId) => {
    const { data } = await api.post(`/api/link/approve/${targetId}`);
    return data;
  },
  declineRequest: async (targetId) => {
    const { data } = await api.post(`/api/link/decline/${targetId}`);
    return data;
  }
};

export const notificationApi = {
  getNotifications: async () => {
    const { data } = await api.get('/api/notifications/');
    return data;
  },
  markRead: async (notifId) => {
    const { data } = await api.post(`/api/notifications/${notifId}/read`);
    return data;
  }
};

export const healthRecordApi = {
  getRecords: async () => {
    const { data } = await api.get('/api/health-records/');
    return data;
  },
  createRecord: async (recordData) => {
    const { data } = await api.post('/api/health-records/', recordData);
    return data;
  },
  updateRecord: async (id, recordData) => {
    const { data } = await api.put(`/api/health-records/${id}`, recordData);
    return data;
  },
  deleteRecord: async (id) => {
    const { data } = await api.delete(`/api/health-records/${id}`);
    return data;
  }
};

export const healthPlannerApi = {
  getEvents: async () => {
    const { data } = await api.get('/api/health-planner/');
    return data;
  },
  createEvent: async (eventData) => {
    const { data } = await api.post('/api/health-planner/', eventData);
    return data;
  },
  completeEvent: async (id) => {
    const { data } = await api.put(`/api/health-planner/${id}/completed`);
    return data;
  },
  deleteEvent: async (id) => {
    const { data } = await api.delete(`/api/health-planner/${id}`);
    return data;
  }
};

export const ocmeMemoryApi = {
  getMemories: async (params) => {
    const { data } = await api.get('/api/ocme/', { params });
    return data;
  },
  getMemory: async (id) => {
    const { data } = await api.get(`/api/ocme/${id}`);
    return data;
  },
  updateMemory: async (id, updates) => {
    const { data } = await api.put(`/api/ocme/${id}`, updates);
    return data;
  },
  deleteMemory: async (id) => {
    const { data } = await api.delete(`/api/ocme/${id}`);
    return data;
  },
  pinMemory: async (id) => {
    const { data } = await api.post(`/api/ocme/${id}/pin`);
    return data;
  },
  shareMemory: async (id) => {
    const { data } = await api.post(`/api/ocme/${id}/share`);
    return data;
  },
  explainMemory: async (id) => {
    const { data } = await api.post(`/api/ocme/${id}/explain`);
    return data;
  }
};

export const aleApi = {
  getProfile: async (userId = 1) => {
    const { data } = await api.get(`/api/ale/profile/${userId}`);
    return data;
  },
  updateProfile: async (userId = 1, updates) => {
    const { data } = await api.put(`/api/ale/profile/${userId}`, updates);
    return data;
  },
  getCandidates: async (userId = 1, status = 'pending') => {
    const { data } = await api.get(`/api/ale/candidates/${userId}`, { params: { status } });
    return data;
  },
  resolveCandidate: async (id, resolution) => {
    const { data } = await api.post(`/api/ale/candidates/${id}/resolve`, { resolution });
    return data;
  },
  testGenerate: async () => {
    const { data } = await api.post('/api/ale/test-generate');
    return data;
  }
};

export const rljApi = {
  getJournalEntries: async (userId = 1, entryType = '') => {
    const { data } = await api.get(`/api/rlj/journal/${userId}`, { params: { entry_type: entryType } });
    return data;
  },
  getTimeline: async (userId = 1) => {
    const { data } = await api.get(`/api/rlj/timeline/${userId}`);
    return data;
  },
  getCaregiverSummaries: async (userId = 1) => {
    const { data } = await api.get(`/api/rlj/caregiver-summary/${userId}`);
    return data;
  },
  triggerGeneration: async (userId = 1, reflectionType = 'daily') => {
    const { data } = await api.post(`/api/rlj/generate/${userId}?reflection_type=${reflectionType}`);
    return data;
  },
  triggerMockEvent: async (userId = 1) => {
    const { data } = await api.post(`/api/rlj/timeline/${userId}/mock-event`);
    return data;
  }
};

export const oweApi = {
  getAuditLogs: async (limit = 50) => {
    const { data } = await api.get(`/api/owe/audit`, { params: { limit } });
    return data;
  },
  getPendingApprovals: async () => {
    const { data } = await api.get(`/api/owe/approvals`);
    return data;
  },
  resolveApproval: async (id, status) => {
    const { data } = await api.post(`/api/owe/approvals/${id}/resolve`, { status });
    return data;
  },
  testTrigger: async (eventName, action = 'create') => {
    const { data } = await api.post(`/api/owe/test-trigger`, null, { params: { event_name: eventName, action } });
    return data;
  }
};

export const tsgpApi = {
  getSafetyAudits: async (limit = 50) => {
    const { data } = await api.get(`/api/tsgp/audit`, { params: { limit } });
    return data;
  },
  evaluateRequest: async (requestText, intent = 'GeneralChat', role = 'user') => {
    const { data } = await api.post(`/api/tsgp/evaluate-request`, null, {
      params: { request_text: requestText, intent, role }
    });
    return data;
  }
};

export const reportApi = {
  downloadReport: async () => {
    const response = await api.get('/api/reports/download', {
      responseType: 'blob'
    });
    return response;
  }
};

export const insightsApi = {
  getSummary: async () => {
    const { data } = await api.get('/api/insights/summary');
    return data;
  }
};

export default api;

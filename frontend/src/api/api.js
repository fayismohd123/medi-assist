import axios from 'axios';

const api = axios.create({
  baseURL: '/api',
  withCredentials: true,
  headers: {
    'Content-Type': 'application/json',
  },
});

export const authAPI = {
  login: (email, password) => api.post('/login', { email, password }),
  signup: (name, email, password) => api.post('/signup', { name, email, password }),
  logout: () => api.post('/logout'),
  checkAuth: () => api.get('/auth/status'),
};

export const patientAPI = {
  lookup: (phone) => api.get(`/lookup-patient?phone=${encodeURIComponent(phone)}`),
  register: (name, phone, age) => api.post('/register-patient', { name, phone, age }),
};

// Recording endpoints are at root level, not under /api
const recordingAxios = axios.create({
  baseURL: '/',
  withCredentials: true,
});

export const recordingAPI = {
  start: () => recordingAxios.post('/start-recording'),
  stop: (formData) => {
    return recordingAxios.post('/stop-recording', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
  },
  generateReport: () => recordingAxios.post('/generate_report'),
};

export default api;

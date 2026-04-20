import axios from 'axios';

// In production: nginx proxies /twilio/* → twilio-service:8002/*
// In dev:        vite proxy does the same via vite.config.ts server.proxy
const getTwilioBaseURL = () => {
  if (import.meta.env.VITE_TWILIO_API_URL) {
    return import.meta.env.VITE_TWILIO_API_URL;
  }
  return '/twilio';
};

const twilioClient = axios.create({
  baseURL: getTwilioBaseURL(),
  timeout: 20000,
});

twilioClient.interceptors.request.use((config) => {
  const token = localStorage.getItem('mhealth_auth_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

twilioClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response) {
      console.error('Twilio API error:', error.response.status, error.response.data);
    } else {
      console.error('Twilio API network error:', error.message);
    }
    return Promise.reject(error);
  },
);

export default twilioClient;

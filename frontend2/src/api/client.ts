import axios from 'axios';

const baseURL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

const apiClient = axios.create({
  baseURL,
  timeout: 15000,
});

// Request interceptor to add auth token
apiClient.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('mhealth_auth_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor for error handling
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response) {
      console.error('API error:', error.response.status, error.response.data);
      
      // Handle unauthorized errors
      if (error.response.status === 401) {
        localStorage.removeItem('mhealth_auth_token');
        localStorage.removeItem('mhealth_admin_id');
        window.location.href = '/login';
      }
    } else {
      console.error('API network error:', error.message);
    }
    return Promise.reject(error);
  },
);

export default apiClient;

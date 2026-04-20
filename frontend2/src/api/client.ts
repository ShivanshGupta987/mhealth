import axios from 'axios';

// Use dynamic API URL based on current host (supports both IP and domain)
// Automatically handles HTTP/HTTPS based on how frontend is accessed
// In production (Docker):
// - Always uses nginx proxy (/api) to avoid mixed content and CORS issues
// - Nginx forwards /api/* to backend-api:8000 internally
// In development, uses VITE_API_URL or localhost
const getBaseURL = () => {
  if (import.meta.env.VITE_API_URL) {
    return import.meta.env.VITE_API_URL;
  }
  
  if (import.meta.env.MODE === 'production') {
    // In production Docker, always use nginx proxy
    // This works for both HTTP and HTTPS, any port
    return '/api';
  }
  
  return 'http://localhost:8000';
};

const baseURL = getBaseURL();

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

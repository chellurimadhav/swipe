// API Configuration
// Use environment variable in production, localhost for development
const getApiBaseUrl = (): string => {
  // Check for environment variable first
  if (import.meta.env.VITE_API_URL) {
    const url = import.meta.env.VITE_API_URL;
    // Ensure no trailing slash
    return url.replace(/\/$/, '');
  }
  
  // Default to localhost for development
  const baseUrl = 'http://localhost:5000/api';
  // Ensure no trailing slash
  return baseUrl.replace(/\/$/, '');
};

const API_BASE_URL = getApiBaseUrl();

export default API_BASE_URL;


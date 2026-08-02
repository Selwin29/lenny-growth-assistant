import axios from "axios";

const API_BASE_URL = import.meta.env.VITE_API_URL || "http://localhost:8000/api/v1";

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    "Content-Type": "application/json",
  },
  timeout: 60000, // 60s timeout for LLM responses
});

// Request interceptor to dynamically inject the bearer token
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem("lenny_auth_token");
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor for unified error handling
api.interceptors.response.use(
  (response) => response,
  (error) => {
    // Automatically redirect to /login on 401 Unauthorized
    if (error.response && error.response.status === 401) {
      console.warn("Unauthorized request. Clearing credentials and redirecting to login.");
      localStorage.removeItem("lenny_auth_token");
      localStorage.removeItem("lenny_auth_user");
      // Check if not already on the login page to avoid redirect loops
      if (!window.location.pathname.startsWith("/login")) {
        window.location.href = "/login?expired=true";
      }
    }
    console.error("API Error:", error.response || error.message);
    return Promise.reject(error);
  }
);

export default api;

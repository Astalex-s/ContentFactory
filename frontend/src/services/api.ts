/**
 * Centralized Axios instance.
 * baseURL from .env (VITE_API_BASE_URL)
 * Interceptors for request/response handling.
 */
import axios, { AxiosError } from "axios";

/** /api = proxy (nginx/vite); http://localhost:8000 = direct backend */
const baseURL = import.meta.env.VITE_API_BASE_URL || "/api";

/** Base URL for API (used for image URLs) */
export const apiBaseURL = baseURL;

export const api = axios.create({
  baseURL,
  timeout: 10000,
  headers: {
    "Content-Type": "application/json",
  },
});

// Request interceptor
api.interceptors.request.use(
  (config) => {
    // Add auth token, logging, etc. if needed
    return config;
  },
  (error) => Promise.reject(error)
);

// Response interceptor
api.interceptors.response.use(
  (response) => response,
  (error: AxiosError) => {
    // Centralized error handling
    if (error.response) {
      // Server responded with error status
      const status = error.response.status;
      const data = error.response.data as { detail?: string } | undefined;
      console.error(`API Error ${status}:`, data?.detail ?? error.message);
    } else if (error.request) {
      console.error("Network error:", error.message);
    } else {
      console.error("Request error:", error.message);
    }
    return Promise.reject(error);
  }
);

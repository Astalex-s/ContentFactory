/**
 * Centralized Axios instance.
 * baseURL from .env (VITE_API_BASE_URL)
 * Interceptors for request/response handling.
 */
import axios, { AxiosError } from "axios";

/** /api = proxy (prod/nginx); http://localhost:8000 = локальная разработка */
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
    if (config.url?.includes("publish/bulk") && config.data?.publications) {
      const pubs = config.data.publications as Array<{ content_id?: unknown; account_id?: unknown }>;
      for (let i = 0; i < pubs.length; i++) {
        const cid = String(pubs[i]?.content_id ?? "");
        const aid = String(pubs[i]?.account_id ?? "");
        if (cid === "undefined" || cid === "null" || aid === "undefined" || aid === "null") {
          return Promise.reject(
            new Error(
              `Некорректные данные публикации ${i + 1}. Обновите страницу, выберите контент и аккаунт заново.`
            )
          );
        }
      }
    }
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

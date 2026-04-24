import axios, { AxiosError, InternalAxiosRequestConfig } from "axios";

// Build the API base URL dynamically from the page's hostname so the app works
// whether it's accessed via localhost, an IP (e.g. 192.168.x.y), or a hostname.
// VITE_API_BASE_URL still wins if explicitly set.
function resolveApiBaseUrl(): string {
  const fromEnv = import.meta.env.VITE_API_BASE_URL;
  if (fromEnv !== undefined) return fromEnv;
  if (typeof window !== "undefined") {
    const { protocol, hostname } = window.location;
    return `${protocol}//${hostname}:8000`;
  }
  return "http://localhost:8000";
}

const baseURL = resolveApiBaseUrl();

export const httpClient = axios.create({
  baseURL,
  withCredentials: true, // send httpOnly cookies cross-origin
});

// --- 401 → refresh → retry original request ---------------------------------
interface RetryConfig extends InternalAxiosRequestConfig {
  _retry?: boolean;
}

let refreshInFlight: Promise<void> | null = null;

async function refreshTokens(): Promise<void> {
  if (!refreshInFlight) {
    refreshInFlight = httpClient.post("/api/v1/auth/refresh").then(
      () => {
        refreshInFlight = null;
      },
      (err) => {
        refreshInFlight = null;
        throw err;
      },
    );
  }
  return refreshInFlight;
}

httpClient.interceptors.response.use(
  (response) => response,
  async (error: AxiosError) => {
    const original = error.config as RetryConfig | undefined;
    const status = error.response?.status;
    const url = original?.url ?? "";

    // Do not attempt refresh for the auth endpoints themselves
    const isAuthEndpoint =
      url.includes("/auth/login") ||
      url.includes("/auth/refresh") ||
      url.includes("/auth/logout");

    if (status === 401 && original && !original._retry && !isAuthEndpoint) {
      original._retry = true;
      try {
        await refreshTokens();
        return httpClient(original);
      } catch {
        // fall through — interceptor below handles redirect via AuthContext
      }
    }

    return Promise.reject(error);
  },
);

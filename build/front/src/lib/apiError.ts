import { AxiosError } from "axios";

/** Extract the `detail` message returned by the backend, or a sensible fallback. */
export function getApiErrorMessage(err: unknown, fallback = "Erreur serveur"): string {
  if (err instanceof AxiosError) {
    const detail = err.response?.data?.detail;
    if (typeof detail === "string") return detail;
    if (Array.isArray(detail)) {
      return detail.map((d) => d.msg ?? String(d)).join(", ");
    }
    if (err.response?.status === 401) return "Non authentifié";
    if (err.response?.status === 403) return "Accès refusé";
    if (err.message) return err.message;
  }
  if (err instanceof Error) return err.message;
  return fallback;
}

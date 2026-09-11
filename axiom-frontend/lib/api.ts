const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export class ApiError extends Error {
  status: number;
  constructor(status: number, message: string) {
    super(message);
    this.status = status;
  }
}

function getAccessToken(): string | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem("axiom_access_token");
}

function getRefreshToken(): string | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem("axiom_refresh_token");
}

export function setAccessToken(token: string | null) {
  if (typeof window === "undefined") return;
  if (token) localStorage.setItem("axiom_access_token", token);
  else localStorage.removeItem("axiom_access_token");
}

export function setRefreshToken(token: string | null) {
  if (typeof window === "undefined") return;
  if (token) localStorage.setItem("axiom_refresh_token", token);
  else localStorage.removeItem("axiom_refresh_token");
}

// Несколько запросов могут словить 401 почти одновременно (например, дашборд
// сразу после открытия делает пару параллельных запросов) — де-дуплицируем
// попытки обновления токена в один промис, чтобы не слать /auth/refresh
// несколько раз подряд для одного и того же истёкшего токена.
let refreshInFlight: Promise<boolean> | null = null;

async function tryRefreshToken(): Promise<boolean> {
  const refreshToken = getRefreshToken();
  if (!refreshToken) return false;

  if (!refreshInFlight) {
    refreshInFlight = (async () => {
      try {
        const res = await fetch(`${API_URL}/api/v1/auth/refresh`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ refresh_token: refreshToken }),
        });
        if (!res.ok) return false;
        const body = await res.json();
        setAccessToken(body.access_token);
        if (body.refresh_token) setRefreshToken(body.refresh_token);
        return true;
      } catch {
        return false;
      } finally {
        refreshInFlight = null;
      }
    })();
  }
  return refreshInFlight;
}

function extractErrorDetail(body: unknown): string | null {
  // FastAPI отдаёт detail то строкой (бизнес-ошибки), то массивом объектов
  // Pydantic-валидации ({"loc", "msg", "type"}) — без этой развилки 422 на
  // форме регистрации показывал бы "[object Object]" вместо текста ошибки.
  const detail = (body as { detail?: unknown } | null)?.detail;
  if (typeof detail === "string") return detail;
  if (Array.isArray(detail)) {
    const messages = detail
      .map((e) => (e && typeof e === "object" && "msg" in e ? String((e as { msg: unknown }).msg) : null))
      .filter((m): m is string => !!m);
    if (messages.length) return messages.join(", ");
  }
  return null;
}

export async function apiFetch<T>(
  path: string,
  options: RequestInit = {},
  _retriedAfterRefresh = false
): Promise<T> {
  const token = getAccessToken();
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...(options.headers as Record<string, string> | undefined),
  };
  if (token) headers["Authorization"] = `Bearer ${token}`;

  const res = await fetch(`${API_URL}${path}`, { ...options, headers });

  if (res.status === 401 && !_retriedAfterRefresh && getRefreshToken()) {
    const refreshed = await tryRefreshToken();
    if (refreshed) return apiFetch<T>(path, options, true);
    // Refresh не помог (истёк/отозван) — сессия действительно закончилась.
    setAccessToken(null);
    setRefreshToken(null);
  }

  if (!res.ok) {
    let detail = "Что-то пошло не так. Попробуйте ещё раз.";
    try {
      const body = await res.json();
      detail = extractErrorDetail(body) ?? detail;
    } catch {
      // тело не JSON — оставляем сообщение по умолчанию
    }
    throw new ApiError(res.status, detail);
  }

  if (res.status === 204) return undefined as T;
  return res.json() as Promise<T>;
}

export { API_URL };

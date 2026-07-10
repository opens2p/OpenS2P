// ---------------------------------------------------------------------------
// OpenS2P API client — base fetch wrapper with auth header injection
// ---------------------------------------------------------------------------

const TOKEN_KEY = 'opens2p_access_token';

export function getToken(): string | null {
  return localStorage.getItem(TOKEN_KEY);
}

export function setToken(token: string): void {
  localStorage.setItem(TOKEN_KEY, token);
}

export function clearToken(): void {
  localStorage.removeItem(TOKEN_KEY);
}

// ── client-side JWT helpers ─────────────────────────────────────────────

/**
 * Lightweight JWT payload decoder (no signature verification).
 * Useful for reading claims like `exp` and `sub` client-side.
 */
export function decodeTokenPayload(token: string): Record<string, unknown> | null {
  try {
    const parts = token.split('.');
    if (parts.length !== 3) return null;
    const payload = parts[1];
    const decoded = atob(payload.replace(/-/g, '+').replace(/_/g, '/'));
    return JSON.parse(decoded);
  } catch {
    return null;
  }
}

/**
 * Check whether a stored token is expired by reading its `exp` claim.
 * Returns `true` if the token is missing, malformed, or past its expiry.
 */
export function isTokenExpired(token: string | null): boolean {
  if (!token) return true;
  const payload = decodeTokenPayload(token);
  if (!payload) return true;
  const exp = payload.exp as number | undefined;
  if (!exp) return false; // no exp claim — assume valid
  // `exp` is seconds since epoch; compare with current time
  return Date.now() >= exp * 1000;
}

// ── base fetch ───────────────────────────────────────────────────────────

export class ApiError extends Error {
  status: number;
  constructor(status: number, message: string) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
  }
}

export async function apiFetch<T>(
  path: string,
  options: RequestInit = {},
): Promise<T> {
  const token = getToken();
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    ...(options.headers as Record<string, string>),
  };
  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }

  const res = await fetch(path, { ...options, headers });
  const body = await res.json();

  if (!res.ok) {
    throw new ApiError(res.status, body.detail || 'Request failed');
  }

  // Unwrap ApiResponse wrapper if present
  if (body && typeof body === 'object' && 'success' in body && 'data' in body) {
    return body.data as T;
  }
  return body as T;
}

// ── convenience helpers ──────────────────────────────────────────────────

export function apiGet<T>(path: string): Promise<T> {
  return apiFetch<T>(path);
}

export function apiPost<T>(path: string, data?: unknown): Promise<T> {
  return apiFetch<T>(path, {
    method: 'POST',
    body: data ? JSON.stringify(data) : undefined,
  });
}

export function apiPatch<T>(path: string, data: unknown): Promise<T> {
  return apiFetch<T>(path, {
    method: 'PATCH',
    body: JSON.stringify(data),
  });
}

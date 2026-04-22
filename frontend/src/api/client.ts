import { ApiError } from "./errors";

type TokenGetter = () => string | null;
let _getToken: TokenGetter = () => null;

export function setTokenGetter(getter: TokenGetter): void {
  _getToken = getter;
}

export async function apiFetch<T>(path: string, init: RequestInit = {}): Promise<T> {
  const token = _getToken();
  const headers = new Headers(init.headers);

  if (!(init.body instanceof FormData)) {
    headers.set("Content-Type", "application/json");
  }
  if (token !== null) {
    headers.set("Authorization", `Bearer ${token}`);
  }

  const response = await fetch(`/api${path}`, { ...init, headers });

  if (!response.ok) {
    let detail = response.statusText;
    try {
      const body = (await response.json()) as { detail?: string };
      if (body.detail !== undefined) detail = body.detail;
    } catch {
      // keep statusText
    }
    throw new ApiError(response.status, detail);
  }

  if (response.status === 204) {
    return undefined as T;
  }

  return response.json() as Promise<T>;
}

export async function apiFetchBlob(path: string): Promise<Blob> {
  const token = _getToken();
  const headers = new Headers();
  if (token !== null) {
    headers.set("Authorization", `Bearer ${token}`);
  }

  const response = await fetch(`/api${path}`, { headers });

  if (!response.ok) {
    let detail = response.statusText;
    try {
      const body = (await response.json()) as { detail?: string };
      if (body.detail !== undefined) detail = body.detail;
    } catch {
      // keep statusText
    }
    throw new ApiError(response.status, detail);
  }

  return response.blob();
}

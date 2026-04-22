import { apiFetch } from "@/api/client";

export interface AuthResponse {
  id: number;
  email: string;
  jwt_token: string;
}

interface AuthStoreWriter {
  setSession(token: string, user: { id: number; email: string }): void;
}

export function signInApi(email: string, password: string): Promise<AuthResponse> {
  return apiFetch<AuthResponse>("/auth/signin", {
    method: "POST",
    body: JSON.stringify({ email, password }),
  });
}

export function signUpApi(
  email: string,
  username: string,
  password: string,
): Promise<AuthResponse> {
  return apiFetch<AuthResponse>("/auth/signup", {
    method: "POST",
    body: JSON.stringify({ email, username, password }),
  });
}

export async function signIn(
  store: AuthStoreWriter,
  email: string,
  password: string,
): Promise<void> {
  const response = await signInApi(email, password);
  store.setSession(response.jwt_token, { id: response.id, email: response.email });
}

export async function signUp(
  store: AuthStoreWriter,
  email: string,
  username: string,
  password: string,
): Promise<void> {
  const response = await signUpApi(email, username, password);
  store.setSession(response.jwt_token, { id: response.id, email: response.email });
}

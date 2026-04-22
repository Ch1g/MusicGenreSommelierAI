import { makeAutoObservable } from "mobx";

const TOKEN_KEY = "auth_token";
const USER_KEY = "auth_user";

export interface CurrentUser {
  id: number;
  email: string;
}

function loadStoredUser(): CurrentUser | null {
  const stored = localStorage.getItem(USER_KEY);
  if (stored === null) return null;
  try {
    return JSON.parse(stored) as CurrentUser;
  } catch {
    return null;
  }
}

export class AuthStore {
  token: string | null = localStorage.getItem(TOKEN_KEY);
  currentUser: CurrentUser | null = loadStoredUser();

  constructor() {
    makeAutoObservable(this);
  }

  get isAuthenticated(): boolean {
    return this.token !== null;
  }

  setSession(token: string, user: CurrentUser): void {
    this.token = token;
    this.currentUser = user;
    localStorage.setItem(TOKEN_KEY, token);
    localStorage.setItem(USER_KEY, JSON.stringify(user));
  }

  clearSession(): void {
    this.token = null;
    this.currentUser = null;
    localStorage.removeItem(TOKEN_KEY);
    localStorage.removeItem(USER_KEY);
  }
}

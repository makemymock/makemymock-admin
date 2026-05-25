// Admin-scoped localStorage keys. We deliberately namespace under `mmma_*`
// so they cannot collide with the Client app (`mmm_*`) when the two
// frontends are served from the same origin during local dev.

const ACCESS_KEY = 'mmma_access_token';
const REFRESH_KEY = 'mmma_refresh_token';
const USER_KEY = 'mmma_admin_user';

export const tokenStorage = {
  getAccessToken() {
    return localStorage.getItem(ACCESS_KEY);
  },
  getRefreshToken() {
    return localStorage.getItem(REFRESH_KEY);
  },
  getUser() {
    const raw = localStorage.getItem(USER_KEY);
    if (!raw) return null;
    try {
      return JSON.parse(raw);
    } catch {
      return null;
    }
  },
  setSession({ tokens, user }) {
    if (tokens?.access_token) localStorage.setItem(ACCESS_KEY, tokens.access_token);
    if (tokens?.refresh_token) localStorage.setItem(REFRESH_KEY, tokens.refresh_token);
    if (user) localStorage.setItem(USER_KEY, JSON.stringify(user));
  },
  setTokens(tokens) {
    if (tokens?.access_token) localStorage.setItem(ACCESS_KEY, tokens.access_token);
    if (tokens?.refresh_token) localStorage.setItem(REFRESH_KEY, tokens.refresh_token);
  },
  clear() {
    localStorage.removeItem(ACCESS_KEY);
    localStorage.removeItem(REFRESH_KEY);
    localStorage.removeItem(USER_KEY);
  },
  isAuthenticated() {
    return !!localStorage.getItem(ACCESS_KEY);
  },
};

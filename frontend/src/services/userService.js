import api from './axiosInstance';
import { API_BASE_URL } from '../config';
import { tokenStorage } from '../utils/token';

export const userService = {
  async list({ page = 1, page_size = 25, q = '' } = {}) {
    const { data } = await api.get('/users', { params: { page, page_size, q: q || undefined } });
    return data;
  },

  async get(userId) {
    const { data } = await api.get(`/users/${userId}`);
    return data;
  },

  async allEmails(q = '') {
    const { data } = await api.get('/users/emails', { params: { q: q || undefined } });
    return data;
  },

  // CSV download — we hit the endpoint directly with `fetch` so the browser
  // can stream the body straight to disk. Axios would buffer it into a Blob
  // first, which doubles memory for large exports.
  async downloadCsv(q = '') {
    const token = tokenStorage.getAccessToken();
    const url = new URL(`${API_BASE_URL}/users/export.csv`);
    if (q) url.searchParams.set('q', q);
    const res = await fetch(url.toString(), {
      headers: token ? { Authorization: `Bearer ${token}` } : {},
    });
    if (!res.ok) {
      throw new Error(`Download failed (${res.status})`);
    }
    const blob = await res.blob();
    const filename =
      res.headers.get('content-disposition')?.match(/filename="?([^"]+)"?/)?.[1] ||
      'makemymock_users.csv';
    const objectUrl = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = objectUrl;
    link.download = filename;
    document.body.appendChild(link);
    link.click();
    link.remove();
    URL.revokeObjectURL(objectUrl);
  },
};

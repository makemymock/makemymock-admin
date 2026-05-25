import api from './axiosInstance';
import { tokenStorage } from '../utils/token';

export const authService = {
  async login({ email, password }) {
    const { data } = await api.post('/auth/login', { email, password });
    tokenStorage.setSession({ tokens: data.tokens, user: data.user });
    return data;
  },

  async me() {
    const { data } = await api.get('/auth/me');
    return data;
  },

  logout() {
    tokenStorage.clear();
  },
};

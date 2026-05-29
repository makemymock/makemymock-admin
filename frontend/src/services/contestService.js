import api from './axiosInstance';

export const contestService = {
  async list() {
    const { data } = await api.get('/contests');
    return data;
  },

  async get(contestId) {
    const { data } = await api.get(`/contests/${contestId}`);
    return data;
  },

  async create(payload) {
    const { data } = await api.post('/contests', payload);
    return data;
  },

  async update(contestId, payload) {
    const { data } = await api.patch(`/contests/${contestId}`, payload);
    return data;
  },

  async remove(contestId) {
    const { data } = await api.delete(`/contests/${contestId}`);
    return data;
  },

  async participants(contestId) {
    const { data } = await api.get(`/contests/${contestId}/participants`);
    return data;
  },

  async defaultRules() {
    const { data } = await api.get('/contests/default-rules');
    return data;
  },
};

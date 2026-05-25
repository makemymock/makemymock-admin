import api from './axiosInstance';

export const statsService = {
  async getOverview() {
    const { data } = await api.get('/stats/overview');
    return data;
  },
};

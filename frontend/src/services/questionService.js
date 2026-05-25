import api from './axiosInstance';

export const questionService = {
  async getCatalog() {
    const { data } = await api.get('/questions/catalog');
    return data;
  },

  async list(params = {}) {
    const cleaned = Object.fromEntries(
      Object.entries(params).filter(([, v]) => v !== '' && v !== null && v !== undefined)
    );
    const { data } = await api.get('/questions', { params: cleaned });
    return data;
  },

  async get(questionId) {
    const { data } = await api.get(`/questions/${questionId}`);
    return data;
  },
};

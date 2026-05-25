import api from './axiosInstance';

export const emailService = {
  async preview(payload) {
    const { data } = await api.post('/promo-emails/preview', payload);
    return data;
  },

  async send(payload) {
    const { data } = await api.post('/promo-emails/send', payload);
    return data;
  },
};

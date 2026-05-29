import api from './axiosInstance';

/**
 * Observability client — calls into Admin's `/observability/*` endpoints.
 * Usage payload comes from Mongo `usage_events` (instant); infra payload
 * comes from GCP Cloud Monitoring (60s cached server-side).
 */
export const observabilityService = {
  async getUsage() {
    const { data } = await api.get('/observability/usage');
    return data;
  },

  async getInfra() {
    const { data } = await api.get('/observability/infra');
    return data;
  },
};

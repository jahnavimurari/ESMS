import api from './authService';

export const performanceService = {
  // Cycles
  getCycles: async (params = {}) => {
    const query = new URLSearchParams();
    if (params.status) query.append('status', params.status);
    if (params.page) query.append('page', params.page);
    if (params.per_page) query.append('per_page', params.per_page);

    const response = await api.get(`/api/performance/cycles?${query.toString()}`);
    return response.data;
  },

  getCycle: async (id) => {
    const response = await api.get(`/api/performance/cycles/${id}`);
    return response.data;
  },

  createCycle: async (data) => {
    const response = await api.post('/api/performance/cycles', data);
    return response.data;
  },

  updateCycle: async (id, data) => {
    const response = await api.put(`/api/performance/cycles/${id}`, data);
    return response.data;
  },

  updateCycleStatus: async (id, status) => {
    const response = await api.patch(`/api/performance/cycles/${id}/status`, { status });
    return response.data;
  },

  // Reviews
  getReviews: async (params = {}) => {
    const query = new URLSearchParams();
    if (params.cycle_id) query.append('cycle_id', params.cycle_id);
    if (params.employee_id) query.append('employee_id', params.employee_id);
    if (params.reviewer_id) query.append('reviewer_id', params.reviewer_id);
    if (params.status) query.append('status', params.status);
    if (params.department_id) query.append('department_id', params.department_id);
    if (params.search) query.append('search', params.search);
    if (params.page) query.append('page', params.page);
    if (params.per_page) query.append('per_page', params.per_page);

    const response = await api.get(`/api/performance/reviews?${query.toString()}`);
    return response.data;
  },

  getReview: async (id) => {
    const response = await api.get(`/api/performance/reviews/${id}`);
    return response.data;
  },

  createReview: async (data) => {
    const response = await api.post('/api/performance/reviews', data);
    return response.data;
  },

  updateSelfAssessment: async (id, data) => {
    const response = await api.patch(`/api/performance/reviews/${id}/self-assessment`, data);
    return response.data;
  },

  submitSelfAssessment: async (id) => {
    const response = await api.patch(`/api/performance/reviews/${id}/submit`);
    return response.data;
  },

  submitManagerReview: async (id, data) => {
    const response = await api.patch(`/api/performance/reviews/${id}/manager-review`, data);
    return response.data;
  },

  completeReview: async (id) => {
    const response = await api.patch(`/api/performance/reviews/${id}/complete`);
    return response.data;
  },

  reopenReview: async (id, reason) => {
    const response = await api.patch(`/api/performance/reviews/${id}/reopen`, { reason });
    return response.data;
  },

  // Analytics & Summary
  getPerformanceSummary: async () => {
    const response = await api.get('/api/performance/summary');
    return response.data;
  },

  getReviewHistory: async (id) => {
    const response = await api.get(`/api/performance/reviews/${id}/history`);
    return response.data;
  },

  getRatingsScale: async () => {
    const response = await api.get('/api/performance/ratings-scale');
    return response.data;
  }
};


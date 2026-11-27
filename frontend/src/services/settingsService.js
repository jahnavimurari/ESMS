import api from './authService';

export const settingsService = {
  // Organization settings
  getOrganizationSettings: async () => {
    const response = await api.get('/api/settings/organization');
    return response.data;
  },

  updateOrganizationSettings: async (data) => {
    const response = await api.put('/api/settings/organization', data);
    return response.data;
  },

  // Designations
  getDesignations: async (params = {}) => {
    const response = await api.get('/api/settings/designations', { params });
    return response.data;
  },

  createDesignation: async (data) => {
    const response = await api.post('/api/settings/designations', data);
    return response.data;
  },

  updateDesignation: async (id, data) => {
    const response = await api.put(`/api/settings/designations/${id}`, data);
    return response.data;
  },

  deleteDesignation: async (id) => {
    const response = await api.delete(`/api/settings/designations/${id}`);
    return response.data;
  },

  // Holidays
  getHolidays: async (year = null) => {
    const params = year ? { year } : {};
    const response = await api.get('/api/settings/holidays', { params });
    return response.data;
  },

  createHoliday: async (data) => {
    const response = await api.post('/api/settings/holidays', data);
    return response.data;
  },

  updateHoliday: async (id, data) => {
    const response = await api.put(`/api/settings/holidays/${id}`, data);
    return response.data;
  },

  deleteHoliday: async (id) => {
    const response = await api.delete(`/api/settings/holidays/${id}`);
    return response.data;
  },

  // Shifts
  getShifts: async (params = {}) => {
    const response = await api.get('/api/settings/shifts', { params });
    return response.data;
  },

  createShift: async (data) => {
    const response = await api.post('/api/settings/shifts', data);
    return response.data;
  },

  updateShift: async (id, data) => {
    const response = await api.put(`/api/settings/shifts/${id}`, data);
    return response.data;
  },

  deleteShift: async (id) => {
    const response = await api.delete(`/api/settings/shifts/${id}`);
    return response.data;
  },

  // Employee categories
  getCategories: async (params = {}) => {
    const response = await api.get('/api/settings/categories', { params });
    return response.data;
  },

  createCategory: async (data) => {
    const response = await api.post('/api/settings/categories', data);
    return response.data;
  },

  updateCategory: async (id, data) => {
    const response = await api.put(`/api/settings/categories/${id}`, data);
    return response.data;
  },

  // Leave policies
  getLeavePolicies: async (params = {}) => {
    const response = await api.get('/api/settings/leave-policies', { params });
    return response.data;
  },

  updateLeavePolicy: async (id, data) => {
    const response = await api.put(`/api/settings/leave-policies/${id}`, data);
    return response.data;
  },

  // User preferences
  getUserPreferences: async () => {
    const response = await api.get('/api/settings/preferences');
    return response.data;
  },

  updateUserPreferences: async (data) => {
    const response = await api.put('/api/settings/preferences', data);
    return response.data;
  }
};


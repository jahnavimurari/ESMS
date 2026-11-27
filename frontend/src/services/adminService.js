import api from './authService';

export const adminService = {
  // User Management
  listUsers: async (params = {}) => {
    const response = await api.get('/api/admin/users', { params });
    return response.data;
  },

  getUsers: async (params = {}) => {
    const response = await api.get('/api/admin/users', { params });
    return response.data;
  },

  getUserDetails: async (userId) => {
    const response = await api.get(`/api/admin/users/${userId}`);
    return response.data;
  },

  updateUserRole: async (userId, role) => {
    const response = await api.patch(`/api/admin/users/${userId}/role`, { role });
    return response.data;
  },

  updateUserStatus: async (userId, isActive) => {
    const response = await api.patch(`/api/admin/users/${userId}/status`, { is_active: isActive });
    return response.data;
  },

  // Audit Logs
  listAuditLogs: async (params = {}) => {
    const response = await api.get('/api/admin/audit-logs', { params });
    return response.data;
  },

  getAuditLogs: async (params = {}) => {
    const response = await api.get('/api/admin/audit-logs', { params });
    return response.data;
  },

  // System Administration & Health
  getSystemStats: async () => {
    const response = await api.get('/api/admin/system-stats');
    return response.data;
  }
};

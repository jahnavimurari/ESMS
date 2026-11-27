import api from './authService';

export const leaveService = {
  getLeaveTypes: async (includeInactive = false) => {
    const response = await api.get(`/api/leaves/types?include_inactive=${includeInactive}`);
    return response.data;
  },

  createLeaveType: async (data) => {
    const response = await api.post('/api/leaves/types', data);
    return response.data;
  },

  updateLeaveType: async (typeId, data) => {
    const response = await api.put(`/api/leaves/types/${typeId}`, data);
    return response.data;
  },

  applyLeave: async (data) => {
    const response = await api.post('/api/leaves', data);
    return response.data;
  },

  getMyLeaves: async (params = {}) => {
    const query = new URLSearchParams();
    if (params.status) query.append('status', params.status);
    if (params.year) query.append('year', params.year);
    if (params.limit) query.append('limit', params.limit);
    if (params.offset) query.append('offset', params.offset);

    const response = await api.get(`/api/leaves/my?${query.toString()}`);
    return response.data;
  },

  getMyBalances: async (year = '') => {
    const query = new URLSearchParams();
    if (year) query.append('year', year);

    const response = await api.get(`/api/leaves/balance?${query.toString()}`);
    return response.data;
  },

  getLeavesList: async (params = {}) => {
    const query = new URLSearchParams();
    if (params.search) query.append('search', params.search);
    if (params.department_id) query.append('department_id', params.department_id);
    if (params.leave_type_id) query.append('leave_type_id', params.leave_type_id);
    if (params.status) query.append('status', params.status);
    if (params.start_date) query.append('start_date', params.start_date);
    if (params.end_date) query.append('end_date', params.end_date);
    if (params.limit) query.append('limit', params.limit);
    if (params.offset) query.append('offset', params.offset);

    const response = await api.get(`/api/leaves?${query.toString()}`);
    return response.data;
  },

  getLeaveSummary: async (year = '') => {
    const query = new URLSearchParams();
    if (year) query.append('year', year);

    const response = await api.get(`/api/leaves/summary?${query.toString()}`);
    return response.data;
  },

  updateLeaveRequest: async (leaveId, data) => {
    const response = await api.put(`/api/leaves/${leaveId}`, data);
    return response.data;
  },

  approveLeave: async (leaveId, comments = '') => {
    const response = await api.patch(`/api/leaves/${leaveId}/approve`, { comments });
    return response.data;
  },

  rejectLeave: async (leaveId, comments = '') => {
    const response = await api.patch(`/api/leaves/${leaveId}/reject`, { comments });
    return response.data;
  },

  cancelLeave: async (leaveId) => {
    const response = await api.patch(`/api/leaves/${leaveId}/cancel`);
    return response.data;
  },
};


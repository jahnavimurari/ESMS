import api from './authService';

export const taskService = {
  getTasks: async (params = {}) => {
    const query = new URLSearchParams();
    if (params.status) query.append('status', params.status);
    if (params.priority) query.append('priority', params.priority);
    if (params.category) query.append('category', params.category);
    if (params.assigned_to) query.append('assigned_to', params.assigned_to);
    if (params.department_id) query.append('department_id', params.department_id);
    if (params.overdue) query.append('overdue', params.overdue);
    if (params.search) query.append('search', params.search);
    if (params.page) query.append('page', params.page);
    if (params.per_page) query.append('per_page', params.per_page);

    const response = await api.get(`/api/tasks?${query.toString()}`);
    return response.data;
  },

  getMyTasks: async (params = {}) => {
    const query = new URLSearchParams();
    if (params.status) query.append('status', params.status);
    if (params.priority) query.append('priority', params.priority);
    if (params.category) query.append('category', params.category);
    if (params.overdue) query.append('overdue', params.overdue);
    if (params.search) query.append('search', params.search);
    if (params.page) query.append('page', params.page);
    if (params.per_page) query.append('per_page', params.per_page);

    const response = await api.get(`/api/tasks/my?${query.toString()}`);
    return response.data;
  },

  getTask: async (id) => {
    const response = await api.get(`/api/tasks/${id}`);
    return response.data;
  },

  createTask: async (data) => {
    const response = await api.post('/api/tasks', data);
    return response.data;
  },

  updateTask: async (id, data) => {
    const response = await api.put(`/api/tasks/${id}`, data);
    return response.data;
  },

  updateTaskStatus: async (id, status, comment = null) => {
    const payload = { status };
    if (comment) payload.comment = comment;
    const response = await api.patch(`/api/tasks/${id}/status`, payload);
    return response.data;
  },

  assignTask: async (id, assignedTo, comment = null) => {
    const payload = { assigned_to: assignedTo };
    if (comment) payload.comment = comment;
    const response = await api.patch(`/api/tasks/${id}/assign`, payload);
    return response.data;
  },

  cancelTask: async (id, reason = null) => {
    const payload = {};
    if (reason) payload.reason = reason;
    const response = await api.patch(`/api/tasks/${id}/cancel`, payload);
    return response.data;
  },

  getTaskSummary: async (departmentId = null) => {
    const query = departmentId ? `?department_id=${departmentId}` : '';
    const response = await api.get(`/api/tasks/summary${query}`);
    return response.data;
  },

  getTaskHistory: async (id) => {
    const response = await api.get(`/api/tasks/${id}/history`);
    return response.data;
  }
};


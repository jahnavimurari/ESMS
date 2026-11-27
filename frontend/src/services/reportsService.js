import api from './authService';

export const reportsService = {
  // 1. Employee Report
  getEmployeeReport: async (params = {}) => {
    const response = await api.get('/reports/employees', { params });
    return response.data;
  },
  exportEmployeeReport: (params = {}, format = 'csv') => {
    return api.get('/reports/employees/export', {
      params: { ...params, format },
      responseType: 'blob'
    });
  },

  // 2. Attendance Report
  getAttendanceReport: async (params = {}) => {
    const response = await api.get('/reports/attendance', { params });
    return response.data;
  },
  exportAttendanceReport: (params = {}, format = 'csv') => {
    return api.get('/reports/attendance/export', {
      params: { ...params, format },
      responseType: 'blob'
    });
  },

  // 3. Leave Report
  getLeaveReport: async (params = {}) => {
    const response = await api.get('/reports/leaves', { params });
    return response.data;
  },
  exportLeaveReport: (params = {}, format = 'csv') => {
    return api.get('/reports/leaves/export', {
      params: { ...params, format },
      responseType: 'blob'
    });
  },

  // 4. Task Report
  getTaskReport: async (params = {}) => {
    const response = await api.get('/reports/tasks', { params });
    return response.data;
  },
  exportTaskReport: (params = {}, format = 'csv') => {
    return api.get('/reports/tasks/export', {
      params: { ...params, format },
      responseType: 'blob'
    });
  },

  // 5. Performance Report
  getPerformanceReport: async (params = {}) => {
    const response = await api.get('/reports/performance', { params });
    return response.data;
  },
  exportPerformanceReport: (params = {}, format = 'csv') => {
    return api.get('/reports/performance/export', {
      params: { ...params, format },
      responseType: 'blob'
    });
  }
};

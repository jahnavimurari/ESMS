import api from './authService';

export const dashboardService = {
  getAdminDashboard: async () => {
    const response = await api.get('/api/dashboard/admin');
    return response.data;
  },

  getHRDashboard: async (departmentId = null) => {
    const url = departmentId ? `/api/dashboard/hr?department_id=${departmentId}` : '/api/dashboard/hr';
    const response = await api.get(url);
    return response.data;
  },

  getEmployeeDashboard: async () => {
    const response = await api.get('/api/dashboard/employee');
    return response.data;
  },

  getAttendanceTrends: async (days = 7) => {
    const response = await api.get(`/api/dashboard/attendance-trends?days=${days}`);
    return response.data;
  },

  getDepartmentDistribution: async () => {
    const response = await api.get('/api/dashboard/department-distribution');
    return response.data;
  },

  getTaskAnalytics: async () => {
    const response = await api.get('/api/dashboard/task-analytics');
    return response.data;
  },

  getLeaveAnalytics: async () => {
    const response = await api.get('/api/dashboard/leave-analytics');
    return response.data;
  },

  getPerformanceAnalytics: async (cycleId = null) => {
    const url = cycleId ? `/api/dashboard/performance-analytics?cycle_id=${cycleId}` : '/api/dashboard/performance-analytics';
    const response = await api.get(url);
    return response.data;
  }
};


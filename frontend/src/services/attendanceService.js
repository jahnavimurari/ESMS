import api from './authService';

export const attendanceService = {
  checkIn: async (notes = '') => {
    const response = await api.post('/api/attendance/check-in', { notes });
    return response.data;
  },

  checkOut: async (notes = '') => {
    const response = await api.post('/api/attendance/check-out', { notes });
    return response.data;
  },

  getMyAttendance: async (params = {}) => {
    const query = new URLSearchParams();
    if (params.start_date) query.append('start_date', params.start_date);
    if (params.end_date) query.append('end_date', params.end_date);
    if (params.limit) query.append('limit', params.limit);
    if (params.offset) query.append('offset', params.offset);

    const response = await api.get(`/api/attendance/my?${query.toString()}`);
    return response.data;
  },

  getAttendanceList: async (params = {}) => {
    const query = new URLSearchParams();
    if (params.search) query.append('search', params.search);
    if (params.department_id) query.append('department_id', params.department_id);
    if (params.status) query.append('status', params.status);
    if (params.work_date) query.append('work_date', params.work_date);
    if (params.start_date) query.append('start_date', params.start_date);
    if (params.end_date) query.append('end_date', params.end_date);
    if (params.limit) query.append('limit', params.limit);
    if (params.offset) query.append('offset', params.offset);

    const response = await api.get(`/api/attendance?${query.toString()}`);
    return response.data;
  },

  getSummary: async (workDate = '', departmentId = '') => {
    const query = new URLSearchParams();
    if (workDate) query.append('work_date', workDate);
    if (departmentId) query.append('department_id', departmentId);

    const response = await api.get(`/api/attendance/summary?${query.toString()}`);
    return response.data;
  },

  correctAttendance: async (attendanceId, data) => {
    const response = await api.put(`/api/attendance/${attendanceId}`, data);
    return response.data;
  },
};


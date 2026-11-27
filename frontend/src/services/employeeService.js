import api from './authService';

export const employeeService = {
  // Departments
  getDepartments: async (includeInactive = false) => {
    const response = await api.get(`/api/employees/departments?include_inactive=${includeInactive}`);
    return response.data;
  },

  createDepartment: async (deptData) => {
    const response = await api.post('/api/employees/departments', deptData);
    return response.data;
  },

  updateDepartment: async (deptId, deptData) => {
    const response = await api.put(`/api/employees/departments/${deptId}`, deptData);
    return response.data;
  },

  // Employees
  getEmployees: async (params = {}) => {
    const query = new URLSearchParams();
    if (params.search) query.append('search', params.search);
    if (params.department_id) query.append('department_id', params.department_id);
    if (params.status) query.append('status', params.status);
    if (params.role) query.append('role', params.role);
    if (params.limit) query.append('limit', params.limit);
    if (params.offset) query.append('offset', params.offset);

    const response = await api.get(`/api/employees?${query.toString()}`);
    return response.data;
  },

  getEmployeeById: async (employeeId) => {
    const response = await api.get(`/api/employees/${employeeId}`);
    return response.data;
  },

  createEmployee: async (employeeData) => {
    const response = await api.post('/api/employees', employeeData);
    return response.data;
  },

  updateEmployee: async (employeeId, employeeData) => {
    const response = await api.put(`/api/employees/${employeeId}`, employeeData);
    return response.data;
  },

  updateEmployeeStatus: async (employeeId, statusData) => {
    const response = await api.patch(`/api/employees/${employeeId}/status`, statusData);
    return response.data;
  },
};


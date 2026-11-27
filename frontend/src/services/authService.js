import axios from 'axios';

const api = axios.create({
  baseURL: '',
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor to ensure JWT access token is always sent
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('esms_access_token');
    if (token) {
      config.headers['Authorization'] = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// Response interceptor to handle transparent token refresh on 401
let isRefreshing = false;
let failedQueue = [];

const processQueue = (error, token = null) => {
  failedQueue.forEach((prom) => {
    if (error) {
      prom.reject(error);
    } else {
      prom.resolve(token);
    }
  });
  failedQueue = [];
};

api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;

    const isAuthRoute = originalRequest?.url?.includes('/api/auth/login') ||
                        originalRequest?.url?.includes('/api/auth/refresh');

    if (error.response?.status === 401 && !originalRequest?._retry && !isAuthRoute) {
      const storedRefresh = localStorage.getItem('esms_refresh_token');
      if (!storedRefresh) {
        return Promise.reject(error);
      }

      if (isRefreshing) {
        return new Promise((resolve, reject) => {
          failedQueue.push({ resolve, reject });
        })
          .then((newToken) => {
            originalRequest.headers['Authorization'] = `Bearer ${newToken}`;
            return api(originalRequest);
          })
          .catch((err) => Promise.reject(err));
      }

      originalRequest._retry = true;
      isRefreshing = true;

      try {
        const res = await axios.post('/api/auth/refresh', {}, {
          headers: { Authorization: `Bearer ${storedRefresh}` },
        });

        if (res.data?.success && res.data?.data?.access_token) {
          const newAccess = res.data.data.access_token;
          localStorage.setItem('esms_access_token', newAccess);
          setAuthHeader(newAccess);
          processQueue(null, newAccess);
          originalRequest.headers['Authorization'] = `Bearer ${newAccess}`;
          return api(originalRequest);
        } else {
          processQueue(new Error('Refresh failed'));
          return Promise.reject(error);
        }
      } catch (refreshErr) {
        processQueue(refreshErr);
        localStorage.removeItem('esms_access_token');
        localStorage.removeItem('esms_refresh_token');
        if (typeof window !== 'undefined' && !window.location.pathname.startsWith('/login')) {
          window.location.href = '/login';
        }
        return Promise.reject(refreshErr);
      } finally {
        isRefreshing = false;
      }
    }

    return Promise.reject(error);
  }
);

export const setAuthHeader = (token) => {
  if (token) {
    api.defaults.headers.common['Authorization'] = `Bearer ${token}`;
  } else {
    delete api.defaults.headers.common['Authorization'];
  }
};

export const authApi = {
  login: async (credentials) => {
    const response = await api.post('/api/auth/login', credentials);
    return response.data;
  },

  refresh: async (refreshToken) => {
    const response = await axios.post('/api/auth/refresh', {}, {
      headers: {
        'Authorization': `Bearer ${refreshToken}`,
      },
    });
    return response.data;
  },

  logout: async (token) => {
    const response = await api.post('/api/auth/logout', {}, {
      headers: token ? { 'Authorization': `Bearer ${token}` } : {},
    });
    return response.data;
  },

  getCurrentUser: async () => {
    const response = await api.get('/api/auth/me');
    return response.data;
  },

  changePassword: async (passwords) => {
    const response = await api.post('/api/auth/change-password', passwords);
    return response.data;
  },

  health: async () => {
    const response = await api.get('/api/auth/health');
    return response.data;
  },
};

export default api;


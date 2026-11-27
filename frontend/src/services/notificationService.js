import api from './authService';

export const notificationService = {
  getNotifications: async (params = {}) => {
    const response = await api.get('/api/notifications', { params });
    return response.data;
  },

  getUnreadCount: async () => {
    const response = await api.get('/api/notifications/unread-count');
    return response.data;
  },

  markAsRead: async (notifId) => {
    const response = await api.patch(`/api/notifications/${notifId}/read`);
    return response.data;
  },

  markAllAsRead: async () => {
    const response = await api.patch('/api/notifications/read-all');
    return response.data;
  },

  deleteNotification: async (notifId) => {
    const response = await api.delete(`/api/notifications/${notifId}`);
    return response.data;
  },

  broadcastAnnouncement: async (announcementData) => {
    const response = await api.post('/api/notifications/announcements', announcementData);
    return response.data;
  }
};


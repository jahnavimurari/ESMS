import React, { useState, useEffect } from 'react';
import { 
  Bell, Check, Trash2, Filter, Megaphone, Clock, CheckSquare, 
  Calendar, Award, ArrowLeft, RefreshCw, Send, Plus
} from 'lucide-react';
import { useAuth } from '../../context/AuthContext';
import { notificationService } from '../../services/notificationService';

export default function NotificationPage() {
  const { user } = useAuth();
  const [notifications, setNotifications] = useState([]);
  const [loading, setLoading] = useState(true);
  const [unreadOnly, setUnreadOnly] = useState(false);
  const [selectedCategory, setSelectedCategory] = useState('');
  const [unreadCount, setUnreadCount] = useState(0);

  // Announcement modal state for Admin / HR
  const [showAnnouncementModal, setShowAnnouncementModal] = useState(false);
  const [announcementTitle, setAnnouncementTitle] = useState('');
  const [announcementMsg, setAnnouncementMsg] = useState('');
  const [targetRole, setTargetRole] = useState('');
  const [broadcasting, setBroadcasting] = useState(false);

  useEffect(() => {
    fetchNotifications();
  }, [unreadOnly, selectedCategory]);

  const fetchNotifications = async () => {
    setLoading(true);
    try {
      const params = {};
      if (unreadOnly) params.unread_only = true;
      if (selectedCategory) params.category = selectedCategory;
      const res = await notificationService.getNotifications(params);
      if (res?.success) {
        setNotifications(res.data.notifications);
        setUnreadCount(res.data.unread_count);
      }
    } catch {
      // Ignore
    } finally {
      setLoading(false);
    }
  };

  const handleMarkAsRead = async (id) => {
    try {
      await notificationService.markAsRead(id);
      setNotifications(prev => prev.map(n => n.id === id ? { ...n, is_read: true } : n));
      setUnreadCount(prev => Math.max(0, prev - 1));
    } catch {
      // Ignore
    }
  };

  const handleMarkAllAsRead = async () => {
    try {
      await notificationService.markAllAsRead();
      setNotifications(prev => prev.map(n => ({ ...n, is_read: true })));
      setUnreadCount(0);
    } catch {
      // Ignore
    }
  };

  const handleDelete = async (id) => {
    try {
      await notificationService.deleteNotification(id);
      setNotifications(prev => prev.filter(n => n.id !== id));
    } catch {
      // Ignore
    }
  };

  const handleBroadcast = async (e) => {
    e.preventDefault();
    if (!announcementTitle.trim() || !announcementMsg.trim()) return;

    setBroadcasting(true);
    try {
      await notificationService.broadcastAnnouncement({
        title: announcementTitle.trim(),
        message: announcementMsg.trim(),
        target_role: targetRole || null
      });
      setShowAnnouncementModal(false);
      setAnnouncementTitle('');
      setAnnouncementMsg('');
      setTargetRole('');
      fetchNotifications();
    } catch (err) {
      alert(err?.response?.data?.error?.message || 'Failed to broadcast announcement.');
    } finally {
      setBroadcasting(false);
    }
  };

  const getCategoryIcon = (cat) => {
    switch (cat) {
      case 'ATTENDANCE': return <Clock size={16} className="text-emerald-400" />;
      case 'LEAVE': return <Calendar size={16} className="text-amber-400" />;
      case 'TASK': return <CheckSquare size={16} className="text-blue-400" />;
      case 'PERFORMANCE': return <Award size={16} className="text-purple-400" />;
      case 'ANNOUNCEMENT': return <Megaphone size={16} className="text-rose-400" />;
      default: return <Bell size={16} className="text-zinc-400" />;
    }
  };

  const dashboardUrl = user?.role === 'ADMIN' ? '/dashboard/admin' : user?.role === 'HR' ? '/dashboard/hr' : '/dashboard/employee';

  return (
    <div style={{ padding: '2rem', maxWidth: '1200px', margin: '0 auto', width: '100%' }} className="space-y-6">
      {/* Top Header */}
      <div style={{
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        paddingBottom: '1.25rem',
        borderBottom: '1px solid var(--border)'
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
          <div style={{ backgroundColor: 'rgba(59, 130, 246, 0.15)', padding: '0.625rem', borderRadius: 'var(--radius-md)' }}>
            <Bell size={26} color="var(--primary)" />
          </div>
          <div>
            <h1 style={{ fontSize: '1.5rem', fontWeight: 700 }}>Notification Center</h1>
            <span style={{ fontSize: '0.8125rem', color: 'var(--text-secondary)' }}>
              In-app reminders, system alerts, assignments, and organizational announcements
            </span>
          </div>
        </div>

        <div className="flex items-center gap-3">
          {['ADMIN', 'HR'].includes(user?.role) && (
            <button
              onClick={() => setShowAnnouncementModal(true)}
              className="flex items-center gap-2 px-3 py-1.5 bg-blue-600 hover:bg-blue-700 text-white rounded-xl text-xs font-semibold shadow-sm transition-colors"
            >
              <Megaphone size={14} /> New Announcement
            </button>
          )}

          <a
            href={dashboardUrl}
            style={{
              display: 'inline-flex',
              alignItems: 'center',
              gap: '0.5rem',
              padding: '0.5rem 1rem',
              backgroundColor: 'var(--bg-surface-hover)',
              border: '1px solid var(--border)',
              borderRadius: 'var(--radius-md)',
              color: 'var(--text-primary)',
              fontSize: '0.875rem',
              textDecoration: 'none'
            }}
          >
            <ArrowLeft size={16} /> Back
          </a>
        </div>
      </div>

      {/* Filter and Action Bar */}
      <div className="p-4 bg-[var(--surface)] border border-[var(--border)] rounded-2xl flex flex-wrap items-center justify-between gap-4">
        <div className="flex flex-wrap items-center gap-2 text-xs">
          <button
            onClick={() => { setSelectedCategory(''); setUnreadOnly(false); }}
            className={`px-3 py-1.5 rounded-xl font-medium transition-colors ${!selectedCategory && !unreadOnly ? 'bg-blue-600 text-white' : 'bg-[var(--surface-hover)] text-[var(--text-secondary)]'}`}
          >
            All
          </button>
          <button
            onClick={() => setUnreadOnly(prev => !prev)}
            className={`px-3 py-1.5 rounded-xl font-medium transition-colors ${unreadOnly ? 'bg-amber-600 text-white' : 'bg-[var(--surface-hover)] text-[var(--text-secondary)]'}`}
          >
            Unread Only ({unreadCount})
          </button>

          {['ATTENDANCE', 'LEAVE', 'TASK', 'PERFORMANCE', 'ANNOUNCEMENT'].map(cat => (
            <button
              key={cat}
              onClick={() => setSelectedCategory(selectedCategory === cat ? '' : cat)}
              className={`px-3 py-1.5 rounded-xl font-medium transition-colors ${selectedCategory === cat ? 'bg-blue-600 text-white' : 'bg-[var(--surface-hover)] text-[var(--text-secondary)]'}`}
            >
              {cat}
            </button>
          ))}
        </div>

        {unreadCount > 0 && (
          <button
            onClick={handleMarkAllAsRead}
            className="flex items-center gap-1.5 text-xs text-blue-500 hover:text-blue-400 font-semibold"
          >
            <Check size={14} /> Mark all as read
          </button>
        )}
      </div>

      {/* Notifications List */}
      <div className="p-5 bg-[var(--surface)] border border-[var(--border)] rounded-2xl space-y-3">
        {loading ? (
          <div className="p-12 text-center text-xs text-[var(--text-secondary)]">
            <RefreshCw size={24} className="animate-spin text-blue-500 mx-auto mb-2" />
            Loading notifications...
          </div>
        ) : notifications.length === 0 ? (
          <div className="p-12 text-center text-xs text-[var(--text-secondary)] border border-dashed border-[var(--border)] rounded-xl">
            No notifications found in this view.
          </div>
        ) : (
          <div className="divide-y divide-[var(--border)]">
            {notifications.map(n => (
              <div 
                key={n.id} 
                className={`py-4 flex items-start gap-4 transition-colors ${!n.is_read ? 'bg-blue-500/5 px-3 rounded-xl' : ''}`}
              >
                <div className="p-2 bg-[var(--surface-hover)] rounded-xl shrink-0 mt-0.5">
                  {getCategoryIcon(n.category)}
                </div>

                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2">
                    <span className={`text-sm font-semibold ${!n.is_read ? 'text-[var(--text-primary)] font-bold' : 'text-[var(--text-secondary)]'}`}>
                      {n.title}
                    </span>
                    <span className="text-[10px] px-2 py-0.5 rounded-full bg-[var(--surface-hover)] text-[var(--text-secondary)] border border-[var(--border)]">
                      {n.category}
                    </span>
                    {n.priority === 'URGENT' && (
                      <span className="text-[10px] px-2 py-0.5 rounded-full bg-red-500/10 text-red-500 font-bold border border-red-500/20">
                        URGENT
                      </span>
                    )}
                  </div>
                  <p className="text-xs text-[var(--text-secondary)] mt-1 leading-relaxed">
                    {n.message}
                  </p>
                  <div className="flex items-center gap-4 mt-2 text-[11px] text-[var(--text-secondary)]">
                    <span>{new Date(n.created_at).toLocaleString()}</span>
                    {n.action_url && (
                      <a href={n.action_url} className="text-blue-500 hover:underline">
                        Go to item →
                      </a>
                    )}
                  </div>
                </div>

                <div className="flex items-center gap-1 shrink-0">
                  {!n.is_read && (
                    <button
                      onClick={() => handleMarkAsRead(n.id)}
                      title="Mark as read"
                      className="p-1.5 text-zinc-400 hover:text-blue-500 rounded-lg hover:bg-[var(--surface-hover)]"
                    >
                      <Check size={14} />
                    </button>
                  )}
                  <button
                    onClick={() => handleDelete(n.id)}
                    title="Delete notification"
                    className="p-1.5 text-zinc-400 hover:text-red-500 rounded-lg hover:bg-[var(--surface-hover)]"
                  >
                    <Trash2 size={14} />
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Announcement Modal */}
      {showAnnouncementModal && (
        <div className="fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center p-4 z-50">
          <div className="bg-[var(--surface)] border border-[var(--border)] rounded-2xl w-full max-w-md p-6 space-y-4 shadow-2xl">
            <div className="flex items-center justify-between border-b border-[var(--border)] pb-3">
              <h2 className="text-base font-bold text-[var(--text-primary)] flex items-center gap-2">
                <Megaphone size={18} className="text-blue-500" /> Organization Announcement
              </h2>
              <button onClick={() => setShowAnnouncementModal(false)} className="text-zinc-400 hover:text-white">✕</button>
            </div>

            <form onSubmit={handleBroadcast} className="space-y-3 text-xs">
              <div>
                <label className="block text-[var(--text-secondary)] mb-1 font-medium">Announcement Title</label>
                <input
                  type="text"
                  required
                  placeholder="e.g. Annual Company All-Hands Meeting"
                  value={announcementTitle}
                  onChange={e => setAnnouncementTitle(e.target.value)}
                  className="w-full px-3 py-2 bg-[var(--background)] border border-[var(--border)] rounded-xl text-[var(--text-primary)] focus:outline-none focus:border-blue-500"
                />
              </div>

              <div>
                <label className="block text-[var(--text-secondary)] mb-1 font-medium">Target Audience</label>
                <select
                  value={targetRole}
                  onChange={e => setTargetRole(e.target.value)}
                  className="w-full px-3 py-2 bg-[var(--background)] border border-[var(--border)] rounded-xl text-[var(--text-primary)] focus:outline-none focus:border-blue-500"
                >
                  <option value="">All Active Employees</option>
                  <option value="EMPLOYEE">Employees Only</option>
                  <option value="HR">HR Staff Only</option>
                  <option value="ADMIN">Admins Only</option>
                </select>
              </div>

              <div>
                <label className="block text-[var(--text-secondary)] mb-1 font-medium">Message Body</label>
                <textarea
                  rows={4}
                  required
                  placeholder="Type the message to broadcast to all matching users..."
                  value={announcementMsg}
                  onChange={e => setAnnouncementMsg(e.target.value)}
                  className="w-full px-3 py-2 bg-[var(--background)] border border-[var(--border)] rounded-xl text-[var(--text-primary)] focus:outline-none focus:border-blue-500"
                />
              </div>

              <div className="flex items-center justify-end gap-2 pt-2">
                <button
                  type="button"
                  onClick={() => setShowAnnouncementModal(false)}
                  className="px-4 py-2 bg-[var(--surface-hover)] border border-[var(--border)] rounded-xl font-medium"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={broadcasting}
                  className="flex items-center gap-1.5 px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-xl font-semibold disabled:opacity-50"
                >
                  <Send size={13} /> {broadcasting ? 'Broadcasting...' : 'Broadcast'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}


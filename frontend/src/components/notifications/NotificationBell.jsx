import React, { useState, useEffect, useRef } from 'react';
import { Bell, Check, Trash2, ExternalLink, Megaphone, Clock, CheckSquare, Calendar, Award } from 'lucide-react';
import { notificationService } from '../../services/notificationService';

export default function NotificationBell() {
  const [unreadCount, setUnreadCount] = useState(0);
  const [notifications, setNotifications] = useState([]);
  const [isOpen, setIsOpen] = useState(false);
  const [loading, setLoading] = useState(false);
  const dropdownRef = useRef(null);

  useEffect(() => {
    fetchUnreadCount();
    const interval = setInterval(fetchUnreadCount, 30000); // Poll every 30s
    return () => clearInterval(interval);
  }, []);

  useEffect(() => {
    function handleClickOutside(event) {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target)) {
        setIsOpen(false);
      }
    }
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const fetchUnreadCount = async () => {
    try {
      const res = await notificationService.getUnreadCount();
      if (res?.success) {
        setUnreadCount(res.data.unread_count);
      }
    } catch {
      // Ignore background poll errors
    }
  };

  const handleToggle = async () => {
    if (!isOpen) {
      setIsOpen(true);
      setLoading(true);
      try {
        const res = await notificationService.getNotifications({ limit: 6 });
        if (res?.success) {
          setNotifications(res.data.notifications);
          setUnreadCount(res.data.unread_count);
        }
      } catch {
        // Fallback
      } finally {
        setLoading(false);
      }
    } else {
      setIsOpen(false);
    }
  };

  const handleMarkAsRead = async (id, e) => {
    e.stopPropagation();
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

  const getCategoryIcon = (cat) => {
    switch (cat) {
      case 'ATTENDANCE': return <Clock size={14} className="text-emerald-400" />;
      case 'LEAVE': return <Calendar size={14} className="text-amber-400" />;
      case 'TASK': return <CheckSquare size={14} className="text-blue-400" />;
      case 'PERFORMANCE': return <Award size={14} className="text-purple-400" />;
      case 'ANNOUNCEMENT': return <Megaphone size={14} className="text-rose-400" />;
      default: return <Bell size={14} className="text-zinc-400" />;
    }
  };

  return (
    <div className="relative" ref={dropdownRef}>
      <button
        onClick={handleToggle}
        className="relative p-2 rounded-xl text-[var(--text-secondary)] hover:text-[var(--text-primary)] hover:bg-[var(--surface-hover)] transition-colors"
        title="Notifications"
      >
        <Bell size={20} />
        {unreadCount > 0 && (
          <span className="absolute top-1 right-1 flex items-center justify-center min-w-[18px] h-[18px] px-1 text-[10px] font-bold text-white bg-red-500 rounded-full border-2 border-[var(--surface)] animate-pulse">
            {unreadCount > 99 ? '99+' : unreadCount}
          </span>
        )}
      </button>

      {isOpen && (
        <div className="absolute right-0 mt-2 w-80 sm:w-96 bg-[var(--surface)] border border-[var(--border)] rounded-2xl shadow-xl z-50 overflow-hidden">
          {/* Header */}
          <div className="p-3.5 border-b border-[var(--border)] flex items-center justify-between">
            <div className="flex items-center gap-2">
              <span className="text-sm font-bold text-[var(--text-primary)]">Notifications</span>
              {unreadCount > 0 && (
                <span className="px-2 py-0.5 text-[11px] font-semibold bg-red-500/10 text-red-500 rounded-full border border-red-500/20">
                  {unreadCount} unread
                </span>
              )}
            </div>
            {unreadCount > 0 && (
              <button
                onClick={handleMarkAllAsRead}
                className="text-xs text-blue-500 hover:text-blue-400 font-medium flex items-center gap-1"
              >
                <Check size={12} /> Mark all read
              </button>
            )}
          </div>

          {/* List */}
          <div className="max-h-80 overflow-y-auto divide-y divide-[var(--border)]">
            {loading ? (
              <div className="p-8 text-center text-xs text-[var(--text-secondary)]">
                Loading notifications...
              </div>
            ) : notifications.length === 0 ? (
              <div className="p-8 text-center text-xs text-[var(--text-secondary)]">
                No notifications right now.
              </div>
            ) : (
              notifications.map((n) => (
                <div
                  key={n.id}
                  className={`p-3.5 hover:bg-[var(--surface-hover)] transition-colors flex gap-3 ${!n.is_read ? 'bg-blue-500/5' : ''}`}
                >
                  <div className="mt-0.5 shrink-0">
                    {getCategoryIcon(n.category)}
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center justify-between gap-2">
                      <span className={`text-xs font-semibold truncate ${!n.is_read ? 'text-[var(--text-primary)] font-bold' : 'text-[var(--text-secondary)]'}`}>
                        {n.title}
                      </span>
                      {!n.is_read && (
                        <button
                          onClick={(e) => handleMarkAsRead(n.id, e)}
                          title="Mark as read"
                          className="shrink-0 p-1 text-zinc-400 hover:text-blue-500"
                        >
                          <Check size={12} />
                        </button>
                      )}
                    </div>
                    <p className="text-xs text-[var(--text-secondary)] mt-0.5 line-clamp-2">
                      {n.message}
                    </p>
                    <div className="flex items-center justify-between mt-1.5 text-[10px] text-[var(--text-secondary)]">
                      <span>{new Date(n.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</span>
                      {n.action_url && (
                        <a href={n.action_url} className="text-blue-500 hover:underline flex items-center gap-0.5">
                          View <ExternalLink size={10} />
                        </a>
                      )}
                    </div>
                  </div>
                </div>
              ))
            )}
          </div>

          {/* Footer link to full notification center */}
          <div className="p-2.5 border-t border-[var(--border)] text-center bg-[var(--surface)]">
            <a
              href="/notifications"
              className="text-xs text-blue-500 hover:text-blue-400 font-semibold block"
            >
              View All Notifications
            </a>
          </div>
        </div>
      )}
    </div>
  );
}


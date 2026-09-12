import React, { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { apiClient } from '../services/apiClient';
import type { NotificationItem, PaginatedNotifications } from '../types/notification';

export const NotificationCenterPage: React.FC = () => {
  const navigate = useNavigate();
  const [filter, setFilter] = useState<'all' | 'unread'>('all');
  const [page, setPage] = useState(1);
  const pageSize = 10;

  const [notifications, setNotifications] = useState<NotificationItem[]>([]);
  const [total, setTotal] = useState(0);
  const [hasNext, setHasNext] = useState(false);
  const [isLoading, setIsLoading] = useState(true);
  const [isMarkingAll, setIsMarkingAll] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchNotifications = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    try {
      const params: Record<string, any> = {
        page,
        page_size: pageSize,
      };
      if (filter === 'unread') {
        params.is_read = false;
      }

      const response = await apiClient.get<PaginatedNotifications>('/notifications', {
        params,
      });

      setNotifications(response.data.items || []);
      setTotal(response.data.total || 0);
      setHasNext(response.data.has_next || false);
    } catch (err: any) {
      setError(
        err.response?.data?.detail || 'Failed to load notifications. Please check your connection.'
      );
    } finally {
      setIsLoading(false);
    }
  }, [filter, page]);

  useEffect(() => {
    fetchNotifications();
  }, [fetchNotifications]);

  const handleFilterChange = (newFilter: 'all' | 'unread') => {
    if (newFilter !== filter) {
      setFilter(newFilter);
      setPage(1);
    }
  };

  const handleMarkAsRead = async (notificationId: string) => {
    try {
      await apiClient.post(`/notifications/${notificationId}/read`);
      // Update local state immediately
      setNotifications((prev) =>
        prev.map((n) => (n.id === notificationId ? { ...n, is_read: true } : n))
      );
      if (filter === 'unread') {
        setTotal((prev) => Math.max(0, prev - 1));
      }
    } catch (err) {
      console.error('Failed to mark notification as read', err);
    }
  };

  const handleMarkAllAsRead = async () => {
    setIsMarkingAll(true);
    try {
      await apiClient.post('/notifications/read-all');
      setNotifications((prev) => prev.map((n) => ({ ...n, is_read: true })));
      if (filter === 'unread') {
        setNotifications([]);
        setTotal(0);
      }
    } catch (err) {
      console.error('Failed to mark all as read', err);
    } finally {
      setIsMarkingAll(false);
    }
  };

  const handleNavigateReference = (notification: NotificationItem) => {
    if (notification.reference_type === 'DRIVE' && notification.reference_id) {
      navigate(`/drives/${notification.reference_id}`);
    }
  };

  const formatTimestamp = (dateString: string) => {
    try {
      const date = new Date(dateString);
      return date.toLocaleString(undefined, {
        month: 'short',
        day: 'numeric',
        year: 'numeric',
        hour: '2-digit',
        minute: '2-digit',
      });
    } catch {
      return dateString;
    }
  };

  const getNotificationIcon = (type: string) => {
    switch (type) {
      case 'DRIVE_PUBLISHED':
        return (
          <div className="w-9 h-9 rounded-xl bg-blue-100 text-blue-600 flex items-center justify-center flex-shrink-0">
            <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M21 13.255A23.931 23.931 0 0112 15c-3.183 0-6.22-.62-9-1.745M16 6V4a2 2 0 00-2-2h-4a2 2 0 00-2 2v2m4 6h.01M5 20h14a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
            </svg>
          </div>
        );
      case 'SHORTLISTED':
        return (
          <div className="w-9 h-9 rounded-xl bg-emerald-100 text-emerald-600 flex items-center justify-center flex-shrink-0">
            <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M11.049 2.927c.3-.921 1.603-.921 1.902 0l1.519 4.674a1 1 0 00.95.69h4.915c.969 0 1.371 1.24.588 1.81l-3.976 2.888a1 1 0 00-.363 1.118l1.518 4.674c.3.922-.755 1.688-1.538 1.118l-3.976-2.888a1 1 0 00-1.176 0l-3.976 2.888c-.783.57-1.838-.197-1.538-1.118l1.518-4.674a1 1 0 00-.363-1.118l-3.976-2.888c-.784-.57-.38-1.81.588-1.81h4.914a1 1 0 00.951-.69l1.519-4.674z" />
            </svg>
          </div>
        );
      case 'STAGE_UPDATED':
        return (
          <div className="w-9 h-9 rounded-xl bg-purple-100 text-purple-600 flex items-center justify-center flex-shrink-0">
            <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-6 9l2 2 4-4" />
            </svg>
          </div>
        );
      default:
        return (
          <div className="w-9 h-9 rounded-xl bg-indigo-100 text-indigo-600 flex items-center justify-center flex-shrink-0">
            <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
          </div>
        );
    }
  };

  const totalPages = Math.ceil(total / pageSize) || 1;
  const unreadCount = notifications.filter((n) => !n.is_read).length;

  return (
    <div className="max-w-4xl mx-auto space-y-6 animate-fade-in">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between pb-6 border-b border-slate-200 gap-4">
        <div>
          <div className="flex items-center space-x-2">
            <div className="w-8 h-8 rounded-lg bg-indigo-100 text-indigo-600 flex items-center justify-center font-bold">
              <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9" />
              </svg>
            </div>
            <h1 className="text-2xl font-bold text-slate-900 tracking-tight">Notification Center</h1>
          </div>
          <p className="text-sm text-slate-500 mt-1">
            Stay updated with real-time placement announcements, shortlist alerts, and schedule changes.
          </p>
        </div>
        <div className="flex items-center space-x-3">
          <button
            onClick={handleMarkAllAsRead}
            disabled={isMarkingAll || unreadCount === 0}
            className="px-4 py-2 text-xs font-semibold text-indigo-700 bg-indigo-50 hover:bg-indigo-100 disabled:opacity-50 disabled:cursor-not-allowed rounded-xl border border-indigo-200 transition shadow-sm"
          >
            {isMarkingAll ? 'Marking All...' : 'Mark all as read'}
          </button>
        </div>
      </div>

      {/* Tabs */}
      <div className="flex items-center space-x-2 border-b border-slate-200 pb-1">
        <button
          onClick={() => handleFilterChange('all')}
          className={`px-4 py-2 text-xs font-bold rounded-lg transition ${
            filter === 'all'
              ? 'bg-indigo-600 text-white shadow-sm'
              : 'text-slate-600 hover:text-slate-900 hover:bg-slate-100'
          }`}
        >
          All Notifications
        </button>
        <button
          onClick={() => handleFilterChange('unread')}
          className={`px-4 py-2 text-xs font-bold rounded-lg transition flex items-center space-x-1.5 ${
            filter === 'unread'
              ? 'bg-indigo-600 text-white shadow-sm'
              : 'text-slate-600 hover:text-slate-900 hover:bg-slate-100'
          }`}
        >
          <span>Unread</span>
          {unreadCount > 0 && (
            <span
              className={`px-1.5 py-0.2 rounded-full text-[10px] font-mono ${
                filter === 'unread' ? 'bg-white text-indigo-600' : 'bg-indigo-100 text-indigo-700'
              }`}
            >
              {unreadCount}
            </span>
          )}
        </button>
      </div>

      {/* Content Area */}
      <div>
        {isLoading ? (
          <div className="space-y-4">
            {[1, 2, 3].map((i) => (
              <div
                key={i}
                className="animate-pulse bg-white p-5 rounded-2xl border border-slate-200 flex space-x-4 shadow-sm"
              >
                <div className="rounded-xl bg-slate-200 h-10 w-10"></div>
                <div className="flex-1 space-y-2 py-1">
                  <div className="h-4 bg-slate-200 rounded w-1/4"></div>
                  <div className="h-3 bg-slate-200 rounded w-3/4"></div>
                </div>
              </div>
            ))}
          </div>
        ) : error ? (
          <div className="bg-red-50 border border-red-200 rounded-2xl p-6 text-center shadow-sm">
            <p className="text-red-700 font-medium mb-3">{error}</p>
            <button
              onClick={fetchNotifications}
              className="px-4 py-2 bg-red-600 text-white rounded-xl text-xs font-semibold hover:bg-red-700 transition"
            >
              Retry
            </button>
          </div>
        ) : notifications.length === 0 ? (
          <div className="bg-white border border-slate-200 rounded-2xl p-12 text-center shadow-sm">
            <div className="mx-auto flex items-center justify-center h-12 w-12 rounded-full bg-slate-100 text-slate-400 mb-3">
              <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth="2"
                  d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9"
                />
              </svg>
            </div>
            <h3 className="text-base font-bold text-slate-900">No notifications found</h3>
            <p className="text-xs text-slate-500 mt-1">
              {filter === 'unread'
                ? "You're all caught up! No unread notifications."
                : "You don't have any notifications yet."}
            </p>
          </div>
        ) : (
          <div className="space-y-3">
            {notifications.map((notification) => (
              <div
                key={notification.id}
                className={`p-5 rounded-2xl border transition-all ${
                  notification.is_read
                    ? 'bg-white border-slate-200 shadow-sm'
                    : 'bg-indigo-50/40 border-indigo-200 shadow-md shadow-indigo-500/5 ring-1 ring-indigo-500/10'
                }`}
              >
                <div className="flex items-start justify-between gap-3">
                  <div className="flex items-start space-x-4 flex-1">
                    {getNotificationIcon(notification.notification_type)}

                    <div className="flex-1 min-w-0">
                      <div className="flex items-center space-x-2 flex-wrap mb-1.5">
                        <span className="text-[10px] font-bold uppercase tracking-wider px-2.5 py-0.5 rounded-full bg-slate-100 text-slate-700">
                          {notification.notification_type.replace(/_/g, ' ')}
                        </span>
                        {notification.push_sent && (
                          <span className="text-[10px] font-semibold text-emerald-700 bg-emerald-50 px-2 py-0.5 rounded-full border border-emerald-200">
                            Push Sent
                          </span>
                        )}
                        <span className="text-[11px] text-slate-400">
                          {formatTimestamp(notification.created_at)}
                        </span>
                      </div>
                      <h4 className="text-sm font-bold text-slate-900 leading-snug">
                        {notification.title}
                      </h4>
                      <p className="text-xs sm:text-sm text-slate-600 mt-1 whitespace-pre-wrap leading-relaxed">
                        {notification.body}
                      </p>

                      {/* Drive deep link if available */}
                      {notification.reference_type === 'DRIVE' && notification.reference_id && (
                        <div className="mt-3">
                          <button
                            onClick={() => handleNavigateReference(notification)}
                            className="inline-flex items-center text-xs font-bold text-indigo-600 hover:text-indigo-800 transition"
                          >
                            <span>View Placement Drive Details</span>
                            <svg className="w-3.5 h-3.5 ml-1" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 5l7 7-7 7" />
                            </svg>
                          </button>
                        </div>
                      )}
                    </div>
                  </div>

                  {/* Mark as read action */}
                  {!notification.is_read && (
                    <button
                      onClick={() => handleMarkAsRead(notification.id)}
                      className="ml-2 text-xs font-semibold text-indigo-600 hover:text-indigo-800 px-2.5 py-1 hover:bg-indigo-50 rounded-lg transition whitespace-nowrap"
                      title="Mark as read"
                    >
                      Mark read
                    </button>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}

        {/* Pagination */}
        {total > pageSize && (
          <div className="flex items-center justify-between mt-6 pt-4 border-t border-slate-200">
            <span className="text-xs text-slate-500">
              Showing page <span className="font-bold text-slate-700">{page}</span> of{' '}
              <span className="font-bold text-slate-700">{totalPages}</span> ({total} total)
            </span>
            <div className="flex space-x-2">
              <button
                onClick={() => setPage((p) => Math.max(1, p - 1))}
                disabled={page <= 1 || isLoading}
                className="px-3.5 py-1.5 text-xs font-semibold text-slate-700 bg-white border border-slate-300 rounded-xl hover:bg-slate-50 disabled:opacity-40 disabled:cursor-not-allowed shadow-sm transition"
              >
                Previous
              </button>
              <button
                onClick={() => setPage((p) => p + 1)}
                disabled={!hasNext || isLoading}
                className="px-3.5 py-1.5 text-xs font-semibold text-slate-700 bg-white border border-slate-300 rounded-xl hover:bg-slate-50 disabled:opacity-40 disabled:cursor-not-allowed shadow-sm transition"
              >
                Next
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

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

  const totalPages = Math.ceil(total / pageSize) || 1;

  return (
    <div className="max-w-4xl mx-auto px-4 py-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between pb-6 border-b border-gray-200">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Notification Center</h1>
          <p className="text-sm text-gray-500 mt-1">
            Stay updated with placement drives, schedule changes, and application statuses.
          </p>
        </div>
        <div className="mt-4 sm:mt-0 flex items-center space-x-3">
          <button
            onClick={handleMarkAllAsRead}
            disabled={isMarkingAll || notifications.filter((n) => !n.is_read).length === 0}
            className="px-3.5 py-1.5 text-xs font-medium text-blue-700 bg-blue-50 hover:bg-blue-100 disabled:opacity-50 disabled:cursor-not-allowed rounded-lg border border-blue-200 transition-colors"
          >
            {isMarkingAll ? 'Marking All...' : 'Mark all as read'}
          </button>
        </div>
      </div>

      {/* Tabs */}
      <div className="flex items-center space-x-4 mt-6 border-b border-gray-200">
        <button
          onClick={() => handleFilterChange('all')}
          className={`pb-3 text-sm font-semibold border-b-2 transition-colors ${
            filter === 'all'
              ? 'border-blue-600 text-blue-600'
              : 'border-transparent text-gray-500 hover:text-gray-700'
          }`}
        >
          All Notifications
        </button>
        <button
          onClick={() => handleFilterChange('unread')}
          className={`pb-3 text-sm font-semibold border-b-2 transition-colors ${
            filter === 'unread'
              ? 'border-blue-600 text-blue-600'
              : 'border-transparent text-gray-500 hover:text-gray-700'
          }`}
        >
          Unread
        </button>
      </div>

      {/* Content Area */}
      <div className="mt-6">
        {isLoading ? (
          <div className="space-y-4">
            {[1, 2, 3].map((i) => (
              <div
                key={i}
                className="animate-pulse bg-white p-5 rounded-xl border border-gray-200 flex space-x-4"
              >
                <div className="rounded-full bg-gray-200 h-10 w-10"></div>
                <div className="flex-1 space-y-2 py-1">
                  <div className="h-4 bg-gray-200 rounded w-1/4"></div>
                  <div className="h-3 bg-gray-200 rounded w-3/4"></div>
                </div>
              </div>
            ))}
          </div>
        ) : error ? (
          <div className="bg-red-50 border border-red-200 rounded-xl p-6 text-center">
            <p className="text-red-700 font-medium mb-3">{error}</p>
            <button
              onClick={fetchNotifications}
              className="px-4 py-2 bg-red-600 text-white rounded-lg text-sm font-medium hover:bg-red-700"
            >
              Retry
            </button>
          </div>
        ) : notifications.length === 0 ? (
          <div className="bg-white border border-gray-200 rounded-xl p-12 text-center">
            <div className="mx-auto flex items-center justify-center h-12 w-12 rounded-full bg-gray-100 text-gray-400 mb-3">
              <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth="2"
                  d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9"
                />
              </svg>
            </div>
            <h3 className="text-base font-semibold text-gray-900">No notifications found</h3>
            <p className="text-sm text-gray-500 mt-1">
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
                className={`p-5 rounded-xl border transition-all ${
                  notification.is_read
                    ? 'bg-white border-gray-200'
                    : 'bg-blue-50/40 border-blue-200 shadow-sm'
                }`}
              >
                <div className="flex items-start justify-between">
                  <div className="flex items-start space-x-3 flex-1">
                    {!notification.is_read && (
                      <span
                        className="mt-1.5 h-2.5 w-2.5 rounded-full bg-blue-600 flex-shrink-0"
                        title="Unread"
                      />
                    )}
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center space-x-2 flex-wrap mb-1">
                        <span className="text-xs font-semibold px-2.5 py-0.5 rounded-full bg-gray-100 text-gray-700">
                          {notification.notification_type.replace(/_/g, ' ')}
                        </span>
                        {notification.push_sent && (
                          <span className="text-xs text-green-700 bg-green-50 px-2 py-0.5 rounded border border-green-200">
                            Push Sent
                          </span>
                        )}
                        <span className="text-xs text-gray-400">
                          {formatTimestamp(notification.created_at)}
                        </span>
                      </div>
                      <h4 className="text-sm font-bold text-gray-900 leading-snug">
                        {notification.title}
                      </h4>
                      <p className="text-sm text-gray-600 mt-1 whitespace-pre-wrap">
                        {notification.body}
                      </p>

                      {/* Drive deep link if available */}
                      {notification.reference_type === 'DRIVE' && notification.reference_id && (
                        <div className="mt-3">
                          <button
                            onClick={() => handleNavigateReference(notification)}
                            className="inline-flex items-center text-xs font-semibold text-blue-600 hover:text-blue-800"
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

                  {/* Actions */}
                  {!notification.is_read && (
                    <button
                      onClick={() => handleMarkAsRead(notification.id)}
                      className="ml-4 text-xs font-medium text-gray-500 hover:text-blue-600 p-1 hover:bg-gray-100 rounded"
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
          <div className="flex items-center justify-between mt-6 pt-4 border-t border-gray-200">
            <span className="text-xs text-gray-500">
              Showing page <span className="font-semibold">{page}</span> of{' '}
              <span className="font-semibold">{totalPages}</span> ({total} total)
            </span>
            <div className="flex space-x-2">
              <button
                onClick={() => setPage((p) => Math.max(1, p - 1))}
                disabled={page <= 1 || isLoading}
                className="px-3 py-1.5 text-xs font-medium text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 disabled:opacity-40 disabled:cursor-not-allowed"
              >
                Previous
              </button>
              <button
                onClick={() => setPage((p) => p + 1)}
                disabled={!hasNext || isLoading}
                className="px-3 py-1.5 text-xs font-medium text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 disabled:opacity-40 disabled:cursor-not-allowed"
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

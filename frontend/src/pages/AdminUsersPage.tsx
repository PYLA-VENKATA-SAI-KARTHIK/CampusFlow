import React, { useEffect, useState, useCallback } from 'react';
import { adminService } from '../services/adminService';
import { useAuthStore } from '../store/authStore';
import type { AdminUser, PaginatedResult } from '../types/admin';
import { CreateUserModal } from '../components/admin/CreateUserModal';
import { EditUserModal } from '../components/admin/EditUserModal';
import { BulkImportModal } from '../components/admin/BulkImportModal';

export const AdminUsersPage: React.FC = () => {
  const { user: currentAdmin } = useAuthStore();

  const [data, setData] = useState<PaginatedResult<AdminUser> | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [actionSuccess, setActionSuccess] = useState<string | null>(null);

  // Filters
  const [searchTerm, setSearchTerm] = useState('');
  const [debouncedSearch, setDebouncedSearch] = useState('');
  const [roleFilter, setRoleFilter] = useState<string>('');
  const [statusFilter, setStatusFilter] = useState<string>('');
  const [page, setPage] = useState(1);
  const pageSize = 15;

  // Modals
  const [isCreateOpen, setIsCreateOpen] = useState(false);
  const [isBulkOpen, setIsBulkOpen] = useState(false);
  const [editingUser, setEditingUser] = useState<AdminUser | null>(null);
  const [actionLoadingId, setActionLoadingId] = useState<string | null>(null);

  // Debounce search input
  useEffect(() => {
    if (searchTerm === debouncedSearch) return;
    const handler = setTimeout(() => {
      setDebouncedSearch(searchTerm);
      setPage(1);
    }, 300);
    return () => clearTimeout(handler);
  }, [searchTerm, debouncedSearch]);

  const fetchUsers = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const params: any = {
        page,
        page_size: pageSize,
      };
      if (debouncedSearch.trim()) params.search = debouncedSearch.trim();
      if (roleFilter) params.role = roleFilter;
      if (statusFilter !== '') params.is_active = statusFilter === 'active';

      const res = await adminService.listUsers(params);
      setData(res);
    } catch (err: any) {
      setError(err?.response?.data?.detail || 'Failed to fetch user accounts.');
    } finally {
      setLoading(false);
    }
  }, [page, debouncedSearch, roleFilter, statusFilter]);

  useEffect(() => {
    fetchUsers();
  }, [fetchUsers]);

  const handleToggleActive = async (targetUser: AdminUser) => {
    if (currentAdmin?.id === targetUser.id && targetUser.is_active) {
      setError('Security constraint: You cannot deactivate your own account.');
      return;
    }

    const confirmMsg = targetUser.is_active
      ? `Are you sure you want to deactivate ${targetUser.full_name}? All active sessions will be terminated.`
      : `Reactivate account for ${targetUser.full_name}?`;

    if (!window.confirm(confirmMsg)) return;

    try {
      setActionLoadingId(targetUser.id);
      setError(null);
      await adminService.updateUser(targetUser.id, {
        is_active: !targetUser.is_active,
      });
      setActionSuccess(
        `User ${targetUser.full_name} was successfully ${targetUser.is_active ? 'deactivated' : 'activated'}.`
      );
      setTimeout(() => setActionSuccess(null), 4000);
      fetchUsers();
    } catch (err: any) {
      setError(err?.response?.data?.detail || 'Failed to update user status.');
    } finally {
      setActionLoadingId(null);
    }
  };

  const getRoleBadge = (role: string) => {
    switch (role) {
      case 'ADMIN':
        return (
          <span className="px-2.5 py-0.5 rounded-full text-xs font-bold bg-purple-100 text-purple-800 border border-purple-200">
            ADMIN
          </span>
        );
      case 'OFFICER':
        return (
          <span className="px-2.5 py-0.5 rounded-full text-xs font-bold bg-blue-100 text-blue-800 border border-blue-200">
            OFFICER
          </span>
        );
      case 'STUDENT':
      default:
        return (
          <span className="px-2.5 py-0.5 rounded-full text-xs font-bold bg-emerald-100 text-emerald-800 border border-emerald-200">
            STUDENT
          </span>
        );
    }
  };

  return (
    <div className="space-y-6 animate-fade-in">
      {/* Top Header */}
      <div className="flex flex-col sm:flex-row justify-between sm:items-center gap-4 border-b border-slate-200 pb-5">
        <div>
          <div className="flex items-center space-x-2">
            <div className="w-8 h-8 rounded-lg bg-indigo-100 text-indigo-600 flex items-center justify-center font-bold">
              <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 4.354a4 4 0 110 5.292M15 21H3v-1a6 6 0 0112 0v1zm0 0h6v-1a6 6 0 00-9-5.197M13 7a4 4 0 11-8 0 4 4 0 018 0z" />
              </svg>
            </div>
            <h1 className="text-2xl font-bold text-slate-900 tracking-tight">User Management</h1>
          </div>
          <p className="text-sm text-slate-500 mt-1">
            Manage institutional users, staff privileges, and batch student onboarding.
          </p>
        </div>
        <div className="flex items-center space-x-3">
          <button
            onClick={() => setIsBulkOpen(true)}
            className="px-4 py-2 text-xs font-bold text-slate-700 bg-white border border-slate-300 hover:bg-slate-50 rounded-xl transition flex items-center space-x-2 shadow-sm"
          >
            <svg className="w-4 h-4 text-emerald-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
            </svg>
            <span>Bulk Import Students</span>
          </button>
          <button
            onClick={() => setIsCreateOpen(true)}
            className="px-4 py-2 text-xs font-bold text-white bg-indigo-600 hover:bg-indigo-700 rounded-xl transition flex items-center space-x-2 shadow-md shadow-indigo-600/20"
          >
            <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 4v16m8-8H4" />
            </svg>
            <span>Add Staff User</span>
          </button>
        </div>
      </div>

      {/* Notification banners */}
      {actionSuccess && (
        <div className="p-4 bg-emerald-50 border border-emerald-200 text-emerald-800 text-xs rounded-xl flex items-center justify-between animate-fade-in shadow-sm">
          <div className="flex items-center space-x-2">
            <svg className="w-4 h-4 text-emerald-600 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M5 13l4 4L19 7" />
            </svg>
            <span className="font-semibold">{actionSuccess}</span>
          </div>
          <button onClick={() => setActionSuccess(null)} className="text-emerald-600 hover:text-emerald-800">✕</button>
        </div>
      )}

      {error && (
        <div className="p-4 bg-red-50 border border-red-200 text-red-700 text-xs rounded-xl flex items-center justify-between animate-fade-in shadow-sm">
          <div className="flex items-center space-x-2">
            <svg className="w-4 h-4 text-red-500 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            <span>{error}</span>
          </div>
          <button onClick={() => setError(null)} className="text-red-600 hover:text-red-800">✕</button>
        </div>
      )}

      {/* Filter and Search Bar */}
      <div className="bg-white p-4 rounded-2xl border border-slate-200 shadow-sm flex flex-col md:flex-row gap-3 items-center justify-between">
        <div className="relative w-full md:w-80">
          <svg
            className="w-4 h-4 text-slate-400 absolute left-3.5 top-1/2 -translate-y-1/2"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
          >
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
          </svg>
          <input
            type="text"
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            placeholder="Search by name or email..."
            className="w-full pl-10 pr-3.5 py-2 text-xs border border-slate-300 rounded-xl focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-600 outline-none transition"
          />
        </div>

        <div className="flex flex-wrap items-center gap-3 w-full md:w-auto justify-end">
          <select
            value={roleFilter}
            onChange={(e) => {
              setRoleFilter(e.target.value);
              setPage(1);
            }}
            className="px-3.5 py-2 text-xs border border-slate-300 rounded-xl bg-white focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-600 outline-none font-medium"
          >
            <option value="">All Roles</option>
            <option value="STUDENT">Student</option>
            <option value="OFFICER">Officer</option>
            <option value="ADMIN">Admin</option>
          </select>

          <select
            value={statusFilter}
            onChange={(e) => {
              setStatusFilter(e.target.value);
              setPage(1);
            }}
            className="px-3.5 py-2 text-xs border border-slate-300 rounded-xl bg-white focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-600 outline-none font-medium"
          >
            <option value="">All Statuses</option>
            <option value="active">Active</option>
            <option value="inactive">Inactive</option>
          </select>
        </div>
      </div>

      {/* Users Table */}
      <div className="bg-white border border-slate-200 rounded-2xl shadow-sm overflow-hidden">
        {loading && !data ? (
          <div className="flex flex-col items-center justify-center p-12 space-y-3">
            <div className="w-8 h-8 border-4 border-indigo-600 border-t-transparent rounded-full animate-spin" />
            <p className="text-xs text-slate-500 font-medium">Loading user directory...</p>
          </div>
        ) : !data || data.items.length === 0 ? (
          <div className="p-12 text-center text-slate-500 space-y-2">
            <svg className="w-12 h-12 text-slate-300 mx-auto" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="1.5" d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z" />
            </svg>
            <p className="text-sm font-bold text-slate-700">No users found</p>
            <p className="text-xs text-slate-400">Try adjusting your search query or filters.</p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-slate-200 text-xs">
              <thead className="bg-slate-50">
                <tr>
                  <th className="px-6 py-3.5 text-left font-bold text-slate-600 uppercase tracking-wider text-[11px]">User</th>
                  <th className="px-6 py-3.5 text-left font-bold text-slate-600 uppercase tracking-wider text-[11px]">Role</th>
                  <th className="px-6 py-3.5 text-left font-bold text-slate-600 uppercase tracking-wider text-[11px]">Status</th>
                  <th className="px-6 py-3.5 text-left font-bold text-slate-600 uppercase tracking-wider text-[11px]">Password</th>
                  <th className="px-6 py-3.5 text-left font-bold text-slate-600 uppercase tracking-wider text-[11px]">Created</th>
                  <th className="px-6 py-3.5 text-right font-bold text-slate-600 uppercase tracking-wider text-[11px]">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 bg-white">
                {data.items.map((u) => {
                  const isSelf = currentAdmin?.id === u.id;
                  const isActionLoading = actionLoadingId === u.id;

                  return (
                    <tr key={u.id} className="hover:bg-slate-50/80 transition">
                      <td className="px-6 py-4">
                        <div className="flex items-center space-x-3">
                          <div className="w-8 h-8 rounded-full bg-indigo-100 text-indigo-700 flex items-center justify-center font-bold text-xs">
                            {u.full_name.charAt(0).toUpperCase()}
                          </div>
                          <div>
                            <div className="font-bold text-slate-900 flex items-center space-x-1.5">
                              <span>{u.full_name}</span>
                              {isSelf && (
                                <span className="text-[10px] bg-slate-200 text-slate-700 px-1.5 py-0.2 rounded-full font-bold">
                                  You
                                </span>
                              )}
                            </div>
                            <div className="text-[11px] text-slate-500 font-mono">{u.email}</div>
                          </div>
                        </div>
                      </td>
                      <td className="px-6 py-4">{getRoleBadge(u.role)}</td>
                      <td className="px-6 py-4">
                        {u.is_active ? (
                          <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-[11px] font-bold bg-emerald-50 text-emerald-700 border border-emerald-200">
                            <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 mr-1.5" />
                            Active
                          </span>
                        ) : (
                          <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-[11px] font-bold bg-slate-100 text-slate-600 border border-slate-200">
                            <span className="w-1.5 h-1.5 rounded-full bg-slate-400 mr-1.5" />
                            Inactive
                          </span>
                        )}
                      </td>
                      <td className="px-6 py-4">
                        {u.must_change_password ? (
                          <span className="text-amber-600 text-[11px] font-bold flex items-center space-x-1">
                            <span>Pending Change</span>
                          </span>
                        ) : (
                          <span className="text-slate-400 text-[11px]">Set</span>
                        )}
                      </td>
                      <td className="px-6 py-4 text-slate-500 text-[11px]">
                        {new Date(u.created_at).toLocaleDateString()}
                      </td>
                      <td className="px-6 py-4 text-right">
                        <div className="flex items-center justify-end space-x-2">
                          <button
                            onClick={() => setEditingUser(u)}
                            className="text-indigo-600 hover:text-indigo-800 font-bold px-2.5 py-1 rounded-lg hover:bg-indigo-50 transition"
                          >
                            Edit
                          </button>
                          <button
                            disabled={isSelf || isActionLoading}
                            onClick={() => handleToggleActive(u)}
                            title={isSelf ? 'You cannot deactivate your own account' : undefined}
                            className={`px-2.5 py-1 rounded-lg font-bold transition ${
                              isSelf
                                ? 'text-slate-300 cursor-not-allowed'
                                : u.is_active
                                ? 'text-rose-600 hover:text-rose-800 hover:bg-rose-50'
                                : 'text-emerald-600 hover:text-emerald-800 hover:bg-emerald-50'
                            }`}
                          >
                            {isActionLoading
                              ? 'Updating...'
                              : u.is_active
                              ? 'Deactivate'
                              : 'Activate'}
                          </button>
                        </div>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}

        {/* Pagination Bar */}
        {data && data.total_pages > 1 && (
          <div className="px-6 py-3.5 border-t border-slate-200 bg-slate-50 flex items-center justify-between text-xs text-slate-600">
            <div>
              Showing <span className="font-bold">{data.items.length}</span> of{' '}
              <span className="font-bold">{data.total}</span> users (Page {data.page} of {data.total_pages})
            </div>
            <div className="flex items-center space-x-2">
              <button
                disabled={page <= 1}
                onClick={() => setPage((p) => Math.max(1, p - 1))}
                className="px-3 py-1.5 border border-slate-300 rounded-xl bg-white hover:bg-slate-50 disabled:opacity-50 transition font-semibold"
              >
                Previous
              </button>
              <button
                disabled={page >= data.total_pages}
                onClick={() => setPage((p) => Math.min(data.total_pages, p + 1))}
                className="px-3 py-1.5 border border-slate-300 rounded-xl bg-white hover:bg-slate-50 disabled:opacity-50 transition font-semibold"
              >
                Next
              </button>
            </div>
          </div>
        )}
      </div>

      {/* Modals */}
      <CreateUserModal
        isOpen={isCreateOpen}
        onClose={() => setIsCreateOpen(false)}
        onUserCreated={() => {
          fetchUsers();
          setActionSuccess('New user account created successfully.');
          setTimeout(() => setActionSuccess(null), 4000);
        }}
      />

      <EditUserModal
        user={editingUser}
        isOpen={!!editingUser}
        onClose={() => setEditingUser(null)}
        onUserUpdated={() => {
          fetchUsers();
          setActionSuccess('User profile updated successfully.');
          setTimeout(() => setActionSuccess(null), 4000);
        }}
      />

      <BulkImportModal
        isOpen={isBulkOpen}
        onClose={() => setIsBulkOpen(false)}
        onImportComplete={() => {
          fetchUsers();
          setActionSuccess('Bulk student import completed.');
          setTimeout(() => setActionSuccess(null), 4000);
        }}
      />
    </div>
  );
};

import React, { useEffect, useState, useCallback } from 'react';
import { adminService } from '../services/adminService';
import type { AdminAuditLog, PaginatedResult } from '../types/admin';

export const AdminAuditLogsPage: React.FC = () => {
  const [data, setData] = useState<PaginatedResult<AdminAuditLog> | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Filters
  const [actionFilter, setActionFilter] = useState('');
  const [entityTypeFilter, setEntityTypeFilter] = useState('');
  const [startDate, setStartDate] = useState('');
  const [endDate, setEndDate] = useState('');
  const [page, setPage] = useState(1);
  const pageSize = 20;

  // State inspection modal
  const [inspectingLog, setInspectingLog] = useState<AdminAuditLog | null>(null);

  const fetchAuditLogs = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const params: any = {
        page,
        page_size: pageSize,
      };
      if (actionFilter) params.action = actionFilter;
      if (entityTypeFilter) params.entity_type = entityTypeFilter;
      if (startDate) params.start_date = new Date(startDate).toISOString();
      if (endDate) {
        // Add end of day
        const endD = new Date(endDate);
        endD.setHours(23, 59, 59, 999);
        params.end_date = endD.toISOString();
      }

      const res = await adminService.listAuditLogs(params);
      setData(res);
    } catch (err: any) {
      setError(err?.response?.data?.detail || 'Failed to fetch institutional audit logs.');
    } finally {
      setLoading(false);
    }
  }, [page, actionFilter, entityTypeFilter, startDate, endDate]);

  useEffect(() => {
    fetchAuditLogs();
  }, [fetchAuditLogs]);

  const handleResetFilters = () => {
    setActionFilter('');
    setEntityTypeFilter('');
    setStartDate('');
    setEndDate('');
    setPage(1);
  };

  const getActionBadge = (action: string) => {
    if (action.includes('CREATED') || action.includes('IMPORT')) {
      return (
        <span className="px-2 py-0.5 rounded-md text-[11px] font-bold bg-emerald-100 text-emerald-800 border border-emerald-200">
          {action}
        </span>
      );
    }
    if (action.includes('UPDATED') || action.includes('SENT')) {
      return (
        <span className="px-2 py-0.5 rounded-md text-[11px] font-bold bg-blue-100 text-blue-800 border border-blue-200">
          {action}
        </span>
      );
    }
    if (action.includes('DELETED') || action.includes('REVOKED') || action.includes('CANCEL')) {
      return (
        <span className="px-2 py-0.5 rounded-md text-[11px] font-bold bg-rose-100 text-rose-800 border border-rose-200">
          {action}
        </span>
      );
    }
    return (
      <span className="px-2 py-0.5 rounded-md text-[11px] font-bold bg-gray-100 text-gray-800 border border-gray-200">
        {action}
      </span>
    );
  };

  return (
    <div className="space-y-6">
      {/* Top Header */}
      <div className="flex flex-col sm:flex-row justify-between sm:items-center gap-4 border-b border-gray-200 pb-5">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 tracking-tight">System Audit Logs</h1>
          <p className="text-sm text-gray-500 mt-1">
            Immutable, append-only institutional activity and security compliance trails.
          </p>
        </div>
        <div className="flex items-center space-x-2">
          <button
            onClick={fetchAuditLogs}
            className="px-3 py-1.5 text-xs font-semibold text-gray-700 bg-white border border-gray-300 hover:bg-gray-50 rounded-xl transition flex items-center space-x-1 shadow-sm"
          >
            <svg className="w-3.5 h-3.5 text-gray-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
            </svg>
            <span>Refresh</span>
          </button>
        </div>
      </div>

      {error && (
        <div className="p-3.5 bg-red-50 border border-red-200 text-red-700 text-xs rounded-xl flex items-center justify-between">
          <span>{error}</span>
          <button onClick={() => setError(null)} className="text-red-600 hover:text-red-800">✕</button>
        </div>
      )}

      {/* Filter Bar */}
      <div className="bg-white p-4 rounded-xl border border-gray-200 shadow-sm flex flex-wrap gap-3 items-center justify-between">
        <div className="flex flex-wrap items-center gap-3">
          <div>
            <label className="block text-[10px] uppercase font-bold text-gray-400 mb-1">Entity Type</label>
            <select
              value={entityTypeFilter}
              onChange={(e) => {
                setEntityTypeFilter(e.target.value);
                setPage(1);
              }}
              className="px-3 py-1.5 text-xs border border-gray-300 rounded-lg bg-white focus:ring-2 focus:ring-blue-500 outline-none"
            >
              <option value="">All Entities</option>
              <option value="USER">USER</option>
              <option value="STUDENT_PROFILE">STUDENT_PROFILE</option>
              <option value="DRIVE">DRIVE</option>
              <option value="STAGE">STAGE</option>
              <option value="REGISTRATION">REGISTRATION</option>
              <option value="NOTIFICATION">NOTIFICATION</option>
            </select>
          </div>

          <div>
            <label className="block text-[10px] uppercase font-bold text-gray-400 mb-1">Action</label>
            <input
              type="text"
              placeholder="e.g. USER_CREATED"
              value={actionFilter}
              onChange={(e) => {
                setActionFilter(e.target.value);
                setPage(1);
              }}
              className="px-3 py-1.5 text-xs border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 outline-none w-36"
            />
          </div>

          <div>
            <label className="block text-[10px] uppercase font-bold text-gray-400 mb-1">From Date</label>
            <input
              type="date"
              value={startDate}
              onChange={(e) => {
                setStartDate(e.target.value);
                setPage(1);
              }}
              className="px-3 py-1.5 text-xs border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 outline-none"
            />
          </div>

          <div>
            <label className="block text-[10px] uppercase font-bold text-gray-400 mb-1">To Date</label>
            <input
              type="date"
              value={endDate}
              onChange={(e) => {
                setEndDate(e.target.value);
                setPage(1);
              }}
              className="px-3 py-1.5 text-xs border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 outline-none"
            />
          </div>
        </div>

        <div className="pt-3 sm:pt-0">
          <button
            onClick={handleResetFilters}
            className="text-xs text-gray-600 hover:text-gray-900 font-medium underline"
          >
            Clear Filters
          </button>
        </div>
      </div>

      {/* Audit Log Table */}
      <div className="bg-white border border-gray-200 rounded-2xl shadow-sm overflow-hidden">
        {loading && !data ? (
          <div className="flex flex-col items-center justify-center p-12 space-y-3">
            <div className="w-8 h-8 border-4 border-blue-600 border-t-transparent rounded-full animate-spin" />
            <p className="text-xs text-gray-500 font-medium">Fetching audit logs...</p>
          </div>
        ) : !data || data.items.length === 0 ? (
          <div className="p-12 text-center text-gray-500 space-y-2">
            <svg className="w-12 h-12 text-gray-300 mx-auto" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="1.5" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
            </svg>
            <p className="text-sm font-semibold text-gray-700">No audit log entries found</p>
            <p className="text-xs text-gray-400">Try loosening your filter parameters.</p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200 text-xs">
              <thead className="bg-gray-50/75">
                <tr>
                  <th className="px-4 py-3 text-left font-semibold text-gray-600">Timestamp</th>
                  <th className="px-4 py-3 text-left font-semibold text-gray-600">Action</th>
                  <th className="px-4 py-3 text-left font-semibold text-gray-600">Target Entity</th>
                  <th className="px-4 py-3 text-left font-semibold text-gray-600">Actor (User ID)</th>
                  <th className="px-4 py-3 text-left font-semibold text-gray-600">IP Address</th>
                  <th className="px-4 py-3 text-right font-semibold text-gray-600">Payload State</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100 bg-white font-mono text-[11px]">
                {data.items.map((log) => (
                  <tr key={log.id} className="hover:bg-gray-50/80 transition">
                    <td className="px-4 py-3 text-gray-600 whitespace-nowrap">
                      {new Date(log.created_at).toLocaleString()}
                    </td>
                    <td className="px-4 py-3 whitespace-nowrap font-sans">
                      {getActionBadge(log.action)}
                    </td>
                    <td className="px-4 py-3 text-gray-800 whitespace-nowrap">
                      <span className="font-semibold text-gray-900">{log.entity_type}</span>
                      {log.entity_id && (
                        <span className="text-gray-400 ml-1.5 font-mono text-[10px]" title={log.entity_id}>
                          ({log.entity_id.substring(0, 8)}...)
                        </span>
                      )}
                    </td>
                    <td className="px-4 py-3 text-gray-600 whitespace-nowrap">
                      {log.performed_by_user_id ? (
                        <span title={log.performed_by_user_id}>
                          {log.performed_by_user_id.substring(0, 8)}...
                        </span>
                      ) : (
                        <span className="text-gray-400 font-sans italic">system</span>
                      )}
                    </td>
                    <td className="px-4 py-3 text-gray-500 whitespace-nowrap">
                      {log.ip_address || '—'}
                    </td>
                    <td className="px-4 py-3 text-right whitespace-nowrap font-sans">
                      <button
                        onClick={() => setInspectingLog(log)}
                        className="px-2.5 py-1 text-xs font-semibold text-blue-600 bg-blue-50 hover:bg-blue-100 rounded-lg transition"
                      >
                        Inspect Diff
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}

        {/* Pagination Bar */}
        {data && data.total_pages > 1 && (
          <div className="px-4 py-3 border-t border-gray-200 bg-gray-50 flex items-center justify-between text-xs text-gray-600">
            <div>
              Showing <span className="font-semibold">{data.items.length}</span> of{' '}
              <span className="font-semibold">{data.total}</span> entries (Page {data.page} of {data.total_pages})
            </div>
            <div className="flex items-center space-x-2">
              <button
                disabled={page <= 1}
                onClick={() => setPage((p) => Math.max(1, p - 1))}
                className="px-2.5 py-1.5 border border-gray-300 rounded-lg bg-white hover:bg-gray-50 disabled:opacity-50 transition"
              >
                Previous
              </button>
              <button
                disabled={page >= data.total_pages}
                onClick={() => setPage((p) => Math.min(data.total_pages, p + 1))}
                className="px-2.5 py-1.5 border border-gray-300 rounded-lg bg-white hover:bg-gray-50 disabled:opacity-50 transition"
              >
                Next
              </button>
            </div>
          </div>
        )}
      </div>

      {/* State Inspection Modal */}
      {inspectingLog && (
        <div className="fixed inset-0 z-50 overflow-y-auto bg-black/50 flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl max-w-2xl w-full shadow-2xl overflow-hidden animate-in fade-in zoom-in-95 duration-200 flex flex-col max-h-[85vh]">
            <div className="px-6 py-4 border-b border-gray-100 flex justify-between items-center bg-gray-50/50">
              <div>
                <h3 className="text-base font-bold text-gray-900 flex items-center space-x-2">
                  <span>Audit Entry Payload:</span>
                  <span className="font-mono text-sm text-blue-600">{inspectingLog.action}</span>
                </h3>
                <p className="text-xs text-gray-500 font-mono mt-0.5">
                  ID: {inspectingLog.id} • {new Date(inspectingLog.created_at).toLocaleString()}
                </p>
              </div>
              <button
                onClick={() => setInspectingLog(null)}
                className="text-gray-400 hover:text-gray-600 rounded-lg p-1 transition"
              >
                <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>

            <div className="p-6 overflow-y-auto space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {/* Old State */}
                <div>
                  <h4 className="text-xs font-bold text-gray-700 uppercase tracking-wide mb-2 flex items-center space-x-1.5">
                    <span className="w-2 h-2 rounded-full bg-rose-400" />
                    <span>Old State</span>
                  </h4>
                  <pre className="bg-gray-900 text-gray-100 p-3.5 rounded-xl text-[11px] font-mono overflow-x-auto max-h-72 border border-gray-800">
                    {inspectingLog.old_state
                      ? JSON.stringify(inspectingLog.old_state, null, 2)
                      : 'null'}
                  </pre>
                </div>

                {/* New State */}
                <div>
                  <h4 className="text-xs font-bold text-gray-700 uppercase tracking-wide mb-2 flex items-center space-x-1.5">
                    <span className="w-2 h-2 rounded-full bg-emerald-400" />
                    <span>New State</span>
                  </h4>
                  <pre className="bg-gray-900 text-gray-100 p-3.5 rounded-xl text-[11px] font-mono overflow-x-auto max-h-72 border border-gray-800">
                    {inspectingLog.new_state
                      ? JSON.stringify(inspectingLog.new_state, null, 2)
                      : 'null'}
                  </pre>
                </div>
              </div>

              <div className="bg-gray-50 p-3 rounded-xl border border-gray-200 text-xs space-y-1 text-gray-600">
                <div><span className="font-semibold">Entity Type:</span> {inspectingLog.entity_type}</div>
                <div><span className="font-semibold">Entity ID:</span> {inspectingLog.entity_id || 'None'}</div>
                <div><span className="font-semibold">Actor:</span> {inspectingLog.performed_by_user_id || 'System'}</div>
                <div><span className="font-semibold">Client IP:</span> {inspectingLog.ip_address || 'None recorded'}</div>
              </div>
            </div>

            <div className="px-6 py-3 bg-gray-50 border-t border-gray-100 flex justify-end">
              <button
                onClick={() => setInspectingLog(null)}
                className="px-4 py-1.5 text-xs font-semibold text-gray-700 bg-white border border-gray-300 hover:bg-gray-100 rounded-lg transition"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

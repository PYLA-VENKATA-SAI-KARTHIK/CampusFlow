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
        <span className="px-2.5 py-0.5 rounded-full text-[11px] font-bold bg-emerald-100 text-emerald-800 border border-emerald-200">
          {action}
        </span>
      );
    }
    if (action.includes('UPDATED') || action.includes('SENT')) {
      return (
        <span className="px-2.5 py-0.5 rounded-full text-[11px] font-bold bg-blue-100 text-blue-800 border border-blue-200">
          {action}
        </span>
      );
    }
    if (action.includes('DELETED') || action.includes('REVOKED') || action.includes('CANCEL')) {
      return (
        <span className="px-2.5 py-0.5 rounded-full text-[11px] font-bold bg-rose-100 text-rose-800 border border-rose-200">
          {action}
        </span>
      );
    }
    return (
      <span className="px-2.5 py-0.5 rounded-full text-[11px] font-bold bg-slate-100 text-slate-800 border border-slate-200">
        {action}
      </span>
    );
  };

  return (
    <div className="space-y-6 animate-fade-in">
      {/* Top Header */}
      <div className="flex flex-col sm:flex-row justify-between sm:items-center gap-4 border-b border-slate-200 pb-5">
        <div>
          <div className="flex items-center space-x-2">
            <div className="w-8 h-8 rounded-lg bg-indigo-100 text-indigo-600 flex items-center justify-center font-bold">
              <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
              </svg>
            </div>
            <h1 className="text-2xl font-bold text-slate-900 tracking-tight">System Audit Logs</h1>
          </div>
          <p className="text-sm text-slate-500 mt-1">
            Immutable, append-only institutional activity and security compliance trails.
          </p>
        </div>
        <div className="flex items-center space-x-2">
          <button
            onClick={fetchAuditLogs}
            className="px-3.5 py-2 text-xs font-bold text-slate-700 bg-white border border-slate-300 hover:bg-slate-50 rounded-xl transition flex items-center space-x-1.5 shadow-sm"
          >
            <svg className="w-4 h-4 text-slate-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
            </svg>
            <span>Refresh Logs</span>
          </button>
        </div>
      </div>

      {error && (
        <div className="p-4 bg-red-50 border border-red-200 text-red-700 text-xs rounded-xl flex items-center justify-between animate-fade-in shadow-sm">
          <span>{error}</span>
          <button onClick={() => setError(null)} className="text-red-600 hover:text-red-800">✕</button>
        </div>
      )}

      {/* Filter Bar */}
      <div className="bg-white p-4 rounded-2xl border border-slate-200 shadow-sm flex flex-wrap gap-4 items-center justify-between">
        <div className="flex flex-wrap items-center gap-3">
          <div>
            <label className="block text-[10px] uppercase font-bold text-slate-400 mb-1">Entity Type</label>
            <select
              value={entityTypeFilter}
              onChange={(e) => {
                setEntityTypeFilter(e.target.value);
                setPage(1);
              }}
              className="px-3 py-1.5 text-xs border border-slate-300 rounded-xl bg-white focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-600 outline-none font-medium"
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
            <label className="block text-[10px] uppercase font-bold text-slate-400 mb-1">Action</label>
            <input
              type="text"
              placeholder="e.g. USER_CREATED"
              value={actionFilter}
              onChange={(e) => {
                setActionFilter(e.target.value);
                setPage(1);
              }}
              className="px-3 py-1.5 text-xs border border-slate-300 rounded-xl focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-600 outline-none w-36 font-mono"
            />
          </div>

          <div>
            <label className="block text-[10px] uppercase font-bold text-slate-400 mb-1">From Date</label>
            <input
              type="date"
              value={startDate}
              onChange={(e) => {
                setStartDate(e.target.value);
                setPage(1);
              }}
              className="px-3 py-1.5 text-xs border border-slate-300 rounded-xl focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-600 outline-none"
            />
          </div>

          <div>
            <label className="block text-[10px] uppercase font-bold text-slate-400 mb-1">To Date</label>
            <input
              type="date"
              value={endDate}
              onChange={(e) => {
                setEndDate(e.target.value);
                setPage(1);
              }}
              className="px-3 py-1.5 text-xs border border-slate-300 rounded-xl focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-600 outline-none"
            />
          </div>
        </div>

        <div className="pt-3 sm:pt-0">
          <button
            onClick={handleResetFilters}
            className="text-xs text-indigo-600 hover:text-indigo-800 font-bold underline"
          >
            Clear Filters
          </button>
        </div>
      </div>

      {/* Audit Log Table */}
      <div className="bg-white border border-slate-200 rounded-2xl shadow-sm overflow-hidden">
        {loading && !data ? (
          <div className="flex flex-col items-center justify-center p-12 space-y-3">
            <div className="w-8 h-8 border-4 border-indigo-600 border-t-transparent rounded-full animate-spin" />
            <p className="text-xs text-slate-500 font-medium">Fetching audit logs...</p>
          </div>
        ) : !data || data.items.length === 0 ? (
          <div className="p-12 text-center text-slate-500 space-y-2">
            <svg className="w-12 h-12 text-slate-300 mx-auto" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="1.5" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
            </svg>
            <p className="text-sm font-bold text-slate-700">No audit log entries found</p>
            <p className="text-xs text-slate-400">Try loosening your filter parameters.</p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-slate-200 text-xs">
              <thead className="bg-slate-50">
                <tr>
                  <th className="px-6 py-3.5 text-left font-bold text-slate-600 uppercase tracking-wider text-[11px]">Timestamp</th>
                  <th className="px-6 py-3.5 text-left font-bold text-slate-600 uppercase tracking-wider text-[11px]">Action</th>
                  <th className="px-6 py-3.5 text-left font-bold text-slate-600 uppercase tracking-wider text-[11px]">Target Entity</th>
                  <th className="px-6 py-3.5 text-left font-bold text-slate-600 uppercase tracking-wider text-[11px]">Actor (User ID)</th>
                  <th className="px-6 py-3.5 text-left font-bold text-slate-600 uppercase tracking-wider text-[11px]">IP Address</th>
                  <th className="px-6 py-3.5 text-right font-bold text-slate-600 uppercase tracking-wider text-[11px]">Payload State</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 bg-white font-mono text-[11px]">
                {data.items.map((log) => (
                  <tr key={log.id} className="hover:bg-slate-50/80 transition">
                    <td className="px-6 py-4 text-slate-600 whitespace-nowrap">
                      {new Date(log.created_at).toLocaleString()}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap font-sans">
                      {getActionBadge(log.action)}
                    </td>
                    <td className="px-6 py-4 text-slate-800 whitespace-nowrap font-sans">
                      <span className="font-bold text-slate-900">{log.entity_type}</span>
                      {log.entity_id && (
                        <span className="text-slate-400 ml-1.5 font-mono text-[10px]" title={log.entity_id}>
                          ({log.entity_id.substring(0, 8)}...)
                        </span>
                      )}
                    </td>
                    <td className="px-6 py-4 text-slate-600 whitespace-nowrap">
                      {log.performed_by_user_id ? (
                        <span title={log.performed_by_user_id}>
                          {log.performed_by_user_id.substring(0, 8)}...
                        </span>
                      ) : (
                        <span className="text-slate-400 font-sans italic">system</span>
                      )}
                    </td>
                    <td className="px-6 py-4 text-slate-600 whitespace-nowrap font-mono">
                      {log.ip_address || '—'}
                    </td>
                    <td className="px-6 py-4 text-right whitespace-nowrap font-sans">
                      <button
                        onClick={() => setInspectingLog(log)}
                        className="px-3 py-1 text-xs font-bold text-indigo-600 bg-indigo-50 hover:bg-indigo-100 rounded-lg transition"
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
          <div className="px-6 py-3.5 border-t border-slate-200 bg-slate-50 flex items-center justify-between text-xs text-slate-600">
            <div>
              Showing <span className="font-bold">{data.items.length}</span> of{' '}
              <span className="font-bold">{data.total}</span> entries (Page {data.page} of {data.total_pages})
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

      {/* State Inspection Modal */}
      {inspectingLog && (
        <div className="fixed inset-0 z-50 overflow-y-auto bg-black/60 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl max-w-2xl w-full shadow-2xl overflow-hidden animate-fade-in flex flex-col max-h-[85vh]">
            <div className="px-6 py-4 border-b border-slate-100 flex justify-between items-center bg-slate-50">
              <div>
                <h3 className="text-base font-bold text-slate-900 flex items-center space-x-2">
                  <span>Audit Entry Payload:</span>
                  <span className="font-mono text-sm text-indigo-600 font-bold">{inspectingLog.action}</span>
                </h3>
                <p className="text-xs text-slate-500 font-mono mt-0.5">
                  ID: {inspectingLog.id} • {new Date(inspectingLog.created_at).toLocaleString()}
                </p>
              </div>
              <button
                onClick={() => setInspectingLog(null)}
                className="text-slate-400 hover:text-slate-600 rounded-lg p-1 transition"
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
                  <h4 className="text-xs font-bold text-slate-700 uppercase tracking-wide mb-2 flex items-center space-x-1.5">
                    <span className="w-2 h-2 rounded-full bg-rose-400" />
                    <span>Old State</span>
                  </h4>
                  <pre className="bg-slate-900 text-slate-100 p-4 rounded-xl text-[11px] font-mono overflow-x-auto max-h-72 border border-slate-800">
                    {inspectingLog.old_state
                      ? JSON.stringify(inspectingLog.old_state, null, 2)
                      : 'null'}
                  </pre>
                </div>

                {/* New State */}
                <div>
                  <h4 className="text-xs font-bold text-slate-700 uppercase tracking-wide mb-2 flex items-center space-x-1.5">
                    <span className="w-2 h-2 rounded-full bg-emerald-400" />
                    <span>New State</span>
                  </h4>
                  <pre className="bg-slate-900 text-slate-100 p-4 rounded-xl text-[11px] font-mono overflow-x-auto max-h-72 border border-slate-800">
                    {inspectingLog.new_state
                      ? JSON.stringify(inspectingLog.new_state, null, 2)
                      : 'null'}
                  </pre>
                </div>
              </div>

              <div className="bg-slate-50 p-4 rounded-xl border border-slate-200 text-xs space-y-1.5 text-slate-700">
                <div><span className="font-bold text-slate-900">Entity Type:</span> {inspectingLog.entity_type}</div>
                <div><span className="font-bold text-slate-900">Entity ID:</span> {inspectingLog.entity_id || 'None'}</div>
                <div><span className="font-bold text-slate-900">Actor:</span> {inspectingLog.performed_by_user_id || 'System'}</div>
                <div><span className="font-bold text-slate-900">Client IP:</span> {inspectingLog.ip_address || 'None recorded'}</div>
              </div>
            </div>

            <div className="px-6 py-3.5 bg-slate-50 border-t border-slate-100 flex justify-end">
              <button
                onClick={() => setInspectingLog(null)}
                className="px-4 py-2 text-xs font-bold text-slate-700 bg-white border border-slate-300 hover:bg-slate-100 rounded-xl transition shadow-sm"
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

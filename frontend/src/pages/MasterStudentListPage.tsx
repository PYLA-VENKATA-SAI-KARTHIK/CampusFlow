import React, { useState, useEffect, useCallback } from 'react';
import { studentService } from '../services/studentService';
import type { MasterStudentProfile } from '../services/studentService';
import { StudentMasterImportModal } from '../components/admin/StudentMasterImportModal';
import { LoadingSpinner } from '../components/ui/StatusFeedback';

export const MasterStudentListPage: React.FC = () => {
  const [students, setStudents] = useState<MasterStudentProfile[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [pageSize] = useState(20);
  const [search, setSearch] = useState('');
  const [branchFilter, setBranchFilter] = useState('');
  const [batchFilter, setBatchFilter] = useState<number | undefined>(undefined);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [isImportModalOpen, setIsImportModalOpen] = useState(false);

  const fetchStudents = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const res = await studentService.listMasterStudents({
        page,
        page_size: pageSize,
        search: search.trim() || undefined,
        branch_code: branchFilter || undefined,
        batch_year: batchFilter || undefined,
      });
      setStudents(res.items);
      setTotal(res.total);
    } catch (err: any) {
      setError(err?.response?.data?.detail || 'Failed to load master student list.');
    } finally {
      setLoading(false);
    }
  }, [page, pageSize, search, branchFilter, batchFilter]);

  useEffect(() => {
    fetchStudents();
  }, [fetchStudents]);

  const activeCount = students.filter((s) => s.user?.is_active).length;
  const pendingCount = students.filter((s) => !s.user?.is_active).length;

  return (
    <div className="space-y-6 max-w-7xl mx-auto">
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-xl font-bold text-slate-900 tracking-tight">Master Student List</h1>
          <p className="text-xs text-slate-500 mt-0.5">
            Authoritative institutional student roster for final-year placement and registration
          </p>
        </div>
        <div className="flex items-center space-x-3">
          <button
            onClick={() => setIsImportModalOpen(true)}
            className="px-4 py-2 bg-indigo-600 hover:bg-indigo-700 text-white rounded-xl text-xs font-semibold shadow-sm hover:shadow transition flex items-center space-x-1.5"
            data-testid="btn-import-excel"
          >
            <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
            </svg>
            <span>Import Excel</span>
          </button>
        </div>
      </div>

      {/* Metric Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <div className="p-4 bg-white rounded-2xl border border-slate-200 shadow-xs flex items-center justify-between">
          <div>
            <span className="text-[11px] font-bold text-slate-400 uppercase tracking-wider block">
              Total Master Students
            </span>
            <span className="text-2xl font-black text-slate-900 mt-1 block" data-testid="metric-total-students">
              {total}
            </span>
          </div>
          <div className="w-11 h-11 rounded-xl bg-indigo-50 border border-indigo-100 flex items-center justify-center text-indigo-600">
            <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 4.354a4 4 0 110 5.292M15 21H3v-1a6 6 0 0112 0v1zm0 0h6v-1a6 6 0 00-9-5.197M13 7a4 4 0 11-8 0 4 4 0 018 0z" />
            </svg>
          </div>
        </div>

        <div className="p-4 bg-white rounded-2xl border border-slate-200 shadow-xs flex items-center justify-between">
          <div>
            <span className="text-[11px] font-bold text-slate-400 uppercase tracking-wider block">
              Registered / Active Accounts
            </span>
            <span className="text-2xl font-black text-emerald-600 mt-1 block">
              {students.length > 0 ? activeCount : 0}
            </span>
          </div>
          <div className="w-11 h-11 rounded-xl bg-emerald-50 border border-emerald-100 flex items-center justify-center text-emerald-600">
            <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
          </div>
        </div>

        <div className="p-4 bg-white rounded-2xl border border-slate-200 shadow-xs flex items-center justify-between">
          <div>
            <span className="text-[11px] font-bold text-slate-400 uppercase tracking-wider block">
              Pre-provisioned / Pending
            </span>
            <span className="text-2xl font-black text-amber-600 mt-1 block">
              {students.length > 0 ? pendingCount : 0}
            </span>
          </div>
          <div className="w-11 h-11 rounded-xl bg-amber-50 border border-amber-100 flex items-center justify-center text-amber-600">
            <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
          </div>
        </div>
      </div>

      {/* Filter & Search Bar */}
      <div className="p-4 bg-white rounded-2xl border border-slate-200 shadow-xs flex flex-col sm:flex-row gap-3 items-center justify-between">
        <div className="w-full sm:w-80 relative">
          <input
            type="text"
            placeholder="Search by registration number, name, email..."
            value={search}
            onChange={(e) => {
              setSearch(e.target.value);
              setPage(1);
            }}
            className="w-full pl-9 pr-4 py-2 rounded-xl border border-slate-200 bg-slate-50/50 text-xs text-slate-900 placeholder:text-slate-400 focus:outline-none focus:ring-1 focus:ring-indigo-500 transition"
            data-testid="input-search-student"
          />
          <svg className="w-4 h-4 text-slate-400 absolute left-3 top-2.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
          </svg>
        </div>

        <div className="flex items-center space-x-3 w-full sm:w-auto">
          <select
            value={branchFilter}
            onChange={(e) => {
              setBranchFilter(e.target.value);
              setPage(1);
            }}
            className="px-3 py-2 rounded-xl border border-slate-200 bg-slate-50/50 text-xs font-semibold text-slate-700 focus:ring-1 focus:ring-indigo-500"
          >
            <option value="">All Branches</option>
            <option value="CSE">CSE</option>
            <option value="ECE">ECE</option>
            <option value="IT">IT</option>
            <option value="MECH">MECH</option>
            <option value="CIVIL">CIVIL</option>
            <option value="EEE">EEE</option>
          </select>

          <select
            value={batchFilter || ''}
            onChange={(e) => {
              setBatchFilter(e.target.value ? Number(e.target.value) : undefined);
              setPage(1);
            }}
            className="px-3 py-2 rounded-xl border border-slate-200 bg-slate-50/50 text-xs font-semibold text-slate-700 focus:ring-1 focus:ring-indigo-500"
          >
            <option value="">All Batches</option>
            <option value="2026">2026</option>
            <option value="2025">2025</option>
            <option value="2024">2024</option>
          </select>
        </div>
      </div>

      {/* Student Table */}
      <div className="bg-white rounded-2xl border border-slate-200 shadow-xs overflow-hidden">
        {loading ? (
          <div className="py-16 flex flex-col items-center justify-center">
            <LoadingSpinner size="md" label="Loading master student roster..." />
          </div>
        ) : error ? (
          <div className="p-8 text-center text-xs text-rose-600">{error}</div>
        ) : students.length === 0 ? (
          <div className="p-12 text-center">
            <div className="w-12 h-12 rounded-2xl bg-indigo-50 border border-indigo-100 flex items-center justify-center text-indigo-600 mx-auto">
              <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 4.354a4 4 0 110 5.292M15 21H3v-1a6 6 0 0112 0v1zm0 0h6v-1a6 6 0 00-9-5.197M13 7a4 4 0 11-8 0 4 4 0 018 0z" />
              </svg>
            </div>
            <h3 className="mt-3 text-sm font-bold text-slate-900">No students found</h3>
            <p className="text-xs text-slate-500 mt-1 max-w-sm mx-auto">
              Import the college final-year Excel list to populate the master student database.
            </p>
            <button
              onClick={() => setIsImportModalOpen(true)}
              className="mt-4 px-4 py-2 bg-indigo-600 text-white rounded-xl text-xs font-semibold hover:bg-indigo-700 transition"
            >
              Import Excel List
            </button>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="bg-slate-50 text-slate-500 font-semibold border-b border-slate-100 uppercase tracking-wider text-[10px]">
                <tr>
                  <th className="px-4 py-3">Registration Number</th>
                  <th className="px-4 py-3">Student Name</th>
                  <th className="px-4 py-3">University Email</th>
                  <th className="px-4 py-3">Branch</th>
                  <th className="px-4 py-3">Batch</th>
                  <th className="px-4 py-3">CGPA</th>
                  <th className="px-4 py-3">Backlogs</th>
                  <th className="px-4 py-3">Account Status</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 text-slate-700">
                {students.map((student) => (
                  <tr key={student.id} className="hover:bg-slate-50/70 transition">
                    <td className="px-4 py-3 font-mono font-bold text-slate-900">
                      {student.roll_number}
                    </td>
                    <td className="px-4 py-3 font-medium text-slate-800">
                      {student.user?.full_name || '—'}
                    </td>
                    <td className="px-4 py-3 font-mono text-slate-500 text-[11px]">
                      {student.user?.email || `${student.roll_number}@klu.ac.in`}
                    </td>
                    <td className="px-4 py-3">
                      <span className="px-2 py-0.5 rounded-lg bg-slate-100 text-slate-700 font-semibold text-[10px]">
                        {student.branch_code}
                      </span>
                    </td>
                    <td className="px-4 py-3">{student.batch_year}</td>
                    <td className="px-4 py-3 font-semibold text-slate-900">{student.cgpa.toFixed(2)}</td>
                    <td className="px-4 py-3">
                      {student.active_backlogs > 0 ? (
                        <span className="px-2 py-0.5 rounded-full bg-rose-100 text-rose-700 font-semibold text-[10px]">
                          {student.active_backlogs} Backlog{student.active_backlogs > 1 ? 's' : ''}
                        </span>
                      ) : (
                        <span className="text-slate-400 text-[11px]">0</span>
                      )}
                    </td>
                    <td className="px-4 py-3">
                      {student.user?.is_active ? (
                        <span className="px-2 py-0.5 rounded-full bg-emerald-100 text-emerald-800 font-semibold text-[10px] inline-flex items-center space-x-1">
                          <span className="w-1.5 h-1.5 rounded-full bg-emerald-500" />
                          <span>Active / Registered</span>
                        </span>
                      ) : (
                        <span className="px-2 py-0.5 rounded-full bg-amber-100 text-amber-800 font-semibold text-[10px] inline-flex items-center space-x-1">
                          <span className="w-1.5 h-1.5 rounded-full bg-amber-500" />
                          <span>Pending Registration</span>
                        </span>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}

        {/* Pagination footer */}
        {total > pageSize && (
          <div className="px-4 py-3 border-t border-slate-100 bg-slate-50/50 flex items-center justify-between text-xs text-slate-500">
            <span>
              Showing {(page - 1) * pageSize + 1} to {Math.min(page * pageSize, total)} of {total} students
            </span>
            <div className="flex items-center space-x-2">
              <button
                onClick={() => setPage((p) => Math.max(1, p - 1))}
                disabled={page === 1}
                className="px-3 py-1.5 rounded-lg border border-slate-200 bg-white hover:bg-slate-50 disabled:opacity-50 transition"
              >
                Previous
              </button>
              <span className="font-semibold text-slate-700">Page {page}</span>
              <button
                onClick={() => setPage((p) => p + 1)}
                disabled={page * pageSize >= total}
                className="px-3 py-1.5 rounded-lg border border-slate-200 bg-white hover:bg-slate-50 disabled:opacity-50 transition"
              >
                Next
              </button>
            </div>
          </div>
        )}
      </div>

      {/* Import Modal */}
      <StudentMasterImportModal
        isOpen={isImportModalOpen}
        onClose={() => setIsImportModalOpen(false)}
        onSuccess={fetchStudents}
      />
    </div>
  );
};

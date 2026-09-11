import React, { useState, useRef } from 'react';
import { adminService } from '../../services/adminService';
import type { BulkImportResponse } from '../../types/admin';

interface BulkImportModalProps {
  isOpen: boolean;
  onClose: () => void;
  onImportComplete: () => void;
}

export const BulkImportModal: React.FC<BulkImportModalProps> = ({
  isOpen,
  onClose,
  onImportComplete,
}) => {
  const [file, setFile] = useState<File | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<BulkImportResponse | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  if (!isOpen) return null;

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      const selected = e.target.files[0];
      if (!selected.name.endsWith('.csv')) {
        setError('Please select a valid CSV file.');
        setFile(null);
        return;
      }
      setFile(selected);
      setError(null);
      setResult(null);
    }
  };

  const handleDownloadSample = () => {
    const csvContent =
      'email,full_name,roll_number,branch_code,batch_year,cgpa,active_backlogs\n' +
      'student1@campus.edu,Alice Smith,21CS001,CSE,2025,8.75,0\n' +
      'student2@campus.edu,Bob Johnson,21EC002,ECE,2025,7.90,1\n';
    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.setAttribute('href', url);
    link.setAttribute('download', 'campusflow_student_import_sample.csv');
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!file) {
      setError('Please choose a CSV file to upload.');
      return;
    }

    try {
      setLoading(true);
      setError(null);
      const res = await adminService.bulkImportStudents(file);
      setResult(res);
      if (res.success_count > 0) {
        onImportComplete();
      }
    } catch (err: any) {
      const detail = err?.response?.data?.detail;
      setError(typeof detail === 'string' ? detail : 'Failed to process bulk import.');
    } finally {
      setLoading(false);
    }
  };

  const handleReset = () => {
    setFile(null);
    setResult(null);
    setError(null);
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  return (
    <div className="fixed inset-0 z-50 overflow-y-auto bg-black/50 flex items-center justify-center p-4">
      <div className="bg-white rounded-2xl max-w-2xl w-full shadow-2xl overflow-hidden animate-in fade-in zoom-in-95 duration-200 flex flex-col max-h-[90vh]">
        {/* Header */}
        <div className="px-6 py-4 border-b border-gray-100 flex justify-between items-center bg-gray-50/50 flex-shrink-0">
          <div className="flex items-center space-x-2">
            <div className="w-8 h-8 rounded-lg bg-emerald-100 flex items-center justify-center text-emerald-600">
              <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
              </svg>
            </div>
            <div>
              <h3 className="text-base font-bold text-gray-900">Bulk Student Import</h3>
              <p className="text-xs text-gray-500">Upload CSV to onboard students in batch</p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600 rounded-lg p-1 transition"
          >
            <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        <div className="p-6 overflow-y-auto flex-1 space-y-5">
          {/* Format helper */}
          <div className="bg-blue-50/60 border border-blue-100 rounded-xl p-4 text-xs text-blue-800 space-y-2">
            <div className="flex justify-between items-center">
              <span className="font-semibold text-blue-900">Required CSV Columns:</span>
              <button
                type="button"
                onClick={handleDownloadSample}
                className="text-blue-600 hover:text-blue-800 font-semibold underline flex items-center space-x-1"
              >
                <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
                </svg>
                <span>Download Sample Template</span>
              </button>
            </div>
            <code className="block bg-white/80 p-2 rounded border border-blue-200 text-blue-950 font-mono text-[11px] overflow-x-auto">
              email, full_name, roll_number, branch_code, batch_year, cgpa, active_backlogs
            </code>
            <p className="text-[11px] text-blue-700">
              Students will be registered as inactive with activation tokens dispatched via email.
            </p>
          </div>

          {error && (
            <div className="p-3 bg-red-50 border border-red-200 text-red-700 text-xs rounded-lg flex items-start space-x-2">
              <svg className="w-4 h-4 text-red-500 flex-shrink-0 mt-0.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              <span>{error}</span>
            </div>
          )}

          {!result ? (
            <form onSubmit={handleSubmit} className="space-y-4">
              <div>
                <label className="block text-xs font-semibold text-gray-700 mb-2">
                  Select CSV File
                </label>
                <div
                  onClick={() => fileInputRef.current?.click()}
                  className="border-2 border-dashed border-gray-300 hover:border-blue-400 rounded-xl p-6 text-center cursor-pointer bg-gray-50/50 hover:bg-blue-50/20 transition flex flex-col items-center justify-center space-y-2"
                >
                  <svg className="w-10 h-10 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="1.5" d="M9 13h6m-3-3v6m5 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                  </svg>
                  <div className="text-xs text-gray-600 font-medium">
                    {file ? (
                      <span className="text-blue-600 font-bold">{file.name}</span>
                    ) : (
                      <>
                        <span className="text-blue-600 font-bold hover:underline">Click to browse</span> or drag and drop CSV
                      </>
                    )}
                  </div>
                  <p className="text-[11px] text-gray-400">CSV file format only</p>
                </div>
                <input
                  ref={fileInputRef}
                  type="file"
                  accept=".csv"
                  className="hidden"
                  onChange={handleFileChange}
                />
              </div>

              <div className="flex justify-end space-x-3 pt-2">
                <button
                  type="button"
                  onClick={onClose}
                  className="px-4 py-2 text-xs font-semibold text-gray-700 bg-gray-100 hover:bg-gray-200 rounded-lg transition"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={!file || loading}
                  className="px-4 py-2 text-xs font-semibold text-white bg-blue-600 hover:bg-blue-700 disabled:opacity-50 rounded-lg transition flex items-center space-x-1.5"
                >
                  {loading ? (
                    <>
                      <div className="w-3.5 h-3.5 border-2 border-white border-t-transparent rounded-full animate-spin" />
                      <span>Processing CSV...</span>
                    </>
                  ) : (
                    <span>Upload & Import</span>
                  )}
                </button>
              </div>
            </form>
          ) : (
            /* Result View */
            <div className="space-y-4">
              <div className="grid grid-cols-3 gap-3">
                <div className="p-3.5 bg-gray-50 border border-gray-200 rounded-xl text-center">
                  <div className="text-xl font-extrabold text-gray-900">{result.total_rows}</div>
                  <div className="text-[11px] font-medium text-gray-500 uppercase tracking-wide mt-0.5">Total Rows</div>
                </div>
                <div className="p-3.5 bg-emerald-50 border border-emerald-200 rounded-xl text-center">
                  <div className="text-xl font-extrabold text-emerald-600">{result.success_count}</div>
                  <div className="text-[11px] font-medium text-emerald-700 uppercase tracking-wide mt-0.5">Imported</div>
                </div>
                <div className="p-3.5 bg-rose-50 border border-rose-200 rounded-xl text-center">
                  <div className="text-xl font-extrabold text-rose-600">{result.error_count}</div>
                  <div className="text-[11px] font-medium text-rose-700 uppercase tracking-wide mt-0.5">Errors</div>
                </div>
              </div>

              {result.errors.length > 0 && (
                <div className="space-y-2">
                  <h4 className="text-xs font-bold text-gray-900 flex items-center space-x-1.5">
                    <span className="w-2 h-2 rounded-full bg-rose-500" />
                    <span>Row Validation Failures ({result.errors.length})</span>
                  </h4>
                  <div className="max-h-56 overflow-y-auto border border-gray-200 rounded-xl">
                    <table className="min-w-full divide-y divide-gray-200 text-xs">
                      <thead className="bg-gray-50 sticky top-0">
                        <tr>
                          <th className="px-3 py-2 text-left font-semibold text-gray-600 w-20">Row #</th>
                          <th className="px-3 py-2 text-left font-semibold text-gray-600">Error Description</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-gray-100 bg-white">
                        {result.errors.map((err, idx) => (
                          <tr key={idx} className="hover:bg-gray-50">
                            <td className="px-3 py-2 font-mono font-bold text-gray-700">{err.row_number}</td>
                            <td className="px-3 py-2 text-rose-600">{err.error}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              )}

              <div className="flex justify-end space-x-3 pt-2">
                <button
                  type="button"
                  onClick={handleReset}
                  className="px-4 py-2 text-xs font-semibold text-gray-700 bg-gray-100 hover:bg-gray-200 rounded-lg transition"
                >
                  Import Another File
                </button>
                <button
                  type="button"
                  onClick={onClose}
                  className="px-4 py-2 text-xs font-semibold text-white bg-blue-600 hover:bg-blue-700 rounded-lg transition"
                >
                  Done
                </button>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

import React, { useState, useRef } from 'react';
import { studentService } from '../../services/studentService';
import type {
  StudentImportPreviewResponse,
  StudentImportConfirmItem,
} from '../../services/studentService';

interface StudentMasterImportModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSuccess: () => void;
}

export const StudentMasterImportModal: React.FC<StudentMasterImportModalProps> = ({
  isOpen,
  onClose,
  onSuccess,
}) => {
  const [file, setFile] = useState<File | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [preview, setPreview] = useState<StudentImportPreviewResponse | null>(null);
  const [customMapping, setCustomMapping] = useState<Record<string, string>>({});
  const [confirming, setConfirming] = useState(false);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  if (!isOpen) return null;

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      setFile(e.target.files[0]);
      setError(null);
      setPreview(null);
      setSuccessMessage(null);
    }
  };

  const handlePreview = async (mappingOverride?: Record<string, string>) => {
    if (!file) {
      setError('Please select an Excel (.xlsx) or CSV (.csv) file.');
      return;
    }

    try {
      setLoading(true);
      setError(null);
      const res = await studentService.previewImport(file, mappingOverride || customMapping);
      setPreview(res);
      setCustomMapping(res.detected_mappings || {});
    } catch (err: any) {
      setError(err?.response?.data?.detail || 'Failed to parse and preview student list file.');
    } finally {
      setLoading(false);
    }
  };

  const handleMappingChange = (field: string, header: string) => {
    const updated = { ...customMapping, [field]: header };
    setCustomMapping(updated);
    handlePreview(updated);
  };

  const handleConfirm = async () => {
    if (!preview || !file) return;

    try {
      setConfirming(true);
      setError(null);

      const itemsToImport: StudentImportConfirmItem[] = preview.preview_items
        .filter((item) => item.status === 'VALID')
        .map((item) => ({
          roll_number: item.roll_number,
          full_name: item.full_name,
          branch_code: item.branch_code || 'CSE',
          batch_year: item.batch_year || 2026,
          cgpa: item.cgpa !== null && item.cgpa !== undefined ? item.cgpa : 0.0,
          active_backlogs: item.active_backlogs || 0,
          personal_email: item.personal_email,
          phone_number: item.phone_number,
          gender: item.gender,
        }));

      if (itemsToImport.length === 0) {
        setError('No valid student rows to import.');
        return;
      }

      const res = await studentService.confirmImport(file.name, itemsToImport);
      setSuccessMessage(res.message);
      setTimeout(() => {
        onSuccess();
        onClose();
      }, 1800);
    } catch (err: any) {
      setError(err?.response?.data?.detail || 'Failed to commit master student list.');
    } finally {
      setConfirming(false);
    }
  };

  const resetAll = () => {
    setFile(null);
    setPreview(null);
    setError(null);
    setSuccessMessage(null);
    setCustomMapping({});
    if (fileInputRef.current) fileInputRef.current.value = '';
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/70 backdrop-blur-sm animate-fadeIn">
      <div className="bg-white rounded-2xl shadow-2xl border border-slate-200 w-full max-w-4xl max-h-[90vh] flex flex-col overflow-hidden">
        {/* Header */}
        <div className="px-6 py-4 border-b border-slate-100 flex items-center justify-between bg-slate-50/80">
          <div className="flex items-center space-x-3">
            <div className="w-10 h-10 rounded-xl bg-indigo-50 border border-indigo-100 flex items-center justify-center text-indigo-600 font-bold">
              <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
              </svg>
            </div>
            <div>
              <h3 className="text-base font-bold text-slate-900">Import Master Student List</h3>
              <p className="text-xs text-slate-500">
                Upload college final-year Excel/CSV spreadsheet as authoritative student master data
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-2 text-slate-400 hover:text-slate-600 rounded-lg hover:bg-slate-100 transition"
          >
            <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        {/* Content Area */}
        <div className="p-6 overflow-y-auto space-y-6 flex-1">
          {error && (
            <div className="p-4 rounded-xl bg-rose-50 border border-rose-200 text-rose-700 text-xs flex items-start space-x-2">
              <svg className="w-4 h-4 shrink-0 mt-0.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              <span>{error}</span>
            </div>
          )}

          {successMessage && (
            <div className="p-4 rounded-xl bg-emerald-50 border border-emerald-200 text-emerald-700 text-xs flex items-start space-x-2">
              <svg className="w-4 h-4 shrink-0 mt-0.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M5 13l4 4L19 7" />
              </svg>
              <span>{successMessage}</span>
            </div>
          )}

          {/* STEP 1: File Selection */}
          {!preview && (
            <div className="space-y-4">
              <div
                onClick={() => fileInputRef.current?.click()}
                className="border-2 border-dashed border-slate-300 hover:border-indigo-500 rounded-2xl p-8 flex flex-col items-center justify-center cursor-pointer bg-slate-50/50 hover:bg-indigo-50/20 transition group"
              >
                <div className="w-14 h-14 rounded-2xl bg-white shadow-sm border border-slate-200 flex items-center justify-center text-indigo-600 group-hover:scale-105 transition">
                  <svg className="w-7 h-7" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="1.5" d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
                  </svg>
                </div>
                <p className="mt-3 text-sm font-semibold text-slate-700">
                  {file ? file.name : 'Click or drag & drop to choose an Excel file (.xlsx, .csv)'}
                </p>
                <p className="text-xs text-slate-400 mt-1">
                  Registration numbers are strictly preserved as string identifiers with leading zeros
                </p>
                <input
                  ref={fileInputRef}
                  type="file"
                  accept=".xlsx,.xls,.csv"
                  onChange={handleFileChange}
                  className="hidden"
                  data-testid="file-upload-input"
                />
              </div>

              {file && (
                <div className="flex items-center justify-between p-3 rounded-xl bg-slate-100 border border-slate-200">
                  <div className="flex items-center space-x-2">
                    <span className="text-xs font-semibold text-slate-700">{file.name}</span>
                    <span className="text-[10px] text-slate-400 font-mono">
                      ({(file.size / 1024).toFixed(1)} KB)
                    </span>
                  </div>
                  <button
                    onClick={() => handlePreview()}
                    disabled={loading}
                    className="px-4 py-2 bg-indigo-600 hover:bg-indigo-700 text-white rounded-xl text-xs font-semibold shadow-xs disabled:opacity-50 transition flex items-center space-x-1.5"
                    data-testid="btn-preview-file"
                  >
                    {loading ? (
                      <>
                        <svg className="animate-spin -ml-1 mr-2 h-3.5 w-3.5 text-white" fill="none" viewBox="0 0 24 24">
                          <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                          <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z" />
                        </svg>
                        <span>Reading spreadsheet...</span>
                      </>
                    ) : (
                      <span>Preview Import</span>
                    )}
                  </button>
                </div>
              )}
            </div>
          )}

          {/* STEP 2: Preview & Column Mapping Screen */}
          {preview && (
            <div className="space-y-5">
              {/* Summary Stats Badges */}
              <div className="grid grid-cols-2 sm:grid-cols-5 gap-3">
                <div className="p-3 bg-slate-50 border border-slate-200 rounded-xl">
                  <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider block">Total Rows</span>
                  <span className="text-lg font-extrabold text-slate-900">{preview.total_rows}</span>
                </div>
                <div className="p-3 bg-emerald-50 border border-emerald-200 rounded-xl">
                  <span className="text-[10px] font-bold text-emerald-600 uppercase tracking-wider block">Valid Students</span>
                  <span className="text-lg font-extrabold text-emerald-700">{preview.valid_count}</span>
                </div>
                <div className="p-3 bg-amber-50 border border-amber-200 rounded-xl">
                  <span className="text-[10px] font-bold text-amber-600 uppercase tracking-wider block">Duplicate Reg Nos</span>
                  <span className="text-lg font-extrabold text-amber-700">{preview.duplicate_in_file_count}</span>
                </div>
                <div className="p-3 bg-rose-50 border border-rose-200 rounded-xl">
                  <span className="text-[10px] font-bold text-rose-600 uppercase tracking-wider block">Missing Reg No</span>
                  <span className="text-lg font-extrabold text-rose-700">{preview.missing_reg_no_count}</span>
                </div>
                <div className="p-3 bg-indigo-50 border border-indigo-200 rounded-xl">
                  <span className="text-[10px] font-bold text-indigo-600 uppercase tracking-wider block">Existing in DB</span>
                  <span className="text-lg font-extrabold text-indigo-700">{preview.existing_in_db_count}</span>
                </div>
              </div>

              {/* Column Mapping Section */}
              <div className="p-4 rounded-xl bg-slate-50 border border-slate-200 space-y-3">
                <div className="flex items-center justify-between">
                  <h4 className="text-xs font-bold text-slate-800 uppercase tracking-wider">
                    Detected Column Mappings
                  </h4>
                  <span className="text-[11px] text-slate-500">
                    Adjust mappings if needed for custom column headers
                  </span>
                </div>

                <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 text-xs">
                  {/* Reg No */}
                  <div>
                    <label className="block text-[11px] font-semibold text-slate-600 mb-1">
                      Registration Number <span className="text-rose-500">*</span>
                    </label>
                    <select
                      value={customMapping.roll_number || ''}
                      onChange={(e) => handleMappingChange('roll_number', e.target.value)}
                      className="w-full px-2.5 py-1.5 rounded-lg border border-slate-300 bg-white text-xs font-medium focus:ring-1 focus:ring-indigo-500"
                    >
                      <option value="">-- Select Header --</option>
                      {preview.detected_headers.map((h) => (
                        <option key={h} value={h}>
                          {h}
                        </option>
                      ))}
                    </select>
                  </div>

                  {/* Full Name */}
                  <div>
                    <label className="block text-[11px] font-semibold text-slate-600 mb-1">
                      Student Name
                    </label>
                    <select
                      value={customMapping.full_name || ''}
                      onChange={(e) => handleMappingChange('full_name', e.target.value)}
                      className="w-full px-2.5 py-1.5 rounded-lg border border-slate-300 bg-white text-xs font-medium focus:ring-1 focus:ring-indigo-500"
                    >
                      <option value="">-- Select Header --</option>
                      {preview.detected_headers.map((h) => (
                        <option key={h} value={h}>
                          {h}
                        </option>
                      ))}
                    </select>
                  </div>

                  {/* Branch */}
                  <div>
                    <label className="block text-[11px] font-semibold text-slate-600 mb-1">
                      Branch / Department
                    </label>
                    <select
                      value={customMapping.branch_code || ''}
                      onChange={(e) => handleMappingChange('branch_code', e.target.value)}
                      className="w-full px-2.5 py-1.5 rounded-lg border border-slate-300 bg-white text-xs font-medium focus:ring-1 focus:ring-indigo-500"
                    >
                      <option value="">-- Select Header --</option>
                      {preview.detected_headers.map((h) => (
                        <option key={h} value={h}>
                          {h}
                        </option>
                      ))}
                    </select>
                  </div>
                </div>
              </div>

              {/* Preview Table */}
              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <h4 className="text-xs font-bold text-slate-800 uppercase tracking-wider">
                    Student Preview ({preview.preview_items.length} rows shown)
                  </h4>
                </div>

                <div className="border border-slate-200 rounded-xl overflow-x-auto max-h-56 scrollbar-thin">
                  <table className="w-full text-left text-xs">
                    <thead className="bg-slate-100 text-slate-600 font-semibold border-b border-slate-200 sticky top-0">
                      <tr>
                        <th className="px-3 py-2">Row</th>
                        <th className="px-3 py-2">Reg Number</th>
                        <th className="px-3 py-2">Name</th>
                        <th className="px-3 py-2">Branch</th>
                        <th className="px-3 py-2">Batch</th>
                        <th className="px-3 py-2">CGPA</th>
                        <th className="px-3 py-2">Status</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-100 text-slate-700">
                      {preview.preview_items.map((item) => (
                        <tr key={item.row_index} className="hover:bg-slate-50">
                          <td className="px-3 py-2 text-slate-400 font-mono text-[11px]">{item.row_index}</td>
                          <td className="px-3 py-2 font-mono font-semibold text-slate-900">{item.roll_number || '—'}</td>
                          <td className="px-3 py-2 font-medium">{item.full_name || '—'}</td>
                          <td className="px-3 py-2">{item.branch_code || 'CSE'}</td>
                          <td className="px-3 py-2">{item.batch_year || 2026}</td>
                          <td className="px-3 py-2">{item.cgpa != null ? Number(item.cgpa).toFixed(2) : '0.00'}</td>
                          <td className="px-3 py-2">
                            {item.status === 'VALID' ? (
                              <span className="px-2 py-0.5 rounded-full bg-emerald-100 text-emerald-800 font-semibold text-[10px]">
                                {item.is_existing_in_db ? 'Update Record' : 'New Master Record'}
                              </span>
                            ) : (
                              <span className="px-2 py-0.5 rounded-full bg-rose-100 text-rose-800 font-semibold text-[10px]">
                                {item.error_message || item.status}
                              </span>
                            )}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Footer Actions */}
        <div className="px-6 py-4 border-t border-slate-100 bg-slate-50 flex items-center justify-between">
          <div>
            {preview && (
              <button
                onClick={resetAll}
                className="text-xs font-semibold text-slate-500 hover:text-slate-800 transition"
              >
                Choose another file
              </button>
            )}
          </div>
          <div className="flex items-center space-x-3">
            <button
              onClick={onClose}
              disabled={confirming}
              className="px-4 py-2 border border-slate-200 text-slate-700 hover:bg-slate-100 rounded-xl text-xs font-semibold transition"
            >
              Cancel
            </button>

            {preview && (
              <button
                onClick={handleConfirm}
                disabled={confirming || !preview.can_import}
                className="px-5 py-2 bg-indigo-600 hover:bg-indigo-700 text-white rounded-xl text-xs font-semibold shadow-xs disabled:opacity-50 transition flex items-center space-x-1.5"
                data-testid="btn-confirm-import"
              >
                {confirming ? (
                  <>
                    <svg className="animate-spin -ml-1 mr-2 h-3.5 w-3.5 text-white" fill="none" viewBox="0 0 24 24">
                      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z" />
                    </svg>
                    <span>Importing students...</span>
                  </>
                ) : (
                  <span>Confirm Import ({preview.valid_count} Students)</span>
                )}
              </button>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

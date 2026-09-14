import React, { useState, useRef } from 'react';
import { driveService } from '../../services/driveService';
import type {
  PlacementStage,
  StageImportPreviewResponse,
  StageImportCategory,
} from '../../types/drive';

interface StageQualifiedImportModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSuccess: () => void;
  driveId: string;
  stage: PlacementStage;
  driveTitle?: string;
}

export const StageQualifiedImportModal: React.FC<StageQualifiedImportModalProps> = ({
  isOpen,
  onClose,
  onSuccess,
  driveId,
  stage,
  driveTitle,
}) => {
  const [file, setFile] = useState<File | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [preview, setPreview] = useState<StageImportPreviewResponse | null>(null);
  const [customMapping, setCustomMapping] = useState<Record<string, string>>({});
  const [activeCategoryTab, setActiveCategoryTab] = useState<string>('ALL');
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
      setError('Please select an Excel (.xlsx, .xls) or CSV (.csv) file.');
      return;
    }

    try {
      setLoading(true);
      setError(null);
      const res = await driveService.previewStageQualifiedImport(
        driveId,
        stage.id,
        file,
        mappingOverride || customMapping
      );
      setPreview(res);
      setCustomMapping(res.detected_mappings || {});
    } catch (err: any) {
      setError(err?.response?.data?.detail || 'Failed to preview round shortlist file.');
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

      if (preview.valid_student_ids.length === 0) {
        setError('No valid matched applicants to advance to this round.');
        return;
      }

      const res = await driveService.confirmStageQualifiedImport(driveId, stage.id, {
        filename: file.name,
        student_ids: preview.valid_student_ids,
      });

      setSuccessMessage(res.message);
      setTimeout(() => {
        onSuccess();
        onClose();
      }, 1600);
    } catch (err: any) {
      setError(err?.response?.data?.detail || 'Failed to commit round qualification update.');
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
    setActiveCategoryTab('ALL');
    if (fileInputRef.current) fileInputRef.current.value = '';
  };

  // Filter items by category tab
  const filteredItems = preview?.items.filter((item) => {
    if (activeCategoryTab === 'ALL') return true;
    if (activeCategoryTab === 'MATCHED') return item.category === 'MATCHED';
    if (activeCategoryTab === 'ALREADY_AT_STAGE') return item.category === 'ALREADY_AT_STAGE';
    if (activeCategoryTab === 'NOT_APPLIED') return item.category === 'NOT_APPLIED';
    if (activeCategoryTab === 'UNKNOWN_REG_NO') return item.category === 'UNKNOWN_REG_NO';
    if (activeCategoryTab === 'DUPLICATE_IN_FILE') return item.category === 'DUPLICATE_IN_FILE';
    return true;
  }) || [];

  const getCategoryBadge = (category: StageImportCategory) => {
    switch (category) {
      case 'MATCHED':
        return (
          <span className="px-2 py-0.5 rounded-full bg-emerald-100 text-emerald-800 font-semibold text-[10px]">
            Ready to Qualify
          </span>
        );
      case 'ALREADY_AT_STAGE':
        return (
          <span className="px-2 py-0.5 rounded-full bg-blue-100 text-blue-800 font-semibold text-[10px]">
            Already at Stage
          </span>
        );
      case 'NOT_APPLIED':
        return (
          <span className="px-2 py-0.5 rounded-full bg-amber-100 text-amber-800 font-semibold text-[10px]">
            Not Applied
          </span>
        );
      case 'UNKNOWN_REG_NO':
        return (
          <span className="px-2 py-0.5 rounded-full bg-rose-100 text-rose-800 font-semibold text-[10px]">
            Unknown Reg No
          </span>
        );
      case 'DUPLICATE_IN_FILE':
        return (
          <span className="px-2 py-0.5 rounded-full bg-purple-100 text-purple-800 font-semibold text-[10px]">
            Duplicate Row
          </span>
        );
      default:
        return null;
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/70 backdrop-blur-sm animate-fadeIn">
      <div className="bg-white rounded-2xl shadow-2xl border border-slate-200 w-full max-w-4xl max-h-[90vh] flex flex-col overflow-hidden">
        {/* Header */}
        <div className="px-6 py-4 border-b border-slate-100 flex items-center justify-between bg-slate-50/80">
          <div className="flex items-center space-x-3">
            <div className="w-10 h-10 rounded-xl bg-indigo-50 border border-indigo-100 flex items-center justify-center text-indigo-600 font-bold">
              <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
            </div>
            <div>
              <div className="flex items-center space-x-2">
                <span className="px-2 py-0.5 bg-indigo-100 text-indigo-800 text-[10px] font-black rounded-md uppercase">
                  Round {stage.sequence_order}
                </span>
                <h3 className="text-base font-bold text-slate-900">
                  Upload Qualified Students: {stage.name}
                </h3>
              </div>
              <p className="text-xs text-slate-500">
                {driveTitle ? `${driveTitle} • ` : ''}Matched strictly against registered applicants by university registration number
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
        <div className="p-6 overflow-y-auto space-y-5 flex-1">
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

          {/* STEP 1: Upload File */}
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
                  {file ? file.name : `Select company shortlist spreadsheet for Round ${stage.sequence_order}`}
                </p>
                <p className="text-xs text-slate-400 mt-1 text-center max-w-md">
                  Upload .xlsx, .xls, or .csv containing qualified registration numbers. Unlisted students will NOT be auto-rejected.
                </p>
                <input
                  ref={fileInputRef}
                  type="file"
                  accept=".xlsx,.xls,.csv"
                  onChange={handleFileChange}
                  className="hidden"
                  data-testid="stage-file-upload-input"
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
                    data-testid="btn-preview-stage-file"
                  >
                    {loading ? (
                      <>
                        <svg className="animate-spin -ml-1 mr-2 h-3.5 w-3.5 text-white" fill="none" viewBox="0 0 24 24">
                          <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                          <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z" />
                        </svg>
                        <span>Analyzing shortlist...</span>
                      </>
                    ) : (
                      <span>Preview Round Update</span>
                    )}
                  </button>
                </div>
              )}
            </div>
          )}

          {/* STEP 2: Preview & Verification */}
          {preview && (
            <div className="space-y-5">
              {/* Summary Stats Badges */}
              <div className="grid grid-cols-2 sm:grid-cols-6 gap-2.5">
                <div className="p-3 bg-slate-50 border border-slate-200 rounded-xl">
                  <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider block">Excel Rows</span>
                  <span className="text-lg font-extrabold text-slate-900">{preview.total_rows}</span>
                </div>
                <div className="p-3 bg-emerald-50 border border-emerald-200 rounded-xl">
                  <span className="text-[10px] font-bold text-emerald-600 uppercase tracking-wider block">Matched</span>
                  <span className="text-lg font-extrabold text-emerald-700">{preview.matched_count}</span>
                </div>
                <div className="p-3 bg-blue-50 border border-blue-200 rounded-xl">
                  <span className="text-[10px] font-bold text-blue-600 uppercase tracking-wider block">At Stage</span>
                  <span className="text-lg font-extrabold text-blue-700">{preview.already_at_stage_count}</span>
                </div>
                <div className="p-3 bg-amber-50 border border-amber-200 rounded-xl">
                  <span className="text-[10px] font-bold text-amber-600 uppercase tracking-wider block">Not Applied</span>
                  <span className="text-lg font-extrabold text-amber-700">{preview.not_applied_count}</span>
                </div>
                <div className="p-3 bg-rose-50 border border-rose-200 rounded-xl">
                  <span className="text-[10px] font-bold text-rose-600 uppercase tracking-wider block">Unknown</span>
                  <span className="text-lg font-extrabold text-rose-700">{preview.unknown_count}</span>
                </div>
                <div className="p-3 bg-purple-50 border border-purple-200 rounded-xl">
                  <span className="text-[10px] font-bold text-purple-600 uppercase tracking-wider block">Duplicates</span>
                  <span className="text-lg font-extrabold text-purple-700">{preview.duplicate_count}</span>
                </div>
              </div>

              {/* Column Mapping Section */}
              <div className="p-4 rounded-xl bg-slate-50 border border-slate-200 space-y-3">
                <div className="flex items-center justify-between">
                  <h4 className="text-xs font-bold text-slate-800 uppercase tracking-wider">
                    Matching Column Configuration
                  </h4>
                  <span className="text-[11px] text-slate-500">
                    Primary Key: Registration Number
                  </span>
                </div>

                <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-xs">
                  <div>
                    <label className="block text-[11px] font-semibold text-slate-600 mb-1">
                      Registration Number Column <span className="text-rose-500">*</span>
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

                  <div>
                    <label className="block text-[11px] font-semibold text-slate-600 mb-1">
                      Student Name (Secondary / Verification)
                    </label>
                    <select
                      value={customMapping.full_name || ''}
                      onChange={(e) => handleMappingChange('full_name', e.target.value)}
                      className="w-full px-2.5 py-1.5 rounded-lg border border-slate-300 bg-white text-xs font-medium focus:ring-1 focus:ring-indigo-500"
                    >
                      <option value="">-- Select Header (Optional) --</option>
                      {preview.detected_headers.map((h) => (
                        <option key={h} value={h}>
                          {h}
                        </option>
                      ))}
                    </select>
                  </div>
                </div>
              </div>

              {/* Category Filter Tabs */}
              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-1.5 overflow-x-auto pb-1">
                    <button
                      onClick={() => setActiveCategoryTab('ALL')}
                      className={`px-3 py-1 rounded-lg text-xs font-semibold transition ${
                        activeCategoryTab === 'ALL'
                          ? 'bg-slate-900 text-white'
                          : 'bg-slate-100 text-slate-600 hover:bg-slate-200'
                      }`}
                    >
                      All ({preview.items.length})
                    </button>
                    <button
                      onClick={() => setActiveCategoryTab('MATCHED')}
                      className={`px-3 py-1 rounded-lg text-xs font-semibold transition ${
                        activeCategoryTab === 'MATCHED'
                          ? 'bg-emerald-600 text-white'
                          : 'bg-emerald-50 text-emerald-700 hover:bg-emerald-100'
                      }`}
                    >
                      Matched ({preview.matched_count})
                    </button>
                    <button
                      onClick={() => setActiveCategoryTab('ALREADY_AT_STAGE')}
                      className={`px-3 py-1 rounded-lg text-xs font-semibold transition ${
                        activeCategoryTab === 'ALREADY_AT_STAGE'
                          ? 'bg-blue-600 text-white'
                          : 'bg-blue-50 text-blue-700 hover:bg-blue-100'
                      }`}
                    >
                      Already at Stage ({preview.already_at_stage_count})
                    </button>
                    <button
                      onClick={() => setActiveCategoryTab('NOT_APPLIED')}
                      className={`px-3 py-1 rounded-lg text-xs font-semibold transition ${
                        activeCategoryTab === 'NOT_APPLIED'
                          ? 'bg-amber-600 text-white'
                          : 'bg-amber-50 text-amber-700 hover:bg-amber-100'
                      }`}
                    >
                      Not Applied ({preview.not_applied_count})
                    </button>
                    <button
                      onClick={() => setActiveCategoryTab('UNKNOWN_REG_NO')}
                      className={`px-3 py-1 rounded-lg text-xs font-semibold transition ${
                        activeCategoryTab === 'UNKNOWN_REG_NO'
                          ? 'bg-rose-600 text-white'
                          : 'bg-rose-50 text-rose-700 hover:bg-rose-100'
                      }`}
                    >
                      Unknown ({preview.unknown_count})
                    </button>
                    <button
                      onClick={() => setActiveCategoryTab('DUPLICATE_IN_FILE')}
                      className={`px-3 py-1 rounded-lg text-xs font-semibold transition ${
                        activeCategoryTab === 'DUPLICATE_IN_FILE'
                          ? 'bg-purple-600 text-white'
                          : 'bg-purple-50 text-purple-700 hover:bg-purple-100'
                      }`}
                    >
                      Duplicates ({preview.duplicate_count})
                    </button>
                  </div>
                </div>

                {/* Preview Table */}
                <div className="border border-slate-200 rounded-xl overflow-x-auto max-h-56 scrollbar-thin">
                  <table className="w-full text-left text-xs">
                    <thead className="bg-slate-100 text-slate-600 font-semibold border-b border-slate-200 sticky top-0">
                      <tr>
                        <th className="px-3 py-2">Row</th>
                        <th className="px-3 py-2">Reg Number</th>
                        <th className="px-3 py-2">Student Name</th>
                        <th className="px-3 py-2">Branch</th>
                        <th className="px-3 py-2">CGPA</th>
                        <th className="px-3 py-2">Match Status</th>
                        <th className="px-3 py-2">Details</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-100 text-slate-700">
                      {filteredItems.length === 0 ? (
                        <tr>
                          <td colSpan={7} className="px-3 py-6 text-center text-slate-400 text-xs">
                            No students in this category.
                          </td>
                        </tr>
                      ) : (
                        filteredItems.map((item) => (
                          <tr key={item.row_index} className="hover:bg-slate-50">
                            <td className="px-3 py-2 text-slate-400 font-mono text-[11px]">{item.row_index}</td>
                            <td className="px-3 py-2 font-mono font-semibold text-slate-900">{item.roll_number}</td>
                            <td className="px-3 py-2 font-medium">{item.student_name || '—'}</td>
                            <td className="px-3 py-2">{item.branch_code || '—'}</td>
                            <td className="px-3 py-2">{item.cgpa != null ? Number(item.cgpa).toFixed(2) : '—'}</td>
                            <td className="px-3 py-2">{getCategoryBadge(item.category)}</td>
                            <td className="px-3 py-2 text-slate-500 text-[11px]">{item.details || '—'}</td>
                          </tr>
                        ))
                      )}
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
                disabled={confirming || !preview.can_confirm}
                className="px-5 py-2 bg-indigo-600 hover:bg-indigo-700 text-white rounded-xl text-xs font-semibold shadow-xs disabled:opacity-50 transition flex items-center space-x-1.5"
                data-testid="btn-confirm-round-update"
              >
                {confirming ? (
                  <>
                    <svg className="animate-spin -ml-1 mr-2 h-3.5 w-3.5 text-white" fill="none" viewBox="0 0 24 24">
                      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z" />
                    </svg>
                    <span>Updating round stages...</span>
                  </>
                ) : (
                  <span>
                    Confirm Round Update ({preview.valid_student_ids.length} Qualified Students)
                  </span>
                )}
              </button>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

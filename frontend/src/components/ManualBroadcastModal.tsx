import React, { useState } from 'react';
import { apiClient } from '../services/apiClient';
import type { BroadcastAudience, ManualBroadcastRequest, ManualBroadcastResponse } from '../types/notification';

interface ManualBroadcastModalProps {
  driveId: string;
  driveTitle?: string;
  isOpen: boolean;
  onClose: () => void;
  onSuccess?: (response: ManualBroadcastResponse) => void;
}

export const ManualBroadcastModal: React.FC<ManualBroadcastModalProps> = ({
  driveId,
  driveTitle,
  isOpen,
  onClose,
  onSuccess,
}) => {
  const [audience, setAudience] = useState<BroadcastAudience>('ELIGIBLE');
  const [title, setTitle] = useState('');
  const [body, setBody] = useState('');
  const [step, setStep] = useState<'form' | 'confirm' | 'success'>('form');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [result, setResult] = useState<ManualBroadcastResponse | null>(null);

  if (!isOpen) return null;

  const handleReset = () => {
    setAudience('ELIGIBLE');
    setTitle('');
    setBody('');
    setStep('form');
    setIsSubmitting(false);
    setErrorMessage(null);
    setResult(null);
  };

  const handleClose = () => {
    handleReset();
    onClose();
  };

  const validateForm = (): boolean => {
    const trimmedTitle = title.trim();
    const trimmedBody = body.trim();

    if (!trimmedTitle || trimmedTitle.length < 1 || trimmedTitle.length > 255) {
      setErrorMessage('Title must be between 1 and 255 characters.');
      return false;
    }
    if (!trimmedBody || trimmedBody.length < 1 || trimmedBody.length > 2000) {
      setErrorMessage('Message body must be between 1 and 2000 characters.');
      return false;
    }
    setErrorMessage(null);
    return true;
  };

  const handleProceedToConfirm = (e: React.FormEvent) => {
    e.preventDefault();
    if (validateForm()) {
      setStep('confirm');
    }
  };

  const handleSendBroadcast = async () => {
    setIsSubmitting(true);
    setErrorMessage(null);

    const payload: ManualBroadcastRequest = {
      audience,
      title: title.trim(),
      body: body.trim(),
    };

    try {
      const response = await apiClient.post<ManualBroadcastResponse>(
        `/drives/${driveId}/notify`,
        payload
      );
      setResult(response.data);
      setStep('success');
      if (onSuccess) {
        onSuccess(response.data);
      }
    } catch (err: any) {
      if (err.response?.status === 401) {
        setErrorMessage('Authentication session expired. Please log in again.');
      } else if (err.response?.status === 403) {
        setErrorMessage('You do not have permission to broadcast notifications for this drive.');
      } else if (err.response?.status === 404) {
        setErrorMessage('Placement drive was not found.');
      } else if (err.response?.status === 422) {
        setErrorMessage(
          err.response.data?.detail?.[0]?.msg ||
            'Invalid broadcast data. Please check title and body length.'
        );
      } else {
        setErrorMessage(
          err.response?.data?.detail || 'Failed to dispatch manual broadcast. Please try again.'
        );
      }
      setStep('form');
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div
      className="fixed inset-0 z-50 overflow-y-auto bg-black/60 backdrop-blur-sm flex items-center justify-center p-4"
      role="dialog"
      aria-modal="true"
      aria-labelledby="modal-title"
    >
      <div className="bg-white rounded-2xl shadow-2xl max-w-lg w-full p-6 sm:p-8 transition-all transform animate-fade-in">
        {/* Header */}
        <div className="flex justify-between items-center border-b border-slate-100 pb-4 mb-5">
          <div className="flex items-center space-x-3">
            <div className="w-9 h-9 rounded-xl bg-purple-100 text-purple-700 flex items-center justify-center font-bold">
              <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M11 5.882V19.24a1.76 1.76 0 01-3.417.592l-2.147-6.15M18 13a3 3 0 100-6M5.436 13.683A4.001 4.001 0 017 6h1.832c4.1 0 7.625-1.234 9.168-3v14c-1.543-1.766-5.067-3-9.168-3H7a3.988 3.988 0 01-1.564-.317z" />
              </svg>
            </div>
            <div>
              <h3 id="modal-title" className="text-lg font-bold text-slate-900">
                Manual Notification Broadcast
              </h3>
              {driveTitle && (
                <p className="text-xs text-slate-500 font-mono mt-0.5">
                  Target: <span className="font-semibold text-slate-700">{driveTitle}</span>
                </p>
              )}
            </div>
          </div>
          <button
            onClick={handleClose}
            className="text-slate-400 hover:text-slate-600 rounded-lg p-1 transition"
            aria-label="Close modal"
          >
            <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        {/* Error Alert */}
        {errorMessage && (
          <div className="mb-4 bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-xl text-xs flex items-start space-x-2">
            <svg className="w-4 h-4 text-red-500 flex-shrink-0 mt-0.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            <span>{errorMessage}</span>
          </div>
        )}

        {/* Step 1: Broadcast Form */}
        {step === 'form' && (
          <form onSubmit={handleProceedToConfirm} className="space-y-4">
            <div>
              <label htmlFor="audience-select" className="block text-xs font-bold uppercase tracking-wider text-slate-700 mb-1.5">
                Target Audience
              </label>
              <select
                id="audience-select"
                value={audience}
                onChange={(e) => setAudience(e.target.value as BroadcastAudience)}
                className="w-full border border-slate-300 rounded-xl px-3.5 py-2.5 text-xs sm:text-sm focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-600 outline-none bg-white font-medium shadow-sm transition"
              >
                <option value="ELIGIBLE">Eligible Students (Active & Satisfying Criteria)</option>
                <option value="REGISTERED">Registered Students (Status == REGISTERED)</option>
                <option value="SHORTLISTED">Shortlisted Students (Latest Published Stage)</option>
              </select>
            </div>

            <div>
              <div className="flex justify-between items-center mb-1.5">
                <label htmlFor="broadcast-title" className="block text-xs font-bold uppercase tracking-wider text-slate-700">
                  Broadcast Title
                </label>
                <span className={`text-[10px] font-mono ${title.length > 255 ? 'text-rose-600 font-bold' : 'text-slate-400'}`}>
                  {title.length}/255
                </span>
              </div>
              <input
                id="broadcast-title"
                type="text"
                required
                value={title}
                onChange={(e) => setTitle(e.target.value)}
                placeholder="e.g. PPT Session Schedule Updated"
                maxLength={255}
                className="w-full border border-slate-300 rounded-xl px-3.5 py-2.5 text-xs sm:text-sm focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-600 outline-none shadow-sm transition"
              />
            </div>

            <div>
              <div className="flex justify-between items-center mb-1.5">
                <label htmlFor="broadcast-body" className="block text-xs font-bold uppercase tracking-wider text-slate-700">
                  Message Body
                </label>
                <span className={`text-[10px] font-mono ${body.length > 2000 ? 'text-rose-600 font-bold' : 'text-slate-400'}`}>
                  {body.length}/2000
                </span>
              </div>
              <textarea
                id="broadcast-body"
                required
                rows={4}
                value={body}
                onChange={(e) => setBody(e.target.value)}
                placeholder="Write your broadcast announcement..."
                maxLength={2000}
                className="w-full border border-slate-300 rounded-xl px-3.5 py-2.5 text-xs sm:text-sm focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-600 outline-none resize-none shadow-sm transition"
              />
            </div>

            <div className="flex justify-end space-x-3 pt-4 border-t border-slate-100">
              <button
                type="button"
                onClick={handleClose}
                className="px-4 py-2 text-xs font-bold text-slate-700 bg-slate-100 hover:bg-slate-200 rounded-xl transition"
              >
                Cancel
              </button>
              <button
                type="submit"
                className="px-4 py-2 text-xs font-bold text-white bg-indigo-600 hover:bg-indigo-700 rounded-xl shadow-md shadow-indigo-600/20 transition"
              >
                Review Broadcast
              </button>
            </div>
          </form>
        )}

        {/* Step 2: Confirmation */}
        {step === 'confirm' && (
          <div className="space-y-4">
            <div className="bg-amber-50 border border-amber-200 text-amber-900 rounded-xl p-4 text-xs space-y-1">
              <p className="font-bold">Confirm Notification Broadcast</p>
              <p className="text-amber-700">
                You are about to enqueue an in-app and web push notification to all{' '}
                <span className="font-bold underline">{audience}</span> candidates.
              </p>
            </div>

            <div className="bg-slate-50 rounded-xl p-4 space-y-3 border border-slate-200 text-xs">
              <div>
                <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider block">Audience</span>
                <p className="font-bold text-slate-900 mt-0.5">{audience}</p>
              </div>
              <div>
                <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider block">Title</span>
                <p className="font-bold text-slate-900 mt-0.5">{title}</p>
              </div>
              <div>
                <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider block">Message</span>
                <p className="text-slate-700 mt-0.5 whitespace-pre-wrap">{body}</p>
              </div>
            </div>

            <div className="flex justify-end space-x-3 pt-4 border-t border-slate-100">
              <button
                type="button"
                onClick={() => setStep('form')}
                disabled={isSubmitting}
                className="px-4 py-2 text-xs font-bold text-slate-700 bg-slate-100 hover:bg-slate-200 rounded-xl transition"
              >
                Back
              </button>
              <button
                type="button"
                onClick={handleSendBroadcast}
                disabled={isSubmitting}
                className="px-4 py-2 text-xs font-bold text-white bg-indigo-600 hover:bg-indigo-700 rounded-xl shadow-md shadow-indigo-600/20 transition flex items-center space-x-1.5"
              >
                {isSubmitting ? (
                  <>
                    <div className="w-3.5 h-3.5 border-2 border-white border-t-transparent rounded-full animate-spin" />
                    <span>Dispatching...</span>
                  </>
                ) : (
                  <span>Send Broadcast Now</span>
                )}
              </button>
            </div>
          </div>
        )}

        {/* Step 3: Success State */}
        {step === 'success' && result && (
          <div className="text-center py-4 space-y-4">
            <div className="mx-auto flex items-center justify-center h-12 w-12 rounded-2xl bg-emerald-100 text-emerald-600">
              <svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M5 13l4 4L19 7" />
              </svg>
            </div>
            <div>
              <h4 className="text-lg font-bold text-slate-900">Broadcast Dispatched Successfully</h4>
              <p className="text-xs text-slate-600 mt-1">{result.message}</p>
            </div>
            <div className="bg-emerald-50 border border-emerald-200 rounded-xl p-4 inline-block">
              <span className="text-[10px] text-emerald-800 font-bold uppercase tracking-wider block">Recipients Enqueued</span>
              <p className="text-2xl font-extrabold text-emerald-900 mt-0.5">{result.recipient_count}</p>
            </div>
            <div className="pt-4 border-t border-slate-100">
              <button
                type="button"
                onClick={handleClose}
                className="w-full py-2.5 text-xs font-bold text-white bg-indigo-600 hover:bg-indigo-700 rounded-xl shadow-md shadow-indigo-600/20 transition"
              >
                Done
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

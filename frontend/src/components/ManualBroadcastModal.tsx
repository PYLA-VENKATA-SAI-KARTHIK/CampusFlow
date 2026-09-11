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
      className="fixed inset-0 z-50 overflow-y-auto bg-gray-900 bg-opacity-60 flex items-center justify-center p-4"
      role="dialog"
      aria-modal="true"
      aria-labelledby="modal-title"
    >
      <div className="bg-white rounded-xl shadow-2xl max-w-lg w-full p-6 transition-all transform">
        {/* Header */}
        <div className="flex justify-between items-center border-b pb-4 mb-4">
          <div>
            <h3 id="modal-title" className="text-xl font-bold text-gray-900">
              Manual Notification Broadcast
            </h3>
            {driveTitle && (
              <p className="text-sm text-gray-500 mt-0.5">
                Drive: <span className="font-medium text-gray-700">{driveTitle}</span>
              </p>
            )}
          </div>
          <button
            onClick={handleClose}
            className="text-gray-400 hover:text-gray-600 rounded-lg p-1 text-2xl leading-none font-bold"
            aria-label="Close modal"
          >
            &times;
          </button>
        </div>

        {/* Error Alert */}
        {errorMessage && (
          <div className="mb-4 bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg text-sm">
            <span className="font-semibold">Error: </span>
            {errorMessage}
          </div>
        )}

        {/* Step 1: Broadcast Form */}
        {step === 'form' && (
          <form onSubmit={handleProceedToConfirm} className="space-y-4">
            <div>
              <label htmlFor="audience-select" className="block text-sm font-semibold text-gray-700 mb-1">
                Target Audience
              </label>
              <select
                id="audience-select"
                value={audience}
                onChange={(e) => setAudience(e.target.value as BroadcastAudience)}
                className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-primary-500 focus:border-primary-500 outline-none"
              >
                <option value="ELIGIBLE">Eligible Students (Active & Satisfying Criteria)</option>
                <option value="REGISTERED">Registered Students (Status == REGISTERED)</option>
                <option value="SHORTLISTED">Shortlisted Students (Latest Published Stage)</option>
              </select>
            </div>

            <div>
              <div className="flex justify-between items-center mb-1">
                <label htmlFor="broadcast-title" className="block text-sm font-semibold text-gray-700">
                  Broadcast Title
                </label>
                <span className={`text-xs ${title.length > 255 ? 'text-red-600 font-bold' : 'text-gray-400'}`}>
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
                className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-primary-500 focus:border-primary-500 outline-none"
              />
            </div>

            <div>
              <div className="flex justify-between items-center mb-1">
                <label htmlFor="broadcast-body" className="block text-sm font-semibold text-gray-700">
                  Message Body
                </label>
                <span className={`text-xs ${body.length > 2000 ? 'text-red-600 font-bold' : 'text-gray-400'}`}>
                  {body.length}/2000
                </span>
              </div>
              <textarea
                id="broadcast-body"
                required
                rows={5}
                value={body}
                onChange={(e) => setBody(e.target.value)}
                placeholder="Write your broadcast message here..."
                maxLength={2000}
                className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-primary-500 focus:border-primary-500 outline-none resize-none"
              />
            </div>

            <div className="flex justify-end space-x-3 pt-3 border-t">
              <button
                type="button"
                onClick={handleClose}
                className="px-4 py-2 text-sm font-medium text-gray-700 bg-gray-100 hover:bg-gray-200 rounded-lg"
              >
                Cancel
              </button>
              <button
                type="submit"
                className="px-4 py-2 text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 rounded-lg shadow-sm"
              >
                Review Broadcast
              </button>
            </div>
          </form>
        )}

        {/* Step 2: Confirmation */}
        {step === 'confirm' && (
          <div className="space-y-4">
            <div className="bg-yellow-50 border border-yellow-200 text-yellow-800 rounded-lg p-4 text-sm">
              <p className="font-semibold mb-1">Confirm Notification Broadcast</p>
              <p>
                You are about to enqueue a notification and web push alert to all{' '}
                <span className="font-bold underline">{audience}</span> students for this drive.
              </p>
            </div>

            <div className="bg-gray-50 rounded-lg p-4 space-y-2 border">
              <div>
                <span className="text-xs font-medium text-gray-500 uppercase tracking-wider">Audience</span>
                <p className="text-sm font-semibold text-gray-900">{audience}</p>
              </div>
              <div>
                <span className="text-xs font-medium text-gray-500 uppercase tracking-wider">Title</span>
                <p className="text-sm font-medium text-gray-900">{title}</p>
              </div>
              <div>
                <span className="text-xs font-medium text-gray-500 uppercase tracking-wider">Message</span>
                <p className="text-sm text-gray-700 whitespace-pre-wrap">{body}</p>
              </div>
            </div>

            <div className="flex justify-end space-x-3 pt-3 border-t">
              <button
                type="button"
                onClick={() => setStep('form')}
                disabled={isSubmitting}
                className="px-4 py-2 text-sm font-medium text-gray-700 bg-gray-100 hover:bg-gray-200 rounded-lg"
              >
                Back
              </button>
              <button
                type="button"
                onClick={handleSendBroadcast}
                disabled={isSubmitting}
                className="px-4 py-2 text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 rounded-lg shadow-sm flex items-center"
              >
                {isSubmitting ? (
                  <>
                    <svg className="animate-spin -ml-1 mr-2 h-4 w-4 text-white" fill="none" viewBox="0 0 24 24">
                      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z" />
                    </svg>
                    Dispatching...
                  </>
                ) : (
                  'Send Broadcast Now'
                )}
              </button>
            </div>
          </div>
        )}

        {/* Step 3: Success State */}
        {step === 'success' && result && (
          <div className="text-center py-4 space-y-4">
            <div className="mx-auto flex items-center justify-center h-12 w-12 rounded-full bg-green-100">
              <svg className="h-6 w-6 text-green-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M5 13l4 4L19 7" />
              </svg>
            </div>
            <div>
              <h4 className="text-lg font-bold text-gray-900">Broadcast Dispatched Successfully</h4>
              <p className="text-sm text-gray-600 mt-1">{result.message}</p>
            </div>
            <div className="bg-green-50 border border-green-200 rounded-lg p-3 inline-block">
              <span className="text-xs text-green-800 font-medium">Recipients Enqueued</span>
              <p className="text-2xl font-bold text-green-900">{result.recipient_count}</p>
            </div>
            <div className="pt-3 border-t">
              <button
                type="button"
                onClick={handleClose}
                className="w-full px-4 py-2 text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 rounded-lg shadow-sm"
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

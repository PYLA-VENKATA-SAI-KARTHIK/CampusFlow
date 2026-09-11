import React, { useState } from 'react';
import { useAuthStore } from '../store/authStore';
import { ManualBroadcastModal } from '../components/ManualBroadcastModal';

export const DashboardPage = () => {
  const { user } = useAuthStore();
  const isOfficerOrAdmin = user?.role === 'OFFICER' || user?.role === 'ADMIN';

  const [isBroadcastModalOpen, setIsBroadcastModalOpen] = useState(false);
  const [selectedDriveId, setSelectedDriveId] = useState('');
  const [selectedDriveTitle, setSelectedDriveTitle] = useState('');
  const [inputDriveId, setInputDriveId] = useState('');

  const handleOpenBroadcastModal = (e: React.FormEvent) => {
    e.preventDefault();
    if (inputDriveId.trim()) {
      setSelectedDriveId(inputDriveId.trim());
      setSelectedDriveTitle(`Drive ID: ${inputDriveId.trim()}`);
      setIsBroadcastModalOpen(true);
    }
  };

  return (
    <div className="space-y-6">
      <div className="bg-white shadow overflow-hidden sm:rounded-lg">
        <div className="px-4 py-5 sm:px-6">
          <h3 className="text-lg leading-6 font-medium text-gray-900">
            Welcome to CampusFlow
          </h3>
          <p className="mt-1 max-w-2xl text-sm text-gray-500">
            You are successfully logged in.
          </p>
        </div>
        <div className="border-t border-gray-200 px-4 py-5 sm:p-0">
          <dl className="sm:divide-y sm:divide-gray-200">
            <div className="py-4 sm:py-5 sm:grid sm:grid-cols-3 sm:gap-4 sm:px-6">
              <dt className="text-sm font-medium text-gray-500">Full name</dt>
              <dd className="mt-1 text-sm text-gray-900 sm:mt-0 sm:col-span-2">
                {user?.full_name}
              </dd>
            </div>
            <div className="py-4 sm:py-5 sm:grid sm:grid-cols-3 sm:gap-4 sm:px-6">
              <dt className="text-sm font-medium text-gray-500">Email address</dt>
              <dd className="mt-1 text-sm text-gray-900 sm:mt-0 sm:col-span-2">
                {user?.email}
              </dd>
            </div>
            <div className="py-4 sm:py-5 sm:grid sm:grid-cols-3 sm:gap-4 sm:px-6">
              <dt className="text-sm font-medium text-gray-500">Role</dt>
              <dd className="mt-1 text-sm text-gray-900 sm:mt-0 sm:col-span-2">
                <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
                  {user?.role}
                </span>
              </dd>
            </div>
          </dl>
        </div>
      </div>

      {/* Officer/Admin Manual Broadcast Section */}
      {isOfficerOrAdmin && (
        <div className="bg-white shadow rounded-lg p-6 border border-gray-200">
          <div className="flex items-center justify-between pb-4 border-b border-gray-200 mb-4">
            <div>
              <h4 className="text-base font-bold text-gray-900">
                Drive Manual Broadcast Management
              </h4>
              <p className="text-xs text-gray-500 mt-0.5">
                Send targeted in-app and browser push notifications to eligible, registered, or shortlisted students.
              </p>
            </div>
            <span className="text-xs bg-purple-100 text-purple-800 font-semibold px-2.5 py-1 rounded">
              Placement Officer Tool
            </span>
          </div>

          <form onSubmit={handleOpenBroadcastModal} className="flex flex-col sm:flex-row gap-3">
            <div className="flex-1">
              <label htmlFor="drive-id-input" className="sr-only">Drive UUID</label>
              <input
                id="drive-id-input"
                type="text"
                placeholder="Enter Placement Drive UUID (e.g. 550e8400-e29b-41d4-a716-446655440000)"
                value={inputDriveId}
                onChange={(e) => setInputDriveId(e.target.value)}
                className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
              />
            </div>
            <button
              type="submit"
              disabled={!inputDriveId.trim()}
              className="px-4 py-2 bg-blue-600 hover:bg-blue-700 disabled:opacity-50 text-white text-sm font-semibold rounded-lg shadow-sm whitespace-nowrap"
            >
              Compose Broadcast
            </button>
          </form>

          {selectedDriveId && (
            <ManualBroadcastModal
              isOpen={isBroadcastModalOpen}
              driveId={selectedDriveId}
              driveTitle={selectedDriveTitle}
              onClose={() => setIsBroadcastModalOpen(false)}
            />
          )}
        </div>
      )}
    </div>
  );
};


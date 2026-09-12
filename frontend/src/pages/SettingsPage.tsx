import React from 'react';
import { useAuthStore } from '../store/authStore';
import { PushNotificationOptIn } from '../components/PushNotificationOptIn';

export const SettingsPage: React.FC = () => {
  const { user } = useAuthStore();

  return (
    <div className="space-y-8 animate-fade-in max-w-4xl mx-auto">
      {/* PAGE HEADER */}
      <div className="border-b border-slate-200 pb-5">
        <h1 className="text-2xl font-extrabold text-slate-900 tracking-tight">
          Account & Workspace Settings
        </h1>
        <p className="text-sm text-slate-500 mt-1">
          Review your institutional account identity, security session parameters, and notification channels.
        </p>
      </div>

      <div className="space-y-6">
        {/* SECTION 1: ACCOUNT DETAILS */}
        <div className="bg-white rounded-2xl border border-slate-200/90 shadow-sm overflow-hidden">
          <div className="px-6 py-4 border-b border-slate-100 bg-slate-50/50">
            <h2 className="text-base font-bold text-slate-900">Account Identity</h2>
            <p className="text-xs text-slate-500">Institutional credentials and role assignment</p>
          </div>

          <div className="p-6">
            <dl className="grid grid-cols-1 sm:grid-cols-2 gap-5">
              <div className="p-4 rounded-xl bg-slate-50 border border-slate-200/60">
                <dt className="text-xs font-semibold uppercase tracking-wider text-slate-500 mb-1">Full Name</dt>
                <dd className="text-sm font-bold text-slate-900">{user?.full_name}</dd>
              </div>

              <div className="p-4 rounded-xl bg-slate-50 border border-slate-200/60">
                <dt className="text-xs font-semibold uppercase tracking-wider text-slate-500 mb-1">University Email</dt>
                <dd className="text-sm font-bold text-slate-900 font-mono">{user?.email}</dd>
              </div>

              <div className="p-4 rounded-xl bg-slate-50 border border-slate-200/60">
                <dt className="text-xs font-semibold uppercase tracking-wider text-slate-500 mb-1">System Role</dt>
                <dd className="text-sm font-bold text-indigo-700 flex items-center space-x-2">
                  <span>{user?.role}</span>
                  <span className="text-xs text-emerald-600 font-semibold">(Active)</span>
                </dd>
              </div>

              <div className="p-4 rounded-xl bg-slate-50 border border-slate-200/60">
                <dt className="text-xs font-semibold uppercase tracking-wider text-slate-500 mb-1">User Identifier</dt>
                <dd className="text-xs font-bold text-slate-700 font-mono truncate">{user?.id}</dd>
              </div>
            </dl>
          </div>
        </div>

        {/* SECTION 2: NOTIFICATION & WEB PUSH PREFERENCES */}
        <div className="bg-white rounded-2xl border border-slate-200/90 shadow-sm overflow-hidden">
          <div className="px-6 py-4 border-b border-slate-100 bg-slate-50/50">
            <h2 className="text-base font-bold text-slate-900">Real-Time Notifications & Push Opt-in</h2>
            <p className="text-xs text-slate-500">Browser push notification delivery preferences</p>
          </div>

          <div className="p-6 space-y-4">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 p-4 rounded-xl bg-slate-50 border border-slate-200/60">
              <div>
                <div className="text-xs font-bold text-slate-900">Browser Web Push Subscriptions</div>
                <div className="text-xs text-slate-500 mt-0.5">
                  Receive instant drive announcements, interview callups, and shortlist alerts on this device.
                </div>
              </div>
              <div className="self-start sm:self-auto">
                <PushNotificationOptIn />
              </div>
            </div>
          </div>
        </div>

        {/* SECTION 3: SECURITY & SESSION INFORMATION */}
        <div className="bg-white rounded-2xl border border-slate-200/90 shadow-sm overflow-hidden">
          <div className="px-6 py-4 border-b border-slate-100 bg-slate-50/50">
            <h2 className="text-base font-bold text-slate-900">Security & Session Parameters</h2>
            <p className="text-xs text-slate-500">Cryptographic tokens and role enforcement details</p>
          </div>

          <div className="p-6 space-y-3 text-xs text-slate-600">
            <div className="flex items-center justify-between py-2 border-b border-slate-100">
              <span className="font-medium text-slate-700">Authentication Protocol</span>
              <span className="font-semibold text-slate-900">RS256 Asymmetric JWT with JWKS</span>
            </div>
            <div className="flex items-center justify-between py-2 border-b border-slate-100">
              <span className="font-medium text-slate-700">Access Token Lifespan</span>
              <span className="font-semibold text-slate-900">15 Minutes (Auto-Refreshed)</span>
            </div>
            <div className="flex items-center justify-between py-2 border-b border-slate-100">
              <span className="font-medium text-slate-700">Refresh Token Lifespan</span>
              <span className="font-semibold text-slate-900">7 Days</span>
            </div>
            <div className="flex items-center justify-between py-2">
              <span className="font-medium text-slate-700">Session Storage Mechanism</span>
              <span className="font-semibold text-emerald-700">Client Encrypted Local Storage</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

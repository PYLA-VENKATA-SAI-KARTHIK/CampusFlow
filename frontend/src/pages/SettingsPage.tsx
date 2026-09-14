import React from 'react';
import { useAuthStore } from '../store/authStore';
import { PushNotificationOptIn } from '../components/PushNotificationOptIn';
import {
  PageHeader,
  Card,
  CardHeader,
  CardTitle,
  CardDescription,
  CardContent,
  Badge,
} from '../components/ui';

export const SettingsPage: React.FC = () => {
  const { user } = useAuthStore();

  return (
    <div className="space-y-8 animate-fade-in max-w-4xl mx-auto pb-12">
      {/* PAGE HEADER */}
      <PageHeader
        eyebrow="Account & Preferences"
        title="Account & Workspace Settings"
        description="Review your institutional account identity, security session parameters, and notification channels."
      />

      <div className="space-y-6">
        {/* SECTION 1: ACCOUNT DETAILS */}
        <Card>
          <CardHeader>
            <CardTitle>Account Identity</CardTitle>
            <CardDescription>Institutional credentials and role assignment</CardDescription>
          </CardHeader>

          <CardContent>
            <dl className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div className="p-4 rounded-xl bg-slate-50 border border-slate-200/70 shadow-xs">
                <dt className="text-xs font-bold uppercase tracking-wider text-slate-500 mb-1">Full Name</dt>
                <dd className="text-sm font-bold text-slate-900">{user?.full_name}</dd>
              </div>

              <div className="p-4 rounded-xl bg-slate-50 border border-slate-200/70 shadow-xs">
                <dt className="text-xs font-bold uppercase tracking-wider text-slate-500 mb-1">University Email</dt>
                <dd className="text-sm font-bold text-slate-900 font-mono">{user?.email}</dd>
              </div>

              <div className="p-4 rounded-xl bg-slate-50 border border-slate-200/70 shadow-xs">
                <dt className="text-xs font-bold uppercase tracking-wider text-slate-500 mb-1">System Role</dt>
                <dd className="text-sm font-bold text-indigo-700 flex items-center space-x-2">
                  <span>{user?.role}</span>
                  <Badge variant="success" size="sm" dot>
                    Active
                  </Badge>
                </dd>
              </div>

              <div className="p-4 rounded-xl bg-slate-50 border border-slate-200/70 shadow-xs">
                <dt className="text-xs font-bold uppercase tracking-wider text-slate-500 mb-1">User Identifier</dt>
                <dd className="text-xs font-bold text-slate-700 font-mono truncate">{user?.id}</dd>
              </div>
            </dl>
          </CardContent>
        </Card>

        {/* SECTION 2: NOTIFICATION & WEB PUSH PREFERENCES */}
        <Card>
          <CardHeader>
            <CardTitle>Real-Time Notifications & Push Opt-in</CardTitle>
            <CardDescription>Browser push notification delivery preferences</CardDescription>
          </CardHeader>

          <CardContent className="space-y-4">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 p-4 rounded-xl bg-slate-50 border border-slate-200/70 shadow-xs">
              <div className="min-w-0 flex-1">
                <div className="text-xs font-bold text-slate-900">Browser Web Push Subscriptions</div>
                <div className="text-xs text-slate-500 mt-1 leading-relaxed">
                  Receive instant drive announcements, interview callups, and shortlist alerts on this device.
                </div>
              </div>
              <div className="shrink-0 self-start sm:self-auto">
                <PushNotificationOptIn />
              </div>
            </div>
          </CardContent>
        </Card>

        {/* SECTION 3: SECURITY & SESSION INFORMATION */}
        <Card>
          <CardHeader>
            <CardTitle>Security & Session Parameters</CardTitle>
            <CardDescription>Cryptographic tokens and role enforcement details</CardDescription>
          </CardHeader>

          <CardContent>
            <div className="divide-y divide-slate-100 text-xs text-slate-600">
              <div className="flex items-center justify-between py-2.5">
                <span className="font-medium text-slate-700">Authentication Protocol</span>
                <span className="font-semibold text-slate-900 font-mono">RS256 Asymmetric JWT with JWKS</span>
              </div>
              <div className="flex items-center justify-between py-2.5">
                <span className="font-medium text-slate-700">Access Token Lifespan</span>
                <span className="font-semibold text-slate-900">15 Minutes (Auto-Refreshed)</span>
              </div>
              <div className="flex items-center justify-between py-2.5">
                <span className="font-medium text-slate-700">Refresh Token Lifespan</span>
                <span className="font-semibold text-slate-900">7 Days</span>
              </div>
              <div className="flex items-center justify-between py-2.5">
                <span className="font-medium text-slate-700">Session Storage Mechanism</span>
                <span className="font-semibold text-emerald-700">Client Encrypted Local Storage</span>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
};


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

        {/* SECTION 2: PLACEMENT OFFICERS & HELPDESK DIRECTORY */}
        <Card className="border-indigo-100/80 shadow-md overflow-hidden">
          <CardHeader className="bg-linear-to-r from-indigo-50/70 via-teal-50/40 to-white border-b border-indigo-100/60 pb-4">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
              <div>
                <div className="flex items-center gap-2">
                  <span className="p-1.5 rounded-lg bg-indigo-600 text-white shadow-xs">
                    <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M3 5a2 2 0 012-2h3.28a1 1 0 01.948.684l1.498 4.493a1 1 0 01-.502 1.21l-2.257 1.13a11.042 11.042 0 005.516 5.516l1.13-2.257a1 1 0 011.21-.502l4.493 1.498a1 1 0 01.684.949V19a2 2 0 01-2 2h-1C9.716 21 3 14.284 3 6V5z" />
                    </svg>
                  </span>
                  <CardTitle className="text-slate-900">Placement Officers & Emergency Contact Directory</CardTitle>
                </div>
                <CardDescription className="mt-1">
                  Contact our designated placement officers and coordinators for any recruitment, interview, drive scheduling, or student query escalations.
                </CardDescription>
              </div>
              <Badge variant="primary" size="sm" className="self-start sm:self-auto font-medium">
                Official Helpdesk
              </Badge>
            </div>
          </CardHeader>

          <CardContent className="pt-5 space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {/* Officer 1: Mr. Dhilipanrajkumar */}
              <div className="p-4 rounded-xl border border-indigo-200/80 bg-linear-to-br from-indigo-50/50 to-white relative group hover:border-indigo-300 transition shadow-xs">
                <div className="flex items-start justify-between">
                  <div className="flex items-center space-x-3">
                    <div className="w-10 h-10 rounded-xl bg-indigo-600 text-white font-bold flex items-center justify-center text-sm shadow-xs">
                      DR
                    </div>
                    <div>
                      <div className="text-sm font-bold text-slate-900 flex items-center gap-1.5">
                        Mr. Dhilipanrajkumar
                        <Badge variant="success" size="sm" dot>Officer</Badge>
                      </div>
                      <div className="text-xs text-indigo-700 font-medium">Placement Officer</div>
                    </div>
                  </div>
                </div>
                <div className="mt-3.5 pt-3 border-t border-indigo-100 flex flex-col gap-2 text-xs">
                  <div className="flex items-center justify-between text-slate-600">
                    <span className="flex items-center gap-1.5 font-medium text-slate-500">
                      <svg className="w-3.5 h-3.5 text-slate-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
                      </svg>
                      Email:
                    </span>
                    <a
                      href="mailto:dhilipanrajkumar@gmail.com"
                      className="font-mono text-indigo-600 hover:text-indigo-800 font-semibold hover:underline"
                    >
                      dhilipanrajkumar@gmail.com
                    </a>
                  </div>
                </div>
              </div>

              {/* Officer 2: Dr. Alavudeen */}
              <div className="p-4 rounded-xl border border-slate-200 bg-white hover:border-teal-300 hover:shadow-xs transition group">
                <div className="flex items-start justify-between">
                  <div className="flex items-center space-x-3">
                    <div className="w-10 h-10 rounded-xl bg-teal-600 text-white font-bold flex items-center justify-center text-sm shadow-xs">
                      DA
                    </div>
                    <div>
                      <div className="text-sm font-bold text-slate-900">Dr. Alavudeen</div>
                      <div className="text-xs text-teal-700 font-medium">Placement Office & Lead</div>
                    </div>
                  </div>
                </div>
                <div className="mt-3.5 pt-3 border-t border-slate-100 flex items-center justify-between text-xs">
                  <span className="flex items-center gap-1.5 font-medium text-slate-500">
                    <svg className="w-3.5 h-3.5 text-emerald-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M3 5a2 2 0 012-2h3.28a1 1 0 01.948.684l1.498 4.493a1 1 0 01-.502 1.21l-2.257 1.13a11.042 11.042 0 005.516 5.516l1.13-2.257a1 1 0 011.21-.502l4.493 1.498a1 1 0 01.684.949V19a2 2 0 01-2 2h-1C9.716 21 3 14.284 3 6V5z" />
                    </svg>
                    Mobile:
                  </span>
                  <a
                    href="tel:+919443389276"
                    className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-lg bg-emerald-50 text-emerald-700 font-mono font-bold hover:bg-emerald-100 transition border border-emerald-200/60"
                  >
                    +91 94433 89276
                  </a>
                </div>
              </div>

              {/* Officer 3: Mr. Manivannan */}
              <div className="p-4 rounded-xl border border-slate-200 bg-white hover:border-teal-300 hover:shadow-xs transition group">
                <div className="flex items-start justify-between">
                  <div className="flex items-center space-x-3">
                    <div className="w-10 h-10 rounded-xl bg-blue-600 text-white font-bold flex items-center justify-center text-sm shadow-xs">
                      MV
                    </div>
                    <div>
                      <div className="text-sm font-bold text-slate-900">Mr. Manivannan</div>
                      <div className="text-xs text-blue-700 font-medium">Placement Coordinator</div>
                    </div>
                  </div>
                </div>
                <div className="mt-3.5 pt-3 border-t border-slate-100 flex items-center justify-between text-xs">
                  <span className="flex items-center gap-1.5 font-medium text-slate-500">
                    <svg className="w-3.5 h-3.5 text-emerald-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M3 5a2 2 0 012-2h3.28a1 1 0 01.948.684l1.498 4.493a1 1 0 01-.502 1.21l-2.257 1.13a11.042 11.042 0 005.516 5.516l1.13-2.257a1 1 0 011.21-.502l4.493 1.498a1 1 0 01.684.949V19a2 2 0 01-2 2h-1C9.716 21 3 14.284 3 6V5z" />
                    </svg>
                    Mobile:
                  </span>
                  <a
                    href="tel:+918610726834"
                    className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-lg bg-emerald-50 text-emerald-700 font-mono font-bold hover:bg-emerald-100 transition border border-emerald-200/60"
                  >
                    +91 861 072 6834
                  </a>
                </div>
              </div>

              {/* Officer 4: Mr. Velmurugan */}
              <div className="p-4 rounded-xl border border-slate-200 bg-white hover:border-teal-300 hover:shadow-xs transition group">
                <div className="flex items-start justify-between">
                  <div className="flex items-center space-x-3">
                    <div className="w-10 h-10 rounded-xl bg-purple-600 text-white font-bold flex items-center justify-center text-sm shadow-xs">
                      VM
                    </div>
                    <div>
                      <div className="text-sm font-bold text-slate-900">Mr. Velmurugan</div>
                      <div className="text-xs text-purple-700 font-medium">Placement Coordinator</div>
                    </div>
                  </div>
                </div>
                <div className="mt-3.5 pt-3 border-t border-slate-100 flex items-center justify-between text-xs">
                  <span className="flex items-center gap-1.5 font-medium text-slate-500">
                    <svg className="w-3.5 h-3.5 text-emerald-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M3 5a2 2 0 012-2h3.28a1 1 0 01.948.684l1.498 4.493a1 1 0 01-.502 1.21l-2.257 1.13a11.042 11.042 0 005.516 5.516l1.13-2.257a1 1 0 011.21-.502l4.493 1.498a1 1 0 01.684.949V19a2 2 0 01-2 2h-1C9.716 21 3 14.284 3 6V5z" />
                    </svg>
                    Mobile:
                  </span>
                  <a
                    href="tel:+919488335060"
                    className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-lg bg-emerald-50 text-emerald-700 font-mono font-bold hover:bg-emerald-100 transition border border-emerald-200/60"
                  >
                    +91 94883 35060
                  </a>
                </div>
              </div>
            </div>

            <div className="p-3.5 rounded-xl bg-amber-50/80 border border-amber-200 text-xs text-amber-900 flex items-start gap-2.5">
              <svg className="w-4 h-4 text-amber-600 shrink-0 mt-0.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              <span>
                <strong>Support Guidelines:</strong> In case of urgent placement drive issues, shortlisting disputes, or interview scheduling clashes, please contact the respective placement coordinators during office hours (8:30 AM – 5:30 PM).
              </span>
            </div>
          </CardContent>
        </Card>

        {/* SECTION 3: NOTIFICATION & WEB PUSH PREFERENCES */}
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

        {/* SECTION 4: SECURITY & SESSION INFORMATION */}
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


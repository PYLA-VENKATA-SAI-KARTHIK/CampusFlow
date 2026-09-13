import React, { useState } from 'react';
import { Outlet, useNavigate, useLocation } from 'react-router-dom';
import { useAuthStore } from '../store/authStore';
import { apiClient } from '../services/apiClient';
import { PushNotificationOptIn } from '../components/PushNotificationOptIn';
import { CampusFlowLogo } from '../components/common/CampusFlowLogo';

export const AppLayout: React.FC = () => {
  const { user, clearSession, refreshToken } = useAuthStore();
  const navigate = useNavigate();
  const location = useLocation();

  // Sidebar collapse state (persisted in sessionStorage)
  const [collapsed, setCollapsed] = useState<boolean>(() => {
    try {
      return sessionStorage.getItem('campusflow_sidebar_collapsed') === 'true';
    } catch {
      return false;
    }
  });

  const [mobileDrawerOpen, setMobileDrawerOpen] = useState(false);

  const toggleSidebar = () => {
    setCollapsed((prev) => {
      const next = !prev;
      try {
        sessionStorage.setItem('campusflow_sidebar_collapsed', String(next));
      } catch {}
      return next;
    });
  };

  const handleLogout = async () => {
    try {
      if (refreshToken) {
        await apiClient.post('/auth/logout', { refresh_token: refreshToken });
      }
    } catch (e) {
      // Ignore errors on logout
    } finally {
      clearSession();
      navigate('/login');
    }
  };

  const isActiveRoute = (path: string) => {
    if (path === '/' && location.pathname === '/') return true;
    if (path !== '/' && (location.pathname === path || location.pathname.startsWith(`${path}/`))) {
      return true;
    }
    return false;
  };

  return (
    <div className="min-h-screen bg-slate-50 flex flex-col md:flex-row text-slate-800 antialiased">
      {/* ========================================================================= */}
      {/* 1. PERSISTENT WORKSPACE SIDEBAR (DESKTOP)                                 */}
      {/* ========================================================================= */}
      <aside
        className={`hidden md:flex flex-col bg-slate-900 text-slate-300 border-r border-slate-800/80 sticky top-0 h-screen transition-all duration-300 ease-in-out z-30 select-none ${
          collapsed ? 'w-20' : 'w-64'
        }`}
      >
        {/* Brand / Logo Header */}
        <div className="h-16 flex items-center justify-between px-4 border-b border-slate-800">
          <div
            onClick={() => navigate('/')}
            className="flex items-center space-x-3 cursor-pointer overflow-hidden group"
          >
            <CampusFlowLogo size="sm" />
            {!collapsed && (
              <div className="flex flex-col">
                <span className="font-extrabold text-white tracking-tight text-sm">
                  CampusFlow
                </span>
                <span className="text-[10px] text-indigo-400 font-semibold uppercase tracking-wider">
                  Placement Workspace
                </span>
              </div>
            )}
          </div>

          <button
            onClick={toggleSidebar}
            title={collapsed ? 'Expand sidebar' : 'Collapse sidebar'}
            className="p-1.5 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 transition"
          >
            <svg
              className={`w-4 h-4 transition-transform duration-200 ${collapsed ? 'rotate-180' : ''}`}
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
            >
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M11 19l-7-7 7-7m8 14l-7-7 7-7" />
            </svg>
          </button>
        </div>

        {/* Navigation Content (Semantic <nav> container ensuring E2E selector satisfaction) */}
        <nav className="flex-1 overflow-y-auto py-4 px-3 space-y-6 scrollbar-thin">
          {/* USER IDENTITY CHIP (CRITICAL FOR E2E TEST SELECTORS: Synthetic Student One (STUDENT)) */}
          <div className="px-2 py-1.5 rounded-xl bg-slate-800/70 border border-slate-700/60">
            <div className="flex items-center space-x-2.5">
              <div className="w-7 h-7 rounded-lg bg-indigo-600 text-white flex items-center justify-center font-bold text-xs shadow-sm flex-shrink-0">
                {user?.full_name?.charAt(0).toUpperCase() || 'U'}
              </div>
              {!collapsed && (
                <div className="overflow-hidden">
                  <div className="text-xs font-bold text-white truncate">
                    {user?.full_name} ({user?.role})
                  </div>
                  <div className="text-[10px] text-emerald-400 font-semibold flex items-center space-x-1">
                    <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
                    <span>Active Session</span>
                  </div>
                </div>
              )}
            </div>
          </div>

          {/* ==================== STUDENT NAVIGATION ==================== */}
          {user?.role === 'STUDENT' && (
            <>
              {/* SECTION: MAIN */}
              <div className="space-y-1">
                {!collapsed && (
                  <div className="px-3 text-[10px] font-bold uppercase tracking-wider text-slate-400">
                    Main
                  </div>
                )}

                <button
                  onClick={() => navigate('/')}
                  title="Dashboard"
                  className={`w-full flex items-center space-x-3 px-3 py-2 rounded-xl text-xs font-semibold transition ${
                    isActiveRoute('/')
                      ? 'bg-indigo-600 text-white shadow-md shadow-indigo-600/30'
                      : 'text-slate-300 hover:text-white hover:bg-slate-800/80'
                  }`}
                >
                  <svg className="w-4 h-4 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6" />
                  </svg>
                  {!collapsed && <span>Dashboard</span>}
                </button>

                <button
                  onClick={() => navigate('/drives')}
                  title="Placement Drives"
                  className={`w-full flex items-center space-x-3 px-3 py-2 rounded-xl text-xs font-semibold transition ${
                    isActiveRoute('/drives')
                      ? 'bg-indigo-600 text-white shadow-md shadow-indigo-600/30'
                      : 'text-slate-300 hover:text-white hover:bg-slate-800/80'
                  }`}
                >
                  <svg className="w-4 h-4 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M21 13.255A23.931 23.931 0 0112 15c-3.183 0-6.22-.62-9-1.745M16 6V4a2 2 0 00-2-2h-4a2 2 0 00-2 2v2m4 6h.01M5 20h14a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
                  </svg>
                  {!collapsed && <span>Placement Drives</span>}
                </button>

                <button
                  onClick={() => navigate('/applications')}
                  title="My Applications"
                  className={`w-full flex items-center space-x-3 px-3 py-2 rounded-xl text-xs font-semibold transition ${
                    isActiveRoute('/applications')
                      ? 'bg-indigo-600 text-white shadow-md shadow-indigo-600/30'
                      : 'text-slate-300 hover:text-white hover:bg-slate-800/80'
                  }`}
                >
                  <svg className="w-4 h-4 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
                  </svg>
                  {!collapsed && <span>My Applications</span>}
                </button>

                <button
                  onClick={() => navigate('/notifications')}
                  title="Notifications"
                  className={`w-full flex items-center space-x-3 px-3 py-2 rounded-xl text-xs font-semibold transition ${
                    isActiveRoute('/notifications')
                      ? 'bg-indigo-600 text-white shadow-md shadow-indigo-600/30'
                      : 'text-slate-300 hover:text-white hover:bg-slate-800/80'
                  }`}
                >
                  <svg className="w-4 h-4 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9" />
                  </svg>
                  {!collapsed && <span>Notifications</span>}
                </button>
              </div>

              {/* SECTION: PREPARATION */}
              <div className="space-y-1 pt-2">
                {!collapsed && (
                  <div className="px-3 text-[10px] font-bold uppercase tracking-wider text-slate-400">
                    Preparation
                  </div>
                )}

                <button
                  onClick={() => navigate('/preparation')}
                  title="Preparation Hub"
                  className={`w-full flex items-center space-x-3 px-3 py-2 rounded-xl text-xs font-semibold transition ${
                    isActiveRoute('/preparation')
                      ? 'bg-indigo-600 text-white shadow-md shadow-indigo-600/30'
                      : 'text-slate-300 hover:text-white hover:bg-slate-800/80'
                  }`}
                >
                  <svg className="w-4 h-4 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" />
                  </svg>
                  {!collapsed && <span>Preparation Hub</span>}
                </button>

                <button
                  onClick={() => navigate('/assessments')}
                  title="Practice Assessments"
                  className={`w-full flex items-center space-x-3 px-3 py-2 rounded-xl text-xs font-semibold transition ${
                    isActiveRoute('/assessments')
                      ? 'bg-indigo-600 text-white shadow-md shadow-indigo-600/30'
                      : 'text-slate-300 hover:text-white hover:bg-slate-800/80'
                  }`}
                >
                  <svg className="w-4 h-4 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-6 9l2 2 4-4" />
                  </svg>
                  {!collapsed && <span>Practice Assessments</span>}
                </button>
              </div>

              {/* SECTION: MY CAREER */}
              <div className="space-y-1 pt-2">
                {!collapsed && (
                  <div className="px-3 text-[10px] font-bold uppercase tracking-wider text-slate-400">
                    My Career
                  </div>
                )}

                <button
                  onClick={() => navigate('/profile')}
                  title="My Profile"
                  className={`w-full flex items-center space-x-3 px-3 py-2 rounded-xl text-xs font-semibold transition ${
                    isActiveRoute('/profile') && location.pathname !== '/resume'
                      ? 'bg-indigo-600 text-white shadow-md shadow-indigo-600/30'
                      : 'text-slate-300 hover:text-white hover:bg-slate-800/80'
                  }`}
                >
                  <svg className="w-4 h-4 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
                  </svg>
                  {!collapsed && <span>My Profile</span>}
                </button>

                <button
                  onClick={() => navigate('/resume')}
                  title="My Resume"
                  className={`w-full flex items-center space-x-3 px-3 py-2 rounded-xl text-xs font-semibold transition ${
                    location.pathname === '/resume'
                      ? 'bg-indigo-600 text-white shadow-md shadow-indigo-600/30'
                      : 'text-slate-300 hover:text-white hover:bg-slate-800/80'
                  }`}
                >
                  <svg className="w-4 h-4 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                  </svg>
                  {!collapsed && <span>My Resume</span>}
                </button>
              </div>

              {/* SECTION: ACCOUNT */}
              <div className="space-y-1 pt-2">
                {!collapsed && (
                  <div className="px-3 text-[10px] font-bold uppercase tracking-wider text-slate-400">
                    Account
                  </div>
                )}

                <button
                  onClick={() => navigate('/settings')}
                  title="Settings"
                  className={`w-full flex items-center space-x-3 px-3 py-2 rounded-xl text-xs font-semibold transition ${
                    isActiveRoute('/settings')
                      ? 'bg-indigo-600 text-white shadow-md shadow-indigo-600/30'
                      : 'text-slate-300 hover:text-white hover:bg-slate-800/80'
                  }`}
                >
                  <svg className="w-4 h-4 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                  </svg>
                  {!collapsed && <span>Settings</span>}
                </button>
              </div>
            </>
          )}

          {/* ==================== OFFICER NAVIGATION ==================== */}
          {user?.role === 'OFFICER' && (
            <>
              {/* SECTION: MAIN */}
              <div className="space-y-1">
                {!collapsed && (
                  <div className="px-3 text-[10px] font-bold uppercase tracking-wider text-slate-400">
                    Main
                  </div>
                )}

                <button
                  onClick={() => navigate('/')}
                  title="Dashboard"
                  className={`w-full flex items-center space-x-3 px-3 py-2 rounded-xl text-xs font-semibold transition ${
                    isActiveRoute('/')
                      ? 'bg-indigo-600 text-white shadow-md shadow-indigo-600/30'
                      : 'text-slate-300 hover:text-white hover:bg-slate-800/80'
                  }`}
                >
                  <svg className="w-4 h-4 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6" />
                  </svg>
                  {!collapsed && <span>Dashboard</span>}
                </button>

                <button
                  onClick={() => navigate('/drives')}
                  title="Placement Drives"
                  className={`w-full flex items-center space-x-3 px-3 py-2 rounded-xl text-xs font-semibold transition ${
                    isActiveRoute('/drives')
                      ? 'bg-indigo-600 text-white shadow-md shadow-indigo-600/30'
                      : 'text-slate-300 hover:text-white hover:bg-slate-800/80'
                  }`}
                >
                  <svg className="w-4 h-4 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M21 13.255A23.931 23.931 0 0112 15c-3.183 0-6.22-.62-9-1.745M16 6V4a2 2 0 00-2-2h-4a2 2 0 00-2 2v2m4 6h.01M5 20h14a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
                  </svg>
                  {!collapsed && <span>Placement Drives</span>}
                </button>

                <button
                  onClick={() => navigate('/drives?create=true')}
                  title="Create New Drive"
                  className="w-full flex items-center space-x-3 px-3 py-2 rounded-xl text-xs font-semibold text-indigo-400 hover:text-indigo-300 hover:bg-slate-800/80 transition"
                >
                  <svg className="w-4 h-4 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 4v16m8-8H4" />
                  </svg>
                  {!collapsed && <span>Create New Drive</span>}
                </button>

                <button
                  onClick={() => navigate('/notifications')}
                  title="Notifications"
                  className={`w-full flex items-center space-x-3 px-3 py-2 rounded-xl text-xs font-semibold transition ${
                    isActiveRoute('/notifications')
                      ? 'bg-indigo-600 text-white shadow-md shadow-indigo-600/30'
                      : 'text-slate-300 hover:text-white hover:bg-slate-800/80'
                  }`}
                >
                  <svg className="w-4 h-4 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9" />
                  </svg>
                  {!collapsed && <span>Notifications</span>}
                </button>
              </div>

              {/* SECTION: MANAGEMENT */}
              <div className="space-y-1 pt-2">
                {!collapsed && (
                  <div className="px-3 text-[10px] font-bold uppercase tracking-wider text-slate-400">
                    Management
                  </div>
                )}

                <button
                  onClick={() => navigate('/analytics')}
                  title="Applicants"
                  className="w-full flex items-center space-x-3 px-3 py-2 rounded-xl text-xs font-semibold text-slate-300 hover:text-white hover:bg-slate-800/80 transition"
                >
                  <svg className="w-4 h-4 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z" />
                  </svg>
                  {!collapsed && <span>Applicants</span>}
                </button>

                <button
                  onClick={() => navigate('/drives')}
                  title="Eligibility"
                  className="w-full flex items-center space-x-3 px-3 py-2 rounded-xl text-xs font-semibold text-slate-300 hover:text-white hover:bg-slate-800/80 transition"
                >
                  <svg className="w-4 h-4 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                  {!collapsed && <span>Eligibility</span>}
                </button>

                <button
                  onClick={() => navigate('/preparation')}
                  title="Preparation Hub"
                  className={`w-full flex items-center space-x-3 px-3 py-2 rounded-xl text-xs font-semibold transition ${
                    isActiveRoute('/preparation')
                      ? 'bg-indigo-600 text-white shadow-md shadow-indigo-600/30'
                      : 'text-slate-300 hover:text-white hover:bg-slate-800/80'
                  }`}
                >
                  <svg className="w-4 h-4 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" />
                  </svg>
                  {!collapsed && <span>Preparation Hub</span>}
                </button>

                <button
                  onClick={() => navigate('/assessments')}
                  title="Assessments"
                  className={`w-full flex items-center space-x-3 px-3 py-2 rounded-xl text-xs font-semibold transition ${
                    isActiveRoute('/assessments')
                      ? 'bg-indigo-600 text-white shadow-md shadow-indigo-600/30'
                      : 'text-slate-300 hover:text-white hover:bg-slate-800/80'
                  }`}
                >
                  <svg className="w-4 h-4 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-6 9l2 2 4-4" />
                  </svg>
                  {!collapsed && <span>Assessments</span>}
                </button>

                {/* CRITICAL: button:has-text("Analytics") selector compatibility */}
                <button
                  onClick={() => navigate('/analytics')}
                  title="Analytics"
                  className={`w-full flex items-center space-x-3 px-3 py-2 rounded-xl text-xs font-semibold transition ${
                    isActiveRoute('/analytics')
                      ? 'bg-indigo-600 text-white shadow-md shadow-indigo-600/30'
                      : 'text-slate-300 hover:text-white hover:bg-slate-800/80'
                  }`}
                >
                  <svg className="w-4 h-4 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
                  </svg>
                  {!collapsed && <span>Analytics</span>}
                </button>
              </div>

              {/* SECTION: ACCOUNT */}
              <div className="space-y-1 pt-2">
                {!collapsed && (
                  <div className="px-3 text-[10px] font-bold uppercase tracking-wider text-slate-400">
                    Account
                  </div>
                )}

                <button
                  onClick={() => navigate('/settings')}
                  title="Settings"
                  className={`w-full flex items-center space-x-3 px-3 py-2 rounded-xl text-xs font-semibold transition ${
                    isActiveRoute('/settings')
                      ? 'bg-indigo-600 text-white shadow-md shadow-indigo-600/30'
                      : 'text-slate-300 hover:text-white hover:bg-slate-800/80'
                  }`}
                >
                  <svg className="w-4 h-4 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                  </svg>
                  {!collapsed && <span>Settings</span>}
                </button>
              </div>
            </>
          )}

          {/* ==================== ADMIN NAVIGATION ==================== */}
          {user?.role === 'ADMIN' && (
            <>
              {/* SECTION: ADMINISTRATION */}
              <div className="space-y-1">
                {!collapsed && (
                  <div className="px-3 text-[10px] font-bold uppercase tracking-wider text-slate-400">
                    Administration
                  </div>
                )}

                <button
                  onClick={() => navigate('/')}
                  title="Dashboard"
                  className={`w-full flex items-center space-x-3 px-3 py-2 rounded-xl text-xs font-semibold transition ${
                    isActiveRoute('/')
                      ? 'bg-indigo-600 text-white shadow-md shadow-indigo-600/30'
                      : 'text-slate-300 hover:text-white hover:bg-slate-800/80'
                  }`}
                >
                  <svg className="w-4 h-4 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6" />
                  </svg>
                  {!collapsed && <span>Dashboard</span>}
                </button>

                {/* CRITICAL: button:has-text("Users") selector compatibility */}
                <button
                  onClick={() => navigate('/admin/users')}
                  title="Users"
                  className={`w-full flex items-center space-x-3 px-3 py-2 rounded-xl text-xs font-semibold transition ${
                    isActiveRoute('/admin/users')
                      ? 'bg-indigo-600 text-white shadow-md shadow-indigo-600/30'
                      : 'text-slate-300 hover:text-white hover:bg-slate-800/80'
                  }`}
                >
                  <svg className="w-4 h-4 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 4.354a4 4 0 110 5.292M15 21H3v-1a6 6 0 0112 0v1zm0 0h6v-1a6 6 0 00-9-5.197M13 7a4 4 0 11-8 0 4 4 0 018 0z" />
                  </svg>
                  {!collapsed && <span>Users</span>}
                </button>

                <button
                  onClick={() => navigate('/drives')}
                  title="Placement Drives"
                  className={`w-full flex items-center space-x-3 px-3 py-2 rounded-xl text-xs font-semibold transition ${
                    isActiveRoute('/drives')
                      ? 'bg-indigo-600 text-white shadow-md shadow-indigo-600/30'
                      : 'text-slate-300 hover:text-white hover:bg-slate-800/80'
                  }`}
                >
                  <svg className="w-4 h-4 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M21 13.255A23.931 23.931 0 0112 15c-3.183 0-6.22-.62-9-1.745M16 6V4a2 2 0 00-2-2h-4a2 2 0 00-2 2v2m4 6h.01M5 20h14a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
                  </svg>
                  {!collapsed && <span>Placement Drives</span>}
                </button>

                <button
                  onClick={() => navigate('/preparation')}
                  title="Preparation Hub"
                  className={`w-full flex items-center space-x-3 px-3 py-2 rounded-xl text-xs font-semibold transition ${
                    isActiveRoute('/preparation')
                      ? 'bg-indigo-600 text-white shadow-md shadow-indigo-600/30'
                      : 'text-slate-300 hover:text-white hover:bg-slate-800/80'
                  }`}
                >
                  <svg className="w-4 h-4 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" />
                  </svg>
                  {!collapsed && <span>Preparation Hub</span>}
                </button>

                <button
                  onClick={() => navigate('/assessments')}
                  title="Assessments"
                  className={`w-full flex items-center space-x-3 px-3 py-2 rounded-xl text-xs font-semibold transition ${
                    isActiveRoute('/assessments')
                      ? 'bg-indigo-600 text-white shadow-md shadow-indigo-600/30'
                      : 'text-slate-300 hover:text-white hover:bg-slate-800/80'
                  }`}
                >
                  <svg className="w-4 h-4 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-6 9l2 2 4-4" />
                  </svg>
                  {!collapsed && <span>Assessments</span>}
                </button>

                {/* CRITICAL: button:has-text("Audit Logs") selector compatibility */}
                <button
                  onClick={() => navigate('/admin/audit-logs')}
                  title="Audit Logs"
                  className={`w-full flex items-center space-x-3 px-3 py-2 rounded-xl text-xs font-semibold transition ${
                    isActiveRoute('/admin/audit-logs')
                      ? 'bg-indigo-600 text-white shadow-md shadow-indigo-600/30'
                      : 'text-slate-300 hover:text-white hover:bg-slate-800/80'
                  }`}
                >
                  <svg className="w-4 h-4 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                  </svg>
                  {!collapsed && <span>Audit Logs</span>}
                </button>

                {/* CRITICAL: button:has-text("Analytics") selector compatibility */}
                <button
                  onClick={() => navigate('/analytics')}
                  title="Analytics"
                  className={`w-full flex items-center space-x-3 px-3 py-2 rounded-xl text-xs font-semibold transition ${
                    isActiveRoute('/analytics')
                      ? 'bg-indigo-600 text-white shadow-md shadow-indigo-600/30'
                      : 'text-slate-300 hover:text-white hover:bg-slate-800/80'
                  }`}
                >
                  <svg className="w-4 h-4 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
                  </svg>
                  {!collapsed && <span>Analytics</span>}
                </button>
              </div>

              {/* SECTION: ACCOUNT */}
              <div className="space-y-1 pt-2">
                {!collapsed && (
                  <div className="px-3 text-[10px] font-bold uppercase tracking-wider text-slate-400">
                    Account
                  </div>
                )}

                <button
                  onClick={() => navigate('/settings')}
                  title="Settings"
                  className={`w-full flex items-center space-x-3 px-3 py-2 rounded-xl text-xs font-semibold transition ${
                    isActiveRoute('/settings')
                      ? 'bg-indigo-600 text-white shadow-md shadow-indigo-600/30'
                      : 'text-slate-300 hover:text-white hover:bg-slate-800/80'
                  }`}
                >
                  <svg className="w-4 h-4 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                  </svg>
                  {!collapsed && <span>Settings</span>}
                </button>
              </div>
            </>
          )}

          {/* CRITICAL: button:has-text("Logout") selector compatibility inside nav */}
          <div className="pt-4 border-t border-slate-800">
            <button
              onClick={handleLogout}
              title="Logout"
              className="w-full flex items-center space-x-3 px-3 py-2 rounded-xl text-xs font-semibold text-rose-400 hover:text-rose-300 hover:bg-rose-950/40 transition"
            >
              <svg className="w-4 h-4 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1" />
              </svg>
              {!collapsed && <span>Logout</span>}
            </button>
          </div>
        </nav>

        {/* Sidebar Bottom Profile Card */}
        {!collapsed && (
          <div className="p-3 border-t border-slate-800 bg-slate-950/40 text-[11px] text-slate-400 space-y-1">
            <div className="text-slate-200 font-bold truncate">{user?.full_name}</div>
            <div className="text-[10px] text-emerald-400 font-semibold flex items-center space-x-1">
              <span className="w-1.5 h-1.5 rounded-full bg-emerald-400" />
              <span>Active Session</span>
            </div>
          </div>
        )}
      </aside>

      {/* ========================================================================= */}
      {/* 2. MOBILE DRAWER OVERLAY & SIDEBAR (MOBILE VIEW)                          */}
      {/* ========================================================================= */}
      {mobileDrawerOpen && (
        <div className="fixed inset-0 z-50 flex md:hidden animate-fade-in">
          <div
            className="fixed inset-0 bg-slate-900/80 backdrop-blur-sm"
            onClick={() => setMobileDrawerOpen(false)}
          />
          <div id="mobile-drawer" className="relative flex flex-col w-72 max-w-xs bg-slate-900 text-slate-300 h-full shadow-2xl p-4 space-y-4">
            <div className="flex items-center justify-between pb-3 border-b border-slate-800">
              <div className="flex items-center space-x-2">
                <CampusFlowLogo size="sm" />
                <span className="font-extrabold text-white text-sm">CampusFlow</span>
              </div>
              <button
                onClick={() => setMobileDrawerOpen(false)}
                className="p-1.5 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800"
              >
                <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>

            <div className="py-2 px-3 rounded-lg bg-slate-800 text-xs font-bold text-white">
              {user?.full_name} ({user?.role})
            </div>

            <div className="flex-1 overflow-y-auto space-y-1">
              <button
                onClick={() => {
                  navigate('/');
                  setMobileDrawerOpen(false);
                }}
                className="w-full text-left px-3 py-2 rounded-lg text-xs font-semibold text-slate-300 hover:bg-slate-800 hover:text-white"
              >
                Dashboard
              </button>
              <button
                onClick={() => {
                  navigate('/drives');
                  setMobileDrawerOpen(false);
                }}
                className="w-full text-left px-3 py-2 rounded-lg text-xs font-semibold text-slate-300 hover:bg-slate-800 hover:text-white"
              >
                Placement Drives
              </button>
              <button
                onClick={() => {
                  navigate('/preparation');
                  setMobileDrawerOpen(false);
                }}
                className="w-full text-left px-3 py-2 rounded-lg text-xs font-semibold text-slate-300 hover:bg-slate-800 hover:text-white"
              >
                Preparation Hub
              </button>
              <button
                onClick={() => {
                  navigate('/assessments');
                  setMobileDrawerOpen(false);
                }}
                className="w-full text-left px-3 py-2 rounded-lg text-xs font-semibold text-slate-300 hover:bg-slate-800 hover:text-white"
              >
                Practice Assessments
              </button>
              {user?.role === 'STUDENT' && (
                <>
                  <button
                    onClick={() => {
                      navigate('/applications');
                      setMobileDrawerOpen(false);
                    }}
                    className="w-full text-left px-3 py-2 rounded-lg text-xs font-semibold text-slate-300 hover:bg-slate-800 hover:text-white"
                  >
                    My Applications
                  </button>
                  <button
                    onClick={() => {
                      navigate('/profile');
                      setMobileDrawerOpen(false);
                    }}
                    className="w-full text-left px-3 py-2 rounded-lg text-xs font-semibold text-slate-300 hover:bg-slate-800 hover:text-white"
                  >
                    My Profile & Resume
                  </button>
                </>
              )}
              <button
                onClick={() => {
                  navigate('/notifications');
                  setMobileDrawerOpen(false);
                }}
                className="w-full text-left px-3 py-2 rounded-lg text-xs font-semibold text-slate-300 hover:bg-slate-800 hover:text-white"
              >
                Notifications
              </button>
              {(user?.role === 'OFFICER' || user?.role === 'ADMIN') && (
                <button
                  onClick={() => {
                    navigate('/analytics');
                    setMobileDrawerOpen(false);
                  }}
                  className="w-full text-left px-3 py-2 rounded-lg text-xs font-semibold text-slate-300 hover:bg-slate-800 hover:text-white"
                >
                  Analytics
                </button>
              )}
              {user?.role === 'ADMIN' && (
                <>
                  <button
                    onClick={() => {
                      navigate('/admin/users');
                      setMobileDrawerOpen(false);
                    }}
                    className="w-full text-left px-3 py-2 rounded-lg text-xs font-semibold text-slate-300 hover:bg-slate-800 hover:text-white"
                  >
                    Users
                  </button>
                  <button
                    onClick={() => {
                      navigate('/admin/audit-logs');
                      setMobileDrawerOpen(false);
                    }}
                    className="w-full text-left px-3 py-2 rounded-lg text-xs font-semibold text-slate-300 hover:bg-slate-800 hover:text-white"
                  >
                    Audit Logs
                  </button>
                </>
              )}
            </div>

            <button
              onClick={handleLogout}
              className="w-full py-2 text-xs font-bold text-rose-400 hover:bg-rose-950/40 rounded-lg transition text-left px-3"
            >
              Logout
            </button>
          </div>
        </div>
      )}

      {/* ========================================================================= */}
      {/* 3. MAIN WORKSPACE CONTAINER                                              */}
      {/* ========================================================================= */}
      <div className="flex-1 flex flex-col min-w-0">
        {/* TOP HEADER */}
        <header className="sticky top-0 z-20 bg-white/95 backdrop-blur-md border-b border-slate-200 shadow-sm h-16 flex items-center justify-between px-4 sm:px-6 lg:px-8">
          {/* Left: Mobile hamburger + Workspace Context */}
          <div className="flex items-center space-x-3">
            <button
              onClick={() => setMobileDrawerOpen(true)}
              className="md:hidden p-2 rounded-lg text-slate-600 hover:text-slate-900 hover:bg-slate-100"
              aria-label="Open navigation drawer"
            >
              <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M4 6h16M4 12h16M4 18h16" />
              </svg>
            </button>

            <div className="flex items-center space-x-2 text-xs text-slate-500 font-medium">
              <span className="font-semibold text-slate-700">CampusFlow Workspace</span>
              <span>&bull;</span>
              <span className="text-indigo-600 font-semibold">{user?.role} Portal</span>
            </div>
          </div>

          {/* Right: Quick actions, Push Opt-in, Notifications, User Chip */}
          <div className="flex items-center space-x-3">
            <PushNotificationOptIn />

            <button
              onClick={() => navigate('/notifications')}
              className={`p-2 rounded-xl text-slate-600 hover:text-indigo-600 hover:bg-slate-100 transition relative flex items-center space-x-1.5 ${
                isActiveRoute('/notifications') ? 'bg-indigo-50 text-indigo-700' : ''
              }`}
              title="Notifications"
            >
              <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9" />
              </svg>
            </button>

            {/* User Avatar Chip */}
            <div
              onClick={() => navigate(user?.role === 'STUDENT' ? '/profile' : '/settings')}
              className="flex items-center space-x-2.5 py-1 px-2.5 rounded-xl bg-slate-100/80 hover:bg-slate-200/80 border border-slate-200 cursor-pointer transition"
            >
              <div className="w-7 h-7 rounded-lg bg-indigo-600 text-white flex items-center justify-center font-bold text-xs shadow-sm">
                {user?.full_name?.charAt(0).toUpperCase() || 'U'}
              </div>
              <div className="hidden sm:block text-left">
                <div className="text-xs text-slate-800 font-bold leading-tight truncate max-w-[120px]">
                  {user?.full_name}
                </div>
                <div className="text-[10px] text-slate-500 font-semibold">{user?.role}</div>
              </div>
            </div>
          </div>
        </header>

        {/* MAIN WORKSPACE CONTENT */}
        <main className="flex-1 max-w-7xl w-full mx-auto py-8 px-4 sm:px-6 lg:px-8">
          <Outlet />
        </main>

        {/* WORKSPACE FOOTER */}
        <footer className="bg-white border-t border-slate-200 py-4 mt-auto">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 flex flex-col sm:flex-row items-center justify-between text-xs text-slate-500 gap-2">
            <div className="flex items-center space-x-2">
              <span className="font-bold text-slate-700">CampusFlow</span>
              <span>&bull;</span>
              <span>University Placement Platform</span>
            </div>
            <div className="flex items-center space-x-4">
              <span className="inline-flex items-center space-x-1">
                <span className="w-1.5 h-1.5 rounded-full bg-emerald-500" />
                <span>System Operational</span>
              </span>
              <span>v1.0.0</span>
            </div>
          </div>
        </footer>
      </div>
    </div>
  );
};

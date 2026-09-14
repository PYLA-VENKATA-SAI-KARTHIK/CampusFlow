import { Link } from 'react-router-dom';

export const UnauthorizedPage = () => {
  return (
    <div className="min-h-[70vh] flex items-center justify-center p-4">
      <div className="max-w-md w-full p-8 bg-white border border-slate-200/80 rounded-2xl shadow-xs text-center space-y-4 animate-fade-in">
        <div className="w-12 h-12 rounded-2xl bg-amber-50 text-amber-600 flex items-center justify-center mx-auto border border-amber-200/80">
          <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
          </svg>
        </div>

        <div>
          <h2 className="text-xl font-extrabold text-slate-900 tracking-tight">Access Denied</h2>
          <p className="text-xs text-slate-500 mt-1.5 leading-relaxed">
            You do not have permission to view this page or perform this action within your current role.
          </p>
        </div>

        <div className="pt-2">
          <Link
            to="/"
            className="inline-flex items-center justify-center px-4 py-2.5 bg-indigo-600 hover:bg-indigo-700 text-white text-xs font-bold rounded-xl shadow-xs transition duration-150"
          >
            Return to Dashboard
          </Link>
        </div>
      </div>
    </div>
  );
};

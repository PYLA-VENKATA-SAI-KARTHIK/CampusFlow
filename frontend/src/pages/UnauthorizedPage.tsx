import { Link } from 'react-router-dom';

export const UnauthorizedPage = () => {
  return (
    <div className="max-w-md mx-auto my-12 p-8 bg-white border border-slate-200 rounded-2xl shadow-sm text-center space-y-4 animate-fade-in">
      <div className="w-14 h-14 rounded-2xl bg-amber-50 text-amber-600 flex items-center justify-center mx-auto border border-amber-200">
        <svg className="w-7 h-7" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
        </svg>
      </div>

      <div>
        <h2 className="text-2xl font-bold text-slate-900 tracking-tight">Access Denied</h2>
        <p className="text-sm text-slate-500 mt-1.5">
          You do not have permission to view this page or perform this action.
        </p>
      </div>

      <div className="pt-3">
        <Link
          to="/"
          className="inline-flex items-center px-4 py-2 bg-indigo-600 hover:bg-indigo-700 text-white text-xs font-bold rounded-xl shadow-md shadow-indigo-600/20 transition"
        >
          Return to Dashboard
        </Link>
      </div>
    </div>
  );
};

import { Link } from 'react-router-dom';
import { CampusFlowLogo } from '../components/common/CampusFlowLogo';

export const NotFoundPage = () => {
  return (
    <div className="min-h-screen bg-slate-50 flex flex-col items-center justify-center p-6 text-center animate-fade-in">
      <div className="max-w-md w-full bg-white border border-slate-200 rounded-3xl p-8 sm:p-10 shadow-xl space-y-6">
        <CampusFlowLogo size="md" className="justify-center" />

        <div className="space-y-2">
          <span className="text-6xl font-extrabold text-indigo-600 tracking-tight block">404</span>
          <h2 className="text-2xl font-bold text-slate-900">Page Not Found</h2>
          <p className="text-xs sm:text-sm text-slate-500">
            The opportunity or page you are looking for doesn't exist or has been relocated.
          </p>
        </div>

        <div className="pt-2">
          <Link
            to="/"
            className="inline-flex items-center justify-center w-full py-3 px-4 rounded-xl text-sm font-semibold text-white bg-indigo-600 hover:bg-indigo-700 shadow-md shadow-indigo-600/20 transition"
          >
            Go back home
          </Link>
        </div>
      </div>
    </div>
  );
};

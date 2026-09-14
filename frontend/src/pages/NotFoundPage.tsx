import { Link } from 'react-router-dom';
import { CampusFlowLogo } from '../components/common/CampusFlowLogo';

export const NotFoundPage = () => {
  return (
    <div className="min-h-screen bg-slate-50 flex flex-col items-center justify-center p-6 text-center animate-fade-in font-sans">
      <div className="max-w-md w-full bg-white border border-slate-200/80 rounded-2xl p-8 sm:p-10 shadow-xs space-y-6">
        <CampusFlowLogo size="md" className="justify-center" />

        <div className="space-y-2">
          <span className="text-5xl font-black text-indigo-600 tracking-tight block">404</span>
          <h2 className="text-xl font-bold text-slate-900 tracking-tight">Page Not Found</h2>
          <p className="text-xs text-slate-500 leading-relaxed">
            The opportunity or page you are looking for doesn't exist or has been relocated within the workspace.
          </p>
        </div>

        <div className="pt-2">
          <Link
            to="/"
            className="inline-flex items-center justify-center w-full py-2.5 px-4 rounded-xl text-xs font-bold text-white bg-indigo-600 hover:bg-indigo-700 shadow-xs transition duration-150"
          >
            Go back to Dashboard
          </Link>
        </div>
      </div>
    </div>
  );
};

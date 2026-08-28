import { Link } from 'react-router-dom';

export const UnauthorizedPage = () => {
  return (
    <div className="text-center py-12">
      <h2 className="text-2xl font-bold text-gray-900 mb-2">Access Denied</h2>
      <p className="text-gray-600 mb-6">
        You do not have permission to view this page.
      </p>
      <Link
        to="/"
        className="text-primary-600 hover:text-primary-800 font-medium"
      >
        Return to Dashboard
      </Link>
    </div>
  );
};

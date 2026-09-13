import React from 'react';
import { useAuthStore } from '../store/authStore';
import { StudentAssessmentsPage } from './StudentAssessmentsPage';
import { OfficerAssessmentsPage } from './OfficerAssessmentsPage';

export const AssessmentsPage: React.FC = () => {
  const { user } = useAuthStore();

  if (user?.role === 'STUDENT') {
    return <StudentAssessmentsPage />;
  }

  return <OfficerAssessmentsPage />;
};

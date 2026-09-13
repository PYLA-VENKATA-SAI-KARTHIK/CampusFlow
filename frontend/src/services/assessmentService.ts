import { apiClient } from './apiClient';
import type {
  AssessmentAdminDetail,
  AssessmentAssignmentResponse,
  AssessmentCreatePayload,
  AssessmentResultResponse,
  AssessmentStudentPreview,
  AssessmentSummary,
  AssessmentUpdatePayload,
  OfficerAssessmentResultsView,
  QuestionAdminView,
  QuestionAnswerItem,
  QuestionCreatePayload,
  QuestionUpdatePayload,
  StartAttemptResponse,
} from '../types/assessment';

export const assessmentService = {
  // -------------------------------------------------------------------------
  // Officer & Admin Endpoints
  // -------------------------------------------------------------------------

  createAssessment: async (payload: AssessmentCreatePayload): Promise<AssessmentSummary> => {
    const res = await apiClient.post<AssessmentSummary>('/assessments', payload);
    return res.data;
  },

  listAssessments: async (params: Record<string, any> = {}): Promise<AssessmentSummary[]> => {
    const cleanParams: Record<string, any> = {};
    Object.entries(params).forEach(([k, v]) => {
      if (v !== undefined && v !== null && v !== '') {
        cleanParams[k] = v;
      }
    });
    const res = await apiClient.get<AssessmentSummary[]>('/assessments', { params: cleanParams });
    return res.data;
  },

  getAssessmentAdmin: async (assessmentId: string): Promise<AssessmentAdminDetail> => {
    const res = await apiClient.get<AssessmentAdminDetail>(`/assessments/${assessmentId}`);
    return res.data;
  },

  updateAssessment: async (assessmentId: string, payload: AssessmentUpdatePayload): Promise<AssessmentSummary> => {
    const res = await apiClient.patch<AssessmentSummary>(`/assessments/${assessmentId}`, payload);
    return res.data;
  },

  addQuestion: async (assessmentId: string, payload: QuestionCreatePayload): Promise<QuestionAdminView> => {
    const res = await apiClient.post<QuestionAdminView>(`/assessments/${assessmentId}/questions`, payload);
    return res.data;
  },

  updateQuestion: async (
    assessmentId: string,
    questionId: string,
    payload: QuestionUpdatePayload
  ): Promise<QuestionAdminView> => {
    const res = await apiClient.patch<QuestionAdminView>(
      `/assessments/${assessmentId}/questions/${questionId}`,
      payload
    );
    return res.data;
  },

  deleteQuestion: async (assessmentId: string, questionId: string): Promise<void> => {
    await apiClient.delete(`/assessments/${assessmentId}/questions/${questionId}`);
  },

  publishAssessment: async (assessmentId: string): Promise<AssessmentSummary> => {
    const res = await apiClient.post<AssessmentSummary>(`/assessments/${assessmentId}/publish`);
    return res.data;
  },

  archiveAssessment: async (assessmentId: string): Promise<AssessmentSummary> => {
    const res = await apiClient.post<AssessmentSummary>(`/assessments/${assessmentId}/archive`);
    return res.data;
  },

  assignAssessment: async (
    assessmentId: string,
    studentUserIds: string[],
    dueDate?: string | null
  ): Promise<AssessmentAssignmentResponse[]> => {
    const res = await apiClient.post<AssessmentAssignmentResponse[]>(`/assessments/${assessmentId}/assign`, {
      student_user_ids: studentUserIds,
      due_date: dueDate || null,
    });
    return res.data;
  },

  getOfficerResults: async (assessmentId: string): Promise<OfficerAssessmentResultsView> => {
    const res = await apiClient.get<OfficerAssessmentResultsView>(`/assessments/${assessmentId}/results`);
    return res.data;
  },

  // -------------------------------------------------------------------------
  // Student Endpoints
  // -------------------------------------------------------------------------

  getAssignedAssessments: async (status?: string): Promise<AssessmentAssignmentResponse[]> => {
    const params = status ? { status } : {};
    const res = await apiClient.get<AssessmentAssignmentResponse[]>('/assessments/assigned', { params });
    return res.data;
  },

  getStudentPreview: async (assessmentId: string): Promise<AssessmentStudentPreview> => {
    const res = await apiClient.get<AssessmentStudentPreview>(`/assessments/${assessmentId}/preview`);
    return res.data;
  },

  startAttempt: async (assessmentId: string): Promise<StartAttemptResponse> => {
    const res = await apiClient.post<StartAttemptResponse>(`/assessments/${assessmentId}/start`);
    return res.data;
  },

  getActiveAttempt: async (attemptId: string): Promise<StartAttemptResponse> => {
    const res = await apiClient.get<StartAttemptResponse>(`/assessments/attempts/${attemptId}/active`);
    return res.data;
  },

  saveProgress: async (
    attemptId: string,
    responses: QuestionAnswerItem[]
  ): Promise<{ status: string; saved_count: number }> => {
    const res = await apiClient.post<{ status: string; saved_count: number }>(
      `/assessments/attempts/${attemptId}/save-progress`,
      { responses }
    );
    return res.data;
  },

  submitAttempt: async (
    attemptId: string,
    responses?: QuestionAnswerItem[]
  ): Promise<AssessmentResultResponse> => {
    const res = await apiClient.post<AssessmentResultResponse>(
      `/assessments/attempts/${attemptId}/submit`,
      responses ? { responses } : {}
    );
    return res.data;
  },

  getAttemptResult: async (attemptId: string): Promise<AssessmentResultResponse> => {
    const res = await apiClient.get<AssessmentResultResponse>(`/assessments/attempts/${attemptId}/result`);
    return res.data;
  },

  getMyHistory: async (): Promise<AssessmentResultResponse[]> => {
    const res = await apiClient.get<AssessmentResultResponse[]>('/assessments/my-history');
    return res.data;
  },
};

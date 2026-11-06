/**
 * CampusFlow — Mock Interview API Service.
 */
import { apiClient } from './apiClient';
import type {
  MockInterviewEvaluateRequest,
  MockInterviewEvaluationItem,
  MockInterviewSessionCreate,
  MockInterviewSessionResponse,
  RAGDocument,
} from '../types/mockInterview';

export const mockInterviewService = {
  createSession: async (data: MockInterviewSessionCreate): Promise<MockInterviewSessionResponse> => {
    const response = await apiClient.post<MockInterviewSessionResponse>(
      '/mock-interviews/sessions',
      data
    );
    return response.data;
  },

  evaluateAnswer: async (
    sessionId: string,
    request: MockInterviewEvaluateRequest
  ): Promise<MockInterviewEvaluationItem> => {
    const response = await apiClient.post<MockInterviewEvaluationItem>(
      `/mock-interviews/sessions/${sessionId}/evaluate-answer`,
      request
    );
    return response.data;
  },

  completeSession: async (sessionId: string): Promise<MockInterviewSessionResponse> => {
    const response = await apiClient.post<MockInterviewSessionResponse>(
      `/mock-interviews/sessions/${sessionId}/complete`
    );
    return response.data;
  },

  listSessions: async (): Promise<MockInterviewSessionResponse[]> => {
    const response = await apiClient.get<MockInterviewSessionResponse[]>(
      '/mock-interviews/sessions'
    );
    return response.data;
  },

  getSessionDetails: async (sessionId: string): Promise<MockInterviewSessionResponse> => {
    const response = await apiClient.get<MockInterviewSessionResponse>(
      `/mock-interviews/sessions/${sessionId}`
    );
    return response.data;
  },

  getTrackQuestions: async (trackId: string, count = 5, offset = 0): Promise<RAGDocument[]> => {
    const response = await apiClient.get<RAGDocument[]>(
      `/mock-interviews/tracks/${trackId}/rag-questions`,
      { params: { count, offset } }
    );
    return response.data;
  },

  queryRAG: async (query: string, trackId?: string, topK = 3) => {
    const response = await apiClient.post('/mock-interviews/rag/query', {
      query,
      track_id: trackId,
      top_k: topK,
    });
    return response.data;
  },
};

/**
 * CampusFlow — Mock Interview Voice Agent Types.
 */

export interface MockInterviewSessionCreate {
  track_id: string;
  track_title: string;
  target_role?: string;
}

export interface MockInterviewEvaluateRequest {
  question_index: number;
  question_id?: string;
  question_text: string;
  question_category: string;
  student_answer: string;
  expected_keywords?: string[];
  coaching_tips?: string;
  audio_duration_seconds?: number;
}

export interface MockInterviewEvaluationItem {
  id: string;
  session_id: string;
  question_index: number;
  question_id?: string;
  question_text: string;
  question_category: string;
  student_answer: string;
  audio_duration_seconds?: number;
  words_per_minute?: number;
  filler_words: string[];
  score: number;
  technical_depth_score: number;
  communication_score: number;
  structure_score: number;
  feedback_critique: string;
  strengths: string[];
  improvements: string[];
  ideal_response?: string;
  keywords_matched: string[];
  keywords_missed: string[];
  created_at: string;
}

export interface MockInterviewSessionResponse {
  id: string;
  user_id: string;
  track_id: string;
  track_title: string;
  target_role?: string;
  status: 'IN_PROGRESS' | 'COMPLETED' | 'ABANDONED';
  overall_score?: number;
  technical_score?: number;
  communication_score?: number;
  structure_score?: number;
  confidence_score?: number;
  performance_rating?: 'EXCEPTIONAL' | 'JOB_READY' | 'DEVELOPING' | 'NEEDS_PRACTICE' | string;
  summary_feedback?: string;
  strengths: string[];
  improvements: string[];
  action_plan: string[];
  topic_breakdown: Record<string, number>;
  evaluations: MockInterviewEvaluationItem[];
  created_at: string;
  completed_at?: string;
}

export interface RAGDocument {
  id: string;
  track_id: string;
  category: string;
  subtopic: string;
  question: string;
  answer: string;
  key_concepts: string[];
  difficulty: string;
  source_document: string;
}



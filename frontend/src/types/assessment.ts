export type AssessmentDifficulty = 'BEGINNER' | 'INTERMEDIATE' | 'ADVANCED';
export type AssessmentStatus = 'DRAFT' | 'PUBLISHED' | 'ARCHIVED';
export type AssignmentStatus = 'ASSIGNED' | 'IN_PROGRESS' | 'COMPLETED' | 'EXPIRED';
export type AttemptStatus = 'IN_PROGRESS' | 'SUBMITTED' | 'EXPIRED' | 'ABANDONED';

export interface OptionItem {
  key: string;
  text: string;
}

export interface QuestionAdminView {
  id: string;
  assessment_id: string;
  topic_id: string | null;
  topic_name: string | null;
  question_text: string;
  options: OptionItem[];
  correct_option: string;
  explanation: string | null;
  marks: number;
  sequence_order: number;
  created_at: string;
  updated_at: string;
}

export interface QuestionStudentView {
  id: string;
  assessment_id: string;
  topic_id: string | null;
  question_text: string;
  options: OptionItem[];
  marks: number;
  sequence_order: number;
}

export interface QuestionReviewView {
  id: string;
  topic_id: string | null;
  topic_name: string | null;
  question_text: string;
  options: OptionItem[];
  selected_option: string | null;
  correct_option: string;
  is_correct: boolean;
  marks_awarded: number;
  explanation: string | null;
  sequence_order: number;
}

export interface AssessmentSummary {
  id: string;
  title: string;
  description: string | null;
  category_id: string | null;
  category_name: string | null;
  topic_id: string | null;
  topic_name: string | null;
  role_id: string | null;
  role_name: string | null;
  placement_drive_id: string | null;
  placement_drive_title: string | null;
  difficulty: AssessmentDifficulty;
  duration_minutes: number;
  total_marks: number;
  pass_percentage: number;
  status: AssessmentStatus;
  allow_multiple_attempts: boolean;
  questions_count: number;
  created_by_user_id: string;
  created_at: string;
  updated_at: string;
}

export interface AssessmentAdminDetail {
  id: string;
  title: string;
  description: string | null;
  category_id: string | null;
  category_name: string | null;
  topic_id: string | null;
  topic_name: string | null;
  role_id: string | null;
  role_name: string | null;
  placement_drive_id: string | null;
  placement_drive_title: string | null;
  difficulty: AssessmentDifficulty;
  duration_minutes: number;
  total_marks: number;
  pass_percentage: number;
  status: AssessmentStatus;
  allow_multiple_attempts: boolean;
  created_by_user_id: string;
  created_at: string;
  updated_at: string;
  questions: QuestionAdminView[];
  assignments_count: number;
  completed_count: number;
}

export interface AssessmentStudentPreview {
  id: string;
  assignment_id: string | null;
  title: string;
  description: string | null;
  category_name: string | null;
  topic_name: string | null;
  role_name: string | null;
  placement_drive_title: string | null;
  difficulty: AssessmentDifficulty;
  duration_minutes: number;
  question_count: number;
  total_marks: number;
  pass_percentage: number;
  due_date: string | null;
  assignment_status: AssignmentStatus;
  has_active_attempt: boolean;
  active_attempt_id: string | null;
  active_attempt_expires_at: string | null;
  latest_result_id: string | null;
  latest_score: number | null;
  latest_percentage: number | null;
  latest_passed: boolean | null;
}

export interface AssessmentAssignmentResponse {
  id: string;
  assessment_id: string;
  student_user_id: string;
  assigned_by_user_id: string | null;
  due_date: string | null;
  status: AssignmentStatus;
  created_at: string;
  assessment_title: string | null;
  difficulty: AssessmentDifficulty | null;
  duration_minutes: number | null;
  total_marks: number | null;
  pass_percentage: number | null;
  category_name: string | null;
  topic_name: string | null;
  placement_drive_title: string | null;
  student_name: string | null;
  student_email: string | null;
  student_roll_number: string | null;
  student_branch: string | null;
  latest_result_id: string | null;
  latest_score: number | null;
  latest_percentage: number | null;
  latest_passed: boolean | null;
}

export interface StartAttemptResponse {
  attempt_id: string;
  assessment_id: string;
  assignment_id: string;
  title: string;
  duration_minutes: number;
  started_at: string;
  expires_at: string;
  questions: QuestionStudentView[];
  saved_responses: Record<string, string | null>;
}

export interface TopicPerformance {
  total_questions: number;
  correct_answers: number;
  incorrect_answers: number;
  unanswered: number;
  score_obtained: number;
  total_score: number;
}

export interface AssessmentResultResponse {
  id: string;
  attempt_id: string;
  assessment_id: string;
  assessment_title: string;
  score_obtained: number;
  total_score: number;
  percentage: number;
  is_passed: boolean;
  total_questions: number;
  correct_answers: number;
  incorrect_answers: number;
  unanswered: number;
  time_taken_seconds: number;
  topic_breakdown: Record<string, TopicPerformance>;
  created_at: string;
  review?: QuestionReviewView[] | null;
}

export interface OfficerAssessmentResultsView {
  assessment_id: string;
  assessment_title: string;
  total_assigned: number;
  total_started: number;
  total_completed: number;
  average_score: number | null;
  average_percentage: number | null;
  pass_count: number;
  results: AssessmentAssignmentResponse[];
}

export interface AssessmentCreatePayload {
  title: string;
  description?: string | null;
  category_id?: string | null;
  topic_id?: string | null;
  role_id?: string | null;
  placement_drive_id?: string | null;
  difficulty?: AssessmentDifficulty;
  duration_minutes?: number;
  pass_percentage?: number;
  allow_multiple_attempts?: boolean;
}

export interface AssessmentUpdatePayload {
  title?: string;
  description?: string | null;
  category_id?: string | null;
  topic_id?: string | null;
  role_id?: string | null;
  placement_drive_id?: string | null;
  difficulty?: AssessmentDifficulty;
  duration_minutes?: number;
  pass_percentage?: number;
  allow_multiple_attempts?: boolean;
}

export interface QuestionCreatePayload {
  question_text: string;
  options: OptionItem[];
  correct_option: string;
  explanation?: string | null;
  marks?: number;
  topic_id?: string | null;
  sequence_order?: number;
}

export interface QuestionUpdatePayload {
  question_text?: string;
  options?: OptionItem[];
  correct_option?: string;
  explanation?: string | null;
  marks?: number;
  topic_id?: string | null;
  sequence_order?: number;
}

export interface QuestionAnswerItem {
  question_id: string;
  selected_option: string | null;
}

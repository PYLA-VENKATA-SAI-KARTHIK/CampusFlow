export type MaterialType =
  | 'ARTICLE'
  | 'VIDEO'
  | 'PDF'
  | 'PRACTICE_QUESTIONS'
  | 'DOCUMENTATION'
  | 'COURSE'
  | 'OTHER';

export type MaterialDifficulty = 'BEGINNER' | 'INTERMEDIATE' | 'ADVANCED';

export type MaterialStatus = 'PENDING' | 'APPROVED' | 'REJECTED';

export type TopicImportance = 'CORE' | 'ELECTIVE' | 'BONUS';

export interface PreparationRole {
  id: string;
  code: string;
  name: string;
  description: string | null;
  icon: string | null;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface PreparationTopic {
  id: string;
  category_id: string;
  name: string;
  slug: string;
  description: string | null;
  created_at: string;
  updated_at: string;
}

export interface PreparationCategory {
  id: string;
  code: string;
  name: string;
  description: string | null;
  icon: string | null;
  sequence_order: number;
  created_at: string;
  topics: PreparationTopic[];
}

export interface PreparationMaterial {
  id: string;
  topic_id: string;
  role_id: string | null;
  title: string;
  description: string | null;
  url: string;
  material_type: MaterialType;
  difficulty: MaterialDifficulty;
  source: string | null;
  status: MaterialStatus;
  submitted_by_user_id: string | null;
  reviewed_by_user_id: string | null;
  review_notes: string | null;
  created_at: string;
  updated_at: string;
}

export interface RoleRoadmapTopic {
  topic: PreparationTopic;
  importance: TopicImportance;
  material_count: number;
}

export interface RoleRoadmap {
  role: PreparationRole;
  topics: RoleRoadmapTopic[];
}

export interface SuggestMaterialPayload {
  topic_id: string;
  role_id?: string | null;
  title: string;
  url: string;
  description?: string | null;
  material_type: MaterialType;
  difficulty: MaterialDifficulty;
  source?: string | null;
}

export interface OfficerReviewPayload {
  status: 'APPROVED' | 'REJECTED';
  review_notes?: string | null;
}

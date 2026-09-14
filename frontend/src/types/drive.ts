export type DriveStatus =
  | 'DRAFT'
  | 'PUBLISHED'
  | 'REGISTRATION_OPEN'
  | 'REGISTRATION_CLOSED'
  | 'SHORTLISTING'
  | 'ASSESSMENT'
  | 'INTERVIEW'
  | 'RESULT'
  | 'COMPLETED';

export type StageType = 'APTITUDE' | 'TECHNICAL' | 'HR' | 'GD' | 'CODING' | 'OTHER';

export interface Company {
  id: string;
  name: string;
  website?: string | null;
  logo_gcs_path?: string | null;
  industry?: string | null;
  description?: string | null;
}

export interface CompanyCreate {
  name: string;
  website?: string;
  industry?: string;
  description?: string;
}

export interface EligibilityCriteria {
  min_cgpa?: number | null;
  max_active_backlogs?: number | null;
  eligible_branches?: string[] | null;
  eligible_batch_years?: number[] | null;
  gender?: 'MALE' | 'FEMALE' | 'OTHER' | null;
}

export interface EligibilityResult {
  is_eligible: boolean;
  reasons: string[];
}

export interface EligibilityCheckResponse extends EligibilityResult {
  drive_id: string;
}

export interface PlacementStage {
  id: string;
  drive_id: string;
  name: string;
  stage_type: StageType;
  sequence_order: number;
  scheduled_at?: string | null;
  location_or_link?: string | null;
  instructions?: string | null;
  is_published: boolean;
  student_count?: number;
  my_status?: string | null;
  created_at: string;
  updated_at: string;
}

export interface PlacementStageCreate {
  name: string;
  stage_type: StageType;
  sequence_order: number;
  scheduled_at?: string | null;
  location_or_link?: string | null;
  instructions?: string | null;
}

export interface PlacementDrive {
  id: string;
  company_id: string;
  title: string;
  job_role: string;
  description?: string | null;
  ctc_lpa?: number | null;
  stipend_monthly?: number | null;
  location?: string | null;
  bond_details?: string | null;
  registration_deadline?: string | null;
  status: DriveStatus;
  created_by_user_id: string;
  published_at?: string | null;
  created_at: string;
  updated_at: string;

  company?: Company | null;
  eligibility_criteria?: EligibilityCriteria | null;
  my_eligibility?: EligibilityResult | null;
  is_registered?: boolean | null;
}

export interface PlacementDriveCreate {
  company_id: string;
  title: string;
  job_role: string;
  description?: string;
  ctc_lpa?: number;
  stipend_monthly?: number;
  location?: string;
  bond_details?: string;
  registration_deadline?: string;
  eligibility_criteria: EligibilityCriteria;
}

export interface PlacementDriveUpdate {
  title?: string;
  job_role?: string;
  description?: string;
  ctc_lpa?: number;
  stipend_monthly?: number;
  location?: string;
  bond_details?: string;
  registration_deadline?: string;
  eligibility_criteria?: EligibilityCriteria;
}

export interface Branch {
  code: string;
  name: string;
  is_active: boolean;
}

export interface RegistrationStudentSummary {
  id: string;
  user_id: string;
  full_name: string;
  email: string;
  roll_number: string;
  branch: string;
  batch_year: number;
  cgpa: number;
  active_backlogs: number;
  gender?: string | null;
  avatar_url?: string | null;
}

export interface RegistrationStageSummary {
  stage_id: string;
  stage_name: string;
  stage_type: string;
  sequence_order: number;
  status: string;
  result_notes?: string | null;
  assigned_at: string;
}

export interface DriveRegistrationWithStudent {
  id: string;
  drive_id: string;
  student_user_id: string;
  resume_gcs_path_at_registration: string;
  status: string;
  registered_at: string;
  updated_at: string;
  student: RegistrationStudentSummary;
  current_stage?: RegistrationStageSummary | null;
}

export type AssignmentStatus = 'SHORTLISTED' | 'APPEARED' | 'SELECTED' | 'REJECTED';

export interface BulkStageStatusRequest {
  student_ids: string[];
  status: AssignmentStatus;
  result_notes?: string | null;
}

export type StageImportCategory =
  | 'MATCHED'
  | 'ALREADY_AT_STAGE'
  | 'NOT_APPLIED'
  | 'UNKNOWN_REG_NO'
  | 'DUPLICATE_IN_FILE';

export interface StageImportPreviewItem {
  row_index: number;
  roll_number: string;
  student_name?: string | null;
  category: StageImportCategory;
  student_user_id?: string | null;
  branch_code?: string | null;
  cgpa?: number | null;
  current_status?: string | null;
  details?: string | null;
}

export interface StageImportPreviewResponse {
  drive_id: string;
  stage_id: string;
  stage_name: string;
  stage_sequence: number;
  filename: string;
  detected_headers: string[];
  detected_mappings: Record<string, string>;
  total_rows: number;
  matched_count: number;
  already_at_stage_count: number;
  not_applied_count: number;
  unknown_count: number;
  duplicate_count: number;
  can_confirm: boolean;
  items: StageImportPreviewItem[];
  valid_student_ids: string[];
}

export interface StageImportConfirmResponse {
  drive_id: string;
  stage_id: string;
  stage_name: string;
  total_submitted: number;
  newly_assigned_count: number;
  already_assigned_count: number;
  message: string;
}

export interface StageQualifiedStudentItem {
  assignment_id: string;
  stage_id: string;
  student_user_id: string;
  roll_number: string;
  full_name: string;
  email: string;
  branch_code: string;
  cgpa: number;
  status: string;
  assigned_at: string;
}


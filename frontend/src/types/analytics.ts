export interface DriveAnalyticsSummary {
  eligible_count: number;
  registered_count: number;
  registration_rate_percentage: number;
  total_shortlisted_count: number;
  total_selected_count: number;
  overall_conversion_percentage: number;
}

export interface StageFunnelItem {
  stage_id: string;
  name: string;
  stage_type: string;
  sequence_order: number;
  is_published: boolean;
  assigned_count: number;
  shortlisted_count: number;
  appeared_count: number;
  selected_count: number;
  rejected_count: number;
}

export interface DriveBranchBreakdownItem {
  branch_code: string;
  branch_name: string;
  eligible_count: number;
  registered_count: number;
  shortlisted_count: number;
  selected_count: number;
}

export interface DriveAnalyticsResponse {
  drive_id: string;
  title: string;
  company_name: string;
  job_role: string;
  status: string;
  summary: DriveAnalyticsSummary;
  stage_funnel: StageFunnelItem[];
  branch_breakdown: DriveBranchBreakdownItem[];
}

export interface DrivesSummary {
  total_drives: number;
  active_drives: number;
  completed_drives: number;
  draft_drives: number;
}

export interface PlacementMetrics {
  total_active_students: number;
  total_placed_students: number;
  overall_placement_percentage: number;
  total_applications_submitted: number;
  average_ctc_lpa: number | null;
  highest_ctc_lpa: number | null;
}

export interface BranchPlacementStat {
  branch_code: string;
  branch_name: string;
  total_students: number;
  placed_students: number;
  placement_percentage: number;
}

export interface RecentDriveActivity {
  drive_id: string;
  title: string;
  company_name: string;
  job_role: string;
  status: string;
  registered_count: number;
  selected_count: number;
  created_at: string;
}

export interface OverviewAnalyticsResponse {
  drives_summary: DrivesSummary;
  placement_metrics: PlacementMetrics;
  branch_placement_stats: BranchPlacementStat[];
  recent_drives_activity: RecentDriveActivity[];
}

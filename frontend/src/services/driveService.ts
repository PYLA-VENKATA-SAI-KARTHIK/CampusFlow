import { apiClient } from './apiClient';
import type {
  PlacementDrive,
  PlacementDriveCreate,
  PlacementDriveUpdate,
  DriveStatus,
  EligibilityCheckResponse,
  PlacementStage,
  PlacementStageCreate,
  Company,
  CompanyCreate,
  Branch,
  DriveRegistrationWithStudent,
  BulkStageStatusRequest,
  StageImportPreviewResponse,
  StageImportConfirmResponse,
  StageQualifiedStudentItem,
} from '../types/drive';

export const driveService = {
  // Drives
  async listDrives(params?: { status?: string; page?: number; page_size?: number }): Promise<{
    items: PlacementDrive[];
    total: number;
    page: number;
    page_size: number;
    has_next: boolean;
  }> {
    const res = await apiClient.get('/drives', { params });
    return res.data;
  },

  async getDrive(driveId: string): Promise<PlacementDrive> {
    const res = await apiClient.get(`/drives/${driveId}`);
    return res.data;
  },

  async createDrive(data: PlacementDriveCreate): Promise<PlacementDrive> {
    const res = await apiClient.post('/drives', data);
    return res.data;
  },

  async updateDrive(driveId: string, data: PlacementDriveUpdate): Promise<PlacementDrive> {
    const res = await apiClient.patch(`/drives/${driveId}`, data);
    return res.data;
  },

  async updateDriveStatus(driveId: string, status: DriveStatus): Promise<PlacementDrive> {
    const res = await apiClient.post(`/drives/${driveId}/status`, { status });
    return res.data;
  },

  async deleteDrive(driveId: string): Promise<{ message: string; id: string; status: string }> {
    const res = await apiClient.delete(`/drives/${driveId}`);
    return res.data;
  },

  // Eligibility & Registration
  async checkEligibility(driveId: string): Promise<EligibilityCheckResponse> {
    const res = await apiClient.get(`/drives/${driveId}/eligibility-check`);
    return res.data;
  },

  async registerStudent(driveId: string): Promise<any> {
    const res = await apiClient.post(`/drives/${driveId}/register`);
    return res.data;
  },

  async listRegistrations(
    driveId: string,
    params?: { search?: string; branch?: string; status?: string; page?: number; page_size?: number }
  ): Promise<{
    items: DriveRegistrationWithStudent[];
    total: number;
    page: number;
    page_size: number;
    has_next: boolean;
  }> {
    const res = await apiClient.get(`/drives/${driveId}/registrations`, { params });
    return res.data;
  },

  // Stages & Assignments
  async listStages(driveId: string): Promise<PlacementStage[]> {
    const res = await apiClient.get(`/drives/${driveId}/stages`);
    return res.data;
  },

  async createStage(driveId: string, data: PlacementStageCreate): Promise<PlacementStage> {
    const res = await apiClient.post(`/drives/${driveId}/stages`, data);
    return res.data;
  },

  async shortlistStudents(
    driveId: string,
    stageId: string,
    studentIds: string[]
  ): Promise<{ message: string }> {
    const res = await apiClient.post(`/drives/${driveId}/stages/${stageId}/shortlist`, {
      student_ids: studentIds,
    });
    return res.data;
  },

  async bulkUpdateStageStatus(
    driveId: string,
    stageId: string,
    data: BulkStageStatusRequest
  ): Promise<{ message: string }> {
    const res = await apiClient.post(`/drives/${driveId}/stages/${stageId}/bulk-status`, data);
    return res.data;
  },

  async publishStageResults(driveId: string, stageId: string): Promise<{ message: string }> {
    const res = await apiClient.post(`/drives/${driveId}/stages/${stageId}/publish-results`);
    return res.data;
  },

  // Stage Qualified List Import Workflow
  async previewStageQualifiedImport(
    driveId: string,
    stageId: string,
    file: File,
    customMapping?: Record<string, string>
  ): Promise<StageImportPreviewResponse> {
    const formData = new FormData();
    formData.append('file', file);
    if (customMapping) {
      formData.append('custom_mapping', JSON.stringify(customMapping));
    }
    const res = await apiClient.post(`/drives/${driveId}/stages/${stageId}/qualified/preview`, formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return res.data;
  },

  async confirmStageQualifiedImport(
    driveId: string,
    stageId: string,
    data: { filename: string; student_ids: string[] }
  ): Promise<StageImportConfirmResponse> {
    const res = await apiClient.post(`/drives/${driveId}/stages/${stageId}/qualified/confirm`, data);
    return res.data;
  },

  async listStageQualifiedStudents(
    driveId: string,
    stageId: string
  ): Promise<StageQualifiedStudentItem[]> {
    const res = await apiClient.get(`/drives/${driveId}/stages/${stageId}/qualified/students`);
    return res.data;
  },

  // Officer Student Access
  async getStudentResumeDownloadUrl(studentProfileId: string): Promise<string> {
    const res = await apiClient.get(`/officers/students/${studentProfileId}/resume-download-url`);
    return res.data.url;
  },

  // Companies
  async listCompanies(params?: { page?: number; page_size?: number }): Promise<{
    items: Company[];
    total: number;
  }> {
    const res = await apiClient.get('/companies', { params: { page: 1, page_size: 100, ...params } });
    return res.data;
  },

  async createCompany(data: CompanyCreate): Promise<Company> {
    const res = await apiClient.post('/companies', data);
    return res.data;
  },

  // Branches
  async listBranches(): Promise<Branch[]> {
    const res = await apiClient.get('/branches');
    return res.data;
  },
};

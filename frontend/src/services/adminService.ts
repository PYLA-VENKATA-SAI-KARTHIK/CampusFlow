import { apiClient } from './apiClient';
import type {
  AdminUser,
  AdminUserListParams,
  CreateUserPayload,
  UpdateUserPayload,
  BulkImportResponse,
  AdminAuditLog,
  AdminAuditLogListParams,
  PaginatedResult,
} from '../types/admin';

export const adminService = {
  async listUsers(params: AdminUserListParams): Promise<PaginatedResult<AdminUser>> {
    const queryParams = new URLSearchParams();
    if (params.role) queryParams.append('role', params.role);
    if (params.is_active !== undefined) queryParams.append('is_active', String(params.is_active));
    if (params.search) queryParams.append('search', params.search);
    if (params.page) queryParams.append('page', String(params.page));
    if (params.page_size) queryParams.append('page_size', String(params.page_size));

    const response = await apiClient.get<PaginatedResult<AdminUser>>(
      `/admin/users?${queryParams.toString()}`
    );
    return response.data;
  },

  async createUser(payload: CreateUserPayload): Promise<AdminUser> {
    const response = await apiClient.post<AdminUser>('/admin/users', payload);
    return response.data;
  },

  async updateUser(userId: string, payload: UpdateUserPayload): Promise<AdminUser> {
    const response = await apiClient.patch<AdminUser>(`/admin/users/${userId}`, payload);
    return response.data;
  },

  async bulkImportStudents(file: File): Promise<BulkImportResponse> {
    const formData = new FormData();
    formData.append('file', file);

    const response = await apiClient.post<BulkImportResponse>(
      '/admin/students/bulk-import',
      formData,
      {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      }
    );
    return response.data;
  },

  async listAuditLogs(params: AdminAuditLogListParams): Promise<PaginatedResult<AdminAuditLog>> {
    const queryParams = new URLSearchParams();
    if (params.user_id) queryParams.append('user_id', params.user_id);
    if (params.entity_type) queryParams.append('entity_type', params.entity_type);
    if (params.action) queryParams.append('action', params.action);
    if (params.start_date) queryParams.append('start_date', params.start_date);
    if (params.end_date) queryParams.append('end_date', params.end_date);
    if (params.page) queryParams.append('page', String(params.page));
    if (params.page_size) queryParams.append('page_size', String(params.page_size));

    const response = await apiClient.get<PaginatedResult<AdminAuditLog>>(
      `/admin/audit-logs?${queryParams.toString()}`
    );
    return response.data;
  },
};

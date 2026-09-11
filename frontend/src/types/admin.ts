export interface AdminUser {
  id: string;
  email: string;
  full_name: string;
  role: 'STUDENT' | 'OFFICER' | 'ADMIN';
  is_active: boolean;
  must_change_password: boolean;
  last_login_at: string | null;
  created_at: string;
  updated_at: string;
}

export interface AdminUserListParams {
  role?: string;
  is_active?: boolean;
  search?: string;
  page?: number;
  page_size?: number;
}

export interface CreateUserPayload {
  email: string;
  full_name: string;
  role: 'OFFICER' | 'ADMIN';
  password: string;
}

export interface UpdateUserPayload {
  role?: 'OFFICER' | 'ADMIN' | 'STUDENT';
  is_active?: boolean;
  full_name?: string;
}

export interface BulkImportError {
  row_number: number;
  error: string;
}

export interface BulkImportResponse {
  total_rows: number;
  success_count: number;
  error_count: number;
  errors: BulkImportError[];
}

export interface AdminAuditLog {
  id: string;
  performed_by_user_id: string | null;
  action: string;
  entity_type: string;
  entity_id: string | null;
  old_state: Record<string, any> | null;
  new_state: Record<string, any> | null;
  ip_address: string | null;
  created_at: string;
}

export interface AdminAuditLogListParams {
  user_id?: string;
  entity_type?: string;
  action?: string;
  start_date?: string;
  end_date?: string;
  page?: number;
  page_size?: number;
}

export interface PaginatedResult<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

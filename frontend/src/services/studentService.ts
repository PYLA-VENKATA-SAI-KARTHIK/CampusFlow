import { apiClient } from './apiClient';

export interface MasterStudentProfile {
  id: string;
  user_id: string;
  roll_number: string;
  branch_code: string;
  batch_year: number;
  cgpa: number;
  active_backlogs: number;
  phone_number?: string | null;
  personal_email?: string | null;
  gender?: string | null;
  section?: string | null;
  user?: {
    id: string;
    email: string;
    full_name: string;
    role: string;
    is_active: boolean;
  };
  branch?: {
    code: string;
    name: string;
  };
  created_at: string;
  updated_at: string;
}

export interface StudentListResponse {
  items: MasterStudentProfile[];
  total: number;
  page: number;
  page_size: number;
  has_next: boolean;
}

export interface StudentImportPreviewItem {
  row_index: number;
  roll_number: string;
  full_name?: string | null;
  branch_code?: string | null;
  batch_year?: number | null;
  cgpa?: number | null;
  active_backlogs?: number | null;
  personal_email?: string | null;
  phone_number?: string | null;
  gender?: string | null;
  status: 'VALID' | 'DUPLICATE_IN_FILE' | 'MISSING_REG_NO' | 'INVALID_DATA';
  is_existing_in_db: boolean;
  is_active_in_db: boolean;
  error_message?: string | null;
}

export interface StudentImportPreviewResponse {
  filename: string;
  detected_headers: string[];
  detected_mappings: Record<string, string>;
  total_rows: number;
  valid_count: number;
  duplicate_in_file_count: number;
  missing_reg_no_count: number;
  invalid_count: number;
  existing_in_db_count: number;
  can_import: boolean;
  preview_items: StudentImportPreviewItem[];
}

export interface StudentImportConfirmItem {
  roll_number: string;
  full_name?: string | null;
  branch_code: string;
  batch_year: number;
  cgpa: number;
  active_backlogs: number;
  personal_email?: string | null;
  phone_number?: string | null;
  gender?: string | null;
}

export interface StudentImportConfirmResponse {
  total_processed: number;
  created_count: number;
  updated_count: number;
  skipped_count: number;
  message: string;
}

export const studentService = {
  async listMasterStudents(params?: {
    page?: number;
    page_size?: number;
    search?: string;
    branch_code?: string;
    batch_year?: number;
    min_cgpa?: number;
  }): Promise<StudentListResponse> {
    const res = await apiClient.get('/officers/students', { params });
    return res.data;
  },

  async previewImport(file: File, customMapping?: Record<string, string>): Promise<StudentImportPreviewResponse> {
    const formData = new FormData();
    formData.append('file', file);
    if (customMapping) {
      formData.append('custom_mapping', JSON.stringify(customMapping));
    }
    const res = await apiClient.post('/admin/students/import/preview', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return res.data;
  },

  async confirmImport(filename: string, items: StudentImportConfirmItem[]): Promise<StudentImportConfirmResponse> {
    const res = await apiClient.post('/admin/students/import/confirm', {
      filename,
      items,
    });
    return res.data;
  },
};

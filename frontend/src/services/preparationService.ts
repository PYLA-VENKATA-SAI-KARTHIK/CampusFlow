import { apiClient } from './apiClient';
import type {
  OfficerReviewPayload,
  PreparationCategory,
  PreparationMaterial,
  PreparationRole,
  RoleRoadmap,
  SuggestMaterialPayload,
} from '../types/preparation';

export interface PaginatedResult<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
  has_next: boolean;
}

export interface MaterialFilterParams {
  category_id?: string;
  topic_id?: string;
  role_id?: string;
  difficulty?: string;
  material_type?: string;
  search?: string;
  page?: number;
  page_size?: number;
}

export const preparationService = {
  getRoles: async (): Promise<PreparationRole[]> => {
    const res = await apiClient.get<PreparationRole[]>('/preparation/roles');
    return res.data;
  },

  getCategories: async (): Promise<PreparationCategory[]> => {
    const res = await apiClient.get<PreparationCategory[]>('/preparation/categories');
    return res.data;
  },

  getMaterials: async (params: MaterialFilterParams = {}): Promise<PaginatedResult<PreparationMaterial>> => {
    const cleanParams: Record<string, any> = {};
    Object.entries(params).forEach(([key, val]) => {
      if (val !== undefined && val !== null && val !== '') {
        cleanParams[key] = val;
      }
    });
    const res = await apiClient.get<PaginatedResult<PreparationMaterial>>('/preparation/materials', {
      params: cleanParams,
    });
    return res.data;
  },

  getRoleRoadmap: async (roleCode: string): Promise<RoleRoadmap> => {
    const res = await apiClient.get<RoleRoadmap>(`/preparation/roles/${encodeURIComponent(roleCode)}/roadmap`);
    return res.data;
  },

  suggestMaterial: async (payload: SuggestMaterialPayload): Promise<PreparationMaterial> => {
    const res = await apiClient.post<PreparationMaterial>('/preparation/suggest', payload);
    return res.data;
  },

  getMySuggestions: async (page = 1, pageSize = 20): Promise<PaginatedResult<PreparationMaterial>> => {
    const res = await apiClient.get<PaginatedResult<PreparationMaterial>>('/preparation/my-suggestions', {
      params: { page, page_size: pageSize },
    });
    return res.data;
  },

  getPendingSubmissions: async (page = 1, pageSize = 20): Promise<PaginatedResult<PreparationMaterial>> => {
    const res = await apiClient.get<PaginatedResult<PreparationMaterial>>('/preparation/officers/submissions', {
      params: { page, page_size: pageSize },
    });
    return res.data;
  },

  reviewSubmission: async (materialId: string, payload: OfficerReviewPayload): Promise<PreparationMaterial> => {
    const res = await apiClient.post<PreparationMaterial>(
      `/preparation/officers/submissions/${materialId}/review`,
      payload
    );
    return res.data;
  },

  createMaterialAsOfficer: async (payload: SuggestMaterialPayload): Promise<PreparationMaterial> => {
    const res = await apiClient.post<PreparationMaterial>('/preparation/officers/materials', payload);
    return res.data;
  },

  deleteMaterialAsOfficer: async (materialId: string): Promise<void> => {
    await apiClient.delete(`/preparation/officers/materials/${materialId}`);
  },
};

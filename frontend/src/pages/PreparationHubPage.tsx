import React, { useEffect, useState, useMemo } from 'react';
import { useAuthStore } from '../store/authStore';
import { preparationService } from '../services/preparationService';
import type { PaginatedResult } from '../services/preparationService';
import type {
  MaterialDifficulty,
  MaterialType,
  PreparationCategory,
  PreparationMaterial,
  PreparationRole,
  RoleRoadmap,
  SuggestMaterialPayload,
} from '../types/preparation';
import {
  PageHeader,
  Card,
  Badge,
  Button,
  Input,
  Select,
  Textarea,
  Modal,
  Skeleton,
  EmptyState,
  Alert,
} from '../components/ui';

export const PreparationHubPage: React.FC = () => {
  const { user } = useAuthStore();
  const isOfficerOrAdmin = user?.role === 'OFFICER' || user?.role === 'ADMIN';

  // Core data states
  const [roles, setRoles] = useState<PreparationRole[]>([]);
  const [categories, setCategories] = useState<PreparationCategory[]>([]);
  const [materials, setMaterials] = useState<PreparationMaterial[]>([]);
  const [totalMaterials, setTotalMaterials] = useState<number>(0);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  // Active filters
  const [selectedRoleCode, setSelectedRoleCode] = useState<string>('ALL');
  const [roleRoadmap, setRoleRoadmap] = useState<RoleRoadmap | null>(null);
  const [loadingRoadmap, setLoadingRoadmap] = useState<boolean>(false);
  const [selectedCategoryCode, setSelectedCategoryCode] = useState<string>('ALL');
  const [selectedTopicId, setSelectedTopicId] = useState<string>('');
  const [selectedDifficulty, setSelectedDifficulty] = useState<string>('');
  const [selectedType, setSelectedType] = useState<string>('');
  const [searchQuery, setSearchQuery] = useState<string>('');

  // Tab mode for officers/admins and student submissions
  const [activeTab, setActiveTab] = useState<'EXPLORE' | 'REVIEW_QUEUE' | 'MY_SUGGESTIONS'>('EXPLORE');

  // Submissions state
  const [pendingSubmissions, setPendingSubmissions] = useState<PreparationMaterial[]>([]);
  const [totalPending, setTotalPending] = useState<number>(0);
  const [loadingPending, setLoadingPending] = useState<boolean>(false);
  const [mySuggestions, setMySuggestions] = useState<PreparationMaterial[]>([]);
  const [totalMySuggestions, setTotalMySuggestions] = useState<number>(0);
  const [loadingMySuggestions, setLoadingMySuggestions] = useState<boolean>(false);

  // Modal states
  const [isSuggestModalOpen, setIsSuggestModalOpen] = useState<boolean>(false);
  const [isOfficerAddModalOpen, setIsOfficerAddModalOpen] = useState<boolean>(false);
  const [reviewModalMaterial, setReviewModalMaterial] = useState<PreparationMaterial | null>(null);
  const [reviewNotes, setReviewNotes] = useState<string>('');
  const [reviewActionLoading, setReviewActionLoading] = useState<boolean>(false);

  // Suggest / Add form state
  const [formData, setFormData] = useState<{
    topic_id: string;
    role_id: string;
    title: string;
    url: string;
    description: string;
    material_type: MaterialType;
    difficulty: MaterialDifficulty;
    source: string;
  }>({
    topic_id: '',
    role_id: '',
    title: '',
    url: '',
    description: '',
    material_type: 'ARTICLE',
    difficulty: 'BEGINNER',
    source: '',
  });
  const [formError, setFormError] = useState<string | null>(null);
  const [formSuccess, setFormSuccess] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState<boolean>(false);

  // Flattened topic list for dropdowns
  const allTopics = useMemo(() => {
    return categories.flatMap((cat) => cat.topics);
  }, [categories]);

  // Initial load: roles and categories
  useEffect(() => {
    const fetchInitialData = async () => {
      setLoading(true);
      setError(null);
      try {
        const [fetchedRoles, fetchedCats] = await Promise.all([
          preparationService.getRoles(),
          preparationService.getCategories(),
        ]);
        setRoles(fetchedRoles);
        setCategories(fetchedCats);
      } catch (err: any) {
        setError(err.response?.data?.detail || 'Failed to load preparation hub resources. Please refresh.');
      } finally {
        setLoading(false);
      }
    };
    fetchInitialData();
  }, []);

  // Fetch role roadmap when selected role changes
  useEffect(() => {
    if (!selectedRoleCode || selectedRoleCode === 'ALL') {
      setRoleRoadmap(null);
      return;
    }
    const fetchRoadmap = async () => {
      setLoadingRoadmap(true);
      try {
        const roadmap = await preparationService.getRoleRoadmap(selectedRoleCode);
        setRoleRoadmap(roadmap);
      } catch {
        setRoleRoadmap(null);
      } finally {
        setLoadingRoadmap(false);
      }
    };
    fetchRoadmap();
  }, [selectedRoleCode]);

  // Fetch materials when filters change (Shared Library)
  const fetchMaterials = React.useCallback(async () => {
    setLoading(true);
    try {
      const activeCat = categories.find((c) => c.code === selectedCategoryCode);
      const targetRoleId = selectedRoleCode === 'ALL' ? undefined : roles.find((r) => r.code === selectedRoleCode)?.id;
      const result: PaginatedResult<PreparationMaterial> = await preparationService.getMaterials({
        category_id: activeCat?.id,
        topic_id: selectedTopicId || undefined,
        role_id: targetRoleId,
        difficulty: selectedDifficulty || undefined,
        material_type: selectedType || undefined,
        search: searchQuery || undefined,
        page: 1,
        page_size: 50,
      });
      setMaterials(result.items);
      setTotalMaterials(result.total);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to load materials.');
    } finally {
      setLoading(false);
    }
  }, [
    categories,
    selectedCategoryCode,
    selectedTopicId,
    selectedRoleCode,
    selectedDifficulty,
    selectedType,
    searchQuery,
    roles,
  ]);

  useEffect(() => {
    if (activeTab === 'EXPLORE') {
      fetchMaterials();
    }
  }, [activeTab, fetchMaterials]);

  // Fetch officer pending review submissions
  const loadPendingSubmissions = React.useCallback(async () => {
    if (!isOfficerOrAdmin) return;
    setLoadingPending(true);
    try {
      const res = await preparationService.getPendingSubmissions(1, 50);
      setPendingSubmissions(res.items);
      setTotalPending(res.total);
    } catch {
      // Non-blocking catch
    } finally {
      setLoadingPending(false);
    }
  }, [isOfficerOrAdmin]);

  useEffect(() => {
    if (isOfficerOrAdmin) {
      loadPendingSubmissions();
    }
  }, [isOfficerOrAdmin, loadPendingSubmissions]);

  // Fetch student's own submissions
  const loadMySuggestions = React.useCallback(async () => {
    if (user?.role !== 'STUDENT') return;
    setLoadingMySuggestions(true);
    try {
      const res = await preparationService.getMySuggestions(1, 50);
      setMySuggestions(res.items);
      setTotalMySuggestions(res.total);
    } catch {
      // Non-blocking catch
    } finally {
      setLoadingMySuggestions(false);
    }
  }, [user?.role]);

  useEffect(() => {
    if (activeTab === 'MY_SUGGESTIONS') {
      loadMySuggestions();
    }
  }, [activeTab, loadMySuggestions]);

  // Form submit handler (Suggest or Direct Add)
  const handleSubmitMaterial = async (e: React.FormEvent, isOfficerDirect = false) => {
    e.preventDefault();
    setFormError(null);
    setFormSuccess(null);

    if (!formData.title.trim()) {
      setFormError('Please enter a title for the material.');
      return;
    }
    if (!formData.topic_id) {
      setFormError('Please select a relevant topic.');
      return;
    }
    if (!formData.url.trim()) {
      setFormError('Please provide a valid URL.');
      return;
    }
    try {
      const parsed = new URL(formData.url);
      if (parsed.protocol !== 'http:' && parsed.protocol !== 'https:') {
        setFormError('URL must begin with http:// or https://');
        return;
      }
    } catch {
      setFormError('Please enter a valid, well-formed URL (e.g. https://example.com/guide).');
      return;
    }

    setSubmitting(true);
    try {
      const payload: SuggestMaterialPayload = {
        topic_id: formData.topic_id,
        role_id: formData.role_id || null,
        title: formData.title.trim(),
        url: formData.url.trim(),
        description: formData.description.trim() || null,
        material_type: formData.material_type,
        difficulty: formData.difficulty,
        source: formData.source.trim() || null,
      };

      if (isOfficerDirect) {
        await preparationService.createMaterialAsOfficer(payload);
        setFormSuccess('Material published successfully to the Preparation Hub!');
        await fetchMaterials();
      } else {
        await preparationService.suggestMaterial(payload);
        setFormSuccess('Thank you! Your suggestion has been submitted for Placement Officer review.');
        await loadMySuggestions();
      }

      setFormData({
        topic_id: '',
        role_id: '',
        title: '',
        url: '',
        description: '',
        material_type: 'ARTICLE',
        difficulty: 'BEGINNER',
        source: '',
      });
      setTimeout(() => {
        setIsSuggestModalOpen(false);
        setIsOfficerAddModalOpen(false);
        setFormSuccess(null);
      }, 1500);
    } catch (err: any) {
      setFormError(err.response?.data?.detail || 'Failed to submit material. Please check input values.');
    } finally {
      setSubmitting(false);
    }
  };

  // Review submission handler (Officer/Admin)
  const [reviewError, setReviewError] = useState<string | null>(null);

  const handleReviewAction = async (status: 'APPROVED' | 'REJECTED') => {
    if (!reviewModalMaterial) return;
    setReviewActionLoading(true);
    setReviewError(null);
    try {
      await preparationService.reviewSubmission(reviewModalMaterial.id, {
        status,
        review_notes: reviewNotes.trim() || undefined,
      });
      setReviewModalMaterial(null);
      setReviewNotes('');
      await loadPendingSubmissions();
      await fetchMaterials();
    } catch (err: any) {
      setReviewError(err.response?.data?.detail || 'Failed to review submission.');
    } finally {
      setReviewActionLoading(false);
    }
  };

  const handleDeleteMaterial = async (materialId: string) => {
    if (!window.confirm('Are you sure you want to remove this preparation material?')) return;
    try {
      await preparationService.deleteMaterialAsOfficer(materialId);
      await fetchMaterials();
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Failed to delete material.');
    }
  };

  const getTypeIcon = (type: MaterialType) => {
    switch (type) {
      case 'VIDEO':
        return (
          <svg className="w-3.5 h-3.5 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" aria-hidden="true">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M14.752 11.168l-3.197-2.132A1 1 0 0010 9.87v4.263a1 1 0 001.555.832l3.197-2.132a1 1 0 000-1.664z" />
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
        );
      case 'PDF':
        return (
          <svg className="w-3.5 h-3.5 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" aria-hidden="true">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M7 21h10a2 2 0 002-2V9.414a1 1 0 00-.293-.707l-5.414-5.414A1 1 0 0012.586 3H7a2 2 0 00-2 2v14a2 2 0 002 2z" />
          </svg>
        );
      case 'PRACTICE_QUESTIONS':
        return (
          <svg className="w-3.5 h-3.5 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" aria-hidden="true">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-6 9l2 2 4-4" />
          </svg>
        );
      case 'COURSE':
        return (
          <svg className="w-3.5 h-3.5 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" aria-hidden="true">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" />
          </svg>
        );
      default:
        return (
          <svg className="w-3.5 h-3.5 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" aria-hidden="true">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M19 20H5a2 2 0 01-2-2V6a2 2 0 012-2h10a2 2 0 012 2v1m2 13a2 2 0 01-2-2V7m2 13a2 2 0 002-2V9a2 2 0 00-2-2h-2m-4-3H9M7 16h6M7 8h6v4H7V8z" />
          </svg>
        );
    }
  };

  return (
    <div className="space-y-6 max-w-7xl mx-auto pb-12">
      {/* SaaS Page Header */}
      <PageHeader
        eyebrow="Placement Preparation Hub"
        badge={
          <Badge variant="primary" size="sm" dot>
            Career Roadmap Workspace
          </Badge>
        }
        title="Curated Placement Preparation & Roadmaps"
        description="Master Aptitude, Technical Core, Verbal Ability, and Interview rounds with high-yield roadmaps, practice materials, and verified study guides tailored for campus recruitment drives."
        actions={
          <div className="flex flex-wrap items-center gap-2.5">
            {user?.role === 'STUDENT' && (
              <Button
                variant="primary"
                size="md"
                onClick={() => {
                  setFormError(null);
                  setFormSuccess(null);
                  setIsSuggestModalOpen(true);
                }}
                leftIcon={
                  <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 4v16m8-8H4" />
                  </svg>
                }
              >
                Suggest a Material
              </Button>
            )}

            {isOfficerOrAdmin && (
              <Button
                variant="primary"
                size="md"
                onClick={() => {
                  setFormError(null);
                  setFormSuccess(null);
                  setIsOfficerAddModalOpen(true);
                }}
                className="bg-emerald-600 hover:bg-emerald-700 text-white shadow-emerald-600/20"
                leftIcon={
                  <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 4v16m8-8H4" />
                  </svg>
                }
              >
                Publish New Material
              </Button>
            )}
          </div>
        }
      />

      {/* Primary Navigation Tabs */}
      <div className="flex items-center gap-2 border-b border-slate-200/80 pb-3">
        <button
          type="button"
          onClick={() => setActiveTab('EXPLORE')}
          className={`px-3.5 py-2 rounded-xl text-xs font-bold transition duration-150 ${
            activeTab === 'EXPLORE'
              ? 'bg-indigo-600 text-white shadow-xs'
              : 'text-slate-600 hover:text-slate-900 hover:bg-slate-100'
          }`}
        >
          Explore Library
        </button>

        {isOfficerOrAdmin && (
          <button
            type="button"
            onClick={() => {
              setActiveTab('REVIEW_QUEUE');
              loadPendingSubmissions();
            }}
            className={`px-3.5 py-2 rounded-xl text-xs font-bold transition duration-150 inline-flex items-center gap-2 ${
              activeTab === 'REVIEW_QUEUE'
                ? 'bg-indigo-600 text-white shadow-xs'
                : 'text-slate-600 hover:text-slate-900 hover:bg-slate-100'
            }`}
          >
            <span>Review Queue</span>
            {totalPending > 0 && (
              <span className="px-1.5 py-0.5 rounded-full bg-amber-400 text-slate-900 font-black text-[10px]">
                {totalPending}
              </span>
            )}
          </button>
        )}

        {user?.role === 'STUDENT' && (
          <button
            type="button"
            onClick={() => setActiveTab('MY_SUGGESTIONS')}
            className={`px-3.5 py-2 rounded-xl text-xs font-bold transition duration-150 ${
              activeTab === 'MY_SUGGESTIONS'
                ? 'bg-indigo-600 text-white shadow-xs'
                : 'text-slate-600 hover:text-slate-900 hover:bg-slate-100'
            }`}
          >
            My Submitted Suggestions
          </button>
        )}
      </div>

      {/* Main Tab 1: EXPLORE LIBRARY */}
      {activeTab === 'EXPLORE' && (
        <div className="space-y-6">
          {/* Target Role Roadmap Section */}
          <Card className="p-5 sm:p-6 space-y-4">
            <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2">
              <div>
                <h2 className="text-sm font-bold text-slate-900 tracking-tight flex items-center gap-2">
                  <span>Target Role Roadmap</span>
                  <span className="text-xs font-normal text-slate-500">
                    (Select a career profile to view core curriculum)
                  </span>
                </h2>
              </div>
            </div>

            {/* Role Pills Selector */}
            <div className="flex items-center gap-2 overflow-x-auto pb-2 scrollbar-thin">
              <button
                type="button"
                onClick={() => {
                  setSelectedRoleCode('ALL');
                  setSelectedTopicId('');
                }}
                className={`px-4 py-2 rounded-xl text-xs font-bold transition whitespace-nowrap flex items-center gap-2 ${
                  selectedRoleCode === 'ALL'
                    ? 'bg-indigo-600 text-white shadow-sm shadow-indigo-600/30'
                    : 'bg-slate-100 text-slate-700 hover:bg-slate-200'
                }`}
              >
                <span>All Career Tracks</span>
              </button>
              {roles.map((role) => (
                <button
                  key={role.id}
                  type="button"
                  onClick={() => {
                    setSelectedRoleCode(role.code);
                    setSelectedTopicId('');
                  }}
                  className={`px-4 py-2 rounded-xl text-xs font-bold transition whitespace-nowrap flex items-center gap-2 ${
                    selectedRoleCode === role.code
                      ? 'bg-indigo-600 text-white shadow-sm shadow-indigo-600/30'
                      : 'bg-slate-100 text-slate-700 hover:bg-slate-200'
                  }`}
                >
                  <span>{role.name}</span>
                </button>
              ))}
            </div>

            {/* Role Roadmap Details Card */}
            {loadingRoadmap ? (
              <div className="py-6 space-y-2">
                <Skeleton variant="text" className="w-1/3" />
                <Skeleton variant="rectangular" className="h-16" />
              </div>
            ) : selectedRoleCode === 'ALL' ? (
              <div className="bg-slate-50 rounded-xl p-4.5 border border-slate-200/70 space-y-1">
                <div className="text-xs font-bold text-slate-900">
                  Comprehensive Campus Placement Preparation Library
                </div>
                <div className="text-xs text-slate-600 leading-relaxed">
                  Showing all verified foundation study guides, aptitude problem sets, interview cheat-sheets, and role-specific roadmaps.
                </div>
              </div>
            ) : roleRoadmap ? (
              <div className="bg-slate-50 rounded-xl p-4.5 border border-slate-200/70 space-y-3">
                <div className="text-xs text-slate-600 leading-relaxed">
                  <span className="font-bold text-slate-900">{roleRoadmap.role.name}: </span>
                  {roleRoadmap.role.description}
                </div>

                {/* Topic tags for this role */}
                <div className="space-y-2 pt-1 border-t border-slate-200/50">
                  <div className="text-[11px] font-bold uppercase tracking-wider text-slate-500">
                    Recommended Topics for this Profile:
                  </div>
                  <div className="flex flex-wrap gap-2">
                    {roleRoadmap.topics.map((rt) => (
                      <button
                        key={rt.topic.id}
                        type="button"
                        onClick={() => setSelectedTopicId(selectedTopicId === rt.topic.id ? '' : rt.topic.id)}
                        className={`px-3 py-1.5 rounded-lg text-xs font-semibold border transition inline-flex items-center gap-1.5 ${
                          selectedTopicId === rt.topic.id
                            ? 'bg-indigo-50 border-indigo-300 text-indigo-700 font-bold shadow-xs'
                            : 'bg-white border-slate-200 text-slate-700 hover:border-slate-300 hover:bg-slate-50'
                        }`}
                      >
                        <span>{rt.topic.name}</span>
                        <Badge
                          size="sm"
                          variant={
                            rt.importance === 'CORE'
                              ? 'danger'
                              : rt.importance === 'ELECTIVE'
                              ? 'warning'
                              : 'neutral'
                          }
                        >
                          {rt.importance}
                        </Badge>
                      </button>
                    ))}
                  </div>
                </div>
              </div>
            ) : null}
          </Card>

          {/* Category Tabs & Multi-Filter Workspace */}
          <Card className="p-5 sm:p-6 space-y-4">
            {/* Category Pill Tabs */}
            <div className="flex items-center gap-2 overflow-x-auto pb-2 border-b border-slate-100 scrollbar-thin">
              <button
                type="button"
                onClick={() => {
                  setSelectedCategoryCode('ALL');
                  setSelectedTopicId('');
                }}
                className={`px-3.5 py-1.5 rounded-lg text-xs font-bold transition whitespace-nowrap ${
                  selectedCategoryCode === 'ALL'
                    ? 'bg-slate-900 text-white'
                    : 'bg-slate-100 text-slate-600 hover:bg-slate-200 hover:text-slate-900'
                }`}
              >
                All Categories
              </button>
              {categories.map((cat) => (
                <button
                  key={cat.id}
                  type="button"
                  onClick={() => {
                    setSelectedCategoryCode(cat.code);
                    setSelectedTopicId('');
                  }}
                  className={`px-3.5 py-1.5 rounded-lg text-xs font-bold transition whitespace-nowrap flex items-center gap-1.5 ${
                    selectedCategoryCode === cat.code
                      ? 'bg-indigo-600 text-white shadow-xs'
                      : 'bg-slate-100 text-slate-600 hover:bg-slate-200 hover:text-slate-900'
                  }`}
                >
                  <span>{cat.name}</span>
                </button>
              ))}
            </div>

            {/* Sub-filters (Topic, Difficulty, Material Type, Search) */}
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
              {/* Topic Select */}
              <div>
                <Select
                  label="Topic Filter"
                  value={selectedTopicId}
                  onChange={(e) => setSelectedTopicId(e.target.value)}
                >
                  <option value="">All Topics</option>
                  {(selectedCategoryCode === 'ALL'
                    ? allTopics
                    : categories.find((c) => c.code === selectedCategoryCode)?.topics || []
                  ).map((t) => (
                    <option key={t.id} value={t.id}>
                      {t.name}
                    </option>
                  ))}
                </Select>
              </div>

              {/* Difficulty Select */}
              <div>
                <Select
                  label="Difficulty"
                  value={selectedDifficulty}
                  onChange={(e) => setSelectedDifficulty(e.target.value)}
                >
                  <option value="">All Difficulties</option>
                  <option value="BEGINNER">Beginner</option>
                  <option value="INTERMEDIATE">Intermediate</option>
                  <option value="ADVANCED">Advanced</option>
                </Select>
              </div>

              {/* Material Type Select */}
              <div>
                <Select
                  label="Resource Type"
                  value={selectedType}
                  onChange={(e) => setSelectedType(e.target.value)}
                >
                  <option value="">All Types</option>
                  <option value="ARTICLE">Article / Tutorial</option>
                  <option value="VIDEO">Video Lecture</option>
                  <option value="PDF">PDF / Cheatsheet</option>
                  <option value="PRACTICE_QUESTIONS">Practice Questions</option>
                  <option value="DOCUMENTATION">Official Documentation</option>
                  <option value="COURSE">Free Course</option>
                </Select>
              </div>

              {/* Search Bar */}
              <div>
                <Input
                  label="Search Keywords"
                  type="text"
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  placeholder="Search by title..."
                  leftIcon={
                    <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        strokeWidth="2"
                        d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"
                      />
                    </svg>
                  }
                />
              </div>
            </div>
          </Card>

          {/* Section Subheader with count */}
          <div className="flex items-center justify-between px-1">
            <span className="text-xs font-bold text-slate-700">
              Verified Study Resources {totalMaterials > 0 && <span className="text-slate-400 font-normal">({totalMaterials} items)</span>}
            </span>
          </div>

          {/* Resource Library Grid */}
          {loading ? (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {[1, 2, 3, 4, 5, 6].map((idx) => (
                <Card key={idx} className="p-5 space-y-3">
                  <div className="flex justify-between">
                    <Skeleton variant="text" className="w-20" />
                    <Skeleton variant="text" className="w-16" />
                  </div>
                  <Skeleton variant="rectangular" className="h-12" />
                  <Skeleton variant="text" className="w-full" />
                  <div className="pt-3 border-t border-slate-100 flex justify-between">
                    <Skeleton variant="text" className="w-24" />
                    <Skeleton variant="text" className="w-20" />
                  </div>
                </Card>
              ))}
            </div>
          ) : error ? (
            <Alert variant="danger" title="Resource Error">
              <div className="space-y-2">
                <p>{error}</p>
                <Button variant="danger" size="sm" onClick={() => window.location.reload()}>
                  Retry
                </Button>
              </div>
            </Alert>
          ) : materials.length === 0 ? (
            <EmptyState
              title="No Approved Materials Found"
              description="No verified preparation resources match your active filters. Try resetting the topic or search filters, or suggest a high-quality study resource!"
              action={
                user?.role === 'STUDENT' ? (
                  <Button variant="primary" size="sm" onClick={() => setIsSuggestModalOpen(true)}>
                    Suggest a Resource
                  </Button>
                ) : undefined
              }
            />
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {materials.map((mat) => (
                <Card
                  key={mat.id}
                  variant="elevated"
                  hoverable
                  className="p-5 flex flex-col justify-between group"
                >
                  <div className="space-y-3">
                    {/* Header Badges */}
                    <div className="flex items-center justify-between gap-2">
                      <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-lg bg-indigo-50 text-indigo-700 text-[11px] font-bold">
                        {getTypeIcon(mat.material_type)}
                        <span>{mat.material_type.replace('_', ' ')}</span>
                      </span>

                      <span
                        className={`px-2 py-0.5 rounded-md text-[10px] font-bold border ${
                          mat.difficulty === 'BEGINNER'
                            ? 'bg-emerald-50 text-emerald-700 border-emerald-200'
                            : mat.difficulty === 'INTERMEDIATE'
                            ? 'bg-amber-50 text-amber-700 border-amber-200'
                            : 'bg-rose-50 text-rose-700 border-rose-200'
                        }`}
                      >
                        {mat.difficulty}
                      </span>
                    </div>

                    {/* Title */}
                    <h3 className="text-sm font-bold text-slate-900 group-hover:text-indigo-600 transition leading-snug line-clamp-2">
                      {mat.title}
                    </h3>

                    {/* Description */}
                    {mat.description && (
                      <p className="text-xs text-slate-600 line-clamp-3 leading-relaxed">
                        {mat.description}
                      </p>
                    )}
                  </div>

                  {/* Footer metadata & Link button */}
                  <div className="pt-4 mt-3 border-t border-slate-100 flex items-center justify-between">
                    <div className="text-[11px] text-slate-500 truncate max-w-[140px]">
                      {mat.source ? (
                        <span className="font-semibold text-slate-700">{mat.source}</span>
                      ) : (
                        <span>Verified Resource</span>
                      )}
                    </div>

                    <div className="flex items-center gap-1.5">
                      {isOfficerOrAdmin && (
                        <button
                          type="button"
                          title="Delete Material"
                          aria-label="Delete Material"
                          onClick={() => handleDeleteMaterial(mat.id)}
                          className="p-1.5 rounded-lg text-slate-400 hover:text-rose-600 hover:bg-rose-50 transition"
                        >
                          <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                          </svg>
                        </button>
                      )}
                      <a
                        href={mat.url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="px-3 py-1.5 rounded-lg bg-indigo-50 hover:bg-indigo-600 text-indigo-700 hover:text-white text-xs font-bold transition flex items-center gap-1"
                      >
                        <span>Open Guide</span>
                        <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
                        </svg>
                      </a>
                    </div>
                  </div>
                </Card>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Main Tab 2: OFFICER / ADMIN REVIEW QUEUE */}
      {activeTab === 'REVIEW_QUEUE' && isOfficerOrAdmin && (
        <div className="space-y-4">
          <Card className="p-5 flex items-center justify-between">
            <div>
              <h2 className="text-sm font-bold text-slate-900">Student Material Suggestion Queue</h2>
              <p className="text-xs text-slate-500">
                Review, verify URL safety, and approve or reject community suggested placement materials.
              </p>
            </div>
            <Button variant="outline" size="sm" onClick={loadPendingSubmissions}>
              Refresh Queue
            </Button>
          </Card>

          {loadingPending ? (
            <div className="py-12 text-center text-xs text-slate-500">Loading pending suggestions...</div>
          ) : pendingSubmissions.length === 0 ? (
            <EmptyState
              title="Review Queue is Clear"
              description="There are no pending material suggestions awaiting review."
            />
          ) : (
            <div className="grid grid-cols-1 gap-3">
              {pendingSubmissions.map((sub) => (
                <Card key={sub.id} className="p-5 border-amber-200 shadow-xs space-y-3">
                  <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
                    <div className="space-y-1">
                      <div className="flex items-center gap-2">
                        <Badge variant="warning" size="sm">
                          PENDING REVIEW
                        </Badge>
                        <span className="text-xs font-semibold text-slate-500">
                          {sub.material_type} &bull; {sub.difficulty}
                        </span>
                      </div>
                      <h4 className="text-sm font-bold text-slate-900">{sub.title}</h4>
                      {sub.description && (
                        <p className="text-xs text-slate-600">{sub.description}</p>
                      )}
                    </div>

                    <div className="flex items-center gap-2">
                      <a
                        href={sub.url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="px-3 py-1.5 rounded-lg bg-slate-100 hover:bg-slate-200 text-xs font-bold text-slate-700"
                      >
                        Preview URL ↗
                      </a>
                      <Button
                        variant="primary"
                        size="sm"
                        onClick={() => {
                          setReviewModalMaterial(sub);
                          setReviewNotes('');
                        }}
                      >
                        Review Action
                      </Button>
                    </div>
                  </div>

                  <div className="text-[11px] text-slate-400">
                    URL: <span className="font-mono text-slate-600">{sub.url}</span>
                  </div>
                </Card>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Main Tab 3: STUDENT MY SUGGESTIONS */}
      {activeTab === 'MY_SUGGESTIONS' && user?.role === 'STUDENT' && (
        <div className="space-y-4">
          <Card className="p-5 flex items-center justify-between">
            <div>
              <h2 className="text-sm font-bold text-slate-900">
                My Suggested Materials {totalMySuggestions > 0 && <span className="text-slate-400 font-normal">({totalMySuggestions})</span>}
              </h2>
              <p className="text-xs text-slate-500">Track the status of materials you submitted to help fellow students.</p>
            </div>
            <Button variant="primary" size="sm" onClick={() => setIsSuggestModalOpen(true)}>
              + Suggest Another
            </Button>
          </Card>

          {loadingMySuggestions ? (
            <div className="py-12 text-center text-xs text-slate-500">Loading your submissions...</div>
          ) : mySuggestions.length === 0 ? (
            <EmptyState
              title="No suggestions submitted yet"
              description="Found a great tutorial or problem set? Suggest it to earn contribution credit!"
            />
          ) : (
            <div className="grid grid-cols-1 gap-3">
              {mySuggestions.map((item) => (
                <Card key={item.id} className="p-4 space-y-2">
                  <div className="flex items-center justify-between">
                    <h4 className="text-xs font-bold text-slate-900">{item.title}</h4>
                    <Badge
                      size="sm"
                      variant={
                        item.status === 'APPROVED'
                          ? 'success'
                          : item.status === 'REJECTED'
                          ? 'danger'
                          : 'warning'
                      }
                    >
                      {item.status}
                    </Badge>
                  </div>
                  <div className="text-xs text-slate-500 font-mono truncate">{item.url}</div>
                  {item.review_notes && (
                    <div className="text-[11px] text-slate-600 bg-slate-50 p-2.5 rounded-lg border border-slate-200/60">
                      <span className="font-bold">Officer Feedback: </span>
                      {item.review_notes}
                    </div>
                  )}
                </Card>
              ))}
            </div>
          )}
        </div>
      )}

      {/* MODAL 1: STUDENT SUGGEST MATERIAL / OFFICER ADD MATERIAL */}
      <Modal
        isOpen={isSuggestModalOpen || isOfficerAddModalOpen}
        onClose={() => {
          setIsSuggestModalOpen(false);
          setIsOfficerAddModalOpen(false);
        }}
        title={isOfficerAddModalOpen ? 'Publish Official Material' : 'Suggest a Placement Material'}
        maxWidth="lg"
      >
        <div className="space-y-4">
          {formError && (
            <Alert variant="danger">
              {formError}
            </Alert>
          )}

          {formSuccess && (
            <Alert variant="success">
              {formSuccess}
            </Alert>
          )}

          <form onSubmit={(e) => handleSubmitMaterial(e, isOfficerAddModalOpen)} className="space-y-3.5">
            {/* Topic (First Select in modal for E2E contract) */}
            <div>
              <Select
                label="Topic"
                required
                value={formData.topic_id}
                onChange={(e) => setFormData({ ...formData, topic_id: e.target.value })}
              >
                <option value="">-- Select Relevant Topic --</option>
                {allTopics.map((t) => (
                  <option key={t.id} value={t.id}>
                    {t.name}
                  </option>
                ))}
              </Select>
            </div>

            {/* Target Role (Optional) */}
            <div>
              <Select
                label="Target Role (Optional)"
                value={formData.role_id}
                onChange={(e) => setFormData({ ...formData, role_id: e.target.value })}
              >
                <option value="">-- All General Roles --</option>
                {roles.map((r) => (
                  <option key={r.id} value={r.id}>
                    {r.name}
                  </option>
                ))}
              </Select>
            </div>

            {/* Title */}
            <div>
              <Input
                label="Material Title"
                type="text"
                required
                value={formData.title}
                onChange={(e) => setFormData({ ...formData, title: e.target.value })}
                placeholder="e.g. Master Binary Search Patterns & Questions"
              />
            </div>

            {/* URL */}
            <div>
              <Input
                label="Resource URL"
                type="url"
                required
                value={formData.url}
                onChange={(e) => setFormData({ ...formData, url: e.target.value })}
                placeholder="https://..."
              />
            </div>

            {/* Type and Difficulty Grid */}
            <div className="grid grid-cols-2 gap-3">
              <div>
                <Select
                  label="Type"
                  value={formData.material_type}
                  onChange={(e) => setFormData({ ...formData, material_type: e.target.value as MaterialType })}
                >
                  <option value="ARTICLE">Article / Tutorial</option>
                  <option value="VIDEO">Video Lecture</option>
                  <option value="PDF">PDF / Notes</option>
                  <option value="PRACTICE_QUESTIONS">Practice Questions</option>
                  <option value="DOCUMENTATION">Documentation</option>
                  <option value="COURSE">Course</option>
                  <option value="OTHER">Other</option>
                </Select>
              </div>

              <div>
                <Select
                  label="Difficulty"
                  value={formData.difficulty}
                  onChange={(e) => setFormData({ ...formData, difficulty: e.target.value as MaterialDifficulty })}
                >
                  <option value="BEGINNER">Beginner</option>
                  <option value="INTERMEDIATE">Intermediate</option>
                  <option value="ADVANCED">Advanced</option>
                </Select>
              </div>
            </div>

            {/* Source */}
            <div>
              <Input
                label="Source / Author (Optional)"
                type="text"
                value={formData.source}
                onChange={(e) => setFormData({ ...formData, source: e.target.value })}
                placeholder="e.g. GeeksforGeeks, LeetCode, Official Docs"
              />
            </div>

            {/* Description */}
            <div>
              <Textarea
                label="Brief Description (Optional)"
                rows={3}
                value={formData.description}
                onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                placeholder="Explain why this resource is useful for placement preparation..."
              />
            </div>

            {/* Action Buttons */}
            <div className="flex items-center justify-end gap-2 pt-3 border-t border-slate-100">
              <Button
                variant="outline"
                size="md"
                onClick={() => {
                  setIsSuggestModalOpen(false);
                  setIsOfficerAddModalOpen(false);
                }}
              >
                Cancel
              </Button>
              <Button
                variant="primary"
                size="md"
                type="submit"
                isLoading={submitting}
              >
                {isOfficerAddModalOpen ? 'Publish Material' : 'Submit for Review'}
              </Button>
            </div>
          </form>
        </div>
      </Modal>

      {/* MODAL 2: OFFICER REVIEW ACTION MODAL */}
      {reviewModalMaterial && (
        <Modal
          isOpen={!!reviewModalMaterial}
          onClose={() => setReviewModalMaterial(null)}
          title="Review Suggestion"
          maxWidth="md"
        >
          <div className="space-y-4">
            <div className="space-y-2 bg-slate-50 p-3.5 rounded-xl border border-slate-200/70 text-xs">
              <div className="font-bold text-slate-900">{reviewModalMaterial.title}</div>
              <div className="text-slate-600 text-[11px] font-mono break-all">{reviewModalMaterial.url}</div>
              {reviewModalMaterial.description && (
                <div className="text-slate-600 text-xs">{reviewModalMaterial.description}</div>
              )}
            </div>

            {reviewError && (
              <Alert variant="danger" onClose={() => setReviewError(null)}>
                {reviewError}
              </Alert>
            )}

            <div>
              <Textarea
                label="Review Notes (Optional)"
                rows={2}
                value={reviewNotes}
                onChange={(e) => setReviewNotes(e.target.value)}
                placeholder="Optional notes or feedback..."
              />
            </div>

            <div className="flex items-center justify-end gap-2 pt-3 border-t border-slate-100">
              <Button
                variant="outline"
                size="sm"
                onClick={() => setReviewModalMaterial(null)}
              >
                Cancel
              </Button>
              <Button
                variant="danger"
                size="sm"
                disabled={reviewActionLoading}
                onClick={() => handleReviewAction('REJECTED')}
              >
                Reject
              </Button>
              <Button
                variant="primary"
                size="sm"
                className="bg-emerald-600 hover:bg-emerald-700 text-white shadow-emerald-600/20"
                disabled={reviewActionLoading}
                onClick={() => handleReviewAction('APPROVED')}
              >
                Approve & Publish
              </Button>
            </div>
          </div>
        </Modal>
      )}
    </div>
  );
};

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
  const [selectedRoleCode, setSelectedRoleCode] = useState<string>('SOFTWARE_DEVELOPER');
  const [roleRoadmap, setRoleRoadmap] = useState<RoleRoadmap | null>(null);
  const [loadingRoadmap, setLoadingRoadmap] = useState<boolean>(false);
  const [selectedCategoryCode, setSelectedCategoryCode] = useState<string>('ALL');
  const [selectedTopicId, setSelectedTopicId] = useState<string>('');
  const [selectedDifficulty, setSelectedDifficulty] = useState<string>('');
  const [selectedType, setSelectedType] = useState<string>('');
  const [searchQuery, setSearchQuery] = useState<string>('');
  const page = 1;

  // Tab mode for officers/admins
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
        if (fetchedRoles.length > 0 && !selectedRoleCode) {
          setSelectedRoleCode(fetchedRoles[0].code);
        }
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
    if (!selectedRoleCode) return;
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

  // Fetch materials when filters change
  useEffect(() => {
    if (activeTab !== 'EXPLORE') return;
    const fetchMaterials = async () => {
      setLoading(true);
      try {
        const activeCat = categories.find((c) => c.code === selectedCategoryCode);
        const result: PaginatedResult<PreparationMaterial> = await preparationService.getMaterials({
          category_id: activeCat?.id,
          topic_id: selectedTopicId || undefined,
          role_id: roles.find((r) => r.code === selectedRoleCode)?.id,
          difficulty: selectedDifficulty || undefined,
          material_type: selectedType || undefined,
          search: searchQuery || undefined,
          page,
          page_size: 18,
        });
        setMaterials(result.items);
        setTotalMaterials(result.total);
      } catch (err: any) {
        setError(err.response?.data?.detail || 'Failed to load materials.');
      } finally {
        setLoading(false);
      }
    };
    fetchMaterials();
  }, [
    categories,
    selectedCategoryCode,
    selectedTopicId,
    selectedRoleCode,
    selectedDifficulty,
    selectedType,
    searchQuery,
    page,
    activeTab,
    roles,
  ]);

  // Fetch officer pending review submissions
  const loadPendingSubmissions = async () => {
    if (!isOfficerOrAdmin) return;
    setLoadingPending(true);
    try {
      const res = await preparationService.getPendingSubmissions(1, 50);
      setPendingSubmissions(res.items);
      setTotalPending(res.total);
    } catch {
      // Ignore in non-blocking manner
    } finally {
      setLoadingPending(false);
    }
  };

  useEffect(() => {
    if (isOfficerOrAdmin) {
      loadPendingSubmissions();
    }
  }, [isOfficerOrAdmin]);

  // Fetch student's own submissions
  const loadMySuggestions = async () => {
    if (user?.role !== 'STUDENT') return;
    setLoadingMySuggestions(true);
    try {
      const res = await preparationService.getMySuggestions(1, 50);
      setMySuggestions(res.items);
      setTotalMySuggestions(res.total);
    } catch {
      // Ignore
    } finally {
      setLoadingMySuggestions(false);
    }
  };

  useEffect(() => {
    if (activeTab === 'MY_SUGGESTIONS') {
      loadMySuggestions();
    }
  }, [activeTab]);

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
        // Refresh materials
        const res = await preparationService.getMaterials({ page: 1, page_size: 18 });
        setMaterials(res.items);
        setTotalMaterials(res.total);
      } else {
        await preparationService.suggestMaterial(payload);
        setFormSuccess('Thank you! Your suggestion has been submitted for Placement Officer review.');
        loadMySuggestions();
      }

      // Reset form
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
  const handleReviewAction = async (status: 'APPROVED' | 'REJECTED') => {
    if (!reviewModalMaterial) return;
    setReviewActionLoading(true);
    try {
      await preparationService.reviewSubmission(reviewModalMaterial.id, {
        status,
        review_notes: reviewNotes.trim() || undefined,
      });
      setReviewModalMaterial(null);
      setReviewNotes('');
      await loadPendingSubmissions();
      // Refresh explore library
      const res = await preparationService.getMaterials({ page: 1, page_size: 18 });
      setMaterials(res.items);
      setTotalMaterials(res.total);
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Failed to review submission.');
    } finally {
      setReviewActionLoading(false);
    }
  };

  const getDifficultyBadge = (diff: MaterialDifficulty) => {
    switch (diff) {
      case 'BEGINNER':
        return 'bg-emerald-50 text-emerald-700 border-emerald-200';
      case 'INTERMEDIATE':
        return 'bg-amber-50 text-amber-700 border-amber-200';
      case 'ADVANCED':
        return 'bg-rose-50 text-rose-700 border-rose-200';
      default:
        return 'bg-slate-50 text-slate-700 border-slate-200';
    }
  };

  const getTypeIcon = (type: MaterialType) => {
    switch (type) {
      case 'VIDEO':
        return (
          <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M14.752 11.168l-3.197-2.132A1 1 0 0010 9.87v4.263a1 1 0 001.555.832l3.197-2.132a1 1 0 000-1.664z" />
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
        );
      case 'PDF':
        return (
          <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M7 21h10a2 2 0 002-2V9.414a1 1 0 00-.293-.707l-5.414-5.414A1 1 0 0012.586 3H7a2 2 0 00-2 2v14a2 2 0 002 2z" />
          </svg>
        );
      case 'PRACTICE_QUESTIONS':
        return (
          <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-6 9l2 2 4-4" />
          </svg>
        );
      case 'COURSE':
        return (
          <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" />
          </svg>
        );
      default:
        return (
          <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M19 20H5a2 2 0 01-2-2V6a2 2 0 012-2h10a2 2 0 012 2v1m2 13a2 2 0 01-2-2V7m2 13a2 2 0 002-2V9a2 2 0 00-2-2h-2m-4-3H9M7 16h6M7 8h6v4H7V8z" />
          </svg>
        );
    }
  };

  return (
    <div className="space-y-6">
      {/* Header Banner */}
      <div className="bg-gradient-to-r from-slate-900 via-indigo-950 to-slate-900 rounded-2xl p-6 sm:p-8 text-white shadow-xl relative overflow-hidden">
        <div className="absolute top-0 right-0 -mr-16 -mt-16 w-64 h-64 bg-indigo-500/10 rounded-full blur-3xl pointer-events-none" />
        <div className="relative z-10 flex flex-col md:flex-row md:items-center md:justify-between gap-4">
          <div className="space-y-2">
            <div className="inline-flex items-center space-x-2 px-3 py-1 rounded-full bg-indigo-500/20 text-indigo-300 border border-indigo-400/30 text-xs font-semibold">
              <span>🎯 Placement Preparation Hub</span>
              <span>&bull;</span>
              <span>Phase 5.1</span>
            </div>
            <h1 className="text-2xl sm:text-3xl font-extrabold tracking-tight text-white">
              Curated Placement Preparation & Roadmaps
            </h1>
            <p className="text-sm text-slate-300 max-w-2xl leading-relaxed">
              Master Aptitude, Technical Core, Verbal Ability, and Interview rounds with high-yield roadmaps, practice materials, and verified study guides tailored for campus recruitment drives.
            </p>
          </div>

          {/* Action Buttons */}
          <div className="flex flex-wrap items-center gap-3">
            {user?.role === 'STUDENT' && (
              <button
                onClick={() => {
                  setFormError(null);
                  setFormSuccess(null);
                  setIsSuggestModalOpen(true);
                }}
                className="px-4 py-2.5 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white font-semibold text-xs transition shadow-lg shadow-indigo-600/30 flex items-center space-x-2"
              >
                <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 4v16m8-8H4" />
                </svg>
                <span>Suggest a Material</span>
              </button>
            )}

            {isOfficerOrAdmin && (
              <button
                onClick={() => {
                  setFormError(null);
                  setFormSuccess(null);
                  setIsOfficerAddModalOpen(true);
                }}
                className="px-4 py-2.5 rounded-xl bg-emerald-600 hover:bg-emerald-500 text-white font-semibold text-xs transition shadow-lg shadow-emerald-600/30 flex items-center space-x-2"
              >
                <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 4v16m8-8H4" />
                </svg>
                <span>Publish New Material</span>
              </button>
            )}
          </div>
        </div>

        {/* Tab Navigation (Explore vs Officer Review Queue vs My Suggestions) */}
        <div className="flex items-center space-x-2 mt-6 pt-4 border-t border-slate-800">
          <button
            onClick={() => setActiveTab('EXPLORE')}
            className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition ${
              activeTab === 'EXPLORE'
                ? 'bg-indigo-600 text-white'
                : 'text-slate-400 hover:text-white hover:bg-slate-800/60'
            }`}
          >
            Explore Library
          </button>

          {isOfficerOrAdmin && (
            <button
              onClick={() => {
                setActiveTab('REVIEW_QUEUE');
                loadPendingSubmissions();
              }}
              className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition flex items-center space-x-1.5 ${
                activeTab === 'REVIEW_QUEUE'
                  ? 'bg-indigo-600 text-white'
                  : 'text-slate-400 hover:text-white hover:bg-slate-800/60'
              }`}
            >
              <span>Review Queue</span>
              {totalPending > 0 && (
                <span className="px-1.5 py-0.5 rounded-full bg-amber-500 text-slate-900 font-bold text-[10px]">
                  {totalPending}
                </span>
              )}
            </button>
          )}

          {user?.role === 'STUDENT' && (
            <button
              onClick={() => setActiveTab('MY_SUGGESTIONS')}
              className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition ${
                activeTab === 'MY_SUGGESTIONS'
                  ? 'bg-indigo-600 text-white'
                  : 'text-slate-400 hover:text-white hover:bg-slate-800/60'
              }`}
            >
              My Submitted Suggestions
            </button>
          )}
        </div>
      </div>

      {/* Main Tab 1: EXPLORE LIBRARY */}
      {activeTab === 'EXPLORE' && (
        <div className="space-y-6">
          {/* Target Role Selector Card */}
          <div className="bg-white rounded-2xl p-5 border border-slate-200/80 shadow-sm space-y-4">
            <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2">
              <div>
                <h2 className="text-sm font-bold text-slate-800 flex items-center space-x-2">
                  <span>Target Role Roadmap</span>
                  <span className="text-xs font-normal text-slate-500">
                    (Select a career profile to view core curriculum)
                  </span>
                </h2>
              </div>
            </div>

            {/* Role Pills */}
            <div className="flex items-center gap-2 overflow-x-auto pb-2 scrollbar-thin">
              {roles.map((role) => (
                <button
                  key={role.id}
                  onClick={() => {
                    setSelectedRoleCode(role.code);
                    setSelectedTopicId('');
                  }}
                  className={`px-3.5 py-2 rounded-xl text-xs font-semibold transition whitespace-nowrap flex items-center space-x-2 ${
                    selectedRoleCode === role.code
                      ? 'bg-indigo-600 text-white shadow-sm shadow-indigo-600/30'
                      : 'bg-slate-100 text-slate-700 hover:bg-slate-200'
                  }`}
                >
                  <span>{role.name}</span>
                </button>
              ))}
            </div>

            {/* Role Roadmap Details Banner */}
            {loadingRoadmap ? (
              <div className="py-4 text-center text-xs text-slate-400">Loading role roadmap...</div>
            ) : roleRoadmap ? (
              <div className="bg-slate-50 rounded-xl p-4 border border-slate-200/60 space-y-3">
                <div className="text-xs text-slate-600 leading-relaxed">
                  <span className="font-bold text-slate-800">{roleRoadmap.role.name}: </span>
                  {roleRoadmap.role.description}
                </div>

                {/* Topic tags for this role */}
                <div className="space-y-1.5">
                  <div className="text-[11px] font-bold uppercase tracking-wider text-slate-500">
                    Recommended Topics for this Profile:
                  </div>
                  <div className="flex flex-wrap gap-2">
                    {roleRoadmap.topics.map((rt) => (
                      <button
                        key={rt.topic.id}
                        onClick={() => setSelectedTopicId(selectedTopicId === rt.topic.id ? '' : rt.topic.id)}
                        className={`px-2.5 py-1 rounded-lg text-xs font-medium border transition flex items-center space-x-1.5 ${
                          selectedTopicId === rt.topic.id
                            ? 'bg-indigo-100 border-indigo-300 text-indigo-800 font-bold'
                            : 'bg-white border-slate-200 text-slate-700 hover:border-indigo-200'
                        }`}
                      >
                        <span>{rt.topic.name}</span>
                        <span
                          className={`text-[10px] px-1 rounded ${
                            rt.importance === 'CORE'
                              ? 'bg-rose-100 text-rose-700 font-bold'
                              : 'bg-slate-100 text-slate-600'
                          }`}
                        >
                          {rt.importance}
                        </span>
                      </button>
                    ))}
                  </div>
                </div>
              </div>
            ) : null}
          </div>

          {/* Category Tabs & Filters */}
          <div className="bg-white rounded-2xl p-5 border border-slate-200/80 shadow-sm space-y-4">
            {/* Category Pill Tabs */}
            <div className="flex items-center gap-2 overflow-x-auto pb-2 border-b border-slate-100 scrollbar-thin">
              <button
                onClick={() => {
                  setSelectedCategoryCode('ALL');
                  setSelectedTopicId('');
                }}
                className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition whitespace-nowrap ${
                  selectedCategoryCode === 'ALL'
                    ? 'bg-slate-900 text-white'
                    : 'bg-slate-100 text-slate-600 hover:bg-slate-200'
                }`}
              >
                All Categories
              </button>
              {categories.map((cat) => (
                <button
                  key={cat.id}
                  onClick={() => {
                    setSelectedCategoryCode(cat.code);
                    setSelectedTopicId('');
                  }}
                  className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition whitespace-nowrap flex items-center space-x-1.5 ${
                    selectedCategoryCode === cat.code
                      ? 'bg-indigo-600 text-white'
                      : 'bg-slate-100 text-slate-600 hover:bg-slate-200'
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
                <label className="block text-[11px] font-bold uppercase tracking-wider text-slate-500 mb-1">
                  Topic Filter
                </label>
                <select
                  value={selectedTopicId}
                  onChange={(e) => setSelectedTopicId(e.target.value)}
                  className="w-full text-xs rounded-xl border-slate-200 bg-slate-50 p-2 text-slate-700 focus:bg-white focus:ring-2 focus:ring-indigo-500"
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
                </select>
              </div>

              {/* Difficulty Select */}
              <div>
                <label className="block text-[11px] font-bold uppercase tracking-wider text-slate-500 mb-1">
                  Difficulty
                </label>
                <select
                  value={selectedDifficulty}
                  onChange={(e) => setSelectedDifficulty(e.target.value)}
                  className="w-full text-xs rounded-xl border-slate-200 bg-slate-50 p-2 text-slate-700 focus:bg-white focus:ring-2 focus:ring-indigo-500"
                >
                  <option value="">All Difficulties</option>
                  <option value="BEGINNER">Beginner</option>
                  <option value="INTERMEDIATE">Intermediate</option>
                  <option value="ADVANCED">Advanced</option>
                </select>
              </div>

              {/* Material Type Select */}
              <div>
                <label className="block text-[11px] font-bold uppercase tracking-wider text-slate-500 mb-1">
                  Resource Type
                </label>
                <select
                  value={selectedType}
                  onChange={(e) => setSelectedType(e.target.value)}
                  className="w-full text-xs rounded-xl border-slate-200 bg-slate-50 p-2 text-slate-700 focus:bg-white focus:ring-2 focus:ring-indigo-500"
                >
                  <option value="">All Types</option>
                  <option value="ARTICLE">Article / Tutorial</option>
                  <option value="VIDEO">Video Lecture</option>
                  <option value="PDF">PDF / Cheatsheet</option>
                  <option value="PRACTICE_QUESTIONS">Practice Questions</option>
                  <option value="DOCUMENTATION">Official Documentation</option>
                  <option value="COURSE">Free Course</option>
                </select>
              </div>

              {/* Search Bar */}
              <div>
                <label className="block text-[11px] font-bold uppercase tracking-wider text-slate-500 mb-1">
                  Search Keywords
                </label>
                <div className="relative">
                  <input
                    type="text"
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                    placeholder="Search by title..."
                    className="w-full text-xs rounded-xl border-slate-200 bg-slate-50 p-2 pl-8 text-slate-700 focus:bg-white focus:ring-2 focus:ring-indigo-500"
                  />
                  <svg
                    className="w-4 h-4 text-slate-400 absolute left-2.5 top-2.5"
                    fill="none"
                    viewBox="0 0 24 24"
                    stroke="currentColor"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth="2"
                      d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"
                    />
                  </svg>
                </div>
              </div>
            </div>
          </div>

          {/* Section Subheader with count */}
          <div className="flex items-center justify-between px-1">
            <span className="text-xs font-bold text-slate-700">
              Verified Study Resources {totalMaterials > 0 && <span className="text-slate-400 font-normal">({totalMaterials} items)</span>}
            </span>
          </div>

          {/* Resource Library Grid */}
          {loading ? (
            <div className="py-16 text-center space-y-3">
              <div className="w-8 h-8 border-4 border-indigo-600 border-t-transparent rounded-full animate-spin mx-auto" />
              <div className="text-xs text-slate-500 font-medium">Loading preparation resources...</div>
            </div>
          ) : error ? (
            <div className="bg-rose-50 border border-rose-200 rounded-2xl p-6 text-center space-y-2">
              <div className="text-xs font-bold text-rose-800">{error}</div>
              <button
                onClick={() => window.location.reload()}
                className="px-3 py-1.5 rounded-lg bg-rose-600 text-white text-xs font-semibold"
              >
                Retry
              </button>
            </div>
          ) : materials.length === 0 ? (
            <div className="bg-white rounded-2xl p-12 border border-slate-200/80 text-center space-y-3">
              <div className="w-12 h-12 rounded-2xl bg-indigo-50 text-indigo-600 flex items-center justify-center mx-auto">
                <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" />
                </svg>
              </div>
              <h3 className="text-sm font-bold text-slate-800">No Approved Materials Found</h3>
              <p className="text-xs text-slate-500 max-w-md mx-auto">
                No verified preparation resources match your active filters. Try resetting the topic or search filters, or suggest a high-quality study resource!
              </p>
              {user?.role === 'STUDENT' && (
                <button
                  onClick={() => setIsSuggestModalOpen(true)}
                  className="px-4 py-2 rounded-xl bg-indigo-600 text-white text-xs font-semibold hover:bg-indigo-700 transition"
                >
                  Suggest a Resource
                </button>
              )}
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {materials.map((mat) => (
                <div
                  key={mat.id}
                  className="bg-white rounded-2xl p-5 border border-slate-200/80 shadow-sm hover:shadow-md transition flex flex-col justify-between group"
                >
                  <div className="space-y-3">
                    {/* Header Badges */}
                    <div className="flex items-center justify-between gap-2">
                      <span className="inline-flex items-center space-x-1.5 px-2.5 py-1 rounded-lg bg-indigo-50 text-indigo-700 text-[11px] font-semibold">
                        {getTypeIcon(mat.material_type)}
                        <span>{mat.material_type.replace('_', ' ')}</span>
                      </span>

                      <span
                        className={`px-2 py-0.5 rounded-md text-[10px] font-bold border ${getDifficultyBadge(
                          mat.difficulty
                        )}`}
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
                        <span className="font-medium text-slate-700">{mat.source}</span>
                      ) : (
                        <span>Verified Resource</span>
                      )}
                    </div>

                    <a
                      href={mat.url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="px-3 py-1.5 rounded-lg bg-indigo-50 hover:bg-indigo-600 text-indigo-700 hover:text-white text-xs font-semibold transition flex items-center space-x-1"
                    >
                      <span>Open Guide</span>
                      <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
                      </svg>
                    </a>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Main Tab 2: OFFICER / ADMIN REVIEW QUEUE */}
      {activeTab === 'REVIEW_QUEUE' && isOfficerOrAdmin && (
        <div className="space-y-4">
          <div className="bg-white rounded-2xl p-5 border border-slate-200/80 shadow-sm flex items-center justify-between">
            <div>
              <h2 className="text-sm font-bold text-slate-900">Student Material Suggestion Queue</h2>
              <p className="text-xs text-slate-500">
                Review, verify URL safety, and approve or reject community suggested placement materials.
              </p>
            </div>
            <button
              onClick={loadPendingSubmissions}
              className="px-3 py-1.5 rounded-lg bg-slate-100 hover:bg-slate-200 text-xs font-semibold text-slate-700 transition"
            >
              Refresh Queue
            </button>
          </div>

          {loadingPending ? (
            <div className="py-12 text-center text-xs text-slate-500">Loading pending suggestions...</div>
          ) : pendingSubmissions.length === 0 ? (
            <div className="bg-white rounded-2xl p-12 border border-slate-200 text-center space-y-2">
              <div className="w-10 h-10 rounded-full bg-emerald-100 text-emerald-600 flex items-center justify-center mx-auto">
                ✓
              </div>
              <h3 className="text-sm font-bold text-slate-800">Review Queue is Clear</h3>
              <p className="text-xs text-slate-500">There are no pending material suggestions awaiting review.</p>
            </div>
          ) : (
            <div className="grid grid-cols-1 gap-3">
              {pendingSubmissions.map((sub) => (
                <div
                  key={sub.id}
                  className="bg-white rounded-2xl p-5 border border-amber-200 shadow-sm space-y-3"
                >
                  <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
                    <div className="space-y-1">
                      <div className="flex items-center space-x-2">
                        <span className="px-2 py-0.5 rounded bg-amber-100 text-amber-800 font-bold text-[10px]">
                          PENDING REVIEW
                        </span>
                        <span className="text-xs font-semibold text-slate-500">
                          {sub.material_type} &bull; {sub.difficulty}
                        </span>
                      </div>
                      <h4 className="text-sm font-bold text-slate-900">{sub.title}</h4>
                      {sub.description && (
                        <p className="text-xs text-slate-600">{sub.description}</p>
                      )}
                    </div>

                    <div className="flex items-center space-x-2">
                      <a
                        href={sub.url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="px-3 py-1.5 rounded-lg bg-slate-100 hover:bg-slate-200 text-xs font-semibold text-slate-700"
                      >
                        Preview URL ↗
                      </a>
                      <button
                        onClick={() => {
                          setReviewModalMaterial(sub);
                          setReviewNotes('');
                        }}
                        className="px-4 py-1.5 rounded-lg bg-indigo-600 hover:bg-indigo-700 text-xs font-semibold text-white"
                      >
                        Review Action
                      </button>
                    </div>
                  </div>

                  <div className="text-[11px] text-slate-400">
                    URL: <span className="font-mono text-slate-600">{sub.url}</span>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Main Tab 3: STUDENT MY SUGGESTIONS */}
      {activeTab === 'MY_SUGGESTIONS' && user?.role === 'STUDENT' && (
        <div className="space-y-4">
          <div className="bg-white rounded-2xl p-5 border border-slate-200/80 shadow-sm flex items-center justify-between">
            <div>
              <h2 className="text-sm font-bold text-slate-900">
                My Suggested Materials {totalMySuggestions > 0 && <span className="text-slate-400 font-normal">({totalMySuggestions})</span>}
              </h2>
              <p className="text-xs text-slate-500">Track the status of materials you submitted to help fellow students.</p>
            </div>
            <button
              onClick={() => setIsSuggestModalOpen(true)}
              className="px-3 py-1.5 rounded-lg bg-indigo-600 hover:bg-indigo-700 text-white text-xs font-semibold"
            >
              + Suggest Another
            </button>
          </div>

          {loadingMySuggestions ? (
            <div className="py-12 text-center text-xs text-slate-500">Loading your submissions...</div>
          ) : mySuggestions.length === 0 ? (
            <div className="bg-white rounded-2xl p-12 border border-slate-200 text-center space-y-2">
              <h3 className="text-sm font-bold text-slate-800">No suggestions submitted yet</h3>
              <p className="text-xs text-slate-500">
                Found a great tutorial or problem set? Suggest it to earn contribution credit!
              </p>
            </div>
          ) : (
            <div className="grid grid-cols-1 gap-3">
              {mySuggestions.map((item) => (
                <div key={item.id} className="bg-white rounded-2xl p-4 border border-slate-200 shadow-sm space-y-2">
                  <div className="flex items-center justify-between">
                    <h4 className="text-xs font-bold text-slate-900">{item.title}</h4>
                    <span
                      className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                        item.status === 'APPROVED'
                          ? 'bg-emerald-100 text-emerald-800'
                          : item.status === 'REJECTED'
                          ? 'bg-rose-100 text-rose-800'
                          : 'bg-amber-100 text-amber-800'
                      }`}
                    >
                      {item.status}
                    </span>
                  </div>
                  <div className="text-xs text-slate-500 font-mono truncate">{item.url}</div>
                  {item.review_notes && (
                    <div className="text-[11px] text-slate-600 bg-slate-50 p-2 rounded-lg border border-slate-200/60">
                      <span className="font-bold">Officer Feedback: </span>
                      {item.review_notes}
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* MODAL 1: STUDENT SUGGEST MATERIAL / OFFICER ADD MATERIAL */}
      {(isSuggestModalOpen || isOfficerAddModalOpen) && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/60 backdrop-blur-sm animate-fade-in">
          <div className="bg-white rounded-2xl max-w-lg w-full p-6 shadow-2xl border border-slate-200 space-y-4 max-h-[90vh] overflow-y-auto">
            <div className="flex items-center justify-between pb-3 border-b border-slate-100">
              <h3 className="text-sm font-bold text-slate-900">
                {isOfficerAddModalOpen ? 'Publish Official Material' : 'Suggest a Placement Material'}
              </h3>
              <button
                onClick={() => {
                  setIsSuggestModalOpen(false);
                  setIsOfficerAddModalOpen(false);
                }}
                className="p-1 rounded-lg text-slate-400 hover:text-slate-600"
              >
                ✕
              </button>
            </div>

            {formError && (
              <div className="p-3 rounded-xl bg-rose-50 border border-rose-200 text-xs font-semibold text-rose-800">
                {formError}
              </div>
            )}

            {formSuccess && (
              <div className="p-3 rounded-xl bg-emerald-50 border border-emerald-200 text-xs font-semibold text-emerald-800">
                {formSuccess}
              </div>
            )}

            <form onSubmit={(e) => handleSubmitMaterial(e, isOfficerAddModalOpen)} className="space-y-3">
              {/* Topic */}
              <div>
                <label className="block text-xs font-bold text-slate-700 mb-1">
                  Topic <span className="text-rose-500">*</span>
                </label>
                <select
                  value={formData.topic_id}
                  onChange={(e) => setFormData({ ...formData, topic_id: e.target.value })}
                  required
                  className="w-full text-xs rounded-xl border-slate-200 bg-slate-50 p-2 text-slate-800 focus:bg-white focus:ring-2 focus:ring-indigo-500"
                >
                  <option value="">-- Select Relevant Topic --</option>
                  {allTopics.map((t) => (
                    <option key={t.id} value={t.id}>
                      {t.name}
                    </option>
                  ))}
                </select>
              </div>

              {/* Role (Optional) */}
              <div>
                <label className="block text-xs font-bold text-slate-700 mb-1">
                  Target Role (Optional)
                </label>
                <select
                  value={formData.role_id}
                  onChange={(e) => setFormData({ ...formData, role_id: e.target.value })}
                  className="w-full text-xs rounded-xl border-slate-200 bg-slate-50 p-2 text-slate-800 focus:bg-white focus:ring-2 focus:ring-indigo-500"
                >
                  <option value="">-- All General Roles --</option>
                  {roles.map((r) => (
                    <option key={r.id} value={r.id}>
                      {r.name}
                    </option>
                  ))}
                </select>
              </div>

              {/* Title */}
              <div>
                <label className="block text-xs font-bold text-slate-700 mb-1">
                  Material Title <span className="text-rose-500">*</span>
                </label>
                <input
                  type="text"
                  value={formData.title}
                  onChange={(e) => setFormData({ ...formData, title: e.target.value })}
                  placeholder="e.g. Master Binary Search Patterns & Questions"
                  required
                  className="w-full text-xs rounded-xl border-slate-200 bg-slate-50 p-2 text-slate-800 focus:bg-white focus:ring-2 focus:ring-indigo-500"
                />
              </div>

              {/* URL */}
              <div>
                <label className="block text-xs font-bold text-slate-700 mb-1">
                  Resource URL <span className="text-rose-500">*</span>
                </label>
                <input
                  type="url"
                  value={formData.url}
                  onChange={(e) => setFormData({ ...formData, url: e.target.value })}
                  placeholder="https://..."
                  required
                  className="w-full text-xs rounded-xl border-slate-200 bg-slate-50 p-2 text-slate-800 focus:bg-white focus:ring-2 focus:ring-indigo-500"
                />
              </div>

              {/* Type and Difficulty Grid */}
              <div className="grid grid-cols-2 gap-2">
                <div>
                  <label className="block text-xs font-bold text-slate-700 mb-1">Type</label>
                  <select
                    value={formData.material_type}
                    onChange={(e) => setFormData({ ...formData, material_type: e.target.value as MaterialType })}
                    className="w-full text-xs rounded-xl border-slate-200 bg-slate-50 p-2 text-slate-800"
                  >
                    <option value="ARTICLE">Article / Tutorial</option>
                    <option value="VIDEO">Video Lecture</option>
                    <option value="PDF">PDF / Notes</option>
                    <option value="PRACTICE_QUESTIONS">Practice Questions</option>
                    <option value="DOCUMENTATION">Documentation</option>
                    <option value="COURSE">Course</option>
                    <option value="OTHER">Other</option>
                  </select>
                </div>

                <div>
                  <label className="block text-xs font-bold text-slate-700 mb-1">Difficulty</label>
                  <select
                    value={formData.difficulty}
                    onChange={(e) => setFormData({ ...formData, difficulty: e.target.value as MaterialDifficulty })}
                    className="w-full text-xs rounded-xl border-slate-200 bg-slate-50 p-2 text-slate-800"
                  >
                    <option value="BEGINNER">Beginner</option>
                    <option value="INTERMEDIATE">Intermediate</option>
                    <option value="ADVANCED">Advanced</option>
                  </select>
                </div>
              </div>

              {/* Source */}
              <div>
                <label className="block text-xs font-bold text-slate-700 mb-1">Source / Author (Optional)</label>
                <input
                  type="text"
                  value={formData.source}
                  onChange={(e) => setFormData({ ...formData, source: e.target.value })}
                  placeholder="e.g. GeeksforGeeks, LeetCode, Official Docs"
                  className="w-full text-xs rounded-xl border-slate-200 bg-slate-50 p-2 text-slate-800"
                />
              </div>

              {/* Description */}
              <div>
                <label className="block text-xs font-bold text-slate-700 mb-1">Brief Description (Optional)</label>
                <textarea
                  value={formData.description}
                  onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                  rows={3}
                  placeholder="Explain why this resource is useful for placement preparation..."
                  className="w-full text-xs rounded-xl border-slate-200 bg-slate-50 p-2 text-slate-800 focus:bg-white"
                />
              </div>

              {/* Action Buttons */}
              <div className="flex items-center justify-end space-x-2 pt-3 border-t border-slate-100">
                <button
                  type="button"
                  onClick={() => {
                    setIsSuggestModalOpen(false);
                    setIsOfficerAddModalOpen(false);
                  }}
                  className="px-4 py-2 rounded-xl bg-slate-100 hover:bg-slate-200 text-xs font-semibold text-slate-700"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={submitting}
                  className="px-4 py-2 rounded-xl bg-indigo-600 hover:bg-indigo-700 text-xs font-semibold text-white disabled:opacity-50"
                >
                  {submitting ? 'Submitting...' : isOfficerAddModalOpen ? 'Publish Material' : 'Submit for Review'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* MODAL 2: OFFICER REVIEW ACTION MODAL */}
      {reviewModalMaterial && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/60 backdrop-blur-sm animate-fade-in">
          <div className="bg-white rounded-2xl max-w-md w-full p-6 shadow-2xl border border-slate-200 space-y-4">
            <div className="flex items-center justify-between pb-3 border-b border-slate-100">
              <h3 className="text-sm font-bold text-slate-900">Review Suggestion</h3>
              <button onClick={() => setReviewModalMaterial(null)} className="text-slate-400 hover:text-slate-600">
                ✕
              </button>
            </div>

            <div className="space-y-2 bg-slate-50 p-3 rounded-xl border border-slate-200/60 text-xs">
              <div className="font-bold text-slate-900">{reviewModalMaterial.title}</div>
              <div className="text-slate-600 text-[11px] font-mono break-all">{reviewModalMaterial.url}</div>
              {reviewModalMaterial.description && (
                <div className="text-slate-600 text-xs">{reviewModalMaterial.description}</div>
              )}
            </div>

            <div>
              <label className="block text-xs font-bold text-slate-700 mb-1">Review Notes (Optional)</label>
              <textarea
                value={reviewNotes}
                onChange={(e) => setReviewNotes(e.target.value)}
                placeholder="Optional notes or feedback..."
                rows={2}
                className="w-full text-xs rounded-xl border-slate-200 bg-slate-50 p-2"
              />
            </div>

            <div className="flex items-center justify-end space-x-2 pt-3 border-t border-slate-100">
              <button
                type="button"
                onClick={() => setReviewModalMaterial(null)}
                className="px-3 py-1.5 rounded-lg bg-slate-100 hover:bg-slate-200 text-xs font-semibold text-slate-700"
              >
                Cancel
              </button>
              <button
                type="button"
                disabled={reviewActionLoading}
                onClick={() => handleReviewAction('REJECTED')}
                className="px-4 py-1.5 rounded-lg bg-rose-600 hover:bg-rose-700 text-xs font-semibold text-white disabled:opacity-50"
              >
                Reject
              </button>
              <button
                type="button"
                disabled={reviewActionLoading}
                onClick={() => handleReviewAction('APPROVED')}
                className="px-4 py-1.5 rounded-lg bg-emerald-600 hover:bg-emerald-700 text-xs font-semibold text-white disabled:opacity-50"
              >
                Approve & Publish
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

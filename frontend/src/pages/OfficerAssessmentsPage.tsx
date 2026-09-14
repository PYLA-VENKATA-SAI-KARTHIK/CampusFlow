import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { assessmentService } from '../services/assessmentService';
import { preparationService } from '../services/preparationService';
import { apiClient } from '../services/apiClient';
import type {
  AssessmentDifficulty,
  AssessmentSummary,
  AssessmentCreatePayload,
} from '../types/assessment';
import type { PreparationCategory } from '../types/preparation';

export const OfficerAssessmentsPage: React.FC = () => {
  const navigate = useNavigate();

  const [assessments, setAssessments] = useState<AssessmentSummary[]>([]);
  const [categories, setCategories] = useState<PreparationCategory[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Filters
  const [search, setSearch] = useState('');
  const [statusFilter, setStatusFilter] = useState<string>('ALL');
  const [difficultyFilter, setDifficultyFilter] = useState<string>('ALL');

  // Create Modal
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [createForm, setCreateForm] = useState<AssessmentCreatePayload>({
    title: '',
    description: '',
    category_id: '',
    topic_id: '',
    difficulty: 'BEGINNER',
    duration_minutes: 30,
    pass_percentage: 50,
    allow_multiple_attempts: false,
  });
  const [creating, setCreating] = useState(false);
  const [createError, setCreateError] = useState<string | null>(null);

  // Assign Modal
  const [assigningAssessment, setAssigningAssessment] = useState<AssessmentSummary | null>(null);
  const [students, setStudents] = useState<any[]>([]);
  const [selectedStudentIds, setSelectedStudentIds] = useState<string[]>([]);
  const [dueDate, setDueDate] = useState<string>('');
  const [assigning, setAssigning] = useState(false);
  const [assignSuccess, setAssignSuccess] = useState<string | null>(null);
  const [assignError, setAssignError] = useState<string | null>(null);

  useEffect(() => {
    fetchData();
  }, [statusFilter, difficultyFilter]);

  const fetchData = async () => {
    setLoading(true);
    setError(null);
    try {
      const params: Record<string, any> = {};
      if (statusFilter !== 'ALL') params.status = statusFilter;
      if (difficultyFilter !== 'ALL') params.difficulty = difficultyFilter;
      if (search.trim()) params.search = search.trim();

      const [assessmentList, catList] = await Promise.all([
        assessmentService.listAssessments(params),
        preparationService.getCategories(),
      ]);
      setAssessments(assessmentList);
      setCategories(catList);
    } catch (err: any) {
      setError(err?.response?.data?.detail || 'Failed to load assessments.');
    } finally {
      setLoading(false);
    }
  };

  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    fetchData();
  };

  const handleCreateSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setCreating(true);
    setCreateError(null);
    try {
      const payload: AssessmentCreatePayload = {
        title: createForm.title.trim(),
        description: createForm.description?.trim() || null,
        category_id: createForm.category_id || null,
        topic_id: createForm.topic_id || null,
        difficulty: createForm.difficulty,
        duration_minutes: Number(createForm.duration_minutes),
        pass_percentage: Number(createForm.pass_percentage),
        allow_multiple_attempts: Boolean(createForm.allow_multiple_attempts),
      };

      const created = await assessmentService.createAssessment(payload);
      setShowCreateModal(false);
      navigate(`/assessments/builder/${created.id}`);
    } catch (err: any) {
      setCreateError(err?.response?.data?.detail || 'Failed to create assessment.');
    } finally {
      setCreating(false);
    }
  };

  const openAssignModal = async (assessment: AssessmentSummary) => {
    setAssigningAssessment(assessment);
    setSelectedStudentIds([]);
    setDueDate('');
    setAssignSuccess(null);
    setAssignError(null);
    try {
      const res = await apiClient.get('/officers/students', { params: { page_size: 100 } });
      setStudents(res.data.items || []);
    } catch {
      setStudents([]);
    }
  };

  const handleAssignSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!assigningAssessment || selectedStudentIds.length === 0) return;
    setAssigning(true);
    setAssignError(null);
    try {
      await assessmentService.assignAssessment(
        assigningAssessment.id,
        selectedStudentIds,
        dueDate ? new Date(dueDate).toISOString() : null
      );
      setAssignSuccess(`Successfully assigned to ${selectedStudentIds.length} student(s)!`);
      setTimeout(() => {
        setAssigningAssessment(null);
        setAssignSuccess(null);
      }, 1200);
    } catch (err: any) {
      setAssignError(err?.response?.data?.detail || 'Failed to assign assessment.');
    } finally {
      setAssigning(false);
    }
  };

  const toggleSelectAllStudents = () => {
    if (selectedStudentIds.length === students.length) {
      setSelectedStudentIds([]);
    } else {
      setSelectedStudentIds(students.map((s) => s.user_id));
    }
  };

  const toggleStudent = (userId: string) => {
    setSelectedStudentIds((prev) =>
      prev.includes(userId) ? prev.filter((id) => id !== userId) : [...prev, userId]
    );
  };

  const selectedCategoryObj = categories.find((c) => c.id === createForm.category_id);

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-black text-slate-900 tracking-tight">Practice Assessment Engine</h1>
          <p className="text-sm text-slate-500 font-medium">
            Create, publish, and assign server-authoritative MCQ assessments for placement preparation.
          </p>
        </div>

        <button
          onClick={() => setShowCreateModal(true)}
          className="inline-flex items-center space-x-2 px-4 py-2.5 rounded-xl bg-indigo-600 hover:bg-indigo-700 text-white font-bold text-sm shadow-md shadow-indigo-600/20 transition transform active:scale-95"
        >
          <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 4v16m8-8H4" />
          </svg>
          <span>Create Assessment</span>
        </button>
      </div>

      {/* Filter & Search Toolbar */}
      <div className="bg-white rounded-2xl p-4 border border-slate-200/80 shadow-sm flex flex-col md:flex-row gap-4 justify-between items-center">
        <form onSubmit={handleSearchSubmit} className="w-full md:w-80 flex items-center space-x-2">
          <div className="relative w-full">
            <input
              type="text"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="Search assessments..."
              className="w-full pl-9 pr-3 py-2 text-xs font-semibold bg-slate-50 border border-slate-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-600"
            />
            <svg
              className="w-4 h-4 text-slate-400 absolute left-3 top-2.5"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
            >
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
            </svg>
          </div>
          <button type="submit" className="px-3 py-2 bg-slate-100 hover:bg-slate-200 text-slate-700 text-xs font-bold rounded-xl transition">
            Search
          </button>
        </form>

        <div className="flex flex-wrap items-center gap-3 w-full md:w-auto">
          <div className="flex items-center space-x-1.5 text-xs font-semibold text-slate-500">
            <span>Status:</span>
            <select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
              className="bg-slate-50 border border-slate-200 rounded-lg px-2.5 py-1.5 text-xs font-bold text-slate-800 focus:outline-none focus:ring-2 focus:ring-indigo-500/20"
            >
              <option value="ALL">All Statuses</option>
              <option value="DRAFT">Draft</option>
              <option value="PUBLISHED">Published</option>
              <option value="ARCHIVED">Archived</option>
            </select>
          </div>

          <div className="flex items-center space-x-1.5 text-xs font-semibold text-slate-500">
            <span>Difficulty:</span>
            <select
              value={difficultyFilter}
              onChange={(e) => setDifficultyFilter(e.target.value)}
              className="bg-slate-50 border border-slate-200 rounded-lg px-2.5 py-1.5 text-xs font-bold text-slate-800 focus:outline-none focus:ring-2 focus:ring-indigo-500/20"
            >
              <option value="ALL">All Difficulties</option>
              <option value="BEGINNER">Beginner</option>
              <option value="INTERMEDIATE">Intermediate</option>
              <option value="ADVANCED">Advanced</option>
            </select>
          </div>
        </div>
      </div>

      {/* Error / Loading / Content State */}
      {error && (
        <div className="p-4 rounded-2xl bg-rose-50 border border-rose-200 text-rose-700 text-xs font-semibold">
          {error}
        </div>
      )}

      {loading ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 animate-pulse">
          {[1, 2, 3, 4, 5, 6].map((n) => (
            <div key={n} className="h-56 bg-white rounded-2xl border border-slate-200 p-5 space-y-4" />
          ))}
        </div>
      ) : assessments.length === 0 ? (
        <div className="bg-white rounded-3xl border border-slate-200 p-12 text-center space-y-4 shadow-sm">
          <div className="w-14 h-14 bg-indigo-50 text-indigo-600 rounded-2xl flex items-center justify-center mx-auto shadow-inner">
            <svg className="w-7 h-7" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
            </svg>
          </div>
          <div className="space-y-1">
            <h3 className="text-base font-bold text-slate-900">No assessments found</h3>
            <p className="text-xs text-slate-500 max-w-sm mx-auto">
              Create your first practice assessment to start preparing candidates with real timed questions.
            </p>
          </div>
          <button
            onClick={() => setShowCreateModal(true)}
            className="px-4 py-2 bg-indigo-600 hover:bg-indigo-700 text-white rounded-xl text-xs font-bold transition"
          >
            Create First Assessment
          </button>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {assessments.map((a) => (
            <div
              key={a.id}
              className="bg-white rounded-2xl border border-slate-200/80 p-5 shadow-sm hover:shadow-md transition-all flex flex-col justify-between space-y-4 group"
            >
              <div className="space-y-3">
                <div className="flex items-center justify-between gap-2">
                  <span
                    className={`px-2.5 py-0.5 rounded-full text-[10px] font-extrabold tracking-wide uppercase ${
                      a.status === 'PUBLISHED'
                        ? 'bg-emerald-50 text-emerald-700 border border-emerald-200'
                        : a.status === 'DRAFT'
                        ? 'bg-amber-50 text-amber-700 border border-amber-200'
                        : 'bg-slate-100 text-slate-600 border border-slate-200'
                    }`}
                  >
                    {a.status}
                  </span>

                  <span
                    className={`px-2 py-0.5 rounded-md text-[10px] font-bold ${
                      a.difficulty === 'ADVANCED'
                        ? 'bg-rose-50 text-rose-700'
                        : a.difficulty === 'INTERMEDIATE'
                        ? 'bg-indigo-50 text-indigo-700'
                        : 'bg-teal-50 text-teal-700'
                    }`}
                  >
                    {a.difficulty}
                  </span>
                </div>

                <div>
                  <h3 className="text-base font-extrabold text-slate-900 leading-snug group-hover:text-indigo-600 transition">
                    {a.title}
                  </h3>
                  {a.description && (
                    <p className="text-xs text-slate-500 line-clamp-2 mt-1">{a.description}</p>
                  )}
                </div>

                <div className="pt-2 border-t border-slate-100 grid grid-cols-3 gap-2 text-center">
                  <div className="bg-slate-50 p-2 rounded-xl border border-slate-100">
                    <div className="text-[10px] text-slate-400 font-bold uppercase">Duration</div>
                    <div className="text-xs font-extrabold text-slate-800">{a.duration_minutes}m</div>
                  </div>
                  <div className="bg-slate-50 p-2 rounded-xl border border-slate-100">
                    <div className="text-[10px] text-slate-400 font-bold uppercase">Questions</div>
                    <div className="text-xs font-extrabold text-slate-800">{a.questions_count}</div>
                  </div>
                  <div className="bg-slate-50 p-2 rounded-xl border border-slate-100">
                    <div className="text-[10px] text-slate-400 font-bold uppercase">Marks</div>
                    <div className="text-xs font-extrabold text-slate-800">{a.total_marks}</div>
                  </div>
                </div>

                {(a.category_name || a.topic_name) && (
                  <div className="flex items-center space-x-1.5 text-[11px] text-slate-500 font-semibold truncate">
                    <span className="text-indigo-600 font-bold">{a.category_name || 'Taxonomy'}</span>
                    {a.topic_name && <span>&bull;</span>}
                    {a.topic_name && <span className="truncate">{a.topic_name}</span>}
                  </div>
                )}
              </div>

              {/* Action Buttons */}
              <div className="pt-3 border-t border-slate-100 flex items-center gap-2">
                <button
                  onClick={() => navigate(`/assessments/builder/${a.id}`)}
                  className="flex-1 py-2 px-3 rounded-xl bg-slate-900 hover:bg-slate-800 text-white font-bold text-xs transition text-center shadow-sm"
                >
                  {a.status === 'DRAFT' ? 'Edit & Build' : 'View Details'}
                </button>

                {a.status === 'PUBLISHED' && (
                  <button
                    onClick={() => openAssignModal(a)}
                    title="Assign to students"
                    className="py-2 px-3 rounded-xl bg-indigo-50 hover:bg-indigo-100 text-indigo-700 font-bold text-xs transition flex items-center justify-center space-x-1"
                  >
                    <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M18 9v3m0 0v3m0-3h3m-3 0h-3m-2-5a4 4 0 11-8 0 4 4 0 018 0zM3 20a6 6 0 0112 0v1H3v-1z" />
                    </svg>
                    <span>Assign</span>
                  </button>
                )}
              </div>
            </div>
          ))}
        </div>
      )}

      {/* CREATE ASSESSMENT MODAL */}
      {showCreateModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/60 backdrop-blur-sm animate-fade-in">
          <div className="bg-white rounded-3xl border border-slate-200 shadow-2xl max-w-lg w-full p-6 space-y-5">
            <div className="flex items-center justify-between border-b border-slate-100 pb-3">
              <h2 className="text-lg font-extrabold text-slate-900">Create Practice Assessment</h2>
              <button
                onClick={() => setShowCreateModal(false)}
                className="text-slate-400 hover:text-slate-600 p-1 rounded-lg"
              >
                <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>

            {createError && (
              <div className="p-3 bg-rose-50 border border-rose-200 text-rose-700 text-xs font-semibold rounded-xl">
                {createError}
              </div>
            )}

            <form onSubmit={handleCreateSubmit} className="space-y-4">
              <div>
                <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-1">
                  Title *
                </label>
                <input
                  type="text"
                  required
                  placeholder="e.g. Core Java & Collections Practice Test"
                  value={createForm.title}
                  onChange={(e) => setCreateForm({ ...createForm, title: e.target.value })}
                  className="w-full px-3.5 py-2 text-xs font-medium bg-slate-50 border border-slate-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-600"
                />
              </div>

              <div>
                <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-1">
                  Description
                </label>
                <textarea
                  rows={2}
                  placeholder="Assessment instructions and topics covered..."
                  value={createForm.description || ''}
                  onChange={(e) => setCreateForm({ ...createForm, description: e.target.value })}
                  className="w-full px-3.5 py-2 text-xs font-medium bg-slate-50 border border-slate-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-600"
                />
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-1">
                    Category (Preparation Hub)
                  </label>
                  <select
                    value={createForm.category_id || ''}
                    onChange={(e) =>
                      setCreateForm({
                        ...createForm,
                        category_id: e.target.value,
                        topic_id: '',
                      })
                    }
                    className="w-full px-3 py-2 text-xs font-bold bg-slate-50 border border-slate-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-indigo-500/20"
                  >
                    <option value="">Select Category</option>
                    {categories.map((c) => (
                      <option key={c.id} value={c.id}>
                        {c.name}
                      </option>
                    ))}
                  </select>
                </div>

                <div>
                  <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-1">
                    Topic
                  </label>
                  <select
                    value={createForm.topic_id || ''}
                    onChange={(e) => setCreateForm({ ...createForm, topic_id: e.target.value })}
                    disabled={!selectedCategoryObj}
                    className="w-full px-3 py-2 text-xs font-bold bg-slate-50 border border-slate-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-indigo-500/20 disabled:opacity-50"
                  >
                    <option value="">Select Topic</option>
                    {selectedCategoryObj?.topics?.map((t) => (
                      <option key={t.id} value={t.id}>
                        {t.name}
                      </option>
                    ))}
                  </select>
                </div>
              </div>

              <div className="grid grid-cols-3 gap-3">
                <div>
                  <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-1">
                    Difficulty
                  </label>
                  <select
                    value={createForm.difficulty}
                    onChange={(e) =>
                      setCreateForm({
                        ...createForm,
                        difficulty: e.target.value as AssessmentDifficulty,
                      })
                    }
                    className="w-full px-2.5 py-2 text-xs font-bold bg-slate-50 border border-slate-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-indigo-500/20"
                  >
                    <option value="BEGINNER">Beginner</option>
                    <option value="INTERMEDIATE">Intermediate</option>
                    <option value="ADVANCED">Advanced</option>
                  </select>
                </div>

                <div>
                  <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-1">
                    Duration (Mins) *
                  </label>
                  <input
                    type="number"
                    min={5}
                    max={360}
                    required
                    value={createForm.duration_minutes}
                    onChange={(e) =>
                      setCreateForm({ ...createForm, duration_minutes: Number(e.target.value) })
                    }
                    className="w-full px-3 py-2 text-xs font-bold bg-slate-50 border border-slate-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-indigo-500/20"
                  />
                </div>

                <div>
                  <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-1">
                    Pass % *
                  </label>
                  <input
                    type="number"
                    min={0}
                    max={100}
                    required
                    value={createForm.pass_percentage}
                    onChange={(e) =>
                      setCreateForm({ ...createForm, pass_percentage: Number(e.target.value) })
                    }
                    className="w-full px-3 py-2 text-xs font-bold bg-slate-50 border border-slate-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-indigo-500/20"
                  />
                </div>
              </div>

              <div className="flex items-center space-x-2 pt-2">
                <input
                  type="checkbox"
                  id="multi-attempts"
                  checked={createForm.allow_multiple_attempts}
                  onChange={(e) =>
                    setCreateForm({ ...createForm, allow_multiple_attempts: e.target.checked })
                  }
                  className="rounded text-indigo-600 focus:ring-indigo-500 w-4 h-4"
                />
                <label htmlFor="multi-attempts" className="text-xs font-semibold text-slate-700 cursor-pointer">
                  Allow students multiple attempts (Practice mode)
                </label>
              </div>

              <div className="pt-4 border-t border-slate-100 flex items-center justify-end space-x-3">
                <button
                  type="button"
                  onClick={() => setShowCreateModal(false)}
                  className="px-4 py-2 rounded-xl bg-slate-100 hover:bg-slate-200 text-slate-700 font-bold text-xs transition"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={creating}
                  className="px-5 py-2 rounded-xl bg-indigo-600 hover:bg-indigo-700 text-white font-bold text-xs transition shadow-md shadow-indigo-600/20 disabled:opacity-50"
                >
                  {creating ? 'Creating...' : 'Continue to Question Builder →'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* ASSIGN ASSESSMENT MODAL */}
      {assigningAssessment && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/60 backdrop-blur-sm animate-fade-in">
          <div className="bg-white rounded-3xl border border-slate-200 shadow-2xl max-w-xl w-full p-6 space-y-5">
            <div className="flex items-center justify-between border-b border-slate-100 pb-3">
              <div>
                <h2 className="text-lg font-extrabold text-slate-900">Assign Assessment</h2>
                <p className="text-xs text-slate-500 font-medium">{assigningAssessment.title}</p>
              </div>
              <button
                onClick={() => setAssigningAssessment(null)}
                className="text-slate-400 hover:text-slate-600 p-1 rounded-lg"
              >
                <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>

            {assignSuccess && (
              <div className="p-3 bg-emerald-50 border border-emerald-200 text-emerald-700 text-xs font-semibold rounded-xl">
                {assignSuccess}
              </div>
            )}

            {assignError && (
              <div className="p-3 bg-red-50 border border-red-200 text-red-700 text-xs font-semibold rounded-xl">
                {assignError}
              </div>
            )}

            <form onSubmit={handleAssignSubmit} className="space-y-4">
              <div>
                <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-1">
                  Due Date (Optional)
                </label>
                <input
                  type="datetime-local"
                  value={dueDate}
                  onChange={(e) => setDueDate(e.target.value)}
                  className="w-full px-3.5 py-2 text-xs font-medium bg-slate-50 border border-slate-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-indigo-500/20"
                />
              </div>

              <div>
                <div className="flex items-center justify-between mb-2">
                  <label className="text-xs font-bold text-slate-700 uppercase tracking-wider">
                    Select Students ({selectedStudentIds.length} of {students.length} selected)
                  </label>
                  {students.length > 0 && (
                    <button
                      type="button"
                      onClick={toggleSelectAllStudents}
                      className="text-xs font-bold text-indigo-600 hover:text-indigo-800"
                    >
                      {selectedStudentIds.length === students.length ? 'Deselect All' : 'Select All'}
                    </button>
                  )}
                </div>

                <div className="max-h-56 overflow-y-auto border border-slate-200 rounded-xl divide-y divide-slate-100 bg-slate-50/50">
                  {students.length === 0 ? (
                    <div className="p-4 text-center text-xs text-slate-400">No active students found.</div>
                  ) : (
                    students.map((st) => (
                      <label
                        key={st.user_id}
                        className="flex items-center space-x-3 p-2.5 hover:bg-white cursor-pointer transition"
                      >
                        <input
                          type="checkbox"
                          checked={selectedStudentIds.includes(st.user_id)}
                          onChange={() => toggleStudent(st.user_id)}
                          className="rounded text-indigo-600 focus:ring-indigo-500 w-4 h-4"
                        />
                        <div className="flex-1 overflow-hidden">
                          <div className="text-xs font-bold text-slate-800 truncate">
                            {st.full_name} ({st.roll_number || 'N/A'})
                          </div>
                          <div className="text-[10px] text-slate-500 font-semibold truncate">
                            {st.branch_code || 'General'} &bull; {st.email}
                          </div>
                        </div>
                      </label>
                    ))
                  )}
                </div>
              </div>

              <div className="pt-4 border-t border-slate-100 flex items-center justify-end space-x-3">
                <button
                  type="button"
                  onClick={() => setAssigningAssessment(null)}
                  className="px-4 py-2 rounded-xl bg-slate-100 hover:bg-slate-200 text-slate-700 font-bold text-xs transition"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={assigning || selectedStudentIds.length === 0}
                  className="px-5 py-2 rounded-xl bg-indigo-600 hover:bg-indigo-700 text-white font-bold text-xs transition shadow-md shadow-indigo-600/20 disabled:opacity-50"
                >
                  {assigning ? 'Dispatching...' : `Assign to ${selectedStudentIds.length} Student(s)`}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};

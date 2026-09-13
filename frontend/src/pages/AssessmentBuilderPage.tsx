import React, { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { assessmentService } from '../services/assessmentService';
import { apiClient } from '../services/apiClient';
import type {
  AssessmentAdminDetail,
  OfficerAssessmentResultsView,
  QuestionAdminView,
  QuestionCreatePayload,
  QuestionUpdatePayload,
  OptionItem,
} from '../types/assessment';

export const AssessmentBuilderPage: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();

  const [assessment, setAssessment] = useState<AssessmentAdminDetail | null>(null);
  const [resultsView, setResultsView] = useState<OfficerAssessmentResultsView | null>(null);
  const [activeTab, setActiveTab] = useState<'QUESTIONS' | 'RESULTS'>('QUESTIONS');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Question Modal (Add / Edit)
  const [showQuestionModal, setShowQuestionModal] = useState(false);
  const [editingQuestion, setEditingQuestion] = useState<QuestionAdminView | null>(null);
  const [questionText, setQuestionText] = useState('');
  const [options, setOptions] = useState<OptionItem[]>([
    { key: 'A', text: '' },
    { key: 'B', text: '' },
    { key: 'C', text: '' },
    { key: 'D', text: '' },
  ]);
  const [correctOption, setCorrectOption] = useState('A');
  const [marks, setMarks] = useState<number>(1);
  const [explanation, setExplanation] = useState('');
  const [savingQuestion, setSavingQuestion] = useState(false);
  const [questionError, setQuestionError] = useState<string | null>(null);

  // Publish / Archive states
  const [actionLoading, setActionLoading] = useState(false);

  // Assign Modal
  const [showAssignModal, setShowAssignModal] = useState(false);
  const [students, setStudents] = useState<any[]>([]);
  const [selectedStudentIds, setSelectedStudentIds] = useState<string[]>([]);
  const [dueDate, setDueDate] = useState<string>('');
  const [assigning, setAssigning] = useState(false);
  const [assignSuccess, setAssignSuccess] = useState<string | null>(null);

  useEffect(() => {
    if (id) {
      loadAssessmentData();
    }
  }, [id]);

  const loadAssessmentData = async () => {
    if (!id) return;
    setLoading(true);
    setError(null);
    try {
      const adminDetail = await assessmentService.getAssessmentAdmin(id);
      setAssessment(adminDetail);

      if (adminDetail.status === 'PUBLISHED' || adminDetail.status === 'ARCHIVED') {
        const results = await assessmentService.getOfficerResults(id);
        setResultsView(results);
      }
    } catch (err: any) {
      setError(err?.response?.data?.detail || 'Failed to load assessment details.');
    } finally {
      setLoading(false);
    }
  };

  const openAddQuestionModal = () => {
    setEditingQuestion(null);
    setQuestionText('');
    setOptions([
      { key: 'A', text: '' },
      { key: 'B', text: '' },
      { key: 'C', text: '' },
      { key: 'D', text: '' },
    ]);
    setCorrectOption('A');
    setMarks(1);
    setExplanation('');
    setQuestionError(null);
    setShowQuestionModal(true);
  };

  const openEditQuestionModal = (q: QuestionAdminView) => {
    setEditingQuestion(q);
    setQuestionText(q.question_text);
    setOptions(q.options.map((opt) => ({ key: opt.key, text: opt.text })));
    setCorrectOption(q.correct_option);
    setMarks(Number(q.marks));
    setExplanation(q.explanation || '');
    setQuestionError(null);
    setShowQuestionModal(true);
  };

  const handleSaveQuestion = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!id) return;

    // Validate options
    const validOptions = options.map((opt) => ({
      key: opt.key.trim().toUpperCase(),
      text: opt.text.trim(),
    }));

    if (validOptions.some((opt) => !opt.text)) {
      setQuestionError('Please provide text for all options.');
      return;
    }

    setSavingQuestion(true);
    setQuestionError(null);
    try {
      if (editingQuestion) {
        const payload: QuestionUpdatePayload = {
          question_text: questionText.trim(),
          options: validOptions,
          correct_option: correctOption,
          marks: Number(marks),
          explanation: explanation.trim() || null,
        };
        await assessmentService.updateQuestion(id, editingQuestion.id, payload);
      } else {
        const payload: QuestionCreatePayload = {
          question_text: questionText.trim(),
          options: validOptions,
          correct_option: correctOption,
          marks: Number(marks),
          explanation: explanation.trim() || null,
          sequence_order: (assessment?.questions.length || 0) + 1,
        };
        await assessmentService.addQuestion(id, payload);
      }

      setShowQuestionModal(false);
      await loadAssessmentData();
    } catch (err: any) {
      setQuestionError(err?.response?.data?.detail || 'Failed to save question.');
    } finally {
      setSavingQuestion(false);
    }
  };

  const handleDeleteQuestion = async (questionId: string) => {
    if (!id || !confirm('Are you sure you want to remove this question?')) return;
    try {
      await assessmentService.deleteQuestion(id, questionId);
      await loadAssessmentData();
    } catch (err: any) {
      alert(err?.response?.data?.detail || 'Failed to delete question.');
    }
  };

  const handlePublish = async () => {
    if (!id) return;
    if ((assessment?.questions.length || 0) === 0) {
      alert('Cannot publish assessment with 0 questions. Please add at least one question.');
      return;
    }
    if (!confirm('Are you sure you want to publish this assessment? Once published, questions are locked.')) return;

    setActionLoading(true);
    try {
      await assessmentService.publishAssessment(id);
      await loadAssessmentData();
    } catch (err: any) {
      alert(err?.response?.data?.detail || 'Failed to publish assessment.');
    } finally {
      setActionLoading(false);
    }
  };

  const handleArchive = async () => {
    if (!id || !confirm('Are you sure you want to archive this assessment? No new attempts will be allowed.')) return;
    setActionLoading(true);
    try {
      await assessmentService.archiveAssessment(id);
      await loadAssessmentData();
    } catch (err: any) {
      alert(err?.response?.data?.detail || 'Failed to archive assessment.');
    } finally {
      setActionLoading(false);
    }
  };

  const openAssignModal = async () => {
    setSelectedStudentIds([]);
    setDueDate('');
    setAssignSuccess(null);
    setShowAssignModal(true);
    try {
      const res = await apiClient.get('/officers/students', { params: { page_size: 100 } });
      setStudents(res.data.items || []);
    } catch {
      setStudents([]);
    }
  };

  const handleAssignSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!id || selectedStudentIds.length === 0) return;
    setAssigning(true);
    try {
      await assessmentService.assignAssessment(
        id,
        selectedStudentIds,
        dueDate ? new Date(dueDate).toISOString() : null
      );
      setAssignSuccess(`Successfully assigned to ${selectedStudentIds.length} student(s)!`);
      setTimeout(() => {
        setShowAssignModal(false);
        setAssignSuccess(null);
        loadAssessmentData();
      }, 1200);
    } catch (err: any) {
      alert(err?.response?.data?.detail || 'Failed to assign assessment.');
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
      prev.includes(userId) ? prev.filter((sId) => sId !== userId) : [...prev, userId]
    );
  };

  if (loading) {
    return (
      <div className="p-8 text-center text-slate-500 font-bold animate-pulse space-y-4">
        <div className="w-12 h-12 rounded-full border-4 border-indigo-600 border-t-transparent animate-spin mx-auto" />
        <p className="text-xs">Loading assessment details...</p>
      </div>
    );
  }

  if (error || !assessment) {
    return (
      <div className="bg-rose-50 border border-rose-200 text-rose-700 p-6 rounded-2xl text-center space-y-3">
        <div className="text-sm font-bold">{error || 'Assessment not found.'}</div>
        <button
          onClick={() => navigate('/assessments')}
          className="px-4 py-2 bg-slate-900 text-white rounded-xl text-xs font-bold"
        >
          Back to Assessments
        </button>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Top Breadcrumb & Action Header */}
      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
        <div className="space-y-1">
          <div className="flex items-center space-x-2 text-xs font-bold text-slate-400">
            <span
              onClick={() => navigate('/assessments')}
              className="cursor-pointer hover:text-slate-600 transition"
            >
              Assessments
            </span>
            <span>&bull;</span>
            <span className="text-slate-600">Builder</span>
          </div>
          <div className="flex items-center space-x-3">
            <h1 className="text-2xl font-black text-slate-900 tracking-tight">{assessment.title}</h1>
            <span
              className={`px-2.5 py-0.5 rounded-full text-[10px] font-extrabold tracking-wide uppercase ${
                assessment.status === 'PUBLISHED'
                  ? 'bg-emerald-50 text-emerald-700 border border-emerald-200'
                  : assessment.status === 'DRAFT'
                  ? 'bg-amber-50 text-amber-700 border border-amber-200'
                  : 'bg-slate-100 text-slate-600 border border-slate-200'
              }`}
            >
              {assessment.status}
            </span>
          </div>
        </div>

        {/* Action Controls */}
        <div className="flex items-center space-x-3">
          {assessment.status === 'DRAFT' && (
            <>
              <button
                onClick={openAddQuestionModal}
                className="px-4 py-2.5 rounded-xl bg-indigo-600 hover:bg-indigo-700 text-white text-xs font-bold shadow-md shadow-indigo-600/20 transition flex items-center space-x-1.5"
              >
                <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 4v16m8-8H4" />
                </svg>
                <span>Add Question</span>
              </button>

              <button
                onClick={handlePublish}
                disabled={actionLoading}
                className="px-4 py-2.5 rounded-xl bg-emerald-600 hover:bg-emerald-700 text-white text-xs font-bold shadow-md shadow-emerald-600/20 transition disabled:opacity-50"
              >
                {actionLoading ? 'Publishing...' : 'Publish Assessment'}
              </button>
            </>
          )}

          {assessment.status === 'PUBLISHED' && (
            <>
              <button
                onClick={openAssignModal}
                className="px-4 py-2.5 rounded-xl bg-indigo-600 hover:bg-indigo-700 text-white text-xs font-bold shadow-md shadow-indigo-600/20 transition flex items-center space-x-1.5"
              >
                <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M18 9v3m0 0v3m0-3h3m-3 0h-3m-2-5a4 4 0 11-8 0 4 4 0 018 0zM3 20a6 6 0 0112 0v1H3v-1z" />
                </svg>
                <span>Assign Assessment</span>
              </button>

              <button
                onClick={handleArchive}
                disabled={actionLoading}
                className="px-3.5 py-2.5 rounded-xl bg-slate-100 hover:bg-slate-200 text-slate-700 text-xs font-bold transition"
              >
                Archive
              </button>
            </>
          )}
        </div>
      </div>

      {/* Assessment Metadata Banner */}
      <div className="bg-white rounded-2xl border border-slate-200/80 p-5 shadow-sm grid grid-cols-2 sm:grid-cols-4 md:grid-cols-6 gap-4 text-center">
        <div className="p-3 bg-slate-50 rounded-xl border border-slate-100">
          <div className="text-[10px] text-slate-400 font-bold uppercase">Difficulty</div>
          <div className="text-xs font-extrabold text-indigo-600">{assessment.difficulty}</div>
        </div>
        <div className="p-3 bg-slate-50 rounded-xl border border-slate-100">
          <div className="text-[10px] text-slate-400 font-bold uppercase">Duration</div>
          <div className="text-xs font-extrabold text-slate-800">{assessment.duration_minutes} Mins</div>
        </div>
        <div className="p-3 bg-slate-50 rounded-xl border border-slate-100">
          <div className="text-[10px] text-slate-400 font-bold uppercase">Questions</div>
          <div className="text-xs font-extrabold text-slate-800">{assessment.questions.length}</div>
        </div>
        <div className="p-3 bg-slate-50 rounded-xl border border-slate-100">
          <div className="text-[10px] text-slate-400 font-bold uppercase">Total Marks</div>
          <div className="text-xs font-extrabold text-slate-800">{assessment.total_marks}</div>
        </div>
        <div className="p-3 bg-slate-50 rounded-xl border border-slate-100">
          <div className="text-[10px] text-slate-400 font-bold uppercase">Pass %</div>
          <div className="text-xs font-extrabold text-slate-800">{assessment.pass_percentage}%</div>
        </div>
        <div className="p-3 bg-slate-50 rounded-xl border border-slate-100">
          <div className="text-[10px] text-slate-400 font-bold uppercase">Attempts</div>
          <div className="text-xs font-extrabold text-slate-800">
            {assessment.allow_multiple_attempts ? 'Multiple' : 'Single'}
          </div>
        </div>
      </div>

      {/* Tabs */}
      <div className="flex border-b border-slate-200 space-x-6 text-xs font-extrabold">
        <button
          onClick={() => setActiveTab('QUESTIONS')}
          className={`pb-3 transition relative ${
            activeTab === 'QUESTIONS'
              ? 'text-indigo-600 border-b-2 border-indigo-600'
              : 'text-slate-400 hover:text-slate-700'
          }`}
        >
          Questions Builder ({assessment.questions.length})
        </button>

        <button
          onClick={() => setActiveTab('RESULTS')}
          className={`pb-3 transition relative ${
            activeTab === 'RESULTS'
              ? 'text-indigo-600 border-b-2 border-indigo-600'
              : 'text-slate-400 hover:text-slate-700'
          }`}
        >
          Results & Submissions ({assessment.assignments_count})
        </button>
      </div>

      {/* TAB 1: QUESTIONS BUILDER */}
      {activeTab === 'QUESTIONS' && (
        <div className="space-y-4">
          {assessment.status !== 'DRAFT' && (
            <div className="p-3.5 bg-slate-100 border border-slate-200 text-slate-700 text-xs font-semibold rounded-2xl flex items-center space-x-2">
              <svg className="w-4 h-4 text-slate-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
              </svg>
              <span>This assessment is {assessment.status.toLowerCase()}. Questions are locked to protect student scores.</span>
            </div>
          )}

          {assessment.questions.length === 0 ? (
            <div className="bg-white rounded-3xl border border-slate-200 p-12 text-center space-y-3">
              <p className="text-xs text-slate-500 font-semibold">No questions added yet.</p>
              {assessment.status === 'DRAFT' && (
                <button
                  onClick={openAddQuestionModal}
                  className="px-4 py-2 bg-indigo-600 hover:bg-indigo-700 text-white rounded-xl text-xs font-bold transition"
                >
                  + Add First MCQ Question
                </button>
              )}
            </div>
          ) : (
            <div className="space-y-4">
              {assessment.questions.map((q, idx) => (
                <div
                  key={q.id}
                  className="bg-white rounded-2xl border border-slate-200/80 p-5 shadow-sm space-y-4"
                >
                  <div className="flex items-start justify-between gap-3">
                    <div className="flex items-center space-x-3">
                      <span className="w-7 h-7 rounded-xl bg-indigo-50 text-indigo-600 flex items-center justify-center font-black text-xs">
                        #{idx + 1}
                      </span>
                      <h3 className="text-sm font-bold text-slate-900 leading-snug">
                        {q.question_text}
                      </h3>
                    </div>

                    <div className="flex items-center space-x-2">
                      <span className="px-2 py-1 bg-slate-100 text-slate-700 text-[10px] font-extrabold rounded-lg">
                        {q.marks} Mark{Number(q.marks) > 1 ? 's' : ''}
                      </span>
                      {q.topic_name && (
                        <span className="px-2 py-1 bg-indigo-50 text-indigo-700 text-[10px] font-extrabold rounded-lg">
                          {q.topic_name}
                        </span>
                      )}
                      {assessment.status === 'DRAFT' && (
                        <>
                          <button
                            onClick={() => openEditQuestionModal(q)}
                            className="p-1.5 text-slate-400 hover:text-indigo-600 hover:bg-slate-50 rounded-lg transition"
                            title="Edit Question"
                          >
                            <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M15.232 5.232l3.536 3.536m-2.036-5.036a2.5 2.5 0 113.536 3.536L6.5 21.036H3v-3.572L16.732 3.732z" />
                            </svg>
                          </button>
                          <button
                            onClick={() => handleDeleteQuestion(q.id)}
                            className="p-1.5 text-slate-400 hover:text-rose-600 hover:bg-rose-50 rounded-lg transition"
                            title="Delete Question"
                          >
                            <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                            </svg>
                          </button>
                        </>
                      )}
                    </div>
                  </div>

                  {/* Options List */}
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-2.5 pt-2">
                    {q.options.map((opt) => {
                      const isCorrect = opt.key.trim().toUpperCase() === q.correct_option.trim().toUpperCase();
                      return (
                        <div
                          key={opt.key}
                          className={`p-3 rounded-xl border text-xs font-semibold flex items-center space-x-3 transition ${
                            isCorrect
                              ? 'bg-emerald-50/80 border-emerald-300 text-emerald-950 font-bold'
                              : 'bg-slate-50 border-slate-200 text-slate-700'
                          }`}
                        >
                          <span
                            className={`w-6 h-6 rounded-lg flex items-center justify-center font-black text-xs ${
                              isCorrect ? 'bg-emerald-600 text-white' : 'bg-slate-200 text-slate-600'
                            }`}
                          >
                            {opt.key}
                          </span>
                          <span className="flex-1">{opt.text}</span>
                          {isCorrect && (
                            <span className="text-[10px] uppercase font-black tracking-wider text-emerald-700 bg-emerald-100 px-2 py-0.5 rounded-md">
                              Correct Answer
                            </span>
                          )}
                        </div>
                      );
                    })}
                  </div>

                  {q.explanation && (
                    <div className="p-3 bg-indigo-50/50 rounded-xl border border-indigo-100 text-xs text-indigo-900 font-medium">
                      <span className="font-bold text-indigo-700">Explanation: </span>
                      {q.explanation}
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* TAB 2: RESULTS & SUBMISSIONS */}
      {activeTab === 'RESULTS' && (
        <div className="space-y-6">
          {resultsView && (
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
              <div className="bg-white p-4 rounded-2xl border border-slate-200 text-center">
                <div className="text-[10px] font-bold text-slate-400 uppercase">Assigned</div>
                <div className="text-xl font-black text-slate-900">{resultsView.total_assigned}</div>
              </div>
              <div className="bg-white p-4 rounded-2xl border border-slate-200 text-center">
                <div className="text-[10px] font-bold text-slate-400 uppercase">Completed</div>
                <div className="text-xl font-black text-slate-900">{resultsView.total_completed}</div>
              </div>
              <div className="bg-white p-4 rounded-2xl border border-slate-200 text-center">
                <div className="text-[10px] font-bold text-slate-400 uppercase">Avg Score</div>
                <div className="text-xl font-black text-indigo-600">
                  {resultsView.average_score !== null ? resultsView.average_score : 'N/A'}
                </div>
              </div>
              <div className="bg-white p-4 rounded-2xl border border-slate-200 text-center">
                <div className="text-[10px] font-bold text-slate-400 uppercase">Pass Count</div>
                <div className="text-xl font-black text-emerald-600">{resultsView.pass_count}</div>
              </div>
            </div>
          )}

          <div className="bg-white rounded-2xl border border-slate-200 overflow-hidden shadow-sm">
            <div className="p-4 border-b border-slate-100 flex items-center justify-between">
              <h3 className="text-sm font-extrabold text-slate-900">Assigned Students</h3>
              {assessment.status === 'PUBLISHED' && (
                <button
                  onClick={openAssignModal}
                  className="px-3 py-1.5 bg-indigo-50 hover:bg-indigo-100 text-indigo-700 text-xs font-bold rounded-xl transition"
                >
                  + Assign More Students
                </button>
              )}
            </div>

            {!resultsView || resultsView.results.length === 0 ? (
              <div className="p-8 text-center text-xs text-slate-400 font-semibold">
                No students assigned to this assessment yet.
              </div>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full text-left text-xs">
                  <thead className="bg-slate-50 border-b border-slate-100 text-slate-500 font-bold uppercase text-[10px]">
                    <tr>
                      <th className="py-3 px-4">Student</th>
                      <th className="py-3 px-4">Branch / Roll</th>
                      <th className="py-3 px-4">Status</th>
                      <th className="py-3 px-4">Score</th>
                      <th className="py-3 px-4">Percentage</th>
                      <th className="py-3 px-4">Result</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100">
                    {resultsView.results.map((res) => (
                      <tr key={res.id} className="hover:bg-slate-50/80 transition">
                        <td className="py-3 px-4 font-bold text-slate-900">
                          {res.student_name || 'Student'}
                          <div className="text-[10px] text-slate-400 font-normal">{res.student_email}</div>
                        </td>
                        <td className="py-3 px-4 font-semibold text-slate-600">
                          {res.student_branch || 'General'}
                          <div className="text-[10px] text-slate-400">{res.student_roll_number || 'N/A'}</div>
                        </td>
                        <td className="py-3 px-4">
                          <span
                            className={`px-2 py-0.5 rounded-full text-[10px] font-extrabold uppercase ${
                              res.status === 'COMPLETED'
                                ? 'bg-emerald-50 text-emerald-700'
                                : res.status === 'IN_PROGRESS'
                                ? 'bg-amber-50 text-amber-700'
                                : 'bg-slate-100 text-slate-600'
                            }`}
                          >
                            {res.status}
                          </span>
                        </td>
                        <td className="py-3 px-4 font-extrabold text-slate-900">
                          {res.latest_score !== null ? res.latest_score : '—'}
                        </td>
                        <td className="py-3 px-4 font-extrabold text-slate-900">
                          {res.latest_percentage !== null ? `${res.latest_percentage}%` : '—'}
                        </td>
                        <td className="py-3 px-4">
                          {res.latest_passed !== null ? (
                            <span
                              className={`px-2 py-0.5 rounded-md text-[10px] font-black ${
                                res.latest_passed
                                  ? 'bg-emerald-100 text-emerald-800'
                                  : 'bg-rose-100 text-rose-800'
                              }`}
                            >
                              {res.latest_passed ? 'PASSED' : 'FAILED'}
                            </span>
                          ) : (
                            <span className="text-slate-400 text-xs">—</span>
                          )}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        </div>
      )}

      {/* ADD / EDIT QUESTION MODAL */}
      {showQuestionModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/60 backdrop-blur-sm animate-fade-in">
          <div className="bg-white rounded-3xl border border-slate-200 shadow-2xl max-w-2xl w-full p-6 space-y-5 max-h-[90vh] overflow-y-auto">
            <div className="flex items-center justify-between border-b border-slate-100 pb-3">
              <h2 className="text-lg font-extrabold text-slate-900">
                {editingQuestion ? 'Edit MCQ Question' : 'Add MCQ Question'}
              </h2>
              <button
                onClick={() => setShowQuestionModal(false)}
                className="text-slate-400 hover:text-slate-600 p-1 rounded-lg"
              >
                <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>

            {questionError && (
              <div className="p-3 bg-rose-50 border border-rose-200 text-rose-700 text-xs font-semibold rounded-xl">
                {questionError}
              </div>
            )}

            <form onSubmit={handleSaveQuestion} className="space-y-4">
              <div>
                <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-1">
                  Question Text *
                </label>
                <textarea
                  required
                  rows={3}
                  placeholder="Enter the question problem statement..."
                  value={questionText}
                  onChange={(e) => setQuestionText(e.target.value)}
                  className="w-full px-3.5 py-2 text-xs font-medium bg-slate-50 border border-slate-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-600"
                />
              </div>

              {/* Options */}
              <div className="space-y-2.5">
                <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider">
                  Options & Correct Answer Selection *
                </label>

                {options.map((opt, idx) => (
                  <div key={opt.key} className="flex items-center space-x-3">
                    <label className="flex items-center space-x-2 cursor-pointer">
                      <input
                        type="radio"
                        name="correct_option"
                        checked={correctOption === opt.key}
                        onChange={() => setCorrectOption(opt.key)}
                        className="text-emerald-600 focus:ring-emerald-500 w-4 h-4 cursor-pointer"
                      />
                      <span className="w-6 h-6 rounded-lg bg-slate-100 text-slate-800 flex items-center justify-center font-black text-xs">
                        {opt.key}
                      </span>
                    </label>

                    <input
                      type="text"
                      required
                      placeholder={`Option ${opt.key} description...`}
                      value={opt.text}
                      onChange={(e) => {
                        const newOpts = [...options];
                        newOpts[idx].text = e.target.value;
                        setOptions(newOpts);
                      }}
                      className="flex-1 px-3 py-2 text-xs font-medium bg-slate-50 border border-slate-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-indigo-500/20"
                    />
                  </div>
                ))}
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-1">
                    Marks *
                  </label>
                  <input
                    type="number"
                    min={0.5}
                    step={0.5}
                    max={100}
                    required
                    value={marks}
                    onChange={(e) => setMarks(Number(e.target.value))}
                    className="w-full px-3 py-2 text-xs font-bold bg-slate-50 border border-slate-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-indigo-500/20"
                  />
                </div>

                <div>
                  <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-1">
                    Explanation (Optional)
                  </label>
                  <input
                    type="text"
                    placeholder="Solution walkthrough for students..."
                    value={explanation}
                    onChange={(e) => setExplanation(e.target.value)}
                    className="w-full px-3 py-2 text-xs font-medium bg-slate-50 border border-slate-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-indigo-500/20"
                  />
                </div>
              </div>

              <div className="pt-4 border-t border-slate-100 flex items-center justify-end space-x-3">
                <button
                  type="button"
                  onClick={() => setShowQuestionModal(false)}
                  className="px-4 py-2 rounded-xl bg-slate-100 hover:bg-slate-200 text-slate-700 font-bold text-xs transition"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={savingQuestion}
                  className="px-5 py-2 rounded-xl bg-indigo-600 hover:bg-indigo-700 text-white font-bold text-xs transition shadow-md shadow-indigo-600/20 disabled:opacity-50"
                >
                  {savingQuestion ? 'Saving...' : 'Save Question'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* ASSIGN MODAL */}
      {showAssignModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/60 backdrop-blur-sm animate-fade-in">
          <div className="bg-white rounded-3xl border border-slate-200 shadow-2xl max-w-xl w-full p-6 space-y-5">
            <div className="flex items-center justify-between border-b border-slate-100 pb-3">
              <div>
                <h2 className="text-lg font-extrabold text-slate-900">Assign Assessment</h2>
                <p className="text-xs text-slate-500 font-medium">{assessment.title}</p>
              </div>
              <button
                onClick={() => setShowAssignModal(false)}
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
                  onClick={() => setShowAssignModal(false)}
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

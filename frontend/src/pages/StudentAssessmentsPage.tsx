import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { assessmentService } from '../services/assessmentService';
import type {
  AssessmentAssignmentResponse,
  AssessmentResultResponse,
  AssessmentStudentPreview,
} from '../types/assessment';

export const StudentAssessmentsPage: React.FC = () => {
  const navigate = useNavigate();

  const [activeTab, setActiveTab] = useState<'ASSIGNED' | 'HISTORY'>('ASSIGNED');
  const [assignedList, setAssignedList] = useState<AssessmentAssignmentResponse[]>([]);
  const [historyList, setHistoryList] = useState<AssessmentResultResponse[]>([]);
  const [statusFilter, setStatusFilter] = useState<string>('ALL');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Preview Modal
  const [previewData, setPreviewData] = useState<AssessmentStudentPreview | null>(null);
  const [startingTest, setStartingTest] = useState(false);

  useEffect(() => {
    fetchData();
  }, [activeTab, statusFilter]);

  const fetchData = async () => {
    setLoading(true);
    setError(null);
    try {
      if (activeTab === 'ASSIGNED') {
        const filter = statusFilter !== 'ALL' ? statusFilter : undefined;
        const res = await assessmentService.getAssignedAssessments(filter);
        setAssignedList(res);
      } else {
        const res = await assessmentService.getMyHistory();
        setHistoryList(res);
      }
    } catch (err: any) {
      setError(err?.response?.data?.detail || 'Failed to load assessments.');
    } finally {
      setLoading(false);
    }
  };

  const handleOpenPreview = async (assessmentId: string) => {
    try {
      const data = await assessmentService.getStudentPreview(assessmentId);
      setPreviewData(data);
    } catch (err: any) {
      alert(err?.response?.data?.detail || 'Failed to load assessment preview.');
    }
  };

  const handleStartAttempt = async (assessmentId: string) => {
    setStartingTest(true);
    try {
      const startRes = await assessmentService.startAttempt(assessmentId);
      setPreviewData(null);
      navigate(`/assessments/player/${startRes.attempt_id}`);
    } catch (err: any) {
      alert(err?.response?.data?.detail || 'Failed to start assessment attempt.');
    } finally {
      setStartingTest(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-black text-slate-900 tracking-tight">Practice Assessments</h1>
        <p className="text-sm text-slate-500 font-medium">
          Sharpen your placement aptitude, CS fundamentals, and technical interview readiness with timed mock tests.
        </p>
      </div>

      {/* Tabs & Status Filter */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between border-b border-slate-200 gap-4">
        <div className="flex space-x-6 text-xs font-extrabold">
          <button
            onClick={() => setActiveTab('ASSIGNED')}
            className={`pb-3 transition relative ${
              activeTab === 'ASSIGNED'
                ? 'text-indigo-600 border-b-2 border-indigo-600'
                : 'text-slate-400 hover:text-slate-700'
            }`}
          >
            Assigned Assessments
          </button>

          <button
            onClick={() => setActiveTab('HISTORY')}
            className={`pb-3 transition relative ${
              activeTab === 'HISTORY'
                ? 'text-indigo-600 border-b-2 border-indigo-600'
                : 'text-slate-400 hover:text-slate-700'
            }`}
          >
            Test History & Results
          </button>
        </div>

        {activeTab === 'ASSIGNED' && (
          <div className="flex items-center space-x-2 pb-2 text-xs font-semibold text-slate-500">
            <span>Filter:</span>
            <select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
              className="bg-white border border-slate-200 rounded-lg px-2.5 py-1 text-xs font-bold text-slate-800 focus:outline-none focus:ring-2 focus:ring-indigo-500/20"
            >
              <option value="ALL">All Assigned</option>
              <option value="ASSIGNED">Pending</option>
              <option value="IN_PROGRESS">In Progress</option>
              <option value="COMPLETED">Completed</option>
            </select>
          </div>
        )}
      </div>

      {/* Error / Loading / Content State */}
      {error && (
        <div className="p-4 rounded-2xl bg-rose-50 border border-rose-200 text-rose-700 text-xs font-semibold">
          {error}
        </div>
      )}

      {loading ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 animate-pulse">
          {[1, 2, 3].map((n) => (
            <div key={n} className="h-52 bg-white rounded-2xl border border-slate-200 p-5 space-y-4" />
          ))}
        </div>
      ) : activeTab === 'ASSIGNED' ? (
        assignedList.length === 0 ? (
          <div className="bg-white rounded-3xl border border-slate-200 p-12 text-center space-y-3 shadow-sm">
            <div className="w-12 h-12 bg-indigo-50 text-indigo-600 rounded-2xl flex items-center justify-center mx-auto">
              <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
            </div>
            <h3 className="text-sm font-extrabold text-slate-900">No assessments found</h3>
            <p className="text-xs text-slate-500 max-w-sm mx-auto">
              You are all caught up! New practice tests assigned by your placement cell will appear here.
            </p>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {assignedList.map((item) => (
              <div
                key={item.id}
                className="bg-white rounded-2xl border border-slate-200/80 p-5 shadow-sm hover:shadow-md transition-all flex flex-col justify-between space-y-4"
              >
                <div className="space-y-3">
                  <div className="flex items-center justify-between gap-2">
                    <span
                      className={`px-2.5 py-0.5 rounded-full text-[10px] font-black uppercase ${
                        item.status === 'COMPLETED'
                          ? 'bg-emerald-50 text-emerald-700 border border-emerald-200'
                          : item.status === 'IN_PROGRESS'
                          ? 'bg-amber-50 text-amber-700 border border-amber-200'
                          : 'bg-indigo-50 text-indigo-700 border border-indigo-200'
                      }`}
                    >
                      {item.status}
                    </span>

                    <span className="px-2 py-0.5 rounded-md bg-slate-100 text-slate-700 text-[10px] font-extrabold">
                      {item.difficulty}
                    </span>
                  </div>

                  <div>
                    <h3 className="text-base font-extrabold text-slate-900 leading-snug">
                      {item.assessment_title}
                    </h3>
                    {(item.category_name || item.topic_name) && (
                      <p className="text-[11px] text-slate-500 font-semibold mt-1 truncate">
                        {item.category_name} {item.topic_name ? `• ${item.topic_name}` : ''}
                      </p>
                    )}
                  </div>

                  <div className="pt-2 border-t border-slate-100 grid grid-cols-3 gap-2 text-center">
                    <div className="bg-slate-50 p-2 rounded-xl border border-slate-100">
                      <div className="text-[10px] text-slate-400 font-bold uppercase">Duration</div>
                      <div className="text-xs font-extrabold text-slate-800">{item.duration_minutes}m</div>
                    </div>
                    <div className="bg-slate-50 p-2 rounded-xl border border-slate-100">
                      <div className="text-[10px] text-slate-400 font-bold uppercase">Marks</div>
                      <div className="text-xs font-extrabold text-slate-800">{item.total_marks}</div>
                    </div>
                    <div className="bg-slate-50 p-2 rounded-xl border border-slate-100">
                      <div className="text-[10px] text-slate-400 font-bold uppercase">Pass %</div>
                      <div className="text-xs font-extrabold text-slate-800">{item.pass_percentage}%</div>
                    </div>
                  </div>

                  {item.due_date && (
                    <div className="text-[11px] text-slate-400 font-medium">
                      Due: {new Date(item.due_date).toLocaleDateString()}
                    </div>
                  )}

                  {item.status === 'COMPLETED' && item.latest_score !== null && (
                    <div className="p-2.5 rounded-xl bg-slate-50 border border-slate-100 flex items-center justify-between text-xs font-extrabold">
                      <span className="text-slate-600">Your Score:</span>
                      <span className="text-slate-900">{item.latest_score} / {item.total_marks} ({item.latest_percentage}%)</span>
                    </div>
                  )}
                </div>

                {/* Card Action */}
                <div className="pt-3 border-t border-slate-100">
                  {item.status === 'ASSIGNED' && (
                    <button
                      onClick={() => handleOpenPreview(item.assessment_id)}
                      className="w-full py-2.5 px-4 rounded-xl bg-indigo-600 hover:bg-indigo-700 text-white font-bold text-xs shadow-md shadow-indigo-600/20 transition text-center"
                    >
                      Start Assessment →
                    </button>
                  )}

                  {item.status === 'IN_PROGRESS' && (
                    <button
                      onClick={() => handleStartAttempt(item.assessment_id)}
                      className="w-full py-2.5 px-4 rounded-xl bg-amber-600 hover:bg-amber-700 text-white font-bold text-xs shadow-md shadow-amber-600/20 transition flex items-center justify-center space-x-1.5"
                    >
                      <span className="w-2 h-2 rounded-full bg-white animate-pulse" />
                      <span>Resume Attempt →</span>
                    </button>
                  )}

                  {item.status === 'COMPLETED' && (
                    <button
                      onClick={async () => {
                        try {
                          const preview = await assessmentService.getStudentPreview(item.assessment_id);
                          if (preview.latest_result_id) {
                            // Find attempt id
                            const history = await assessmentService.getMyHistory();
                            const matchingResult = history.find((h) => h.assessment_id === item.assessment_id);
                            if (matchingResult) {
                              navigate(`/assessments/results/${matchingResult.attempt_id}`);
                            }
                          }
                        } catch {
                          alert('Unable to load completed result.');
                        }
                      }}
                      className="w-full py-2 px-4 rounded-xl bg-slate-100 hover:bg-slate-200 text-slate-700 font-bold text-xs transition text-center"
                    >
                      View Answer Review
                    </button>
                  )}
                </div>
              </div>
            ))}
          </div>
        )
      ) : (
        /* TAB 2: TEST HISTORY */
        historyList.length === 0 ? (
          <div className="bg-white rounded-3xl border border-slate-200 p-12 text-center space-y-3 shadow-sm">
            <h3 className="text-sm font-extrabold text-slate-900">No test attempts yet</h3>
            <p className="text-xs text-slate-500 max-w-sm mx-auto">
              Your test scores, percentage, pass/fail status, and question answer reviews will be archived here.
            </p>
          </div>
        ) : (
          <div className="bg-white rounded-2xl border border-slate-200 overflow-hidden shadow-sm">
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs">
                <thead className="bg-slate-50 border-b border-slate-100 text-slate-500 font-bold uppercase text-[10px]">
                  <tr>
                    <th className="py-3 px-4">Assessment</th>
                    <th className="py-3 px-4">Submitted Date</th>
                    <th className="py-3 px-4">Questions</th>
                    <th className="py-3 px-4">Score</th>
                    <th className="py-3 px-4">Percentage</th>
                    <th className="py-3 px-4">Result</th>
                    <th className="py-3 px-4 text-right">Action</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {historyList.map((res) => (
                    <tr key={res.id} className="hover:bg-slate-50/80 transition">
                      <td className="py-3.5 px-4 font-bold text-slate-900">{res.assessment_title}</td>
                      <td className="py-3.5 px-4 text-slate-500 font-medium">
                        {new Date(res.created_at).toLocaleDateString()}
                      </td>
                      <td className="py-3.5 px-4 font-semibold text-slate-700">
                        {res.correct_answers} / {res.total_questions} correct
                      </td>
                      <td className="py-3.5 px-4 font-extrabold text-slate-900">
                        {res.score_obtained} / {res.total_score}
                      </td>
                      <td className="py-3.5 px-4 font-extrabold text-slate-900">{res.percentage}%</td>
                      <td className="py-3.5 px-4">
                        <span
                          className={`px-2 py-0.5 rounded-md text-[10px] font-black ${
                            res.is_passed ? 'bg-emerald-100 text-emerald-800' : 'bg-rose-100 text-rose-800'
                          }`}
                        >
                          {res.is_passed ? 'PASSED' : 'FAILED'}
                        </span>
                      </td>
                      <td className="py-3.5 px-4 text-right">
                        <button
                          onClick={() => navigate(`/assessments/results/${res.attempt_id}`)}
                          className="px-3 py-1 bg-indigo-50 hover:bg-indigo-100 text-indigo-700 font-bold rounded-lg text-xs transition"
                        >
                          Review Answers →
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )
      )}

      {/* PRE-TEST PREVIEW MODAL */}
      {previewData && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/60 backdrop-blur-sm animate-fade-in">
          <div className="bg-white rounded-3xl border border-slate-200 shadow-2xl max-w-lg w-full p-6 space-y-5">
            <div className="flex items-center justify-between border-b border-slate-100 pb-3">
              <div>
                <h2 className="text-lg font-black text-slate-900">{previewData.title}</h2>
                <div className="text-xs text-indigo-600 font-bold">{previewData.category_name} &bull; {previewData.topic_name}</div>
              </div>
              <button
                onClick={() => setPreviewData(null)}
                className="text-slate-400 hover:text-slate-600 p-1 rounded-lg"
              >
                <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>

            {previewData.description && (
              <p className="text-xs text-slate-600 bg-slate-50 p-3 rounded-xl border border-slate-100">
                {previewData.description}
              </p>
            )}

            {/* Test rules & metadata */}
            <div className="grid grid-cols-2 gap-3 text-center">
              <div className="bg-slate-50 p-3 rounded-xl border border-slate-100">
                <div className="text-[10px] text-slate-400 font-bold uppercase">Duration</div>
                <div className="text-sm font-black text-slate-800">{previewData.duration_minutes} Minutes</div>
              </div>
              <div className="bg-slate-50 p-3 rounded-xl border border-slate-100">
                <div className="text-[10px] text-slate-400 font-bold uppercase">Questions</div>
                <div className="text-sm font-black text-slate-800">{previewData.question_count} MCQs</div>
              </div>
              <div className="bg-slate-50 p-3 rounded-xl border border-slate-100">
                <div className="text-[10px] text-slate-400 font-bold uppercase">Total Marks</div>
                <div className="text-sm font-black text-slate-800">{previewData.total_marks}</div>
              </div>
              <div className="bg-slate-50 p-3 rounded-xl border border-slate-100">
                <div className="text-[10px] text-slate-400 font-bold uppercase">Passing Score</div>
                <div className="text-sm font-black text-slate-800">{previewData.pass_percentage}%</div>
              </div>
            </div>

            <div className="p-3 bg-amber-50 rounded-xl border border-amber-200 text-amber-900 text-xs font-medium space-y-1">
              <div className="font-bold flex items-center space-x-1 text-amber-800">
                <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
                <span>Important Test Instructions</span>
              </div>
              <p>• The test timer is server-authoritative and starts immediately when you click "Start Test".</p>
              <p>• Your progress is autosaved continuously as you answer.</p>
              <p>• Ensure a stable internet connection before starting.</p>
            </div>

            <div className="pt-4 border-t border-slate-100 flex items-center justify-end space-x-3">
              <button
                type="button"
                onClick={() => setPreviewData(null)}
                className="px-4 py-2 rounded-xl bg-slate-100 hover:bg-slate-200 text-slate-700 font-bold text-xs transition"
              >
                Cancel
              </button>
              <button
                type="button"
                onClick={() => handleStartAttempt(previewData.id)}
                disabled={startingTest}
                className="px-6 py-2.5 rounded-xl bg-indigo-600 hover:bg-indigo-700 text-white font-bold text-xs shadow-md shadow-indigo-600/20 transition disabled:opacity-50"
              >
                {startingTest ? 'Starting...' : 'I am Ready, Start Test →'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

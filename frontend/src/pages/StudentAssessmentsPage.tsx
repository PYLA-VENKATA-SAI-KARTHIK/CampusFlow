import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { assessmentService } from '../services/assessmentService';
import type {
  AssessmentAssignmentResponse,
  AssessmentResultResponse,
  AssessmentStudentPreview,
} from '../types/assessment';
import {
  PageHeader,
  Card,
  Badge,
  Button,
  Select,
  Modal,
  Skeleton,
  EmptyState,
  Alert,
} from '../components/ui';

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
      setError(null);
      const data = await assessmentService.getStudentPreview(assessmentId);
      setPreviewData(data);
    } catch (err: any) {
      setError(err?.response?.data?.detail || 'Failed to load assessment preview.');
    }
  };

  const handleStartAttempt = async (assessmentId: string) => {
    setStartingTest(true);
    setError(null);
    try {
      const startRes = await assessmentService.startAttempt(assessmentId);
      setPreviewData(null);
      navigate(`/assessments/player/${startRes.attempt_id}`);
    } catch (err: any) {
      setError(err?.response?.data?.detail || 'Failed to start assessment attempt.');
    } finally {
      setStartingTest(false);
    }
  };

  return (
    <div className="space-y-6 max-w-7xl mx-auto pb-12">
      {/* SaaS Page Header */}
      <PageHeader
        eyebrow="Practice Assessment Engine"
        badge={
          <Badge variant="primary" size="sm" dot>
            Mock Tests
          </Badge>
        }
        title="Practice Assessments"
        description="Sharpen your placement aptitude, CS fundamentals, and technical interview readiness with timed mock tests."
      />

      {/* Tabs & Status Filter */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between border-b border-slate-200/80 pb-3 gap-4">
        <div className="flex items-center space-x-2">
          <button
            type="button"
            onClick={() => setActiveTab('ASSIGNED')}
            className={`px-3.5 py-2 rounded-xl text-xs font-bold transition duration-150 ${
              activeTab === 'ASSIGNED'
                ? 'bg-indigo-600 text-white shadow-xs'
                : 'text-slate-600 hover:text-slate-900 hover:bg-slate-100'
            }`}
          >
            Assigned Assessments
          </button>

          <button
            type="button"
            onClick={() => setActiveTab('HISTORY')}
            className={`px-3.5 py-2 rounded-xl text-xs font-bold transition duration-150 ${
              activeTab === 'HISTORY'
                ? 'bg-indigo-600 text-white shadow-xs'
                : 'text-slate-600 hover:text-slate-900 hover:bg-slate-100'
            }`}
          >
            Test History & Results
          </button>
        </div>

        {activeTab === 'ASSIGNED' && (
          <div className="flex items-center space-x-2 w-full sm:w-auto">
            <span className="text-xs font-bold text-slate-500 whitespace-nowrap">Filter:</span>
            <div className="w-40">
              <Select
                value={statusFilter}
                onChange={(e) => setStatusFilter(e.target.value)}
              >
                <option value="ALL">All Assigned</option>
                <option value="ASSIGNED">Pending</option>
                <option value="IN_PROGRESS">In Progress</option>
                <option value="COMPLETED">Completed</option>
              </Select>
            </div>
          </div>
        )}
      </div>

      {/* Error / Loading / Content State */}
      {error && (
        <Alert variant="danger" title="Assessment Error">
          <div className="flex items-center justify-between gap-4">
            <span>{error}</span>
            <Button variant="danger" size="sm" onClick={fetchData}>
              Retry
            </Button>
          </div>
        </Alert>
      )}

      {loading ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
          {[1, 2, 3].map((n) => (
            <Card key={n} className="p-5 space-y-4">
              <div className="flex justify-between">
                <Skeleton variant="text" className="w-24" />
                <Skeleton variant="text" className="w-16" />
              </div>
              <Skeleton variant="rectangular" className="h-16" />
              <div className="grid grid-cols-3 gap-2">
                <Skeleton variant="rectangular" className="h-12" />
                <Skeleton variant="rectangular" className="h-12" />
                <Skeleton variant="rectangular" className="h-12" />
              </div>
              <Skeleton variant="rectangular" className="h-10" />
            </Card>
          ))}
        </div>
      ) : activeTab === 'ASSIGNED' ? (
        assignedList.length === 0 ? (
          <EmptyState
            title="No assessments found"
            description="You are all caught up! New practice tests assigned by your placement cell will appear here."
          />
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
            {assignedList.map((item) => (
              <Card
                key={item.id}
                variant="elevated"
                hoverable
                className="p-5 flex flex-col justify-between space-y-4"
              >
                <div className="space-y-3">
                  <div className="flex items-center justify-between gap-2">
                    <span
                      className={`px-2.5 py-0.5 rounded-full text-[10px] font-black uppercase tracking-wider ${
                        item.status === 'COMPLETED'
                          ? 'bg-emerald-50 text-emerald-700 border border-emerald-200'
                          : item.status === 'IN_PROGRESS'
                          ? 'bg-amber-50 text-amber-800 border border-amber-200'
                          : 'bg-indigo-50 text-indigo-700 border border-indigo-200'
                      }`}
                    >
                      {item.status}
                    </span>

                    <span className="px-2 py-0.5 rounded-md bg-slate-100 text-slate-700 text-[10px] font-extrabold border border-slate-200/60">
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
                      <div className="text-xs font-black text-slate-800">{item.duration_minutes}m</div>
                    </div>
                    <div className="bg-slate-50 p-2 rounded-xl border border-slate-100">
                      <div className="text-[10px] text-slate-400 font-bold uppercase">Marks</div>
                      <div className="text-xs font-black text-slate-800">{item.total_marks}</div>
                    </div>
                    <div className="bg-slate-50 p-2 rounded-xl border border-slate-100">
                      <div className="text-[10px] text-slate-400 font-bold uppercase">Pass %</div>
                      <div className="text-xs font-black text-slate-800">{item.pass_percentage}%</div>
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
                      <span className="text-slate-900 font-black">
                        {item.latest_score} / {item.total_marks} ({item.latest_percentage}%)
                      </span>
                    </div>
                  )}
                </div>

                {/* Card Action */}
                <div className="pt-3 border-t border-slate-100">
                  {item.status === 'ASSIGNED' && (
                    <Button
                      variant="primary"
                      size="md"
                      className="w-full"
                      onClick={() => handleOpenPreview(item.assessment_id)}
                    >
                      Start Assessment →
                    </Button>
                  )}

                  {item.status === 'IN_PROGRESS' && (
                    <Button
                      variant="primary"
                      size="md"
                      className="w-full bg-amber-600 hover:bg-amber-700 text-white shadow-amber-600/20"
                      onClick={() => handleStartAttempt(item.assessment_id)}
                      leftIcon={<span className="w-2 h-2 rounded-full bg-white animate-pulse" />}
                    >
                      Resume Attempt →
                    </Button>
                  )}

                  {item.status === 'COMPLETED' && (
                    <Button
                      variant="outline"
                      size="md"
                      className="w-full"
                      onClick={async () => {
                        try {
                          const preview = await assessmentService.getStudentPreview(item.assessment_id);
                          if (preview.latest_result_id) {
                            const history = await assessmentService.getMyHistory();
                            const matchingResult = history.find((h) => h.assessment_id === item.assessment_id);
                            if (matchingResult) {
                              navigate(`/assessments/results/${matchingResult.attempt_id}`);
                            }
                          }
                        } catch {
                          setError('Unable to load completed result.');
                        }
                      }}
                    >
                      View Answer Review
                    </Button>
                  )}
                </div>
              </Card>
            ))}
          </div>
        )
      ) : (
        /* TAB 2: TEST HISTORY */
        historyList.length === 0 ? (
          <EmptyState
            title="No test attempts yet"
            description="Your test scores, percentage, pass/fail status, and question answer reviews will be archived here."
          />
        ) : (
          <Card className="overflow-hidden">
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs">
                <thead className="bg-slate-50 border-b border-slate-100 text-slate-500 font-bold uppercase text-[10px]">
                  <tr>
                    <th className="py-3.5 px-4 font-black">Assessment</th>
                    <th className="py-3.5 px-4 font-black">Submitted Date</th>
                    <th className="py-3.5 px-4 font-black">Questions</th>
                    <th className="py-3.5 px-4 font-black">Score</th>
                    <th className="py-3.5 px-4 font-black">Percentage</th>
                    <th className="py-3.5 px-4 font-black">Result</th>
                    <th className="py-3.5 px-4 text-right font-black">Action</th>
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
                      <td className="py-3.5 px-4 font-black text-slate-900">
                        {res.score_obtained} / {res.total_score}
                      </td>
                      <td className="py-3.5 px-4 font-black text-slate-900">{res.percentage}%</td>
                      <td className="py-3.5 px-4">
                        <span
                          className={`px-2 py-0.5 rounded-md text-[10px] font-black ${
                            res.is_passed
                              ? 'bg-emerald-100 text-emerald-800'
                              : 'bg-rose-100 text-rose-800'
                          }`}
                        >
                          {res.is_passed ? 'PASSED' : 'FAILED'}
                        </span>
                      </td>
                      <td className="py-3.5 px-4 text-right">
                        <Button
                          variant="ghost"
                          size="sm"
                          className="text-indigo-600 hover:text-indigo-700 hover:bg-indigo-50"
                          onClick={() => navigate(`/assessments/results/${res.attempt_id}`)}
                        >
                          Review Answers →
                        </Button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </Card>
        )
      )}

      {/* PRE-TEST PREVIEW MODAL */}
      {previewData && (
        <Modal
          isOpen={!!previewData}
          onClose={() => setPreviewData(null)}
          title={previewData.title}
          description={`${previewData.category_name || 'General'} • ${previewData.topic_name || 'All Topics'}`}
          maxWidth="lg"
        >
          <div className="space-y-5">
            {previewData.description && (
              <p className="text-xs text-slate-600 bg-slate-50 p-3.5 rounded-xl border border-slate-100 leading-relaxed">
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

            <div className="p-3.5 bg-amber-50 rounded-xl border border-amber-200 text-amber-900 text-xs font-medium space-y-1.5">
              <div className="font-bold flex items-center space-x-1.5 text-amber-800">
                <svg className="w-4 h-4 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
                <span>Important Test Instructions</span>
              </div>
              <p>• The test timer is server-authoritative and starts immediately when you click "Start Test".</p>
              <p>• Your progress is autosaved continuously as you answer.</p>
              <p>• Ensure a stable internet connection before starting.</p>
            </div>

            <div className="pt-3 border-t border-slate-100 flex items-center justify-end gap-2.5">
              <Button
                variant="outline"
                size="md"
                onClick={() => setPreviewData(null)}
              >
                Cancel
              </Button>
              <Button
                variant="primary"
                size="md"
                isLoading={startingTest}
                onClick={() => handleStartAttempt(previewData.id)}
              >
                I am Ready, Start Test →
              </Button>
            </div>
          </div>
        </Modal>
      )}
    </div>
  );
};

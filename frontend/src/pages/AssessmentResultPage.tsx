import React, { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { assessmentService } from '../services/assessmentService';
import type { AssessmentResultResponse } from '../types/assessment';
import {
  Card,
  Button,
} from '../components/ui';

export const AssessmentResultPage: React.FC = () => {
  const { attemptId } = useParams<{ attemptId: string }>();
  const navigate = useNavigate();

  const [result, setResult] = useState<AssessmentResultResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [filterMode, setFilterMode] = useState<'ALL' | 'CORRECT' | 'INCORRECT' | 'UNANSWERED'>('ALL');

  useEffect(() => {
    if (!attemptId) return;

    const loadResult = async () => {
      setLoading(true);
      setError(null);
      try {
        const res = await assessmentService.getAttemptResult(attemptId);
        setResult(res);
      } catch (err: any) {
        setError(err?.response?.data?.detail || 'Failed to load assessment result.');
      } finally {
        setLoading(false);
      }
    };

    loadResult();
  }, [attemptId]);

  const formatDuration = (secs: number) => {
    const mins = Math.floor(secs / 60);
    const remainder = secs % 60;
    if (mins === 0) return `${remainder}s`;
    return `${mins}m ${remainder}s`;
  };

  if (loading) {
    return (
      <div className="min-h-[60vh] flex flex-col items-center justify-center space-y-4">
        <div className="w-10 h-10 rounded-full border-3 border-indigo-600 border-t-transparent animate-spin" />
        <p className="text-xs font-bold text-slate-600">Calculating your performance metrics...</p>
      </div>
    );
  }

  if (error || !result) {
    return (
      <div className="max-w-xl mx-auto my-12">
        <Card className="p-8 text-center space-y-4">
          <div className="w-12 h-12 bg-rose-50 text-rose-600 rounded-2xl flex items-center justify-center mx-auto">
            <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
            </svg>
          </div>
          <h2 className="text-lg font-black text-slate-900">Result Not Found</h2>
          <p className="text-xs text-slate-500">{error || 'Unable to retrieve test score.'}</p>
          <Button
            variant="primary"
            size="md"
            onClick={() => navigate('/assessments')}
          >
            Back to Assessments
          </Button>
        </Card>
      </div>
    );
  }

  const reviews = result.review || [];
  const filteredReviews = reviews.filter((q) => {
    if (filterMode === 'CORRECT') return q.is_correct;
    if (filterMode === 'INCORRECT') return !q.is_correct && q.selected_option !== null;
    if (filterMode === 'UNANSWERED') return q.selected_option === null;
    return true;
  });

  const topicEntries = Object.entries(result.topic_breakdown || {});

  return (
    <div className="space-y-8 max-w-7xl mx-auto pb-12">
      {/* Top Banner & Score Card */}
      <div
        className={`rounded-3xl p-6 sm:p-8 text-white relative overflow-hidden shadow-lg ${
          result.is_passed
            ? 'bg-gradient-to-br from-emerald-600 via-emerald-700 to-teal-800'
            : 'bg-gradient-to-br from-rose-600 via-rose-700 to-slate-800'
        }`}
      >
        <div className="relative z-10 flex flex-col md:flex-row md:items-center md:justify-between gap-6">
          <div className="space-y-3">
            <div className="flex items-center space-x-2">
              <span
                className={`px-3 py-1 rounded-full text-[10px] font-black tracking-wider uppercase ${
                  result.is_passed ? 'bg-emerald-950/40 text-emerald-100' : 'bg-rose-950/40 text-rose-100'
                }`}
              >
                {result.is_passed ? '✓ Assessment Passed' : '✕ Needs Practice'}
              </span>
              <span className="text-xs opacity-75">
                Completed on {new Date(result.created_at).toLocaleDateString()}
              </span>
            </div>

            <h1 className="text-2xl sm:text-3xl font-black tracking-tight">{result.assessment_title}</h1>
            <p className="text-xs sm:text-sm font-medium text-white/80 max-w-xl leading-relaxed">
              {result.is_passed
                ? 'Great job! You demonstrated solid mastery of the topics covered in this practice test.'
                : 'Review the question explanations below to strengthen your fundamentals before your placement interviews.'}
            </p>
          </div>

          {/* Big Score Display */}
          <div className="flex items-center space-x-4 bg-white/10 backdrop-blur-md rounded-2xl p-4 sm:p-6 border border-white/20">
            <div className="text-center">
              <div className="text-3xl sm:text-4xl font-black">{result.percentage}%</div>
              <div className="text-[11px] font-bold text-white/80 uppercase mt-0.5">Final Score</div>
            </div>
            <div className="w-px h-12 bg-white/20" />
            <div className="text-left space-y-0.5 text-xs font-semibold text-white/90">
              <div>
                Marks: <span className="font-bold">{result.score_obtained} / {result.total_score}</span>
              </div>
              <div>
                Time: <span className="font-bold">{formatDuration(result.time_taken_seconds)}</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Metric Cards */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
        <Card className="p-5 text-center">
          <div className="text-[10px] font-bold text-slate-400 uppercase">Total Questions</div>
          <div className="text-2xl font-black text-slate-900 mt-1">{result.total_questions}</div>
        </Card>

        <Card className="p-5 text-center bg-emerald-50/30 border-emerald-200/80">
          <div className="text-[10px] font-bold text-emerald-600 uppercase">Correct Answers</div>
          <div className="text-2xl font-black text-emerald-700 mt-1">{result.correct_answers}</div>
        </Card>

        <Card className="p-5 text-center bg-rose-50/30 border-rose-200/80">
          <div className="text-[10px] font-bold text-rose-600 uppercase">Incorrect Answers</div>
          <div className="text-2xl font-black text-rose-700 mt-1">{result.incorrect_answers}</div>
        </Card>

        <Card className="p-5 text-center bg-slate-50/50">
          <div className="text-[10px] font-bold text-slate-500 uppercase">Unanswered</div>
          <div className="text-2xl font-black text-slate-700 mt-1">{result.unanswered}</div>
        </Card>
      </div>

      {/* Topic-Wise Breakdown */}
      {topicEntries.length > 0 && (
        <Card className="p-6 space-y-4">
          <h2 className="text-base font-extrabold text-slate-900">Topic-Wise Performance Breakdown</h2>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {topicEntries.map(([topicName, perf]) => {
              const topicPct =
                perf.total_score > 0 ? Math.round((perf.score_obtained / perf.total_score) * 100) : 0;
              const isStrong = topicPct >= 75;
              const isModerate = topicPct >= 50 && topicPct < 75;

              return (
                <div
                  key={topicName}
                  className="p-4 rounded-2xl bg-slate-50 border border-slate-200/80 space-y-3"
                >
                  <div className="flex items-start justify-between gap-2">
                    <h3 className="text-xs font-extrabold text-slate-900 truncate">{topicName}</h3>
                    <span
                      className={`px-2 py-0.5 rounded-md text-[10px] font-black uppercase ${
                        isStrong
                          ? 'bg-emerald-100 text-emerald-800'
                          : isModerate
                          ? 'bg-amber-100 text-amber-800'
                          : 'bg-rose-100 text-rose-800'
                      }`}
                    >
                      {topicPct}%
                    </span>
                  </div>

                  <div className="w-full bg-slate-200 h-2 rounded-full overflow-hidden">
                    <div
                      className={`h-full transition-all duration-500 ${
                        isStrong ? 'bg-emerald-500' : isModerate ? 'bg-amber-500' : 'bg-rose-500'
                      }`}
                      style={{ width: `${topicPct}%` }}
                    />
                  </div>

                  <div className="flex items-center justify-between text-[11px] font-semibold text-slate-500">
                    <span>
                      {perf.correct_answers} / {perf.total_questions} Correct
                    </span>
                    <span>
                      {perf.score_obtained} / {perf.total_score} Marks
                    </span>
                  </div>
                </div>
              );
            })}
          </div>
        </Card>
      )}

      {/* Question-By-Question Answer Review */}
      <div className="space-y-4">
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
          <div>
            <h2 className="text-lg font-black text-slate-900">Question-by-Question Review</h2>
            <p className="text-xs text-slate-500 font-medium">
              Inspect your responses, correct answers, and full step-by-step explanations.
            </p>
          </div>

          {/* Filter Pills */}
          <div className="flex flex-wrap items-center gap-1.5 bg-slate-100 p-1 rounded-xl">
            {(['ALL', 'CORRECT', 'INCORRECT', 'UNANSWERED'] as const).map((mode) => (
              <button
                key={mode}
                type="button"
                onClick={() => setFilterMode(mode)}
                className={`px-3 py-1 rounded-lg text-xs font-bold transition ${
                  filterMode === mode
                    ? 'bg-white text-slate-900 shadow-sm'
                    : 'text-slate-600 hover:text-slate-900'
                }`}
              >
                {mode.charAt(0) + mode.slice(1).toLowerCase()}
              </button>
            ))}
          </div>
        </div>

        {filteredReviews.length === 0 ? (
          <Card className="p-8 text-center text-xs text-slate-400 font-semibold">
            No questions matching the selected filter.
          </Card>
        ) : (
          <div className="space-y-4">
            {filteredReviews.map((q, idx) => {
              const statusBadge = q.is_correct
                ? { text: 'Correct (+Marks)', bg: 'bg-emerald-50 text-emerald-700 border-emerald-200' }
                : q.selected_option !== null
                ? { text: 'Incorrect', bg: 'bg-rose-50 text-rose-700 border-rose-200' }
                : { text: 'Unanswered', bg: 'bg-slate-100 text-slate-600 border-slate-200' };

              return (
                <Card
                  key={q.id}
                  className="p-5 sm:p-6 space-y-4"
                >
                  {/* Question Header */}
                  <div className="flex items-start justify-between gap-3">
                    <div className="flex items-center space-x-3">
                      <span className="w-7 h-7 rounded-xl bg-slate-100 text-slate-800 flex items-center justify-center font-black text-xs border border-slate-200/60">
                        #{q.sequence_order || idx + 1}
                      </span>
                      <h3 className="text-sm font-bold text-slate-900 leading-snug">
                        {q.question_text}
                      </h3>
                    </div>

                    <div className="flex items-center space-x-2">
                      <span className={`px-2.5 py-1 rounded-lg text-[10px] font-extrabold border ${statusBadge.bg}`}>
                        {statusBadge.text}
                      </span>
                      {q.topic_name && (
                        <span className="px-2 py-1 rounded-lg bg-indigo-50 text-indigo-700 text-[10px] font-extrabold border border-indigo-200/60">
                          {q.topic_name}
                        </span>
                      )}
                    </div>
                  </div>

                  {/* Options List */}
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-2.5 pt-2">
                    {q.options.map((opt) => {
                      const isCorrect = opt.key === q.correct_option;
                      const isSelected = opt.key === q.selected_option;

                      let style = 'bg-slate-50 border-slate-200 text-slate-700';
                      if (isCorrect) {
                        style = 'bg-emerald-50 border-emerald-300 text-emerald-950 font-bold';
                      } else if (isSelected && !isCorrect) {
                        style = 'bg-rose-50 border-rose-300 text-rose-950 font-bold';
                      }

                      return (
                        <div
                          key={opt.key}
                          className={`p-3 rounded-xl border text-xs flex items-center space-x-3 transition ${style}`}
                        >
                          <span
                            className={`w-6 h-6 rounded-lg flex items-center justify-center font-black text-xs ${
                              isCorrect
                                ? 'bg-emerald-600 text-white'
                                : isSelected
                                ? 'bg-rose-600 text-white'
                                : 'bg-slate-200 text-slate-600'
                            }`}
                          >
                            {opt.key}
                          </span>

                          <span className="flex-1 leading-snug">{opt.text}</span>

                          {isCorrect && (
                            <span className="text-[10px] uppercase font-black tracking-wider text-emerald-700 bg-emerald-100 px-2 py-0.5 rounded-md">
                              Correct Answer
                            </span>
                          )}

                          {isSelected && !isCorrect && (
                            <span className="text-[10px] uppercase font-black tracking-wider text-rose-700 bg-rose-100 px-2 py-0.5 rounded-md">
                              Your Choice
                            </span>
                          )}
                        </div>
                      );
                    })}
                  </div>

                  {/* Explanation Card */}
                  {q.explanation && (
                    <div className="p-3.5 bg-indigo-50/60 rounded-xl border border-indigo-100 text-xs text-indigo-950 font-medium leading-relaxed">
                      <span className="font-black text-indigo-700">Explanation: </span>
                      {q.explanation}
                    </div>
                  )}
                </Card>
              );
            })}
          </div>
        )}
      </div>

      {/* Bottom Actions */}
      <div className="flex flex-wrap items-center justify-between gap-4 pt-4 border-t border-slate-200/80">
        <Button
          variant="outline"
          size="md"
          onClick={() => navigate('/assessments')}
        >
          ← Back to Practice Assessments
        </Button>

        <Button
          variant="primary"
          size="md"
          onClick={() => navigate('/preparation')}
        >
          Go to Preparation Hub →
        </Button>
      </div>
    </div>
  );
};

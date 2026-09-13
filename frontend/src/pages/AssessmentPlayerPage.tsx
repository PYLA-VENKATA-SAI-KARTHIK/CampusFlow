import React, { useEffect, useState, useRef, useCallback } from 'react';
import { useParams, useNavigate, useLocation } from 'react-router-dom';
import { assessmentService } from '../services/assessmentService';
import type { StartAttemptResponse, QuestionAnswerItem } from '../types/assessment';

export const AssessmentPlayerPage: React.FC = () => {
  const { attemptId } = useParams<{ attemptId: string }>();
  const navigate = useNavigate();
  const location = useLocation();

  const [attemptData, setAttemptData] = useState<StartAttemptResponse | null>(() => {
    return (location.state as any)?.attemptData || null;
  });
  const [loading, setLoading] = useState(!attemptData);
  const [error, setError] = useState<string | null>(null);

  // Question navigation & answer state
  const [currentIdx, setCurrentIdx] = useState(0);
  const [answers, setAnswers] = useState<Record<string, string>>({});
  const [savingStatus, setSavingStatus] = useState<'idle' | 'saving' | 'saved' | 'error'>('idle');

  // Timer & Submission
  const [remainingSeconds, setRemainingSeconds] = useState<number>(0);
  const [showSubmitModal, setShowSubmitModal] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);

  // Save debouncing ref
  const saveTimeoutRef = useRef<any>(null);

  // 1. Initial Load / Resume Attempt
  useEffect(() => {
    if (!attemptId) return;

    const loadAttempt = async () => {
      try {
        setLoading(true);
        setError(null);
        let data = attemptData;
        if (!data) {
          data = await assessmentService.getActiveAttempt(attemptId);
          setAttemptData(data);
        }

        // Initialize answers from saved_responses
        if (data && data.saved_responses) {
          const initialAnswers: Record<string, string> = {};
          Object.entries(data.saved_responses).forEach(([qId, optKey]) => {
            if (optKey) initialAnswers[qId] = optKey;
          });
          setAnswers(initialAnswers);
        }

        // Calculate initial remaining seconds
        if (data) {
          const expTime = new Date(data.expires_at).getTime();
          const diff = Math.max(0, Math.floor((expTime - Date.now()) / 1000));
          setRemainingSeconds(diff);
        }
      } catch (err: any) {
        setError(err?.response?.data?.detail || 'Failed to load active assessment attempt.');
      } finally {
        setLoading(false);
      }
    };

    loadAttempt();
  }, [attemptId]);

  // 2. Countdown Timer
  useEffect(() => {
    if (!attemptData || remainingSeconds <= 0) return;

    const timer = setInterval(() => {
      setRemainingSeconds((prev) => {
        if (prev <= 1) {
          clearInterval(timer);
          handleAutoSubmit();
          return 0;
        }
        return prev - 1;
      });
    }, 1000);

    return () => clearInterval(timer);
  }, [attemptData, remainingSeconds]);

  // Format seconds to HH:MM:SS or MM:SS
  const formatTime = (secs: number) => {
    const hours = Math.floor(secs / 3600);
    const mins = Math.floor((secs % 3600) / 60);
    const seconds = secs % 60;
    if (hours > 0) {
      return `${String(hours).padStart(2, '0')}:${String(mins).padStart(2, '0')}:${String(
        seconds
      ).padStart(2, '0')}`;
    }
    return `${String(mins).padStart(2, '0')}:${String(seconds).padStart(2, '0')}`;
  };

  // 3. Autosave Helper
  const triggerAutosave = useCallback(
    (questionId: string, optionKey: string | null) => {
      if (!attemptId) return;

      if (saveTimeoutRef.current) {
        clearTimeout(saveTimeoutRef.current);
      }

      setSavingStatus('saving');
      saveTimeoutRef.current = setTimeout(async () => {
        try {
          const payload: QuestionAnswerItem[] = [
            {
              question_id: questionId,
              selected_option: optionKey,
            },
          ];
          await assessmentService.saveProgress(attemptId, payload);
          setSavingStatus('saved');
        } catch {
          setSavingStatus('error');
        }
      }, 300);
    },
    [attemptId]
  );

  // 4. Option Select Handler
  const handleSelectOption = (questionId: string, optionKey: string) => {
    setAnswers((prev) => {
      const next = { ...prev, [questionId]: optionKey };
      return next;
    });
    triggerAutosave(questionId, optionKey);
  };

  // 5. Clear Option Selection
  const handleClearSelection = (questionId: string) => {
    setAnswers((prev) => {
      const next = { ...prev };
      delete next[questionId];
      return next;
    });
    triggerAutosave(questionId, null);
  };

  // 6. Submit Attempt (Manual or Auto on expiry)
  const handleFinalSubmit = async () => {
    if (!attemptId || isSubmitting) return;
    setIsSubmitting(true);
    try {
      const formattedResponses: QuestionAnswerItem[] = (attemptData?.questions || []).map((q) => ({
        question_id: q.id,
        selected_option: answers[q.id] || null,
      }));

      await assessmentService.submitAttempt(attemptId, formattedResponses);
      setShowSubmitModal(false);
      navigate(`/assessments/results/${attemptId}`);
    } catch (err: any) {
      alert(err?.response?.data?.detail || 'Failed to submit assessment. Please try again.');
      setIsSubmitting(false);
    }
  };

  const handleAutoSubmit = async () => {
    if (!attemptId || isSubmitting) return;
    setIsSubmitting(true);
    try {
      const formattedResponses: QuestionAnswerItem[] = (attemptData?.questions || []).map((q) => ({
        question_id: q.id,
        selected_option: answers[q.id] || null,
      }));
      await assessmentService.submitAttempt(attemptId, formattedResponses);
      navigate(`/assessments/results/${attemptId}`);
    } catch {
      navigate(`/assessments/results/${attemptId}`);
    }
  };

  if (loading) {
    return (
      <div className="min-h-[60vh] flex flex-col items-center justify-center space-y-4">
        <div className="w-12 h-12 rounded-full border-4 border-indigo-600 border-t-transparent animate-spin" />
        <p className="text-sm font-bold text-slate-600">Initializing practice test environment...</p>
      </div>
    );
  }

  if (error || !attemptData) {
    return (
      <div className="max-w-xl mx-auto my-12 bg-white rounded-3xl border border-slate-200 p-8 text-center space-y-4 shadow-sm">
        <div className="w-12 h-12 bg-rose-50 text-rose-600 rounded-2xl flex items-center justify-center mx-auto">
          <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
          </svg>
        </div>
        <h2 className="text-lg font-black text-slate-900">Unable to load test</h2>
        <p className="text-xs text-slate-500">{error || 'Attempt not found or has expired.'}</p>
        <button
          onClick={() => navigate('/assessments')}
          className="px-5 py-2.5 bg-slate-900 hover:bg-slate-800 text-white rounded-xl text-xs font-bold transition"
        >
          Return to Assessments
        </button>
      </div>
    );
  }

  const questions = attemptData.questions || [];
  const currentQ = questions[currentIdx];
  const totalQuestions = questions.length;
  const answeredCount = Object.keys(answers).length;
  const unansweredCount = Math.max(0, totalQuestions - answeredCount);

  // Timer style indicator
  const isUrgent = remainingSeconds < 60;
  const isWarning = remainingSeconds < 300 && !isUrgent;

  return (
    <div className="space-y-6 select-none">
      {/* TOP TEST HEADER BAR */}
      <div className="bg-white rounded-2xl border border-slate-200/80 p-4 shadow-sm flex flex-col md:flex-row md:items-center md:justify-between gap-4">
        <div>
          <div className="flex items-center space-x-2">
            <span className="px-2.5 py-0.5 rounded-full bg-indigo-50 text-indigo-700 text-[10px] font-black uppercase tracking-wider border border-indigo-200">
              Live Mock Test
            </span>
            <span className="text-xs text-slate-400 font-semibold">&bull;</span>
            <span className="text-xs text-slate-500 font-medium">{attemptData.title}</span>
          </div>
          <h1 className="text-lg font-black text-slate-900 mt-1">
            Question {currentIdx + 1} of {totalQuestions}
          </h1>
        </div>

        <div className="flex items-center space-x-4">
          {/* Autosave Status Indicator */}
          <div className="hidden sm:flex items-center space-x-1.5 text-[11px] font-semibold text-slate-500">
            {savingStatus === 'saving' && (
              <>
                <span className="w-2 h-2 rounded-full bg-amber-400 animate-ping" />
                <span className="text-amber-600">Autosaving...</span>
              </>
            )}
            {savingStatus === 'saved' && (
              <>
                <span className="w-2 h-2 rounded-full bg-emerald-500" />
                <span className="text-emerald-600">Saved</span>
              </>
            )}
            {savingStatus === 'error' && (
              <>
                <span className="w-2 h-2 rounded-full bg-rose-500" />
                <span className="text-rose-600">Sync Error</span>
              </>
            )}
            {savingStatus === 'idle' && (
              <>
                <span className="w-2 h-2 rounded-full bg-slate-300" />
                <span>Autosaved</span>
              </>
            )}
          </div>

          {/* Countdown Timer */}
          <div
            className={`px-4 py-2 rounded-xl flex items-center space-x-2 font-black text-sm tracking-wider transition ${
              isUrgent
                ? 'bg-rose-600 text-white animate-pulse shadow-md shadow-rose-600/30'
                : isWarning
                ? 'bg-amber-100 text-amber-900 border border-amber-300'
                : 'bg-slate-900 text-white'
            }`}
          >
            <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2.5" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            <span>{formatTime(remainingSeconds)}</span>
          </div>

          {/* Submit Test Button */}
          <button
            onClick={() => setShowSubmitModal(true)}
            className="px-4 py-2 rounded-xl bg-emerald-600 hover:bg-emerald-700 text-white text-xs font-black shadow-md shadow-emerald-600/20 transition transform active:scale-95"
          >
            Submit Test
          </button>
        </div>
      </div>

      {/* MAIN TEST AREA & PALETTE GRID */}
      <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
        {/* CENTER PANE: QUESTION & OPTIONS */}
        <div className="lg:col-span-3 space-y-6">
          {currentQ && (
            <div className="bg-white rounded-3xl border border-slate-200/80 p-6 sm:p-8 shadow-sm space-y-6">
              {/* Question Header */}
              <div className="flex items-center justify-between border-b border-slate-100 pb-4">
                <span className="px-3 py-1 rounded-xl bg-slate-100 text-slate-800 text-xs font-extrabold">
                  Question #{currentIdx + 1}
                </span>

                <div className="flex items-center space-x-2">
                  <span className="px-2.5 py-0.5 rounded-lg bg-indigo-50 text-indigo-700 text-xs font-extrabold">
                    {currentQ.marks} Mark{Number(currentQ.marks) > 1 ? 's' : ''}
                  </span>
                </div>
              </div>

              {/* Question Text */}
              <div className="text-base sm:text-lg font-bold text-slate-900 leading-relaxed">
                {currentQ.question_text}
              </div>

              {/* Options Radio List */}
              <div className="space-y-3 pt-2">
                {currentQ.options.map((opt) => {
                  const isSelected = answers[currentQ.id] === opt.key;
                  return (
                    <div
                      key={opt.key}
                      onClick={() => handleSelectOption(currentQ.id, opt.key)}
                      className={`p-4 rounded-2xl border-2 cursor-pointer transition flex items-center space-x-4 ${
                        isSelected
                          ? 'border-indigo-600 bg-indigo-50/60 shadow-sm'
                          : 'border-slate-200 hover:border-slate-300 hover:bg-slate-50/50'
                      }`}
                    >
                      <div
                        className={`w-7 h-7 rounded-xl flex items-center justify-center font-black text-xs transition ${
                          isSelected
                            ? 'bg-indigo-600 text-white shadow-sm'
                            : 'bg-slate-100 text-slate-700'
                        }`}
                      >
                        {opt.key}
                      </div>

                      <div className="flex-1 text-sm font-semibold text-slate-800 leading-snug">
                        {opt.text}
                      </div>

                      <div className="w-5 h-5 flex items-center justify-center">
                        {isSelected ? (
                          <div className="w-4 h-4 rounded-full bg-indigo-600 flex items-center justify-center text-white text-[10px]">
                            ✓
                          </div>
                        ) : (
                          <div className="w-4 h-4 rounded-full border-2 border-slate-300" />
                        )}
                      </div>
                    </div>
                  );
                })}
              </div>

              {/* Action Buttons: Clear Choice & Navigators */}
              <div className="pt-6 border-t border-slate-100 flex flex-wrap items-center justify-between gap-3">
                <div>
                  {answers[currentQ.id] && (
                    <button
                      onClick={() => handleClearSelection(currentQ.id)}
                      className="text-xs font-bold text-rose-600 hover:text-rose-700 p-1"
                    >
                      Clear Choice
                    </button>
                  )}
                </div>

                <div className="flex items-center space-x-3">
                  <button
                    disabled={currentIdx === 0}
                    onClick={() => setCurrentIdx((prev) => Math.max(0, prev - 1))}
                    className="px-4 py-2.5 rounded-xl bg-slate-100 hover:bg-slate-200 text-slate-700 text-xs font-bold transition disabled:opacity-40 disabled:cursor-not-allowed"
                  >
                    ← Previous
                  </button>

                  {currentIdx < totalQuestions - 1 ? (
                    <button
                      onClick={() => setCurrentIdx((prev) => Math.min(totalQuestions - 1, prev + 1))}
                      className="px-6 py-2.5 rounded-xl bg-indigo-600 hover:bg-indigo-700 text-white text-xs font-bold shadow-md shadow-indigo-600/20 transition"
                    >
                      Next →
                    </button>
                  ) : (
                    <button
                      onClick={() => setShowSubmitModal(true)}
                      className="px-6 py-2.5 rounded-xl bg-emerald-600 hover:bg-emerald-700 text-white text-xs font-bold shadow-md shadow-emerald-600/20 transition"
                    >
                      Review & Submit
                    </button>
                  )}
                </div>
              </div>
            </div>
          )}
        </div>

        {/* RIGHT PALETTE: QUESTION JUMP GRID */}
        <div className="lg:col-span-1 space-y-4">
          <div className="bg-white rounded-3xl border border-slate-200/80 p-5 shadow-sm space-y-4">
            <h3 className="text-xs font-extrabold text-slate-900 uppercase tracking-wider">
              Question Palette
            </h3>

            {/* Status Legend */}
            <div className="grid grid-cols-2 gap-2 text-[10px] font-bold">
              <div className="p-2 rounded-xl bg-emerald-50 border border-emerald-100 text-emerald-800 flex items-center justify-between">
                <span>Answered</span>
                <span className="font-black text-emerald-700">{answeredCount}</span>
              </div>
              <div className="p-2 rounded-xl bg-slate-50 border border-slate-200 text-slate-700 flex items-center justify-between">
                <span>Unanswered</span>
                <span className="font-black text-slate-600">{unansweredCount}</span>
              </div>
            </div>

            {/* Question Jump Circles */}
            <div className="grid grid-cols-5 gap-2 pt-2">
              {questions.map((q, idx) => {
                const isAnswered = Boolean(answers[q.id]);
                const isCurrent = idx === currentIdx;
                return (
                  <button
                    key={q.id}
                    onClick={() => setCurrentIdx(idx)}
                    className={`h-9 rounded-xl font-black text-xs transition flex items-center justify-center relative ${
                      isCurrent
                        ? 'ring-2 ring-indigo-600 ring-offset-2 bg-indigo-600 text-white'
                        : isAnswered
                        ? 'bg-emerald-600 text-white shadow-sm'
                        : 'bg-slate-100 hover:bg-slate-200 text-slate-700'
                    }`}
                  >
                    {idx + 1}
                  </button>
                );
              })}
            </div>

            <div className="pt-3 border-t border-slate-100">
              <button
                onClick={() => setShowSubmitModal(true)}
                className="w-full py-2.5 rounded-xl bg-slate-900 hover:bg-slate-800 text-white text-xs font-bold transition text-center shadow-sm"
              >
                Submit Test ({answeredCount}/{totalQuestions})
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* SUBMISSION CONFIRMATION MODAL */}
      {showSubmitModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/60 backdrop-blur-sm animate-fade-in">
          <div className="bg-white rounded-3xl border border-slate-200 shadow-2xl max-w-md w-full p-6 space-y-5">
            <div className="text-center space-y-2">
              <div className="w-12 h-12 bg-emerald-50 text-emerald-600 rounded-2xl flex items-center justify-center mx-auto shadow-inner">
                <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
              </div>
              <h2 className="text-lg font-black text-slate-900">Submit Practice Assessment?</h2>
              <p className="text-xs text-slate-500 font-medium">
                Are you sure you want to finalize and submit your test? Your score will be evaluated immediately.
              </p>
            </div>

            {/* Test Summary Breakdown */}
            <div className="grid grid-cols-2 gap-3 text-center">
              <div className="bg-emerald-50 p-3 rounded-2xl border border-emerald-100">
                <div className="text-[10px] text-emerald-600 font-bold uppercase">Answered</div>
                <div className="text-base font-black text-emerald-800">{answeredCount}</div>
              </div>

              <div className="bg-amber-50 p-3 rounded-2xl border border-amber-100">
                <div className="text-[10px] text-amber-600 font-bold uppercase">Unanswered</div>
                <div className="text-base font-black text-amber-800">{unansweredCount}</div>
              </div>
            </div>

            <div className="p-3 rounded-xl bg-slate-50 border border-slate-200 text-slate-600 text-xs text-center font-medium">
              Time Remaining: <span className="font-black text-slate-900">{formatTime(remainingSeconds)}</span>
            </div>

            <div className="pt-2 flex items-center space-x-3">
              <button
                type="button"
                disabled={isSubmitting}
                onClick={() => setShowSubmitModal(false)}
                className="flex-1 py-2.5 rounded-xl bg-slate-100 hover:bg-slate-200 text-slate-700 font-bold text-xs transition"
              >
                Back to Test
              </button>
              <button
                type="button"
                disabled={isSubmitting}
                onClick={handleFinalSubmit}
                className="flex-1 py-2.5 rounded-xl bg-emerald-600 hover:bg-emerald-700 text-white font-black text-xs shadow-md shadow-emerald-600/20 transition disabled:opacity-50"
              >
                {isSubmitting ? 'Evaluating...' : 'Yes, Submit Test'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

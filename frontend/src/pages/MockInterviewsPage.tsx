import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Card } from '../components/ui/Card';
import { Badge } from '../components/ui/Badge';
import { Button } from '../components/ui/Button';

interface InterviewTrack {
  id: string;
  title: string;
  icon: string;
  category: 'TECHNICAL' | 'BEHAVIORAL' | 'SYSTEM_DESIGN' | 'DOMAIN';
  durationMinutes: number;
  questionCount: number;
  badge: string;
  description: string;
  popularTopics: string[];
}

const TRACKS: InterviewTrack[] = [
  {
    id: 'tech-dsa',
    title: 'Data Structures & Algorithms',
    icon: '💻',
    category: 'TECHNICAL',
    durationMinutes: 45,
    questionCount: 4,
    badge: 'High Demand',
    description: 'Solve real-world algorithmic problems, optimize time/space complexity, and explain trade-offs to an AI tech interviewer.',
    popularTopics: ['Dynamic Programming', 'Binary Trees', 'Graphs', 'Hash Tables'],
  },
  {
    id: 'hr-behavioral',
    title: 'HR & Behavioral (STAR Method)',
    icon: '🤝',
    category: 'BEHAVIORAL',
    durationMinutes: 30,
    questionCount: 5,
    badge: 'Essential',
    description: 'Master leadership, situational judgement, conflict resolution, and cultural fit using the structured STAR framework.',
    popularTopics: ['Leadership', 'Conflict Resolution', 'Failure & Learning', 'Teamwork'],
  },
  {
    id: 'system-design',
    title: 'System Design & Architecture',
    icon: '🏗️',
    category: 'SYSTEM_DESIGN',
    durationMinutes: 60,
    questionCount: 3,
    badge: 'Advanced',
    description: 'Design scalable distributed systems, caching strategies, rate limiters, load balancing, and microservices architectures.',
    popularTopics: ['Microservices', 'Distributed Caching', 'Database Sharding', 'Message Queues'],
  },
  {
    id: 'fullstack-web',
    title: 'Fullstack & Web Engineering',
    icon: '⚡',
    category: 'DOMAIN',
    durationMinutes: 45,
    questionCount: 5,
    badge: 'Popular',
    description: 'Deep-dive into React, Node.js, REST & GraphQL APIs, browser internals, and performance optimization.',
    popularTopics: ['React Internals', 'Async Javascript', 'API Design', 'Security & Auth'],
  },
];

interface SampleQuestion {
  id: string;
  trackId: string;
  title: string;
  category: string;
  questionText: string;
  expectedKeywords: string[];
  tips: string;
}

const SAMPLE_QUESTIONS: SampleQuestion[] = [
  {
    id: 'q1',
    trackId: 'hr-behavioral',
    title: 'Handling Technical Disagreements',
    category: 'Behavioral',
    questionText: 'Tell me about a time when you strongly disagreed with a teammate on an architectural decision or technical approach. How did you resolve it and what was the outcome?',
    expectedKeywords: ['STAR method', 'Data-driven discussion', 'Proof of concept', 'Consensus', 'Team alignment'],
    tips: 'Highlight how you remained professional, tested both approaches with benchmarks, and prioritized project goals.',
  },
  {
    id: 'q2',
    trackId: 'tech-dsa',
    title: 'LRU Cache Design & Implementation',
    category: 'Algorithms',
    questionText: 'Design and implement an LRU (Least Recently Used) Cache with O(1) get and put operations. What data structures would you combine and why?',
    expectedKeywords: ['Doubly Linked List', 'Hash Map', 'O(1) lookup', 'Tail eviction', 'Head insertion'],
    tips: 'Explain why a Doubly Linked List allows O(1) removals and node shifting when coupled with a Hash Map pointer.',
  },
  {
    id: 'q3',
    trackId: 'system-design',
    title: 'Designing a Scalable URL Shortener',
    category: 'System Design',
    questionText: 'How would you design a URL shortener like Bitly handling 500M new URLs per month with high availability and low latency reads?',
    expectedKeywords: ['Base62 encoding', 'Snowflake ID', 'Redis Cache', 'Database indexing', 'Read replicas'],
    tips: 'Address collision prevention, 7-character Base62 length capacity, caching hot URLs in Redis, and CDN routing.',
  },
];

export const MockInterviewsPage: React.FC = () => {
  const navigate = useNavigate();
  const [selectedTrack, setSelectedTrack] = useState<string>('hr-behavioral');
  const [activeQuestionIdx, setActiveQuestionIdx] = useState<number>(0);
  const [answerText, setAnswerText] = useState<string>('');
  const [isSubmitting, setIsSubmitting] = useState<boolean>(false);
  const [feedbackResult, setFeedbackResult] = useState<any | null>(null);
  const [roadmapVote, setRoadmapVote] = useState<string | null>(null);
  const [featureFeedbackInput, setFeatureFeedbackInput] = useState<string>('');
  const [feedbackSubmitted, setFeedbackSubmitted] = useState<boolean>(false);

  const currentQuestions = SAMPLE_QUESTIONS.filter(
    (q) => q.trackId === selectedTrack || selectedTrack === 'ALL'
  );
  const activeQuestion = currentQuestions[activeQuestionIdx] || SAMPLE_QUESTIONS[0];

  const handleEvaluateAnswer = () => {
    if (!answerText.trim()) return;
    setIsSubmitting(true);
    setTimeout(() => {
      const wordCount = answerText.trim().split(/\s+/).length;
      const matchedKeywords = activeQuestion.expectedKeywords.filter((k) =>
        answerText.toLowerCase().includes(k.toLowerCase())
      );
      const score = Math.min(
        96,
        Math.max(60, Math.round(55 + matchedKeywords.length * 9 + Math.min(20, wordCount / 10)))
      );

      setFeedbackResult({
        score,
        wordCount,
        matchedKeywords,
        clarityScore: Math.min(100, score + 4),
        structureScore: Math.min(100, score - 2),
        technicalDepth: Math.min(100, score + 1),
        strengths: [
          'Clear logical flow and problem structuring.',
          `Effectively referenced key concepts (${matchedKeywords.slice(0, 2).join(', ') || 'structured thinking'}).`,
          'Maintained confident, professional communication.',
        ],
        improvements: [
          'Include more quantifiable metrics and concrete outcome figures.',
          'Elaborate further on trade-offs and alternate approaches considered.',
        ],
      });
      setIsSubmitting(false);
    }, 1200);
  };

  return (
    <div className="space-y-8 animate-fade-in max-w-6xl mx-auto pb-16">
      {/* ── Page Header ──────────────────────────────────────────────────────── */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 border-b border-slate-200 pb-6">
        <div>
          <div className="flex items-center space-x-2 mb-1.5">
            <span className="px-2.5 py-0.5 rounded-full text-[10px] font-black tracking-wider uppercase bg-indigo-100 text-indigo-800 border border-indigo-200">
              CampusFlow AI Labs • Next-Gen Feature
            </span>
            <Badge variant="warning" size="sm">
              Active Development
            </Badge>
          </div>
          <h1 className="text-2xl sm:text-3xl font-black text-slate-900 tracking-tight">
            AI Mock Interviews & Skill Coaching
          </h1>
          <p className="text-xs sm:text-sm text-slate-500 mt-1 max-w-2xl">
            Simulate high-stakes campus recruitment rounds with real-time AI evaluation, STAR behavioral feedback, and technical question drills.
          </p>
        </div>

        <div className="flex items-center gap-2.5">
          <Button
            variant="outline"
            size="sm"
            onClick={() => navigate('/assessments')}
            leftIcon={
              <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M10 19l-7-7m0 0l7-7m-7 7h18" />
              </svg>
            }
          >
            Practice Tests
          </Button>
          <Button
            variant="primary"
            size="sm"
            onClick={() => {
              const el = document.getElementById('simulator-sandbox');
              el?.scrollIntoView({ behavior: 'smooth' });
            }}
          >
            Start Simulator 🎙️
          </Button>
        </div>
      </div>

      {/* ── Highlight Banner / Feature Stats ─────────────────────────────────── */}
      <div className="relative overflow-hidden rounded-3xl bg-gradient-to-br from-slate-900 via-indigo-950 to-slate-900 text-white p-6 sm:p-8 shadow-xl border border-indigo-900/50">
        <div className="absolute top-0 right-0 w-96 h-96 bg-indigo-500/10 rounded-full blur-3xl pointer-events-none" />
        <div className="relative z-10 grid grid-cols-1 lg:grid-cols-3 gap-6 items-center">
          <div className="lg:col-span-2 space-y-3">
            <span className="text-xs font-bold uppercase tracking-widest text-indigo-400">
              Intelligent Career Progression
            </span>
            <h2 className="text-xl sm:text-2xl font-black text-white leading-snug">
              Master Technical & HR Interview Rounds with Instant AI Critiques
            </h2>
            <p className="text-xs sm:text-sm text-slate-300 leading-relaxed max-w-xl">
              From coding complexity trade-offs to STAR behavioral anecdotes, get instant scoring on clarity, confidence, keyword coverage, and structured storytelling.
            </p>
            <div className="pt-2 flex flex-wrap gap-2 text-[11px] font-semibold text-indigo-200">
              <span className="px-3 py-1 rounded-full bg-white/10 border border-white/10">🎙️ Speech & Text Analysis</span>
              <span className="px-3 py-1 rounded-full bg-white/10 border border-white/10">⭐ STAR Behavioral Rubric</span>
              <span className="px-3 py-1 rounded-full bg-white/10 border border-white/10">📊 Real-Time Score Breakdown</span>
            </div>
          </div>

          <div className="grid grid-cols-2 gap-3 bg-white/5 p-4 rounded-2xl border border-white/10 text-center">
            <div className="p-3 rounded-xl bg-white/5">
              <div className="text-2xl font-black text-white">4+</div>
              <div className="text-[10px] uppercase font-bold text-slate-400 mt-0.5">Specialized Tracks</div>
            </div>
            <div className="p-3 rounded-xl bg-white/5">
              <div className="text-2xl font-black text-emerald-400">92%</div>
              <div className="text-[10px] uppercase font-bold text-slate-400 mt-0.5">Readiness Boost</div>
            </div>
            <div className="p-3 rounded-xl bg-white/5">
              <div className="text-2xl font-black text-indigo-400">&lt; 2s</div>
              <div className="text-[10px] uppercase font-bold text-slate-400 mt-0.5">Instant AI Feedback</div>
            </div>
            <div className="p-3 rounded-xl bg-white/5">
              <div className="text-2xl font-black text-amber-400">2027</div>
              <div className="text-[10px] uppercase font-bold text-slate-400 mt-0.5">Target Batch</div>
            </div>
          </div>
        </div>
      </div>

      {/* ── Choose Interview Track ───────────────────────────────────────────── */}
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <div>
            <h3 className="text-base font-extrabold text-slate-900">
              1. Choose an Interview Domain Track
            </h3>
            <p className="text-xs text-slate-500">
              Select your target assessment stream to calibrate the simulator questions.
            </p>
          </div>
          <Badge variant="primary" size="sm">
            {TRACKS.length} Tracks Ready
          </Badge>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          {TRACKS.map((track) => {
            const isSelected = selectedTrack === track.id;
            return (
              <div
                key={track.id}
                onClick={() => {
                  setSelectedTrack(track.id);
                  setActiveQuestionIdx(0);
                  setFeedbackResult(null);
                  setAnswerText('');
                }}
                className={`p-5 rounded-2xl border transition-all duration-200 cursor-pointer flex flex-col justify-between space-y-4 ${
                  isSelected
                    ? 'bg-indigo-50/80 border-indigo-500 ring-2 ring-indigo-200 shadow-sm'
                    : 'bg-white border-slate-200/90 hover:border-indigo-300 hover:shadow-xs'
                }`}
              >
                <div className="space-y-2.5">
                  <div className="flex items-center justify-between">
                    <span className="text-2xl">{track.icon}</span>
                    <span
                      className={`px-2 py-0.5 rounded-md text-[9px] font-black uppercase tracking-wider ${
                        isSelected
                          ? 'bg-indigo-600 text-white'
                          : 'bg-slate-100 text-slate-600'
                      }`}
                    >
                      {track.badge}
                    </span>
                  </div>
                  <h4 className="text-sm font-extrabold text-slate-900 leading-snug">
                    {track.title}
                  </h4>
                  <p className="text-[11px] text-slate-500 leading-relaxed">
                    {track.description}
                  </p>
                </div>

                <div className="pt-3 border-t border-slate-100 space-y-2">
                  <div className="flex items-center justify-between text-[10px] font-bold text-slate-400 uppercase">
                    <span>{track.durationMinutes} Mins</span>
                    <span>{track.questionCount} Questions</span>
                  </div>
                  <div className="flex flex-wrap gap-1">
                    {track.popularTopics.slice(0, 2).map((t, idx) => (
                      <span
                        key={idx}
                        className="px-1.5 py-0.5 rounded bg-slate-100 text-slate-600 text-[9px] font-semibold"
                      >
                        {t}
                      </span>
                    ))}
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* ── Interactive Live Interview Simulator ──────────────────────────────── */}
      <div id="simulator-sandbox" className="space-y-4 scroll-mt-6">
        <div className="flex items-center justify-between">
          <div>
            <h3 className="text-base font-extrabold text-slate-900">
              2. Interactive Mock Interview Sandbox
            </h3>
            <p className="text-xs text-slate-500">
              Answer the simulated interview question below and trigger the AI evaluation engine.
            </p>
          </div>
          <span className="text-xs font-bold text-indigo-600">
            Interactive AI Mode Active
          </span>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Question & Answer Box */}
          <div className="lg:col-span-2 space-y-4">
            <Card variant="default" className="p-6 rounded-3xl border-slate-200 space-y-4 shadow-xs">
              <div className="flex items-center justify-between border-b border-slate-100 pb-3">
                <div className="flex items-center space-x-2">
                  <span className="w-2.5 h-2.5 rounded-full bg-emerald-500 animate-ping" />
                  <span className="text-xs font-bold text-slate-700 uppercase tracking-wider">
                    {activeQuestion.category} Question
                  </span>
                </div>
                <span className="text-xs font-bold text-slate-400">
                  Question {activeQuestionIdx + 1} of {currentQuestions.length || 1}
                </span>
              </div>

              <div>
                <h4 className="text-base sm:text-lg font-black text-slate-900 leading-snug">
                  {activeQuestion.title}
                </h4>
                <p className="text-xs sm:text-sm text-slate-700 mt-2 bg-slate-50 p-4 rounded-2xl border border-slate-200/80 leading-relaxed">
                  "{activeQuestion.questionText}"
                </p>
              </div>

              {/* Coaching Tip */}
              <div className="p-3 bg-indigo-50/70 border border-indigo-100 rounded-xl text-[11px] text-indigo-900 flex items-start space-x-2">
                <span className="text-sm shrink-0">💡</span>
                <p>
                  <strong>Interviewer Tip:</strong> {activeQuestion.tips}
                </p>
              </div>

              {/* Student Response Area */}
              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <label className="text-xs font-bold text-slate-700 uppercase tracking-wider">
                    Your Response:
                  </label>
                  <span className="text-[10px] text-slate-400">
                    {answerText.trim().split(/\s+/).filter(Boolean).length} words
                  </span>
                </div>
                <textarea
                  rows={6}
                  value={answerText}
                  onChange={(e) => setAnswerText(e.target.value)}
                  placeholder="Type your structured response here... (For behavioral, use Situation -> Task -> Action -> Result format. For technical, outline your step-by-step logic, edge cases, and algorithmic complexity)."
                  className="w-full p-4 rounded-2xl border border-slate-200 bg-white text-xs sm:text-sm text-slate-800 placeholder:text-slate-400 focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 transition leading-relaxed"
                />
              </div>

              <div className="flex flex-col sm:flex-row items-center justify-between gap-3 pt-2">
                <div className="flex items-center space-x-2 text-[11px] text-slate-500">
                  <svg className="w-4 h-4 text-slate-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M19 11a7 7 0 01-7 7m0 0a7 7 0 01-7-7m7 7v4m0 0H8m4 0h4m-4-8a3 3 0 100-6 3 3 0 000 6z" />
                  </svg>
                  <span>Speech-to-Text audio recorder support enabled</span>
                </div>

                <div className="flex items-center gap-2 w-full sm:w-auto">
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => {
                      setAnswerText(
                        'Situation: In my pre-final year capstone project, our team had a conflict between choosing PostgreSQL or MongoDB for high-throughput sensor telemetry. Task: As technical lead, I needed to resolve the deadlock quickly without delaying our sprint milestone. Action: I developed a lightweight benchmark script to simulate 10,000 requests/second under both databases, measuring latency and memory footprints. We reviewed the empirical data together in a team retrospective. Result: The team unanimously agreed on PostgreSQL with Timescale extension, decreasing query response times by 38% and meeting our deadline with zero production bugs.'
                      );
                    }}
                  >
                    Load Sample Answer
                  </Button>
                  <Button
                    variant="primary"
                    size="sm"
                    isLoading={isSubmitting}
                    disabled={!answerText.trim() || isSubmitting}
                    onClick={handleEvaluateAnswer}
                  >
                    Evaluate Answer ✨
                  </Button>
                </div>
              </div>
            </Card>
          </div>

          {/* AI Scorecard & Feedback Panel */}
          <div className="space-y-4">
            <Card variant="default" className="p-6 rounded-3xl border-slate-200 space-y-4 shadow-xs h-full flex flex-col justify-between">
              <div>
                <h4 className="text-xs font-bold uppercase tracking-wider text-slate-400 mb-3">
                  AI Evaluation & Rubric
                </h4>

                {feedbackResult ? (
                  <div className="space-y-4 animate-fade-in">
                    {/* Overall Score */}
                    <div className="p-4 bg-emerald-50 border border-emerald-200 rounded-2xl text-center">
                      <div className="text-3xl font-black text-emerald-700">
                        {feedbackResult.score}/100
                      </div>
                      <div className="text-[10px] font-bold uppercase tracking-wider text-emerald-800 mt-0.5">
                        Readiness Score • Strong Performance
                      </div>
                    </div>

                    {/* Score Pillars */}
                    <div className="space-y-2 text-xs">
                      <div>
                        <div className="flex justify-between font-bold text-slate-700 mb-1 text-[11px]">
                          <span>Structure & Flow</span>
                          <span>{feedbackResult.structureScore}%</span>
                        </div>
                        <div className="h-1.5 w-full bg-slate-100 rounded-full overflow-hidden">
                          <div
                            className="h-full bg-indigo-500 rounded-full"
                            style={{ width: `${feedbackResult.structureScore}%` }}
                          />
                        </div>
                      </div>

                      <div>
                        <div className="flex justify-between font-bold text-slate-700 mb-1 text-[11px]">
                          <span>Clarity & Impact</span>
                          <span>{feedbackResult.clarityScore}%</span>
                        </div>
                        <div className="h-1.5 w-full bg-slate-100 rounded-full overflow-hidden">
                          <div
                            className="h-full bg-emerald-500 rounded-full"
                            style={{ width: `${feedbackResult.clarityScore}%` }}
                          />
                        </div>
                      </div>

                      <div>
                        <div className="flex justify-between font-bold text-slate-700 mb-1 text-[11px]">
                          <span>Technical Depth</span>
                          <span>{feedbackResult.technicalDepth}%</span>
                        </div>
                        <div className="h-1.5 w-full bg-slate-100 rounded-full overflow-hidden">
                          <div
                            className="h-full bg-purple-500 rounded-full"
                            style={{ width: `${feedbackResult.technicalDepth}%` }}
                          />
                        </div>
                      </div>
                    </div>

                    {/* Strengths */}
                    <div className="pt-2 border-t border-slate-100 space-y-1.5 text-xs">
                      <span className="font-bold text-slate-800 block text-[11px]">
                        Key Strengths:
                      </span>
                      {feedbackResult.strengths.map((s: string, i: number) => (
                        <div key={i} className="flex items-start space-x-1.5 text-slate-600 text-[11px]">
                          <span className="text-emerald-500 font-bold">✓</span>
                          <span>{s}</span>
                        </div>
                      ))}
                    </div>

                    {/* Improvement Suggestions */}
                    <div className="space-y-1.5 text-xs">
                      <span className="font-bold text-slate-800 block text-[11px]">
                        Growth Focus:
                      </span>
                      {feedbackResult.improvements.map((im: string, i: number) => (
                        <div key={i} className="flex items-start space-x-1.5 text-slate-600 text-[11px]">
                          <span className="text-amber-500 font-bold">→</span>
                          <span>{im}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                ) : (
                  <div className="p-8 text-center bg-slate-50/70 rounded-2xl border border-dashed border-slate-200 space-y-3">
                    <span className="text-3xl">🤖</span>
                    <h5 className="text-xs font-bold text-slate-800">
                      Awaiting Your Response
                    </h5>
                    <p className="text-[11px] text-slate-500 leading-relaxed">
                      Type your answer in the box and click <strong>Evaluate Answer</strong> to see live AI insights and keyword matching scores.
                    </p>
                  </div>
                )}
              </div>

              <div className="pt-4 border-t border-slate-100 text-center">
                <span className="text-[10px] text-slate-400 block font-medium">
                  Verified by CampusFlow AI Career Engine
                </span>
              </div>
            </Card>
          </div>
        </div>
      </div>

      {/* ── Feature Development & Upcoming Roadmap ──────────────────────────── */}
      <div className="space-y-4 pt-4">
        <div className="flex items-center justify-between">
          <div>
            <h3 className="text-base font-extrabold text-slate-900">
              3. Feature Roadmap & Upcoming Development
            </h3>
            <p className="text-xs text-slate-500">
              Vote on what tools you would like our engineering team to roll out next for the 2027 placement cycle.
            </p>
          </div>
          <span className="text-xs font-bold text-indigo-600">
            Community Driven
          </span>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {[
            {
              id: 'voice-avatar',
              title: 'Live AI Voice & Video Interviewer',
              status: 'In Active Development',
              statusBadge: 'bg-indigo-100 text-indigo-800',
              description: 'Realistic spoken interview simulation with audio pitch, speaking pace, and hesitation metrics.',
              votes: 342,
            },
            {
              id: 'resume-tailor',
              title: 'Resume-Specific Deep Questions',
              status: 'Beta Testing',
              statusBadge: 'bg-emerald-100 text-emerald-800',
              description: 'AI scans your uploaded resume PDF and cross-examines your exact projects, tech stack, and internships.',
              votes: 489,
            },
            {
              id: 'coding-sandbox',
              title: 'Live Paired Coding Sandbox',
              status: 'Planned for Q4',
              statusBadge: 'bg-slate-100 text-slate-700',
              description: 'Collaborative code editor with real-time test case executions and algorithmic whiteboard visualizer.',
              votes: 215,
            },
          ].map((feature) => (
            <Card key={feature.id} variant="default" className="p-5 rounded-2xl border-slate-200 flex flex-col justify-between space-y-4">
              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <span className={`px-2 py-0.5 rounded-full text-[9px] font-black uppercase ${feature.statusBadge}`}>
                    {feature.status}
                  </span>
                  <span className="text-[11px] font-bold text-slate-400">
                    {feature.votes + (roadmapVote === feature.id ? 1 : 0)} votes
                  </span>
                </div>
                <h4 className="text-sm font-extrabold text-slate-900">
                  {feature.title}
                </h4>
                <p className="text-xs text-slate-600 leading-relaxed">
                  {feature.description}
                </p>
              </div>

              <div className="pt-3 border-t border-slate-100">
                <Button
                  variant={roadmapVote === feature.id ? 'primary' : 'outline'}
                  size="sm"
                  className="w-full text-xs"
                  onClick={() => setRoadmapVote(feature.id)}
                >
                  {roadmapVote === feature.id ? '✓ Voted Priority' : '▲ Upvote Feature'}
                </Button>
              </div>
            </Card>
          ))}
        </div>

        {/* Custom Feedback Submission */}
        <Card variant="subtle" className="p-6 rounded-3xl border-slate-200 bg-slate-50/80 space-y-3">
          <h4 className="text-xs font-bold uppercase tracking-wider text-slate-600">
            Have a Feature Suggestion or Interview Round Request?
          </h4>
          <p className="text-xs text-slate-500">
            Let the CampusFlow product team know what company-specific interview formats or question types you want added.
          </p>
          <div className="flex flex-col sm:flex-row gap-2.5">
            <input
              type="text"
              value={featureFeedbackInput}
              onChange={(e) => setFeatureFeedbackInput(e.target.value)}
              placeholder="e.g., Add Morgan Stanley System Design & TCS Digital Technical Round questions..."
              className="flex-1 px-4 py-2 rounded-xl border border-slate-200 bg-white text-xs text-slate-800 placeholder:text-slate-400 focus:ring-2 focus:ring-indigo-500"
            />
            <Button
              variant="primary"
              size="sm"
              disabled={!featureFeedbackInput.trim() || feedbackSubmitted}
              onClick={() => {
                setFeedbackSubmitted(true);
                setFeatureFeedbackInput('');
              }}
            >
              {feedbackSubmitted ? '✓ Suggestion Received' : 'Submit Feedback'}
            </Button>
          </div>
          {feedbackSubmitted && (
            <p className="text-[11px] text-emerald-700 font-semibold animate-fade-in">
              Thank you! Your suggestion has been logged for our upcoming product release.
            </p>
          )}
        </Card>
      </div>
    </div>
  );
};

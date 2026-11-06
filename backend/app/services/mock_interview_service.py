"""
CampusFlow — AI Mock Interview Voice Agent Service.

Provides agentic evaluation of candidate spoken/transcribed responses,
scoring across Technical Depth, Communication & Articulation, and Structural Flow,
and generating persistent, multi-pillar Interview Performance Reports.
"""
from __future__ import annotations

from datetime import datetime, timezone
import math
import re
from typing import Sequence
from uuid import UUID

from fastapi import HTTPException, status

from app.models.mock_interview import MockInterviewEvaluation, MockInterviewSession
from app.repositories.mock_interview_repository import MockInterviewRepository
from app.schemas.mock_interview import (
    MockInterviewEvaluateRequest,
    MockInterviewSessionCreate,
)
from app.services.rag_service import RAGService

FILLER_WORD_PATTERNS = [
    r"\bum+\b",
    r"\buh+\b",
    r"\ber+\b",
    r"\bah+\b",
    r"\blike\b",
    r"\byou know\b",
    r"\bbasically\b",
    r"\bactually\b",
    r"\bliterally\b",
    r"\bsort of\b",
    r"\bkind of\b",
    r"\bi mean\b",
]

STAR_INDICATORS = {
    "situation": [r"\bsituation\b", r"\bcontext\b", r"\bwhen i was\b", r"\bduring my\b", r"\bat my previous\b", r"\bin my project\b"],
    "task": [r"\btask\b", r"\bgoal\b", r"\bchallenge\b", r"\bresponsible for\b", r"\bneeded to\b", r"\bobjective\b"],
    "action": [r"\baction\b", r"\bi implemented\b", r"\bi developed\b", r"\bi designed\b", r"\bi coordinated\b", r"\bi investigated\b", r"\bi resolved\b"],
    "result": [r"\bresult\b", r"\boutcome\b", r"\bimpact\b", r"\bincreased\b", r"\bdecreased\b", r"\bimproved\b", r"\bachieved\b", r"\bpercent\b", r"\%"],
}

TECHNICAL_INDICATORS = [
    r"\bo\(",
    r"\bcomplexity\b",
    r"\btrade-?off\b",
    r"\blatency\b",
    r"\bthroughput\b",
    r"\bscale\b",
    r"\bcache\b",
    r"\bdatabase\b",
    r"\bindex\b",
    r"\bdistributed\b",
    r"\bconcurrent\b",
    r"\basync\b",
    r"\bmemory\b",
    r"\bbenchmark\b",
]


class MockInterviewService:
    def __init__(self, repo: MockInterviewRepository) -> None:
        self.repo = repo

    async def create_session(
        self, user_id: UUID, data: MockInterviewSessionCreate
    ) -> MockInterviewSession:
        session = MockInterviewSession(
            user_id=user_id,
            track_id=data.track_id,
            track_title=data.track_title,
            target_role=data.target_role,
            status="IN_PROGRESS",
        )
        return await self.repo.create_session(session)

    async def evaluate_answer(
        self, session_id: UUID, user_id: UUID, request: MockInterviewEvaluateRequest
    ) -> MockInterviewEvaluation:
        session = await self.repo.get_session_by_id(session_id, user_id)
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Mock interview session not found.",
            )

        answer = request.student_answer.strip()
        words = [w for w in re.split(r"\s+", answer) if w]
        word_count = len(words)

        # 1. Filler words detection
        detected_fillers: list[str] = []
        lower_answer = answer.lower()
        for pat in FILLER_WORD_PATTERNS:
            matches = re.findall(pat, lower_answer)
            if matches:
                clean_term = pat.replace(r"\b", "").replace("+", "")
                detected_fillers.extend([clean_term] * len(matches))

        filler_count = len(detected_fillers)
        filler_ratio = filler_count / max(1, word_count)

        # 2. Speaking pace (Words Per Minute)
        wpm = None
        if request.audio_duration_seconds and request.audio_duration_seconds > 0:
            minutes = request.audio_duration_seconds / 60.0
            wpm = round(word_count / max(0.1, minutes), 1)

        # 3. Grounded RAG Knowledge Retrieval & Keyword Matching
        rag_service = RAGService.get_instance()
        rag_eval = rag_service.evaluate_answer_grounded(
            question_text=request.question_text,
            student_answer=answer,
            track_id=session.track_id,
            expected_keywords=request.expected_keywords,
        )

        matched_keywords: list[str] = list(dict.fromkeys(rag_eval.matched_concepts))
        missed_keywords: list[str] = list(dict.fromkeys(rag_eval.missing_concepts))

        # Concept coverage ratio from verified handbooks
        concept_coverage_ratio = rag_eval.concept_coverage_score / 100.0

        # 4. Multi-Pillar Scoring Engine
        # Technical Depth (40%) - Calibrated by Grounded RAG Concept Coverage
        tech_score = 45.0
        tech_score += concept_coverage_ratio * 40.0
        if word_count >= 80:
            tech_score += 10.0
        elif word_count >= 40:
            tech_score += 5.0
        
        tech_indicators_found = sum(
            1 for pat in TECHNICAL_INDICATORS if re.search(pat, lower_answer)
        )
        tech_score += min(10.0, tech_indicators_found * 2.5)
        tech_score = max(30.0, min(98.0, round(tech_score, 1)))

        # Communication & Articulation (30%)
        comm_score = 75.0
        if filler_ratio > 0.08:
            comm_score -= 20.0
        elif filler_ratio > 0.04:
            comm_score -= 10.0
        elif filler_ratio == 0:
            comm_score += 8.0

        if wpm:
            if 110 <= wpm <= 165:
                comm_score += 10.0  # Optimal conversational speed
            elif wpm < 90 or wpm > 195:
                comm_score -= 8.0  # Too slow or hurried

        # Sentence structuring bonus
        sentences = [s for s in re.split(r"[.!?]+", answer) if s.strip()]
        if len(sentences) >= 3:
            comm_score += 7.0
        comm_score = max(35.0, min(97.0, round(comm_score, 1)))

        # Structural Flow & Framework Adherence (30%)
        struct_score = 60.0
        if "behavioral" in request.question_category.lower() or "hr" in session.track_id.lower():
            star_points = 0
            for phase, patterns in STAR_INDICATORS.items():
                if any(re.search(p, lower_answer) for p in patterns):
                    star_points += 1
            struct_score += (star_points / 4.0) * 35.0
        else:
            # Technical / Design: Look for structured decomposition
            has_steps = any(
                w in lower_answer
                for w in ["first", "second", "then", "approach", "step", "algorithm", "finally"]
            )
            if has_steps:
                struct_score += 15.0
            if "trade" in lower_answer or "alternative" in lower_answer:
                struct_score += 15.0
            if word_count > 60:
                struct_score += 10.0
        struct_score = max(30.0, min(96.0, round(struct_score, 1)))

        # Composite question score
        composite_score = round(
            (0.40 * tech_score) + (0.35 * comm_score) + (0.25 * struct_score), 1
        )

        # 5. Strengths, Improvements & Critique
        strengths: list[str] = []
        improvements: list[str] = []

        if len(matched_keywords) >= 2:
            strengths.append(
                f"Effectively demonstrated domain mastery citing {', '.join(matched_keywords[:3])}."
            )
        if word_count >= 60:
            strengths.append("Provided a thoroughly developed response with substantive context.")
        if filler_ratio <= 0.03:
            strengths.append("Maintained polished verbal delivery with minimal filler hesitation.")
        if not strengths:
            strengths.append("Directly engaged the prompt with relevant context.")

        if missed_keywords:
            improvements.append(
                f"Handbook Criteria [{rag_eval.source_document}]: Address core concepts: {', '.join(missed_keywords[:4])}."
            )
        if filler_count >= 3:
            improvements.append(
                f"Reduce filler expressions (detected {filler_count} instances like '{detected_fillers[0]}'). Pause briefly instead of using verbal fillers."
            )
        if word_count < 45:
            improvements.append(
                "Expand on your answer by walking through specific technical trade-offs or measurable results."
            )
        if not improvements:
            improvements.append(
                "Consider concluding with a proactive question or brief retrospective takeaway."
            )

        critique = (
            f"Score: {composite_score}/100 • Handbook Rubric Coverage: {rag_eval.concept_coverage_score}%. "
            f"{rag_eval.rubric_guidance}"
        )

        ideal_response = (
            f"📘 Verified Handbook Model Answer [{rag_eval.source_document}]:\n"
            f"{rag_eval.reference_model_answer}\n\n"
            f"🎯 Candidate High-Impact Delivery Strategy:\n"
            f"Begin with a clear architectural definition, explain implementation trade-offs citing "
            f"{', '.join(matched_keywords[:3]) if matched_keywords else 'fundamental design principles'}, "
            f"and conclude with quantifiable outcomes and operational resilience."
        )

        evaluation = MockInterviewEvaluation(
            session_id=session.id,
            question_index=request.question_index,
            question_id=request.question_id,
            question_text=request.question_text,
            question_category=request.question_category,
            student_answer=answer,
            audio_duration_seconds=request.audio_duration_seconds,
            words_per_minute=wpm,
            filler_words=list(set(detected_fillers)),
            score=composite_score,
            technical_depth_score=tech_score,
            communication_score=comm_score,
            structure_score=struct_score,
            feedback_critique=critique,
            strengths=strengths,
            improvements=improvements,
            ideal_response=ideal_response,
            keywords_matched=matched_keywords,
            keywords_missed=missed_keywords,
        )

        return await self.repo.add_evaluation(evaluation)

    async def complete_session(
        self, session_id: UUID, user_id: UUID
    ) -> MockInterviewSession:
        session = await self.repo.get_session_by_id(session_id, user_id)
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Mock interview session not found.",
            )

        evals = session.evaluations
        if not evals:
            # If completed with 0 evals, record baseline
            session.status = "COMPLETED"
            session.overall_score = 0.0
            session.performance_rating = "NEEDS_PRACTICE"
            session.completed_at = datetime.now(timezone.utc)
            return await self.repo.save_session(session)

        # Aggregate Pillar Scores
        avg_overall = round(sum(e.score for e in evals) / len(evals), 1)
        avg_tech = round(sum(e.technical_depth_score for e in evals) / len(evals), 1)
        avg_comm = round(sum(e.communication_score for e in evals) / len(evals), 1)
        avg_struct = round(sum(e.structure_score for e in evals) / len(evals), 1)
        confidence_calc = round(min(100.0, max(40.0, avg_comm * 0.9 + avg_struct * 0.1)), 1)

        # Performance Rating Tier
        if avg_overall >= 85.0:
            rating = "EXCEPTIONAL"
            rating_desc = "Outstanding Performance • Placement Ready"
        elif avg_overall >= 74.0:
            rating = "JOB_READY"
            rating_desc = "Strong Competency • Ready for Campus Drives"
        elif avg_overall >= 60.0:
            rating = "DEVELOPING"
            rating_desc = "Good Foundation • Focus on Depth & Fluency"
        else:
            rating = "NEEDS_PRACTICE"
            rating_desc = "Needs Structured Practice & Terminology Review"

        # Topic Breakdown
        topic_scores: dict[str, list[float]] = {}
        for e in evals:
            topic_scores.setdefault(e.question_category, []).append(e.score)
        
        topic_breakdown = {
            cat: round(sum(scores) / len(scores), 1)
            for cat, scores in topic_scores.items()
        }

        # Consolidated Strengths & Improvements
        all_strengths = []
        all_improvements = []
        for e in evals:
            all_strengths.extend(e.strengths)
            all_improvements.extend(e.improvements)

        unique_strengths = list(dict.fromkeys(all_strengths))[:4]
        unique_improvements = list(dict.fromkeys(all_improvements))[:4]

        # Action Plan
        action_plan = [
            f"Review {session.track_title} high-frequency question patterns and practice verbalizing step-by-step logic aloud.",
            "Record 2-minute spoken drills using the STAR method to eliminate hesitation and filler words.",
            f"Prioritize improvement on '{min(topic_breakdown, key=topic_breakdown.get)}' to elevate overall benchmark score.",
        ]

        summary = (
            f"Candidate achieved an overall score of {avg_overall}/100 across {len(evals)} interview questions ({rating_desc}). "
            f"Communication clarity reached {avg_comm}%, with technical depth at {avg_tech}%. "
            f"Primary growth opportunity: {unique_improvements[0] if unique_improvements else 'Continue timed mock practice'}."
        )

        session.status = "COMPLETED"
        session.overall_score = avg_overall
        session.technical_score = avg_tech
        session.communication_score = avg_comm
        session.structure_score = avg_struct
        session.confidence_score = confidence_calc
        session.performance_rating = rating
        session.summary_feedback = summary
        session.strengths = unique_strengths
        session.improvements = unique_improvements
        session.action_plan = action_plan
        session.topic_breakdown = topic_breakdown
        session.completed_at = datetime.now(timezone.utc)

        return await self.repo.save_session(session)

    async def list_user_sessions(self, user_id: UUID) -> Sequence[MockInterviewSession]:
        return await self.repo.list_sessions_for_user(user_id)

    async def get_session_details(
        self, session_id: UUID, user_id: UUID
    ) -> MockInterviewSession:
        session = await self.repo.get_session_by_id(session_id, user_id)
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Mock interview session not found.",
            )
        return session

    def get_track_questions(self, track_id: str, count: int = 5, offset: int = 0):
        """Retrieves questions dynamically curated from the RAG knowledge base for a specific role track."""
        return RAGService.get_instance().get_track_questions(
            track_id=track_id, count=count, offset=offset
        )

    def search_rag(self, query: str, track_id: str | None = None, top_k: int = 3):
        """Searches the verified 7-handbook RAG index for relevant question passages."""
        return RAGService.get_instance().search(query=query, track_id=track_id, top_k=top_k)

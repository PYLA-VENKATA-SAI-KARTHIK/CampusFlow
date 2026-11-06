"""
CampusFlow — AI Voice Agent Mock Interview Integration Tests.

Verifies:
1. Student creates a mock interview session for a selected track.
2. AI Agent evaluates spoken responses with:
   - Topic keywords detection
   - Filler word penalty
   - WPM speech pacing
   - Multi-pillar scoring (Technical, Communication, Structural)
   - Constructive critique, actionable strengths, and improvement suggestions
3. Student completes session, generating a comprehensive Performance Report:
   - Overall score & placement readiness rating
   - Pillar breakdown
   - Topic mastery breakdown
   - Actionable growth roadmap
4. Student can list past sessions and view detailed historical reports.
"""
from __future__ import annotations

import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import hash_password
from app.models.branch import Branch
from app.models.student_profile import StudentProfile
from app.models.user import User


@pytest_asyncio.fixture
async def student_auth_setup(db_session: AsyncSession, async_client: AsyncClient) -> dict:
    # Ensure branch exists
    branch = Branch(code="CSE_VOICE", name="Computer Science Voice")
    db_session.add(branch)
    await db_session.commit()

    student_email = "voice_student@klu.ac.in"
    student = User(
        email=student_email,
        password_hash=hash_password("DevPass123!"),
        role="STUDENT",
        full_name="Voice Agent Tester",
        is_active=True,
    )
    db_session.add(student)
    await db_session.commit()

    profile = StudentProfile(
        user_id=student.id,
        roll_number="99230048888",
        branch_code="CSE_VOICE",
        batch_year=2026,
        cgpa=8.9,
        active_backlogs=0,
    )
    db_session.add(profile)
    await db_session.commit()

    # Login student
    login_resp = await async_client.post(
        "/api/v1/auth/login",
        json={"email": student_email, "password": "DevPass123!"},
    )
    assert login_resp.status_code == 200
    token = login_resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    return {"student": student, "headers": headers}


@pytest.mark.asyncio
async def test_mock_interview_full_agent_workflow(
    async_client: AsyncClient, student_auth_setup: dict
) -> None:
    headers = student_auth_setup["headers"]

    # 1. Start Session
    create_payload = {
        "track_id": "full-stack",
        "track_title": "Full-Stack Development (React & FastAPI)",
        "target_role": "Full-Stack Software Engineer",
    }
    create_resp = await async_client.post(
        "/api/v1/mock-interviews/sessions",
        headers=headers,
        json=create_payload,
    )
    assert create_resp.status_code == 201
    session_data = create_resp.json()
    assert session_data["track_id"] == "full-stack"
    assert session_data["status"] == "IN_PROGRESS"
    session_id = session_data["id"]

    # 2. Evaluate Question 1: Strong Technical Answer
    eval_payload_1 = {
        "question_index": 0,
        "question_id": "fs-q1",
        "question_text": "Explain the difference between optimistic UI updates and pessimistic UI updates in web applications.",
        "question_category": "System Architecture & Frontend",
        "student_answer": (
            "In our web application, optimistic UI updates immediately modify the client state and render the change "
            "before the server responds, assuming success to reduce perceived latency. If the network call fails, we rollback "
            "the state and notify the user. On the other hand, pessimistic UI updates wait for the API response and database confirmation "
            "before updating the DOM, which ensures strict consistency at the cost of higher latency."
        ),
        "expected_keywords": ["optimistic", "pessimistic", "rollback", "latency", "consistency"],
        "audio_duration_seconds": 28.5,
    }
    eval_resp_1 = await async_client.post(
        f"/api/v1/mock-interviews/sessions/{session_id}/evaluate-answer",
        headers=headers,
        json=eval_payload_1,
    )
    assert eval_resp_1.status_code == 200
    eval_data_1 = eval_resp_1.json()
    assert eval_data_1["question_index"] == 0
    assert eval_data_1["score"] >= 75.0
    assert eval_data_1["technical_depth_score"] >= 75.0
    assert "latency" in eval_data_1["keywords_matched"] or "optimistic" in eval_data_1["keywords_matched"]
    assert len(eval_data_1["strengths"]) > 0
    assert eval_data_1["words_per_minute"] is not None

    # 3. Evaluate Question 2: Behavioral / STAR Question with some fillers
    eval_payload_2 = {
        "question_index": 1,
        "question_id": "fs-q2",
        "question_text": "Describe a difficult bug you investigated and how you resolved it.",
        "question_category": "Problem Solving & Behavioral",
        "student_answer": (
            "Um, when I was working on my final year capstone project, like, our database query latency spiked by 300%. "
            "The task was to find the bottleneck. My action was that I analyzed the slow query log and discovered missing indexes "
            "on foreign keys. I implemented composite indexes and optimized the join query. As a result, query latency decreased "
            "by 85% and throughput improved significantly."
        ),
        "expected_keywords": ["bottleneck", "indexes", "query", "latency"],
        "audio_duration_seconds": 32.0,
    }
    eval_resp_2 = await async_client.post(
        f"/api/v1/mock-interviews/sessions/{session_id}/evaluate-answer",
        headers=headers,
        json=eval_payload_2,
    )
    assert eval_resp_2.status_code == 200
    eval_data_2 = eval_resp_2.json()
    assert eval_data_2["question_index"] == 1
    # Check that fillers were detected
    assert any("um" in f or "like" in f for f in eval_data_2["filler_words"])
    assert eval_data_2["structure_score"] >= 70.0  # STAR framework matched (situation, task, action, result)

    # 4. Complete Session & Generate Performance Report
    complete_resp = await async_client.post(
        f"/api/v1/mock-interviews/sessions/{session_id}/complete",
        headers=headers,
    )
    assert complete_resp.status_code == 200
    report = complete_resp.json()
    assert report["status"] == "COMPLETED"
    assert report["overall_score"] is not None
    assert report["overall_score"] > 60.0
    assert report["performance_rating"] in ["EXCEPTIONAL", "JOB_READY", "DEVELOPING", "NEEDS_PRACTICE"]
    assert report["technical_score"] is not None
    assert report["communication_score"] is not None
    assert report["structure_score"] is not None
    assert len(report["strengths"]) > 0
    assert len(report["improvements"]) > 0
    assert len(report["action_plan"]) >= 2
    assert "System Architecture & Frontend" in report["topic_breakdown"]
    assert len(report["evaluations"]) == 2

    # 5. List Student Sessions
    list_resp = await async_client.post(
        "/api/v1/mock-interviews/sessions",
        headers=headers,
        json={
            "track_id": "dsa-core",
            "track_title": "Data Structures & Algorithms",
            "target_role": "Backend Engineer",
        },
    )
    assert list_resp.status_code == 201

    sessions_resp = await async_client.get(
        "/api/v1/mock-interviews/sessions",
        headers=headers,
    )
    assert sessions_resp.status_code == 200
    all_sessions = sessions_resp.json()
    assert len(all_sessions) >= 2

    # 6. Get Details of Completed Session
    detail_resp = await async_client.get(
        f"/api/v1/mock-interviews/sessions/{session_id}",
        headers=headers,
    )
    assert detail_resp.status_code == 200
    detail = detail_resp.json()
    assert detail["id"] == session_id
    assert detail["overall_score"] == report["overall_score"]
    assert len(detail["evaluations"]) == 2


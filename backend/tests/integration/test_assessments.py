"""
Comprehensive Integration & Security Tests for Practice Assessment Engine (Phase 5.2).
"""
import uuid
from decimal import Decimal
import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import hash_password
from app.models.assessment import (
    Assessment,
    AssessmentAssignment,
    AssessmentAttempt,
    AssessmentQuestion,
    AssessmentResponse,
    AssessmentResult,
)
from app.models.audit_log import AuditLog
from app.models.preparation import PreparationCategory, PreparationTopic
from app.models.user import User


@pytest_asyncio.fixture
async def seed_assessment_taxonomy(db_session: AsyncSession) -> dict:
    category = PreparationCategory(
        code="TECHNICAL",
        name="Technical Core",
        description="Core technical topics",
        icon="Code",
        sequence_order=1,
    )
    db_session.add(category)
    await db_session.flush()

    topic_sql = PreparationTopic(
        category_id=category.id,
        name="SQL & Databases",
        slug="sql-databases",
    )
    topic_py = PreparationTopic(
        category_id=category.id,
        name="Python Basics",
        slug="python-basics",
    )
    db_session.add_all([topic_sql, topic_py])
    await db_session.commit()

    return {
        "category": category,
        "topic_sql": topic_sql,
        "topic_py": topic_py,
    }


from app.core.security import get_jwt_manager, hash_password


@pytest_asyncio.fixture
async def assessment_users(
    db_session: AsyncSession,
) -> dict:
    suffix = uuid.uuid4().hex[:6]
    student1 = User(
        email=f"astudent1_{suffix}@campusflow.com",
        password_hash=hash_password("password123"),
        role="STUDENT",
        full_name="Assessment Student One",
        is_active=True,
    )
    student2 = User(
        email=f"astudent2_{suffix}@campusflow.com",
        password_hash=hash_password("password123"),
        role="STUDENT",
        full_name="Assessment Student Two",
        is_active=True,
    )
    officer = User(
        email=f"aofficer_{suffix}@campusflow.com",
        password_hash=hash_password("password123"),
        role="OFFICER",
        full_name="Assessment Officer",
        is_active=True,
    )
    admin = User(
        email=f"aadmin_{suffix}@campusflow.com",
        password_hash=hash_password("password123"),
        role="ADMIN",
        full_name="Assessment Admin",
        is_active=True,
    )

    db_session.add_all([student1, student2, officer, admin])
    await db_session.commit()

    jwt_mgr = get_jwt_manager()
    t_s1 = jwt_mgr.create_access_token(user_id=str(student1.id), role="STUDENT", email=student1.email)
    t_s2 = jwt_mgr.create_access_token(user_id=str(student2.id), role="STUDENT", email=student2.email)
    t_off = jwt_mgr.create_access_token(user_id=str(officer.id), role="OFFICER", email=officer.email)
    t_adm = jwt_mgr.create_access_token(user_id=str(admin.id), role="ADMIN", email=admin.email)

    return {
        "student1_auth": {"Authorization": f"Bearer {t_s1}"},
        "student2_auth": {"Authorization": f"Bearer {t_s2}"},
        "officer_auth": {"Authorization": f"Bearer {t_off}"},
        "admin_auth": {"Authorization": f"Bearer {t_adm}"},
        "student1_id": student1.id,
        "student2_id": student2.id,
        "officer_id": officer.id,
        "admin_id": admin.id,
    }



# ===========================================================================
# 1. Assessment Creation & Metadata
# ===========================================================================

@pytest.mark.asyncio
async def test_officer_create_and_update_draft_assessment(
    async_client: AsyncClient,
    assessment_users: dict,
    seed_assessment_taxonomy: dict,
):
    topic_sql = seed_assessment_taxonomy["topic_sql"]
    cat = seed_assessment_taxonomy["category"]

    # 1. Create Assessment (Draft)
    payload = {
        "title": "SQL Practice Test 1",
        "description": "Comprehensive SQL queries assessment",
        "category_id": str(cat.id),
        "topic_id": str(topic_sql.id),
        "difficulty": "BEGINNER",
        "duration_minutes": 20,
        "pass_percentage": "60.00",
        "allow_multiple_attempts": False,
    }

    res = await async_client.post(
        "/api/v1/assessments",
        json=payload,
        headers=assessment_users["officer_auth"],
    )
    assert res.status_code == 201
    data = res.json()
    assert data["title"] == "SQL Practice Test 1"
    assert data["status"] == "DRAFT"
    assert float(data["total_marks"]) == 0.0
    assessment_id = data["id"]

    # 2. Update Draft Assessment
    update_payload = {
        "title": "SQL Practice Assessment - Basic & Intermediate",
        "duration_minutes": 25,
    }
    res_update = await async_client.patch(
        f"/api/v1/assessments/{assessment_id}",
        json=update_payload,
        headers=assessment_users["officer_auth"],
    )
    assert res_update.status_code == 200
    assert res_update.json()["title"] == "SQL Practice Assessment - Basic & Intermediate"
    assert res_update.json()["duration_minutes"] == 25



# ===========================================================================
# 2. Question Management & Validation
# ===========================================================================

@pytest.mark.asyncio
async def test_question_crud_and_validation(
    async_client: AsyncClient,
    assessment_users: dict,
    seed_assessment_taxonomy: dict,
):
    topic_sql = seed_assessment_taxonomy["topic_sql"]

    # Create Draft Assessment
    res = await async_client.post(
        "/api/v1/assessments",
        json={"title": "DB Test", "duration_minutes": 15},
        headers=assessment_users["officer_auth"],
    )
    assert res.status_code == 201
    assessment_id = res.json()["id"]

    # Validation: Option key not in options
    invalid_q = {
        "question_text": "What does SQL stand for?",
        "options": [
            {"key": "A", "text": "Structured Question Language"},
            {"key": "B", "text": "Structured Query Language"},
        ],
        "correct_option": "C", # Not in options!
        "marks": "2.00",
    }
    res_inv = await async_client.post(
        f"/api/v1/assessments/{assessment_id}/questions",
        json=invalid_q,
        headers=assessment_users["officer_auth"],
    )
    assert res_inv.status_code == 422

    # Validation: Less than 2 options
    res_one_opt = await async_client.post(
        f"/api/v1/assessments/{assessment_id}/questions",
        json={
            "question_text": "What is SQL?",
            "options": [{"key": "A", "text": "Only one option"}],
            "correct_option": "A",
        },
        headers=assessment_users["officer_auth"],
    )
    assert res_one_opt.status_code == 422

    # Valid Question 1
    q1 = {
        "question_text": "What does SQL stand for?",
        "options": [
            {"key": "A", "text": "Structured Question Language"},
            {"key": "B", "text": "Structured Query Language"},
            {"key": "C", "text": "Strong Query Language"},
            {"key": "D", "text": "Sequential Query Logic"},
        ],
        "correct_option": "B",
        "explanation": "SQL stands for Structured Query Language.",
        "marks": "2.00",
        "topic_id": str(topic_sql.id),
        "sequence_order": 1,
    }
    res_q1 = await async_client.post(
        f"/api/v1/assessments/{assessment_id}/questions",
        json=q1,
        headers=assessment_users["officer_auth"],
    )
    assert res_q1.status_code == 201
    q1_data = res_q1.json()
    assert q1_data["correct_option"] == "B"
    assert float(q1_data["marks"]) == 2.0

    # Valid Question 2
    q2 = {
        "question_text": "Which clause is used to filter records?",
        "options": [
            {"key": "A", "text": "GROUP BY"},
            {"key": "B", "text": "ORDER BY"},
            {"key": "C", "text": "WHERE"},
            {"key": "D", "text": "SELECT"},
        ],
        "correct_option": "C",
        "marks": "3.00",
        "topic_id": str(topic_sql.id),
        "sequence_order": 2,
    }
    res_q2 = await async_client.post(
        f"/api/v1/assessments/{assessment_id}/questions",
        json=q2,
        headers=assessment_users["officer_auth"],
    )
    assert res_q2.status_code == 201

    # Verify total marks recalculation: 2.0 + 3.0 = 5.0
    res_admin = await async_client.get(
        f"/api/v1/assessments/{assessment_id}",
        headers=assessment_users["officer_auth"],
    )
    assert float(res_admin.json()["total_marks"]) == 5.0
    assert len(res_admin.json()["questions"]) == 2


# ===========================================================================
# 3. Publishing & Archiving Rules
# ===========================================================================

@pytest.mark.asyncio
async def test_publish_validation_and_freeze(
    async_client: AsyncClient,
    assessment_users: dict,
):
    # Assessment with 0 questions cannot be published
    res_empty = await async_client.post(
        "/api/v1/assessments",
        json={"title": "Empty Test", "duration_minutes": 10},
        headers=assessment_users["officer_auth"],
    )
    empty_id = res_empty.json()["id"]

    res_pub_fail = await async_client.post(
        f"/api/v1/assessments/{empty_id}/publish",
        headers=assessment_users["officer_auth"],
    )
    assert res_pub_fail.status_code == 422
    assert "zero questions" in res_pub_fail.json()["detail"].lower()

    # Add question and publish successfully
    await async_client.post(
        f"/api/v1/assessments/{empty_id}/questions",
        json={
            "question_text": "Sample Question",
            "options": [{"key": "A", "text": "Option 1"}, {"key": "B", "text": "Option 2"}],
            "correct_option": "A",
            "marks": "5.00",
        },
        headers=assessment_users["officer_auth"],
    )

    res_pub = await async_client.post(
        f"/api/v1/assessments/{empty_id}/publish",
        headers=assessment_users["officer_auth"],
    )
    assert res_pub.status_code == 200
    assert res_pub.json()["status"] == "PUBLISHED"

    # Modification freeze: Questions cannot be added or modified after publication
    res_add_after = await async_client.post(
        f"/api/v1/assessments/{empty_id}/questions",
        json={
            "question_text": "Late Question",
            "options": [{"key": "A", "text": "1"}, {"key": "B", "text": "2"}],
            "correct_option": "A",
        },
        headers=assessment_users["officer_auth"],
    )
    assert res_add_after.status_code == 400


# ===========================================================================
# 4. RBAC Protection
# ===========================================================================

@pytest.mark.asyncio
async def test_student_cannot_access_officer_endpoints(
    async_client: AsyncClient,
    assessment_users: dict,
):
    # Student cannot create assessment
    res_create = await async_client.post(
        "/api/v1/assessments",
        json={"title": "Student Test", "duration_minutes": 10},
        headers=assessment_users["student1_auth"],
    )
    assert res_create.status_code == 403

    # Student cannot list officer assessments endpoint
    res_list = await async_client.get(
        "/api/v1/assessments",
        headers=assessment_users["student1_auth"],
    )
    assert res_list.status_code == 403


# ===========================================================================
# 5. Full End-to-End Test Taking Flow & Security
# ===========================================================================

@pytest.mark.asyncio
async def test_student_test_taking_scoring_and_security(
    async_client: AsyncClient,
    assessment_users: dict,
    seed_assessment_taxonomy: dict,
):
    topic_sql = seed_assessment_taxonomy["topic_sql"]

    topic_py = seed_assessment_taxonomy["topic_py"]

    # 1. Officer creates and configures assessment
    res_create = await async_client.post(
        "/api/v1/assessments",
        json={
            "title": "Comprehensive Placement Practice 1",
            "description": "SQL & Python Assessment",
            "duration_minutes": 30,
            "pass_percentage": "50.00",
            "difficulty": "INTERMEDIATE",
        },
        headers=assessment_users["officer_auth"],
    )
    assessment_id = res_create.json()["id"]

    # Add Question 1 (SQL - 4 marks)
    res_q1 = await async_client.post(
        f"/api/v1/assessments/{assessment_id}/questions",
        json={
            "question_text": "Which SQL statement is used to extract data?",
            "options": [
                {"key": "A", "text": "GET"},
                {"key": "B", "text": "EXTRACT"},
                {"key": "C", "text": "SELECT"},
                {"key": "D", "text": "OPEN"},
            ],
            "correct_option": "C",
            "explanation": "SELECT is used to query and extract records from a database table.",
            "marks": "4.00",
            "topic_id": str(topic_sql.id),
            "sequence_order": 1,
        },
        headers=assessment_users["officer_auth"],
    )
    q1_id = res_q1.json()["id"]

    # Add Question 2 (Python - 3 marks)
    res_q2 = await async_client.post(
        f"/api/v1/assessments/{assessment_id}/questions",
        json={
            "question_text": "Which data type is immutable in Python?",
            "options": [
                {"key": "A", "text": "list"},
                {"key": "B", "text": "tuple"},
                {"key": "C", "text": "dict"},
                {"key": "D", "text": "set"},
            ],
            "correct_option": "B",
            "explanation": "Tuples are immutable sequences in Python.",
            "marks": "3.00",
            "topic_id": str(topic_py.id),
            "sequence_order": 2,
        },
        headers=assessment_users["officer_auth"],
    )
    q2_id = res_q2.json()["id"]

    # Add Question 3 (Python - 3 marks)
    res_q3 = await async_client.post(
        f"/api/v1/assessments/{assessment_id}/questions",
        json={
            "question_text": "What is the output of bool([]) in Python?",
            "options": [
                {"key": "A", "text": "True"},
                {"key": "B", "text": "False"},
            ],
            "correct_option": "B",
            "explanation": "Empty collections evaluate to False in boolean context.",
            "marks": "3.00",
            "topic_id": str(topic_py.id),
            "sequence_order": 3,
        },
        headers=assessment_users["officer_auth"],
    )
    q3_id = res_q3.json()["id"]

    # Publish Assessment (Total marks = 4 + 3 + 3 = 10)
    res_pub = await async_client.post(
        f"/api/v1/assessments/{assessment_id}/publish",
        headers=assessment_users["officer_auth"],
    )
    assert res_pub.status_code == 200
    assert float(res_pub.json()["total_marks"]) == 10.0

    # 2. Officer assigns to Student 1
    res_assign = await async_client.post(
        f"/api/v1/assessments/{assessment_id}/assign",
        json={"student_user_ids": [str(assessment_users["student1_id"])]},
        headers=assessment_users["officer_auth"],
    )
    assert res_assign.status_code == 200
    assert len(res_assign.json()) == 1

    # 3. Student 1 checks assigned list
    res_student_list = await async_client.get(
        "/api/v1/assessments/assigned",
        headers=assessment_users["student1_auth"],
    )
    assert res_student_list.status_code == 200
    assignments = res_student_list.json()
    assert len(assignments) == 1
    assert assignments[0]["assessment_title"] == "Comprehensive Placement Practice 1"

    # 4. Student 1 views Pre-Test Preview
    res_preview = await async_client.get(
        f"/api/v1/assessments/{assessment_id}/preview",
        headers=assessment_users["student1_auth"],
    )
    assert res_preview.status_code == 200
    preview = res_preview.json()
    assert preview["question_count"] == 3
    assert float(preview["total_marks"]) == 10.0
    assert preview["has_active_attempt"] is False

    # 5. Student 1 Starts Assessment Attempt
    res_start = await async_client.post(
        f"/api/v1/assessments/{assessment_id}/start",
        headers=assessment_users["student1_auth"],
    )
    assert res_start.status_code == 200
    start_data = res_start.json()
    attempt_id = start_data["attempt_id"]
    assert len(start_data["questions"]) == 3

    # CRITICAL SECURITY CHECK: Question payload contains NO answers or explanations
    for q in start_data["questions"]:
        assert "correct_option" not in q
        assert "explanation" not in q
        assert "key" in q["options"][0]
        assert "text" in q["options"][0]

    # 6. Student 1 Resumes Active Attempt
    res_resume = await async_client.post(
        f"/api/v1/assessments/{assessment_id}/start",
        headers=assessment_users["student1_auth"],
    )
    assert res_resume.status_code == 200
    assert res_resume.json()["attempt_id"] == attempt_id

    # 7. Student 1 Saves Progress (Autosave Q1=C, Q2=A)
    res_save = await async_client.post(
        f"/api/v1/assessments/attempts/{attempt_id}/save-progress",
        json={
            "responses": [
                {"question_id": q1_id, "selected_option": "C"}, # Correct!
                {"question_id": q2_id, "selected_option": "A"}, # Incorrect (correct is B)
            ]
        },
        headers=assessment_users["student1_auth"],
    )
    assert res_save.status_code == 200
    assert res_save.json()["saved_count"] == 2

    # 8. IDOR Protection: Student 2 CANNOT save progress or submit Student 1's attempt
    res_idor_save = await async_client.post(
        f"/api/v1/assessments/attempts/{attempt_id}/save-progress",
        json={"responses": [{"question_id": q1_id, "selected_option": "A"}]},
        headers=assessment_users["student2_auth"],
    )
    assert res_idor_save.status_code == 403

    res_idor_sub = await async_client.post(
        f"/api/v1/assessments/attempts/{attempt_id}/submit",
        headers=assessment_users["student2_auth"],
    )
    assert res_idor_sub.status_code == 403

    # 9. Student 1 Submits Attempt
    # Q1 was 'C' (Correct: +4 marks)
    # Q2 was 'A' (Incorrect: 0 marks)
    # Q3 was left unanswered (0 marks)
    # Score: 4.0 / 10.0 = 40.0%, is_passed: False (pass percentage is 50%)
    res_submit = await async_client.post(
        f"/api/v1/assessments/attempts/{attempt_id}/submit",
        headers=assessment_users["student1_auth"],
    )
    assert res_submit.status_code == 200
    result = res_submit.json()

    assert float(result["score_obtained"]) == 4.0
    assert float(result["total_score"]) == 10.0
    assert float(result["percentage"]) == 40.0
    assert result["is_passed"] is False
    assert result["total_questions"] == 3
    assert result["correct_answers"] == 1
    assert result["incorrect_answers"] == 1
    assert result["unanswered"] == 1

    # Topic Breakdown Check
    tb = result["topic_breakdown"]
    assert "SQL & Databases" in tb
    assert tb["SQL & Databases"]["correct_answers"] == 1
    assert "Python Basics" in tb
    assert tb["Python Basics"]["incorrect_answers"] == 1
    assert tb["Python Basics"]["unanswered"] == 1

    # 10. Post-Submission Review Check
    assert result["review"] is not None
    assert len(result["review"]) == 3
    rev_map = {item["id"]: item for item in result["review"]}
    assert rev_map[q1_id]["is_correct"] is True
    assert rev_map[q1_id]["selected_option"] == "C"
    assert rev_map[q1_id]["correct_option"] == "C"
    assert rev_map[q1_id]["explanation"] is not None

    assert rev_map[q2_id]["is_correct"] is False
    assert rev_map[q2_id]["selected_option"] == "A"
    assert rev_map[q2_id]["correct_option"] == "B"

    assert rev_map[q3_id]["selected_option"] is None
    assert rev_map[q3_id]["is_correct"] is False

    # 11. Duplicate Submit Protection (Idempotent return)
    res_sub_dup = await async_client.post(
        f"/api/v1/assessments/attempts/{attempt_id}/submit",
        headers=assessment_users["student1_auth"],
    )
    assert res_sub_dup.status_code == 200
    assert res_sub_dup.json()["id"] == result["id"]

    # 12. Student History Check
    res_hist = await async_client.get(
        "/api/v1/assessments/my-history",
        headers=assessment_users["student1_auth"],
    )
    assert res_hist.status_code == 200
    assert len(res_hist.json()) == 1
    assert res_hist.json()[0]["id"] == result["id"]

    # 13. Officer Result View & Summary Check
    res_off_results = await async_client.get(
        f"/api/v1/assessments/{assessment_id}/results",
        headers=assessment_users["officer_auth"],
    )
    assert res_off_results.status_code == 200
    off_summary = res_off_results.json()
    assert off_summary["total_assigned"] == 1
    assert off_summary["total_completed"] == 1
    assert float(off_summary["average_score"]) == 4.0
    assert off_summary["pass_count"] == 0


# ===========================================================================
# 6. Single Attempt Rule & Re-attempt Block
# ===========================================================================

@pytest.mark.asyncio
async def test_single_attempt_policy_rejection(
    async_client: AsyncClient,
    assessment_users: dict,
):
    # Create single-attempt assessment
    res_create = await async_client.post(
        "/api/v1/assessments",
        json={"title": "Strict Single Attempt Test", "duration_minutes": 10, "allow_multiple_attempts": False},
        headers=assessment_users["officer_auth"],
    )
    assessment_id = res_create.json()["id"]

    await async_client.post(
        f"/api/v1/assessments/{assessment_id}/questions",
        json={
            "question_text": "Question 1?",
            "options": [{"key": "A", "text": "1"}, {"key": "B", "text": "2"}],
            "correct_option": "A",
            "marks": "1.00",
        },
        headers=assessment_users["officer_auth"],
    )
    await async_client.post(
        f"/api/v1/assessments/{assessment_id}/publish",
        headers=assessment_users["officer_auth"],
    )
    await async_client.post(
        f"/api/v1/assessments/{assessment_id}/assign",
        json={"student_user_ids": [str(assessment_users["student1_id"])]},
        headers=assessment_users["officer_auth"],
    )

    # Start and submit attempt
    res_start = await async_client.post(
        f"/api/v1/assessments/{assessment_id}/start",
        headers=assessment_users["student1_auth"],
    )
    attempt_id = res_start.json()["attempt_id"]

    await async_client.post(
        f"/api/v1/assessments/attempts/{attempt_id}/submit",
        headers=assessment_users["student1_auth"],
    )

    # Re-starting should now be forbidden
    res_restart = await async_client.post(
        f"/api/v1/assessments/{assessment_id}/start",
        headers=assessment_users["student1_auth"],
    )
    assert res_restart.status_code == 400
    assert "already completed" in res_restart.json()["detail"].lower()


# ===========================================================================
# 7. Edge Cases: Expiry, Tampered Question IDs & Options
# ===========================================================================

@pytest.mark.asyncio
async def test_tampered_question_id_and_option_rejection(
    async_client: AsyncClient,
    assessment_users: dict,
):
    # Assessment 1
    res1 = await async_client.post(
        "/api/v1/assessments",
        json={"title": "Assessment One", "duration_minutes": 15},
        headers=assessment_users["officer_auth"],
    )
    a1_id = res1.json()["id"]
    res_q1 = await async_client.post(
        f"/api/v1/assessments/{a1_id}/questions",
        json={"question_text": "Q1?", "options": [{"key": "A", "text": "1"}, {"key": "B", "text": "2"}], "correct_option": "A"},
        headers=assessment_users["officer_auth"],
    )
    q1_id = res_q1.json()["id"]
    await async_client.post(f"/api/v1/assessments/{a1_id}/publish", headers=assessment_users["officer_auth"])
    await async_client.post(
        f"/api/v1/assessments/{a1_id}/assign",
        json={"student_user_ids": [str(assessment_users["student1_id"])]},
        headers=assessment_users["officer_auth"],
    )

    # Assessment 2 (Different assessment)
    res2 = await async_client.post(
        "/api/v1/assessments",
        json={"title": "Assessment Two", "duration_minutes": 15},
        headers=assessment_users["officer_auth"],
    )
    a2_id = res2.json()["id"]
    res_q2 = await async_client.post(
        f"/api/v1/assessments/{a2_id}/questions",
        json={"question_text": "Q2 from Assessment 2?", "options": [{"key": "A", "text": "1"}, {"key": "B", "text": "2"}], "correct_option": "A"},
        headers=assessment_users["officer_auth"],
    )
    q2_foreign_id = res_q2.json()["id"]
    await async_client.post(f"/api/v1/assessments/{a2_id}/publish", headers=assessment_users["officer_auth"])

    # Student starts Assessment 1
    res_start = await async_client.post(f"/api/v1/assessments/{a1_id}/start", headers=assessment_users["student1_auth"])
    attempt_id = res_start.json()["attempt_id"]

    # Security: Submitting a question ID belonging to Assessment 2 into Assessment 1 attempt must be rejected (400)
    res_tamper = await async_client.post(
        f"/api/v1/assessments/attempts/{attempt_id}/save-progress",
        json={"responses": [{"question_id": q2_foreign_id, "selected_option": "A"}]},
        headers=assessment_users["student1_auth"],
    )
    assert res_tamper.status_code == 400
    assert "does not belong" in res_tamper.json()["detail"].lower()

    # Security: Submitting an invalid option key (e.g. 'Z') not in options must be rejected (422)
    res_bad_opt = await async_client.post(
        f"/api/v1/assessments/attempts/{attempt_id}/save-progress",
        json={"responses": [{"question_id": q1_id, "selected_option": "Z"}]},
        headers=assessment_users["student1_auth"],
    )
    assert res_bad_opt.status_code == 422


@pytest.mark.asyncio
async def test_allow_multiple_attempts(
    async_client: AsyncClient,
    assessment_users: dict,
):
    # Assessment with allow_multiple_attempts = True
    res = await async_client.post(
        "/api/v1/assessments",
        json={"title": "Multi Attempt Test", "duration_minutes": 10, "allow_multiple_attempts": True},
        headers=assessment_users["officer_auth"],
    )
    a_id = res.json()["id"]
    await async_client.post(
        f"/api/v1/assessments/{a_id}/questions",
        json={"question_text": "Multi Q1?", "options": [{"key": "A", "text": "1"}, {"key": "B", "text": "2"}], "correct_option": "A", "marks": "5.00"},
        headers=assessment_users["officer_auth"],
    )
    await async_client.post(f"/api/v1/assessments/{a_id}/publish", headers=assessment_users["officer_auth"])
    await async_client.post(
        f"/api/v1/assessments/{a_id}/assign",
        json={"student_user_ids": [str(assessment_users["student1_id"])]},
        headers=assessment_users["officer_auth"],
    )

    # Attempt 1
    res1 = await async_client.post(f"/api/v1/assessments/{a_id}/start", headers=assessment_users["student1_auth"])
    att1_id = res1.json()["attempt_id"]
    await async_client.post(f"/api/v1/assessments/attempts/{att1_id}/submit", headers=assessment_users["student1_auth"])

    # Attempt 2 (Allowed because allow_multiple_attempts=True)
    res2 = await async_client.post(f"/api/v1/assessments/{a_id}/start", headers=assessment_users["student1_auth"])
    assert res2.status_code == 200
    att2_id = res2.json()["attempt_id"]
    assert att2_id != att1_id


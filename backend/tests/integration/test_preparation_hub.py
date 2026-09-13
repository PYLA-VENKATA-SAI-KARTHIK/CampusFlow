"""
Integration tests for Preparation Hub (Phase 5.1).
"""
import uuid
import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import hash_password
from app.models.audit_log import AuditLog
from app.models.preparation import (
    PreparationCategory,
    PreparationMaterial,
    PreparationRole,
    PreparationRoleTopic,
    PreparationTopic,
)
from app.models.user import User


@pytest_asyncio.fixture
async def seed_preparation_data(db_session: AsyncSession) -> dict:
    cat_apt = PreparationCategory(
        code="APTITUDE",
        name="Aptitude & Reasoning",
        description="Quantitative and logical reasoning.",
        icon="Calculator",
        sequence_order=1,
    )
    cat_vbl = PreparationCategory(
        code="VERBAL",
        name="Verbal Ability",
        description="Grammar and comprehension.",
        icon="BookOpen",
        sequence_order=2,
    )
    cat_tec = PreparationCategory(
        code="TECHNICAL",
        name="Technical Core",
        description="Programming and CS core.",
        icon="Code",
        sequence_order=3,
    )
    cat_int = PreparationCategory(
        code="INTERVIEW",
        name="Interview Preparation",
        description="HR and technical prep.",
        icon="Users",
        sequence_order=4,
    )
    db_session.add_all([cat_apt, cat_vbl, cat_tec, cat_int])
    await db_session.flush()

    # Topics
    t_quant = PreparationTopic(
        category_id=cat_apt.id,
        name="Quantitative Aptitude",
        slug="quantitative-aptitude",
    )
    t_logic = PreparationTopic(
        category_id=cat_apt.id,
        name="Logical Reasoning",
        slug="logical-reasoning",
    )
    t_py = PreparationTopic(
        category_id=cat_tec.id,
        name="Python Programming",
        slug="python",
    )
    t_sql = PreparationTopic(
        category_id=cat_tec.id,
        name="SQL & Databases",
        slug="sql",
    )
    t_os = PreparationTopic(
        category_id=cat_tec.id,
        name="Operating Systems",
        slug="operating-systems",
    )
    t_hr = PreparationTopic(
        category_id=cat_int.id,
        name="HR & Behavioral",
        slug="hr-behavioral",
    )
    db_session.add_all([t_quant, t_logic, t_py, t_sql, t_os, t_hr])
    await db_session.flush()

    # Roles
    r_swe = PreparationRole(
        code="SOFTWARE_DEVELOPER",
        name="Software Developer",
        description="Full stack & backend development.",
        icon="Code",
    )
    r_aiml = PreparationRole(
        code="AI_ML_ENGINEER",
        name="AI/ML Engineer",
        description="Machine learning and data processing.",
        icon="Cpu",
    )
    r_da = PreparationRole(
        code="DATA_ANALYST",
        name="Data Analyst",
        description="Analytics and visualization.",
        icon="BarChart",
    )
    r_genai = PreparationRole(
        code="GENAI_ENGINEER",
        name="Generative AI Engineer",
        description="LLMs and RAG systems.",
        icon="Sparkles",
    )
    r_qa = PreparationRole(
        code="QA_TEST_ENGINEER",
        name="QA & Test Automation",
        description="Testing frameworks.",
        icon="CheckCircle",
    )
    r_devops = PreparationRole(
        code="CLOUD_DEVOPS",
        name="Cloud & DevOps",
        description="CI/CD and infrastructure.",
        icon="Cloud",
    )
    db_session.add_all([r_swe, r_aiml, r_da, r_genai, r_qa, r_devops])
    await db_session.flush()

    # Mappings
    rt1 = PreparationRoleTopic(role_id=r_swe.id, topic_id=t_quant.id, importance="CORE")
    rt2 = PreparationRoleTopic(role_id=r_swe.id, topic_id=t_py.id, importance="CORE")
    rt3 = PreparationRoleTopic(role_id=r_swe.id, topic_id=t_sql.id, importance="CORE")
    db_session.add_all([rt1, rt2, rt3])

    await db_session.commit()

    return {
        "categories": [cat_apt, cat_vbl, cat_tec, cat_int],
        "topics": [t_quant, t_logic, t_py, t_sql, t_os, t_hr],
        "roles": [r_swe, r_aiml, r_da, r_genai, r_qa, r_devops],
        "t_py": t_py,
        "r_swe": r_swe,
    }


@pytest_asyncio.fixture
async def prep_auth_users(
    async_client: AsyncClient,
    db_session: AsyncSession,
) -> dict:
    suffix = uuid.uuid4().hex[:6]
    student = User(
        email=f"prep_student_{suffix}@campusflow.com",
        password_hash=hash_password("password123"),
        role="STUDENT",
        full_name="Prep Student",
        is_active=True,
    )
    student2 = User(
        email=f"prep_student2_{suffix}@campusflow.com",
        password_hash=hash_password("password123"),
        role="STUDENT",
        full_name="Prep Student 2",
        is_active=True,
    )
    officer = User(
        email=f"prep_officer_{suffix}@campusflow.com",
        password_hash=hash_password("password123"),
        role="OFFICER",
        full_name="Prep Officer",
        is_active=True,
    )
    admin = User(
        email=f"prep_admin_{suffix}@campusflow.com",
        password_hash=hash_password("password123"),
        role="ADMIN",
        full_name="Prep Admin",
        is_active=True,
    )

    db_session.add_all([student, student2, officer, admin])
    await db_session.commit()

    await db_session.refresh(student)
    await db_session.refresh(student2)
    await db_session.refresh(officer)
    await db_session.refresh(admin)

    r_student = await async_client.post("/api/v1/auth/login", json={"email": student.email, "password": "password123"})
    r_student2 = await async_client.post("/api/v1/auth/login", json={"email": student2.email, "password": "password123"})
    r_officer = await async_client.post("/api/v1/auth/login", json={"email": officer.email, "password": "password123"})
    r_admin = await async_client.post("/api/v1/auth/login", json={"email": admin.email, "password": "password123"})

    return {
        "student": {"Authorization": f"Bearer {r_student.json()['access_token']}"},
        "student2": {"Authorization": f"Bearer {r_student2.json()['access_token']}"},
        "officer": {"Authorization": f"Bearer {r_officer.json()['access_token']}"},
        "admin": {"Authorization": f"Bearer {r_admin.json()['access_token']}"},
        "student_id": student.id,
        "student2_id": student2.id,
        "officer_id": officer.id,
        "admin_id": admin.id,
    }


@pytest.mark.asyncio
async def test_get_roles(async_client: AsyncClient, prep_auth_users: dict, seed_preparation_data: dict):
    response = await async_client.get(
        "/api/v1/preparation/roles",
        headers=prep_auth_users["student"],
    )
    assert response.status_code == 200
    roles = response.json()
    assert len(roles) >= 6
    codes = {r["code"] for r in roles}
    assert "SOFTWARE_DEVELOPER" in codes
    assert "AI_ML_ENGINEER" in codes
    assert "DATA_ANALYST" in codes
    assert "GENAI_ENGINEER" in codes


@pytest.mark.asyncio
async def test_get_categories_with_topics(async_client: AsyncClient, prep_auth_users: dict, seed_preparation_data: dict):
    response = await async_client.get(
        "/api/v1/preparation/categories",
        headers=prep_auth_users["student"],
    )
    assert response.status_code == 200
    categories = response.json()
    assert len(categories) >= 4
    category_codes = {c["code"] for c in categories}
    assert {"APTITUDE", "VERBAL", "TECHNICAL", "INTERVIEW"}.issubset(category_codes)

    # Check nested topics
    tech_cat = next(c for c in categories if c["code"] == "TECHNICAL")
    topic_slugs = {t["slug"] for t in tech_cat["topics"]}
    assert "python" in topic_slugs
    assert "sql" in topic_slugs
    assert "operating-systems" in topic_slugs


@pytest.mark.asyncio
async def test_get_role_roadmap(async_client: AsyncClient, prep_auth_users: dict, seed_preparation_data: dict):
    response = await async_client.get(
        "/api/v1/preparation/roles/SOFTWARE_DEVELOPER/roadmap",
        headers=prep_auth_users["student"],
    )
    assert response.status_code == 200
    data = response.json()
    assert data["role"]["code"] == "SOFTWARE_DEVELOPER"
    assert len(data["topics"]) > 0
    topic_names = [t["topic"]["name"] for t in data["topics"]]
    assert any("Python" in name for name in topic_names)

    # Non-existent role returns 404
    bad_res = await async_client.get(
        "/api/v1/preparation/roles/UNKNOWN_ROLE/roadmap",
        headers=prep_auth_users["student"],
    )
    assert bad_res.status_code == 404


@pytest.mark.asyncio
async def test_student_suggest_material_and_validation(
    async_client: AsyncClient, prep_auth_users: dict, seed_preparation_data: dict, db_session: AsyncSession
):
    topic = seed_preparation_data["t_py"]

    # 1. Invalid URL scheme fails validation
    invalid_res = await async_client.post(
        "/api/v1/preparation/suggest",
        headers=prep_auth_users["student"],
        json={
            "topic_id": str(topic.id),
            "title": "Invalid URL Resource",
            "url": "javascript:alert(1)",
            "material_type": "ARTICLE",
            "difficulty": "BEGINNER",
        },
    )
    assert invalid_res.status_code == 422

    # 2. Invalid material type fails validation
    invalid_type_res = await async_client.post(
        "/api/v1/preparation/suggest",
        headers=prep_auth_users["student"],
        json={
            "topic_id": str(topic.id),
            "title": "Invalid Type Resource",
            "url": "https://example.com/guide",
            "material_type": "INVALID_TYPE",
            "difficulty": "BEGINNER",
        },
    )
    assert invalid_type_res.status_code == 422

    # 3. Valid suggestion creates PENDING material
    valid_res = await async_client.post(
        "/api/v1/preparation/suggest",
        headers=prep_auth_users["student"],
        json={
            "topic_id": str(topic.id),
            "title": "Comprehensive Topic Mastery Guide",
            "description": "High yield guide covering all core patterns.",
            "url": "https://example.com/topic-guide",
            "material_type": "ARTICLE",
            "difficulty": "INTERMEDIATE",
            "source": "Example Dev Community",
        },
    )
    assert valid_res.status_code == 201
    created_material = valid_res.json()
    assert created_material["title"] == "Comprehensive Topic Mastery Guide"
    assert created_material["status"] == "PENDING"
    assert created_material["submitted_by_user_id"] == str(prep_auth_users["student_id"])


@pytest.mark.asyncio
async def test_student_my_suggestions_isolation(
    async_client: AsyncClient, prep_auth_users: dict, seed_preparation_data: dict, db_session: AsyncSession
):
    topic = seed_preparation_data["t_py"]

    # Student 1 suggests
    await async_client.post(
        "/api/v1/preparation/suggest",
        headers=prep_auth_users["student"],
        json={
            "topic_id": str(topic.id),
            "title": "Student 1 Suggestion",
            "url": "https://example.com/student1",
            "material_type": "VIDEO",
            "difficulty": "BEGINNER",
        },
    )

    # Student 2 suggests
    await async_client.post(
        "/api/v1/preparation/suggest",
        headers=prep_auth_users["student2"],
        json={
            "topic_id": str(topic.id),
            "title": "Student 2 Suggestion",
            "url": "https://example.com/student2",
            "material_type": "PDF",
            "difficulty": "ADVANCED",
        },
    )

    # Student 1 fetches their suggestions
    s1_res = await async_client.get(
        "/api/v1/preparation/my-suggestions",
        headers=prep_auth_users["student"],
    )
    assert s1_res.status_code == 200
    s1_items = s1_res.json()["items"]
    assert all(item["submitted_by_user_id"] == str(prep_auth_users["student_id"]) for item in s1_items)
    assert any(item["title"] == "Student 1 Suggestion" for item in s1_items)
    assert not any(item["title"] == "Student 2 Suggestion" for item in s1_items)


@pytest.mark.asyncio
async def test_officer_review_workflow_and_audit(
    async_client: AsyncClient, prep_auth_users: dict, seed_preparation_data: dict, db_session: AsyncSession
):
    topic = seed_preparation_data["t_py"]

    # Student creates suggestion
    sug_res = await async_client.post(
        "/api/v1/preparation/suggest",
        headers=prep_auth_users["student"],
        json={
            "topic_id": str(topic.id),
            "title": "Material For Officer Approval",
            "url": "https://example.com/approved-guide",
            "material_type": "DOCUMENTATION",
            "difficulty": "INTERMEDIATE",
        },
    )
    material_id = sug_res.json()["id"]

    # Student cannot access review endpoints (RBAC check)
    forbidden_list = await async_client.get(
        "/api/v1/preparation/officers/submissions",
        headers=prep_auth_users["student"],
    )
    assert forbidden_list.status_code == 403

    forbidden_review = await async_client.post(
        f"/api/v1/preparation/officers/submissions/{material_id}/review",
        headers=prep_auth_users["student"],
        json={"status": "APPROVED", "review_notes": "Attempted self-approval"},
    )
    assert forbidden_review.status_code == 403

    # Officer lists submissions
    pending_res = await async_client.get(
        "/api/v1/preparation/officers/submissions",
        headers=prep_auth_users["officer"],
    )
    assert pending_res.status_code == 200
    pending_items = pending_res.json()["items"]
    assert any(item["id"] == material_id for item in pending_items)

    # Officer approves the material
    approve_res = await async_client.post(
        f"/api/v1/preparation/officers/submissions/{material_id}/review",
        headers=prep_auth_users["officer"],
        json={"status": "APPROVED", "review_notes": "Verified accurate and high quality."},
    )
    assert approve_res.status_code == 200
    approved_mat = approve_res.json()
    assert approved_mat["status"] == "APPROVED"
    assert approved_mat["reviewed_by_user_id"] == str(prep_auth_users["officer_id"])
    assert approved_mat["review_notes"] == "Verified accurate and high quality."

    # Verify audit log recorded
    audit_res = await db_session.execute(
        select(AuditLog).where(
            AuditLog.entity_type == "PREPARATION_MATERIAL",
            AuditLog.entity_id == uuid.UUID(material_id),
            AuditLog.action == "PREPARATION_MATERIAL_APPROVED",
        )
    )
    audit_log = audit_res.scalar_one_or_none()
    assert audit_log is not None
    assert audit_log.performed_by_user_id == prep_auth_users["officer_id"]


@pytest.mark.asyncio
async def test_officer_direct_material_creation(
    async_client: AsyncClient, prep_auth_users: dict, seed_preparation_data: dict, db_session: AsyncSession
):
    topic = seed_preparation_data["t_py"]

    # Officer creates material directly
    create_res = await async_client.post(
        "/api/v1/preparation/officers/materials",
        headers=prep_auth_users["officer"],
        json={
            "topic_id": str(topic.id),
            "title": "Official Placement Preparation Handbook",
            "description": "Standard handbook published by the Placement Cell.",
            "url": "https://example.com/placement-handbook.pdf",
            "material_type": "PDF",
            "difficulty": "BEGINNER",
            "source": "Placement Cell",
        },
    )
    assert create_res.status_code == 201
    mat = create_res.json()
    assert mat["status"] == "APPROVED"
    assert mat["submitted_by_user_id"] == str(prep_auth_users["officer_id"])
    assert mat["reviewed_by_user_id"] == str(prep_auth_users["officer_id"])

    # Appears in public material listing
    list_res = await async_client.get(
        f"/api/v1/preparation/materials?topic_id={topic.id}",
        headers=prep_auth_users["student"],
    )
    assert list_res.status_code == 200
    items = list_res.json()["items"]
    assert any(item["title"] == "Official Placement Preparation Handbook" for item in items)

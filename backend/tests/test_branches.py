"""
Tests for Branch endpoints.
"""
import pytest
from httpx import AsyncClient


from sqlalchemy.ext.asyncio import AsyncSession
from app.models.user import User
from app.core.security import hash_password

@pytest.fixture
async def branch_user(db_session: AsyncSession) -> User:
    user = User(
        email="branch@campusflow.com",
        password_hash=hash_password("password123"),
        role="STUDENT",
        full_name="Branch Student",
        is_active=True,
    )
    db_session.add(user)
    await db_session.commit()
    return user

@pytest.mark.asyncio
async def test_list_branches(async_client: AsyncClient, branch_user: User, db_session: AsyncSession):
    # Seed a couple of branches
    from app.models.branch import Branch
    db_session.add_all([
        Branch(code="CSE", name="Computer Science"),
        Branch(code="ECE", name="Electronics")
    ])
    await db_session.commit()

    login_res = await async_client.post("/api/v1/auth/login", json={"email": branch_user.email, "password": "password123"})
    token = login_res.json()["access_token"]
    response = await async_client.get("/api/v1/branches", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 2
    
    codes = [b["code"] for b in data]
    assert "CSE" in codes
    assert "ECE" in codes

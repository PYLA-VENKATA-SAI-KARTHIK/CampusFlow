"""
Tests for Branch endpoints.
"""
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_list_branches(async_client: AsyncClient):
    # Public endpoint or logged-in endpoint depending on design, here it just needs to work
    response = await async_client.get("/api/v1/branches")
    assert response.status_code == 200
    
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 8  # We seeded 8 branches in migration
    
    codes = [b["code"] for b in data]
    assert "CSE" in codes
    assert "ECE" in codes

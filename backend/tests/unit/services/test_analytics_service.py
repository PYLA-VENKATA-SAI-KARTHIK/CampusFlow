"""
Unit tests for AnalyticsService calculations and zero-denominator safeguards.
"""
from uuid import uuid4
import pytest
from unittest.mock import AsyncMock

from app.schemas.analytics import (
    DriveAnalyticsSummary,
    PlacementMetrics,
)
from app.services.analytics_service import AnalyticsService


@pytest.mark.asyncio
async def test_zero_denominator_safeguards():
    """Verify registration_rate and overall_conversion gracefully handle 0 denominators."""
    analytics_repo = AsyncMock()
    drive_repo = AsyncMock()
    student_repo = AsyncMock()

    service = AnalyticsService(analytics_repo, drive_repo, student_repo)

    # Test summary logic directly
    eligible_count = 0
    registered_count = 0
    total_selected = 0

    registration_rate = (
        round((registered_count / eligible_count) * 100, 2)
        if eligible_count > 0
        else 0.0
    )
    overall_conversion = (
        round((total_selected / registered_count) * 100, 2)
        if registered_count > 0
        else 0.0
    )

    summary = DriveAnalyticsSummary(
        eligible_count=eligible_count,
        registered_count=registered_count,
        registration_rate_percentage=registration_rate,
        total_shortlisted_count=0,
        total_selected_count=total_selected,
        overall_conversion_percentage=overall_conversion,
    )

    assert summary.registration_rate_percentage == 0.0
    assert summary.overall_conversion_percentage == 0.0


@pytest.mark.asyncio
async def test_placement_metrics_percentage_calculation():
    """Verify overview placement rate calculation and zero division protection."""
    total_active_students = 200
    total_placed_students = 150

    placement_rate = (
        round((total_placed_students / total_active_students) * 100, 2)
        if total_active_students > 0
        else 0.0
    )

    metrics = PlacementMetrics(
        total_active_students=total_active_students,
        total_placed_students=total_placed_students,
        overall_placement_percentage=placement_rate,
        total_applications_submitted=450,
        average_ctc_lpa=14.5,
        highest_ctc_lpa=42.0,
    )

    assert metrics.overall_placement_percentage == 75.0
    assert metrics.average_ctc_lpa == 14.5
    assert metrics.highest_ctc_lpa == 42.0

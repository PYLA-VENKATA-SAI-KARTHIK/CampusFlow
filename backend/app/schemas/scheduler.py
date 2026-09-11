"""
CampusFlow — Scheduler Schemas.
"""
from __future__ import annotations

from pydantic import BaseModel, ConfigDict


class CheckDeadlinesResponse(BaseModel):
    """Response returned by /internal/scheduler/check-deadlines."""
    drives_checked: int
    tasks_enqueued: int

    model_config = ConfigDict(extra="ignore")


class AutoCloseResponse(BaseModel):
    """Response returned by /internal/scheduler/auto-close-registrations."""
    drives_checked: int
    drives_closed: int

    model_config = ConfigDict(extra="ignore")

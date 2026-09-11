"""
Eligibility evaluation engine.
"""
from __future__ import annotations

from typing import Any

from app.models.student_profile import StudentProfile


class EligibilityService:
    """
    Core engine for evaluating a student's profile against placement drive criteria.
    """

    @staticmethod
    def evaluate(profile: StudentProfile, criteria: dict[str, Any]) -> tuple[bool, list[str]]:
        """
        Evaluate if a student profile satisfies the drive's eligibility criteria.
        
        Returns:
            (is_eligible: bool, reasons: list[str])
        """
        reasons: list[str] = []

        # 1. Minimum CGPA
        min_cgpa = criteria.get("min_cgpa")
        if min_cgpa is not None:
            if float(profile.cgpa) < float(min_cgpa):
                reasons.append(f"Your CGPA ({profile.cgpa}) is below the minimum required CGPA ({min_cgpa}).")

        # 2. Maximum Active Backlogs
        max_backlogs = criteria.get("max_active_backlogs")
        if max_backlogs is not None:
            if profile.active_backlogs > max_backlogs:
                reasons.append(f"Your active backlogs ({profile.active_backlogs}) exceed the maximum allowed ({max_backlogs}).")

        # 3. Eligible Branches (case-insensitive)
        eligible_branches = criteria.get("eligible_branches")
        if eligible_branches is not None and isinstance(eligible_branches, list) and len(eligible_branches) > 0:
            branch_lower = profile.branch_code.lower()
            allowed_lower = [b.lower() for b in eligible_branches]
            if branch_lower not in allowed_lower:
                allowed_str = ", ".join(eligible_branches)
                reasons.append(f"Your branch ({profile.branch_code}) is not in the eligible branches: {allowed_str}.")

        # 4. Eligible Batch Years
        eligible_batch_years = criteria.get("eligible_batch_years")
        if eligible_batch_years is not None and isinstance(eligible_batch_years, list) and len(eligible_batch_years) > 0:
            if profile.batch_year not in eligible_batch_years:
                allowed_str = ", ".join(str(y) for y in eligible_batch_years)
                reasons.append(f"Your batch year ({profile.batch_year}) is not in the eligible batch years: {allowed_str}.")

        # 5. Gender
        gender = criteria.get("gender")
        if gender is not None:
            if not profile.gender or profile.gender.upper() != gender.upper():
                p_gender = profile.gender if profile.gender else "Not specified"
                reasons.append(f"Your gender ({p_gender}) does not match the required gender ({gender}).")

        return len(reasons) == 0, reasons

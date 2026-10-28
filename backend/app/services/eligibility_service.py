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
            try:
                if float(profile.cgpa) < float(min_cgpa):
                    reasons.append(f"Your CGPA ({profile.cgpa}) is below the minimum required CGPA ({min_cgpa}).")
            except (ValueError, TypeError):
                pass

        # 2. Maximum Active Backlogs
        max_backlogs = criteria.get("max_active_backlogs")
        if max_backlogs is None:
            max_backlogs = criteria.get("max_backlogs")
        if max_backlogs is not None:
            try:
                if int(profile.active_backlogs) > int(max_backlogs):
                    reasons.append(f"Your active backlogs ({profile.active_backlogs}) exceed the maximum allowed ({max_backlogs}).")
            except (ValueError, TypeError):
                pass

        # 3. Eligible Branches (case-insensitive)
        eligible_branches = criteria.get("eligible_branches")
        if eligible_branches is None:
            eligible_branches = criteria.get("allowed_branches")
        if eligible_branches is not None and isinstance(eligible_branches, list) and len(eligible_branches) > 0:
            branch_lower = (profile.branch_code or "").lower()
            allowed_lower = [str(b).lower() for b in eligible_branches]
            if branch_lower not in allowed_lower:
                allowed_str = ", ".join(str(b) for b in eligible_branches)
                reasons.append(f"Your branch ({profile.branch_code}) is not in the eligible branches: {allowed_str}.")

        # 4. Eligible Batch Years
        eligible_batch_years = criteria.get("eligible_batch_years")
        if eligible_batch_years is None:
            eligible_batch_years = criteria.get("batch_years")
        if eligible_batch_years is not None and isinstance(eligible_batch_years, list) and len(eligible_batch_years) > 0:
            allowed_years = [int(y) for y in eligible_batch_years if str(y).isdigit()]
            if profile.batch_year not in allowed_years:
                allowed_str = ", ".join(str(y) for y in eligible_batch_years)
                reasons.append(f"Your batch year ({profile.batch_year}) is not in the eligible batch years: {allowed_str}.")

        # 5. Gender
        gender = criteria.get("gender")
        if gender is not None and gender.strip():
            if not profile.gender or profile.gender.upper() != gender.upper():
                p_gender = profile.gender if profile.gender else "Not specified"
                reasons.append(f"Your gender ({p_gender}) does not match the required gender ({gender}).")

        return len(reasons) == 0, reasons

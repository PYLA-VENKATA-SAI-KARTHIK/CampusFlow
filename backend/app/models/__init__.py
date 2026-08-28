"""
CampusFlow — Database Models
"""
from app.models.account_activation import AccountActivation
from app.models.audit_log import AuditLog
from app.models.branch import Branch
from app.models.company import Company
from app.models.eligibility_criteria import EligibilityCriteria
from app.models.placement_drive import PlacementDrive
from app.models.refresh_token import RefreshToken
from app.models.student_profile import StudentProfile
from app.models.user import User

__all__ = [
    "AccountActivation",
    "AuditLog",
    "Branch",
    "Company",
    "EligibilityCriteria",
    "PlacementDrive",
    "RefreshToken",
    "StudentProfile",
    "User",
]

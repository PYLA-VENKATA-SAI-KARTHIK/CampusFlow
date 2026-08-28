"""
CampusFlow — Database Declarative Base

Provides the base class for all SQLAlchemy ORM models.
Ensures uniform table naming convention (snake_case).
"""
from __future__ import annotations

import re
from typing import Any

from sqlalchemy.orm import DeclarativeBase, declared_attr


class Base(DeclarativeBase):
    """
    SQLAlchemy 2.0 declarative base.
    Automatically generates table names from class names (e.g., StudentProfile -> student_profiles).
    """

    id: Any  # Subclasses must define their primary key

    @declared_attr.directive
    @classmethod
    def __tablename__(cls) -> str:
        """
        Generate table name from class name.
        Uses snake_case and appends 's' if not already present.
        Example: AccountActivation -> account_activations
        """
        name = re.sub(r"(?<!^)(?=[A-Z])", "_", cls.__name__).lower()
        if not name.endswith("s"):
            # A very simplistic pluralization for our specific schema names
            if name.endswith("y"):
                name = name[:-1] + "ies"
            elif name.endswith("h"):
                name = name + "es"
            else:
                name += "s"
        return name

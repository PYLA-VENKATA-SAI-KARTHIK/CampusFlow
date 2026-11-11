"""
CampusFlow — AI & Built-in Assessment Question Generator.
Contains 5 comprehensive sets of 15 questions each (75 questions per category = 300 questions total)
across the 4 core recruitment tracks:
  1. Aptitude & Reasoning
  2. Verbal Ability
  3. Technical Core
  4. Interview Preparation

Supports selecting a specific Set (1 to 5) or sampling a customizable count (e.g. 5, 10, 15).
"""
from __future__ import annotations

from decimal import Decimal
import random
from typing import Any

from app.services.question_banks.aptitude_sets import APTITUDE_SETS
from app.services.question_banks.interview_sets import INTERVIEW_SETS
from app.services.question_banks.technical_sets import TECHNICAL_SETS
from app.services.question_banks.verbal_sets import VERBAL_SETS

CATEGORY_MAPPINGS = {
    "aptitude": APTITUDE_SETS,
    "verbal": VERBAL_SETS,
    "technical": TECHNICAL_SETS,
    "interview": INTERVIEW_SETS,
}


def _resolve_category_key(topic: str) -> str:
    """Matches a topic string to one of the 4 categories."""
    t = topic.lower().strip()
    if any(k in t for k in ["aptitude", "reasoning", "quant", "math", "numerical", "logic"]):
        return "aptitude"
    if any(k in t for k in ["verbal", "english", "grammar", "reading", "vocabulary", "communication"]):
        return "verbal"
    if any(k in t for k in ["interview", "hr", "behavioral", "system design", "managerial", "career"]):
        return "interview"
    if any(k in t for k in ["technical", "core", "dsa", "python", "java", "sql", "dbms", "os", "network", "web"]):
        return "technical"
    # Default to technical core
    return "technical"


async def generate_assessment_mcqs(
    topic: str,
    count: int = 15,
    set_number: int | None = 1,
    difficulty: str = "MEDIUM",
) -> list[dict[str, Any]]:
    """
    Retrieves and tailors high-yield MCQs for the specified topic and set number.
    Each category contains 5 built-in sets of 15 questions each.
    """
    category_key = _resolve_category_key(topic)
    bank_sets = CATEGORY_MAPPINGS.get(category_key, TECHNICAL_SETS)

    # Determine set number (1 to 5)
    target_set = set_number if (set_number and 1 <= set_number <= 5) else 1
    selected_set = bank_sets.get(target_set) or bank_sets[1]

    # If count is requested, return exact count or full set
    if count >= len(selected_set):
        chosen = list(selected_set)
    else:
        chosen = list(selected_set[:count])

    # Format cleanly for database insertion
    formatted: list[dict[str, Any]] = []
    for item in chosen:
        formatted.append({
            "question_text": item.get("question") or item.get("question_text", ""),
            "options": item["options"],
            "correct_option": item["correct_option"],
            "explanation": item.get("explanation", ""),
            "marks": item.get("marks", Decimal("1.00")),
        })

    return formatted

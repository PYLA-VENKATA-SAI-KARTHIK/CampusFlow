import pytest
from app.services.question_generator import generate_assessment_mcqs


@pytest.mark.asyncio
async def test_generate_assessment_mcqs_count_and_keys():
    questions = await generate_assessment_mcqs(topic="Python Programming", count=5, difficulty="MEDIUM")
    assert len(questions) == 5
    for q in questions:
        assert "question_text" in q
        assert "options" in q
        assert len(q["options"]) == 4
        assert "correct_option" in q
        assert q["correct_option"] in ["A", "B", "C", "D"]
        assert "explanation" in q


@pytest.mark.asyncio
async def test_generate_assessment_mcqs_fallback():
    # Unknown topic triggers graceful generic technical generator
    questions = await generate_assessment_mcqs(topic="Quantum Robotics 101", count=3, difficulty="HARD")
    assert len(questions) == 3
    for q in questions:
        assert len(q["options"]) == 4
        assert q["correct_option"] in ["A", "B", "C", "D"]

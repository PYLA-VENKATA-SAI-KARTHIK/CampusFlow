import pytest
from app.services.question_generator import generate_assessment_mcqs


@pytest.mark.asyncio
@pytest.mark.parametrize("topic", [
    "Aptitude & Reasoning",
    "Verbal Ability",
    "Technical Core",
    "Interview Preparation"
])
@pytest.mark.parametrize("set_num", [1, 2, 3, 4, 5])
async def test_all_categories_and_sets_contain_15_questions(topic, set_num):
    questions = await generate_assessment_mcqs(topic=topic, set_number=set_num, count=15)
    assert len(questions) == 15
    for q in questions:
        assert len(q["question_text"]) > 10
        assert len(q["options"]) == 4
        assert q["correct_option"] in ["A", "B", "C", "D"]
        assert len(q["explanation"]) > 5

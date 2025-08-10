# tests/parsing/test_resume_parser.py
# --- agent_meta ---
# role: integration-test
# owner: @backend
# contract: Проверяет, что LLMResumeParser корректно связывает экстракцию PDF, промпт и структурированный ответ LLM
# last_reviewed: 2025-08-10
# dependencies: [pytest]
# --- /agent_meta ---

import pytest

from src.parsing.resume.parser import LLMResumeParser
from src.parsing.resume.pdf_extractor import IPDFExtractor, PdfPlumberExtractor
from src.parsing.llm.client import LLMClient
from src.models.resume_models import ResumeInfo, Experience, Language, Level


class _FakeExtractor(IPDFExtractor):
    def __init__(self, text: str) -> None:
        self._text = text

    def extract_text(self, src):  # type: ignore[override]
        return self._text


class _FakeLLM(LLMClient):
    async def generate_structured(self, prompt, schema, *, model_name=None, temperature=0.0, max_tokens=None):  # type: ignore[override]
        # Возвращаем детерминированный ответ на основе искусственного текста
        return ResumeInfo(
            first_name="Иван",
            last_name="Иванов",
            middle_name=None,
            title="Python Developer",
            total_experience=36,
            skills="Backend, REST, async",
            skill_set=["Python", "FastAPI", "PostgreSQL"],
            experience=[
                Experience(description="Разработка API", position="Backend Engineer", company="ACME", start="2021-01", end="2023-12")
            ],
            employments=["Полная занятость"],
            schedules=["Удаленная работа"],
            languages=[Language(name="English", level=Level(name="B2"))],
            relocation=None,
            salary=None,
            professional_roles=[],
            education=None,
            certificate=[],
            contact=[],
            site=[],
        )


@pytest.mark.asyncio
async def test_llm_resume_parser_happy_path():
    extractor = _FakeExtractor("Some resume text")
    llm = _FakeLLM()
    parser = LLMResumeParser(extractor=extractor, llm=llm)

    model = await parser.parse("/dev/null")  # путь не используется фейковым экстрактором

    assert isinstance(model, ResumeInfo)
    assert model.title == "Python Developer"
    assert "Python" in model.skill_set
    assert model.experience and model.experience[0].company == "ACME"


def test_pdf_extractor_raises_on_missing_file():
    extractor = PdfPlumberExtractor()
    with pytest.raises(FileNotFoundError):
        extractor.extract_text("/path/to/nonexistent.pdf")


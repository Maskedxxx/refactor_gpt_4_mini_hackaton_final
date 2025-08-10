# tests/parsing/test_vacancy_parser.py
# --- agent_meta ---
# role: unit-test
# owner: @backend
# contract: Проверяет парсинг вакансии по URL (извлечение id и маппинг JSON в VacancyInfo)
# last_reviewed: 2025-08-10
# dependencies: [pytest]
# --- /agent_meta ---

import pytest

from src.parsing.vacancy.parser import HHVacancyParser
from src.models.vacancy_models import VacancyInfo


class _FakeHHClient:
    async def request(self, endpoint: str, method: str = "GET", data=None, params=None):
        assert endpoint.startswith("vacancies/")
        return {
            "name": "Python Developer",
            "employer": {"name": "ООО Ромашка"},
            "description": "<p>Разработка и поддержка сервисов</p>",
            "key_skills": [{"name": "Python"}, {"name": "FastAPI"}],
            "professional_roles": [{"name": "Backend разработчик"}],
            "employment_form": {"id": "remote"},
            "experience": {"id": "between1And3"},
            "schedule": {"id": "remote"},
            "employment": {"id": "full"},
        }


@pytest.mark.asyncio
async def test_vacancy_parser_by_url_happy_path():
    parser = HHVacancyParser()
    client = _FakeHHClient()
    model = await parser.parse_by_url("https://hh.ru/vacancy/123456", client)
    assert isinstance(model, VacancyInfo)
    assert model.name == "Python Developer"
    assert model.company_name == "ООО Ромашка"
    assert model.description == "Разработка и поддержка сервисов"
    assert "Python" in model.key_skills
    assert model.professional_roles and model.professional_roles[0].name.startswith("Backend")


@pytest.mark.asyncio
async def test_vacancy_parser_invalid_url():
    parser = HHVacancyParser()
    client = _FakeHHClient()
    with pytest.raises(ValueError):
        await parser.parse_by_url("https://example.com/not-a-vacancy", client)


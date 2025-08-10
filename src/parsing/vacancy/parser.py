# src/parsing/vacancy/parser.py
# --- agent_meta ---
# role: vacancy-parser
# owner: @backend
# contract: Получение данных вакансии по ссылке HH и маппинг в VacancyInfo
# last_reviewed: 2025-08-10
# interfaces:
#   - HHVacancyParser.parse_by_url(url: str, client: HHApiClient) -> VacancyInfo
# --- /agent_meta ---

from __future__ import annotations

import re
from typing import Any

from src.hh_adapter.client import HHApiClient
from src.parsing.vacancy.mapper import map_hh_json_to_vacancy
from src.models.vacancy_models import VacancyInfo
from src.utils import get_logger


VACANCY_ID_RE = re.compile(r"(?:hh\.ru)?/vacancy/(\d+)")


class HHVacancyParser:
    """Парсер вакансии по URL HH.

    Извлекает vacancy_id из URL, получает JSON из HHApiClient,
    затем превращает его в VacancyInfo через маппер.
    """
    def __init__(self) -> None:
        self._log = get_logger(__name__)
    async def parse_by_url(self, url: str, client: HHApiClient) -> VacancyInfo:
        match = VACANCY_ID_RE.search(url)
        if not match:
            raise ValueError("Не удалось извлечь vacancy_id из URL")
        vacancy_id = match.group(1)
        self._log.info("Получение вакансии: id=%s", vacancy_id)
        data: dict[str, Any] = await client.request(f"vacancies/{vacancy_id}")
        model = map_hh_json_to_vacancy(data)
        self._log.info("Вакансия распознана: %s", model.name)
        return model

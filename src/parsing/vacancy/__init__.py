# src/parsing/vacancy/__init__.py
# --- agent_meta ---
# role: vacancy-subpackage
# owner: @backend
# contract: Подпакет парсинга вакансий
# last_reviewed: 2025-08-10
# --- /agent_meta ---

from .parser import HHVacancyParser
from .mapper import map_hh_json_to_vacancy

__all__ = [
    "HHVacancyParser",
    "map_hh_json_to_vacancy",
]


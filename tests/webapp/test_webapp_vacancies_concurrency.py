# --- agent_meta ---
# role: integration-test
# owner: @backend
# contract: Проверяет авто-refresh токена и что при конкуренции refresh вызывается ровно один раз
# last_reviewed: 2025-08-10
# dependencies: [pytest, httpx]
# --- /agent_meta ---

import asyncio
import time
from typing import List

import pytest

from src.webapp.storage import TokenStorage


@pytest.mark.asyncio
async def test_vacancies_concurrent_requests_trigger_single_refresh(monkeypatch, async_client, app_ctx):
    app_module, db_path = app_ctx

    # Предзаполняем БД истекшим access_token и валидным refresh_token
    storage = TokenStorage(db_path)
    storage.save(
        "hr_race",
        {
            "access_token": "expired",
            "refresh_token": "refresh_ok",
            "expires_at": time.time() - 10,  # уже истек
        },
    )

    # Счетчик вызовов refresh
    refresh_calls: List[int] = []

    async def fake_refresh(self):  # type: ignore[no-redef]
        # Имитация запроса к OAuth (без сети) и обновления токена
        await asyncio.sleep(0.01)
        refresh_calls.append(1)
        self._update_tokens(
            {
                "access_token": "fresh_token",
                "refresh_token": "refresh_ok",  # не меняем
                "expires_in": 3600,
            }
        )

    # Патчим низкоуровневое обновление токена у базового менеджера
    monkeypatch.setattr("src.hh_adapter.tokens.HHTokenManager._refresh_token", fake_refresh)

    # Патчим клиент HH API, чтобы он не делал внешний HTTP, но при этом приводил к получению токена
    async def fake_request(self, endpoint: str, method: str = "GET", data=None, params=None):  # type: ignore[no-redef]
        _ = await self._token_manager.get_valid_access_token()
        return {"vacancies": []}

    monkeypatch.setattr("src.hh_adapter.client.HHApiClient.request", fake_request)

    # Запускаем пачку параллельных запросов, которые приведут к гонке за refresh
    N = 20
    calls = [
        async_client.get("/vacancies", params={"hr_id": "hr_race", "text": "python"})
        for _ in range(N)
    ]
    results = await asyncio.gather(*calls)

    # Все запросы успешны
    assert all(r.status_code == 200 for r in results)
    assert all(r.json() == {"vacancies": []} for r in results)

    # Обновление токена произошло ровно один раз
    assert len(refresh_calls) == 1


# WebApp тесты (FastAPI) — кратко

Назначение: проверить, что новый модуль `src/webapp` обеспечивает корректный OAuth‑флоу, персистентное хранение токенов и устойчивость при конкурентном доступе.

Файлы
- conftest.py — фикстуры:
  - Создаёт temp SQLite и прокидывает `WEBAPP_DB_PATH`.
  - Задает тестовые `HH_CLIENT_ID/HH_CLIENT_SECRET/HH_REDIRECT_URI`.
  - Поднимает `httpx.AsyncClient` через `ASGITransport` поверх FastAPI‐приложения (без реального сервера).
- test_webapp_auth_and_storage.py — сценарии авторизации и хранения:
  - `/auth/hh/start`: редирект 302 на HH с корректными query, создание одноразового `state`.
  - `/auth/hh/callback`: мок обмена кода на токены, сохранение `access/refresh/expires_at`, редирект на `redirect_to`.
  - Неверный `state`: 400 `Invalid or expired state`.
- test_webapp_vacancies_concurrency.py — конкурентность и авто‑refresh:
  - Предзаполняем истёкший `access_token` и валидный `refresh_token` в SQLite.
  - Патчим `_refresh_token` и `HHApiClient.request` (без внешней сети).
  - 20 параллельных `/vacancies` → все успешны, refresh происходит ровно один раз (per‑HR лок + синхронизация со стором).

Запуск
- `pip install -r requirements.txt`
- `pytest -q tests/webapp`

Заметки
- Тесты не используют реальную БД из корня репозитория, а создают временную.
- TTL `state` по умолчанию 600 сек; при необходимости можно добавить тест истечения TTL (через freezegun/monkeypatch времени).
- Предупреждение pytest‑asyncio о loop scope можно устранить настройкой в `pytest.ini`.


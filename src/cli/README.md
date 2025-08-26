# src/cli/README.md
# --- agent_meta ---
# role: cli-docs
# owner: @backend
# contract: Документация по использованию CLI для запуска сценариев без фронта
# last_reviewed: 2025-08-25
# --- /agent_meta ---

## Введение

CLI позволяет запускать пользовательские сценарии поверх WebApp без UI: аутентификация, подключение HH.ru, инициализация сессий, выполнение LLM‑фич и экспорт в PDF.

Запуск:

```
python -m src.cli --help
```

Глобальные опции:
- `--base-url` (по умолчанию `http://localhost:8080`)
- `--cookies` путь к файлу cookie (по умолчанию `.hh_cli_cookies.json`)
- `--timeout` таймаут запросов (сек)
- `--no-browser` не открывать браузер для HH OAuth

## Быстрый старт

1) Запустить WebApp:
```
python -m src.webapp
```

2) Настроить демо‑пользователя:
```
python -m src.cli scenarios test-user-setup
```

3) Подключить HH аккаунт (откроется браузер):
```
python -m src.cli hh connect
```

4) Проверить статус подключения:
```
python -m src.cli hh status
```

## Сценарии

- Полный демо‑поток (если HH уже подключен):
```
python -m src.cli scenarios full-demo
```

- Фича с дедупликацией по хешу:
```
python -m src.cli scenarios feature-with-hash --feature cover_letter
```

- Фича без дедупликации (парсинг):
```
python -m src.cli scenarios feature-no-hash --feature gap_analyzer
```

## Команды

- `status` — проверка сервисов и списка фич.
- `auth signup|login|logout|me` — операции аутентификации.
- `hh status|connect|disconnect` — подключение HH через OAuth.
- `sessions init-json|init-upload` — создание сессий (JSON вход или PDF+URL).
- `features list|run` — список фич и запуск генерации.
- `pdf export` — экспорт результата фичи в PDF через маршрут
  `POST /features/{feature_name}/export/pdf`.

## Примеры

- Инициализация сессии из JSON:
```
python -m src.cli sessions init-json \
  --resume tests/data/simple_resume.json \
  --vacancy tests/data/simple_vacancy.json
```

- Запуск фичи из сессии и сохранение результата:
```
python -m src.cli features run \
  --name cover_letter \
  --session-id <uuid> \
  --out result.json
```

- Экспорт в PDF:
```
python -m src.cli pdf export \
  --feature-name cover_letter \
  --result result.json \
  --out report.pdf
```

## Примечания

- Cookie `sid` сохраняется в `.hh_cli_cookies.json` и повторно используется между командами.
- Для HH OAuth CLI выводит ссылку и, при возможности, открывает браузер. Возвращайтесь в консоль и нажмите Enter после завершения входа.
- PDF API в WebApp — `POST /features/{feature_name}/export/pdf`.


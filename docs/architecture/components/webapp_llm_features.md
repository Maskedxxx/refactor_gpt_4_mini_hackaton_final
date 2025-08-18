# WebApp: LLM Features — специфика API

Этот документ дополняет `components/webapp.md` детализированными аспектами универсального API LLM‑фич.

## Версионирование

- Версия фичи может быть указана как в теле запроса (`{"version": "v1"}`), так и в query параметре (`?version=v1`).
- Приоритет у query параметра: если указаны оба — берётся значение из query.

## Приведение опций (options)

- Для фичи `interview_checklist` опции приводятся к `InterviewChecklistOptions` (строгая валидация структуры и значений).
- Для базовых/прочих фич опции приводятся к `BaseLLMOptions`.

## Примеры вызовов Interview Checklist

С моделями непосредственно:

```bash
curl -X POST "http://localhost:8080/features/interview_checklist/generate?version=v1" \
  -H "Content-Type: application/json" \
  -d '{
    "resume": { /* ResumeInfo */ },
    "vacancy": { /* VacancyInfo */ },
    "options": { "temperature": 0.3, "language": "ru" }
  }'
```

Через session_id (рекомендуется):

```bash
curl -X POST "http://localhost:8080/features/interview_checklist/generate?version=v1" \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "<uuid>",
    "options": { "temperature": 0.3, "language": "ru" }
  }'
```

## Примечания

- В ответе помимо `result` может присутствовать `formatted_output`, если генератор поддерживает форматированный вывод.
- Ошибки поиска/регистрации фичи маппируются в коды 404/500.

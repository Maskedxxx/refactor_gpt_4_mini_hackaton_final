# src/webapp/__main__.py
# --- agent_meta ---
# role: webapp-entrypoint
# owner: @backend
# contract: Точка входа для запуска FastAPI сервиса через `python -m src.webapp`
# last_reviewed: 2025-08-10
# --- /agent_meta ---

import uvicorn


def main() -> None:
    uvicorn.run("src.webapp.app:app", host="0.0.0.0", port=8080, reload=False)


if __name__ == "__main__":
    main()

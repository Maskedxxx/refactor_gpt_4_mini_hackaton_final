# src/cli/__main__.py
# --- agent_meta ---
# role: cli-entrypoint
# owner: @backend
# contract: Точка входа для CLI `python -m src.cli`
# last_reviewed: 2025-08-25
# interfaces:
#   - python -m src.cli [args]
# --- /agent_meta ---

from __future__ import annotations

import sys
from .app import main


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))


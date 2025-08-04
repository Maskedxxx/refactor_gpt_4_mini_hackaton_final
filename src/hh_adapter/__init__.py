# src/hh_adapter/__init__.py
# --- agent_meta ---
# role: hh-adapter-public-interface
# owner: @backend
# contract: Exports the main components for interacting with the HH.ru API.
# last_reviewed: 2025-07-24
# interfaces:
#   - HHAuthService
#   - HHTokenManager
#   - HHApiClient
#   - HHSettings
# --- /agent_meta ---

"""
Public interface for the HH adapter module.

This module exports the necessary components for authenticating and interacting
with the HH.ru API.
"""

from .auth import HHAuthService
from .client import HHApiClient
from .config import HHSettings
from .tokens import HHTokenManager

__all__ = [
    "HHAuthService",
    "HHApiClient",
    "HHSettings",
    "HHTokenManager",
]

# src/cli/client.py
# --- agent_meta ---
# role: cli-http-client
# owner: @backend
# contract: Синхронный HTTP клиент для CLI с персистентными cookie (sid)
# last_reviewed: 2025-08-25
# interfaces:
#   - ApiClient(base_url, cookies_path, timeout)
#   - CookieStore(path).get(host)/set(host,value)
# --- /agent_meta ---

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Optional
from urllib.parse import urlparse

import httpx


class CookieStore:
    """Простой хранилище cookie (только sid), JSON формат.

    Структура файла:
    {
      "hosts": {
        "localhost:8080": {"sid": "..."}
      }
    }
    """

    def __init__(self, path: Path) -> None:
        self.path = path
        self._data: Dict[str, Any] = {"hosts": {}}
        self._loaded = False

    def load(self) -> None:
        if self._loaded:
            return
        if self.path.exists():
            try:
                self._data = json.loads(self.path.read_text(encoding="utf-8"))
                if not isinstance(self._data, dict) or "hosts" not in self._data:
                    self._data = {"hosts": {}}
            except Exception:
                self._data = {"hosts": {}}
        self._loaded = True

    def save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(json.dumps(self._data, ensure_ascii=False, indent=2), encoding="utf-8")

    def _key(self, host_with_port: str) -> str:
        return host_with_port

    def get_sid(self, host_with_port: str) -> Optional[str]:
        self.load()
        return self._data.get("hosts", {}).get(self._key(host_with_port), {}).get("sid")

    def set_sid(self, host_with_port: str, sid: Optional[str]) -> None:
        self.load()
        hosts = self._data.setdefault("hosts", {})
        entry = hosts.setdefault(self._key(host_with_port), {})
        if sid is None:
            entry.pop("sid", None)
        else:
            entry["sid"] = sid
        self.save()


@dataclass
class ApiClient:
    """HTTP клиент для CLI с персистентной cookie 'sid'."""

    base_url: str
    cookies_path: Path
    timeout: float = 600.0  # 10 минут для длительных операций (interview_simulation)

    def __post_init__(self) -> None:
        self.store = CookieStore(self.cookies_path)
        self.host_with_port = self._extract_host_with_port(self.base_url)
        self.client = self._build_client()

    def _extract_host_with_port(self, url: str) -> str:
        p = urlparse(url)
        host = p.hostname or "localhost"
        port = p.port
        return f"{host}:{port}" if port else host

    def _build_client(self) -> httpx.Client:
        sid = self.store.get_sid(self.host_with_port)
        cookies = httpx.Cookies()
        if sid:
            # Доменные атрибуты не критичны для локальных запросов
            cookies.set("sid", sid)
        return httpx.Client(base_url=self.base_url, timeout=self.timeout, follow_redirects=True, cookies=cookies)

    def close(self) -> None:
        try:
            self.client.close()
        except Exception:
            pass

    # --- helpers ---
    def _update_sid_from_response(self, resp: httpx.Response) -> None:
        # Если сервер выставил новую cookie sid — сохраним
        sid = resp.cookies.get("sid")
        if sid:
            self.store.set_sid(self.host_with_port, sid)
            # Обновим клиентский jar
            self.client.cookies.set("sid", sid)

    # --- HTTP methods ---
    def get(self, path: str, params: Optional[Dict[str, Any]] = None) -> httpx.Response:
        resp = self.client.get(path, params=params)
        self._update_sid_from_response(resp)
        return resp

    def post_json(self, path: str, json_body: Dict[str, Any]) -> httpx.Response:
        resp = self.client.post(path, json=json_body)
        self._update_sid_from_response(resp)
        return resp

    def post_form(self, path: str, data: Dict[str, Any], files: Optional[Dict[str, Any]] = None, timeout: Optional[float] = None) -> httpx.Response:
        resp = self.client.post(path, data=data, files=files, timeout=timeout)
        self._update_sid_from_response(resp)
        return resp

    # --- auth helpers ---
    def clear_sid(self) -> None:
        self.store.set_sid(self.host_with_port, None)
        try:
            self.client.cookies.delete("sid")
        except Exception:
            pass


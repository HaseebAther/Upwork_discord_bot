"""
Single browser refresh for all Upwork fetches.

- One global lock so parallel keyword polls never spawn multiple SeleniumBase sessions.
- Merges tokens/cookies into the shared capture dict and optionally persists to data/cookies.py.
"""

from __future__ import annotations

import threading
from pathlib import Path
from typing import Any

from src.auth.seleniumbase_session import refresh_cookies_with_seleniumbase
from src.upwork.capture_loader import load_capture_dicts
from src.upwork.capture_persist import save_capture_to_py_file

DEFAULT_REFRESH_SEARCH_URL = "https://www.upwork.com/nx/search/jobs/"

_refresh_lock = threading.Lock()


def merge_refresh_into_capture(capture: dict[str, Any], refreshed: dict[str, Any]) -> None:
    """
    Merge SeleniumBase refresh payload into capture (mutates capture).

    `refreshed` contains cookie-name keys plus optional ``token`` for Authorization.
    """
    if not refreshed:
        return

    cookies: dict[str, Any] = dict(capture.get("cookies") or {})
    headers: dict[str, Any] = dict(capture.get("headers") or {})

    token = refreshed.get("token")
    for key, value in refreshed.items():
        if key == "token" or value is None or value == "":
            continue
        cookies[str(key)] = str(value)

    if token:
        t = str(token).strip()
        if t.lower().startswith("bearer "):
            t = t[7:].strip()
        headers = {
            k: v
            for k, v in headers.items()
            if str(k).lower() != "authorization"
        }
        headers["Authorization"] = f"Bearer {t}"

    capture["cookies"] = cookies
    capture["headers"] = headers


def locked_refresh_merge_persist(
    capture: dict[str, Any],
    capture_path: Path | None,
    search_url: str = DEFAULT_REFRESH_SEARCH_URL,
) -> bool:
    """
    Under a process-wide lock: run one browser refresh, merge into ``capture``,
    and save to ``capture_path`` when provided. Returns True on success.
    """
    with _refresh_lock:
        refreshed = refresh_cookies_with_seleniumbase(search_url)
        if not refreshed:
            return False
        merge_refresh_into_capture(capture, refreshed)
        if capture_path is not None:
            save_capture_to_py_file(capture_path, capture)
        return True


def refresh_capture_file(
    capture_path: Path,
    search_url: str = DEFAULT_REFRESH_SEARCH_URL,
) -> bool:
    """Load capture from disk, refresh once, merge, save. For scheduled maintenance."""
    capture = load_capture_dicts(capture_path)
    return locked_refresh_merge_persist(capture, capture_path, search_url)

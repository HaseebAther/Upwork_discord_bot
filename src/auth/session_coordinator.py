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


def _is_useful_cookie(name: str, value: str) -> bool:
    """Keep auth/session cookies and drop noisy telemetry/ads cookies."""
    n = (name or "").strip()
    if not n:
        return False
    v = (value or "").strip()
    if not v:
        return False
    if len(v) > 1200:
        return False

    lower = n.lower()
    blocked_markers = (
        "snowplow",
        "_vwo",
        "analytics",
        "guest_id",
        "personalization",
        "forter",
        "ttcsid",
        "_ttp",
        "_ga",
        "_fbp",
        "muid",
        "bcookie",
        "li_",
        "optanon",
    )
    if any(marker in lower for marker in blocked_markers):
        return False

    allow_exact = {
        "cf_clearance",
        "__cf_bm",
        "visitor_gql_token",
        "UniversalSearchNuxt_vt",
        "XSRF-TOKEN",
        "odesk_csrf_token",
        "oauth2_global_js_token",
        "country_code",
        "visitor_id",
        "x-spec-id",
    }
    if n in allow_exact:
        return True

    allow_prefixes = (
        "_upw_ses",
        "_upw_id",
        "oauth2v2_",
        "oauth2_",
    )
    return any(n.startswith(prefix) for prefix in allow_prefixes)


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
    cookie_names = refreshed.get("_cookie_names")
    if isinstance(cookie_names, list) and cookie_names:
        # Strict mode: only merge keys that came from browser cookies.
        for key in cookie_names:
            if key in refreshed and refreshed.get(key):
                cookie_key = str(key)
                cookie_val = str(refreshed.get(key))
                if _is_useful_cookie(cookie_key, cookie_val):
                    cookies[cookie_key] = cookie_val
    else:
        # Backward-compatible fallback for older refresh payloads.
        for key, value in refreshed.items():
            if key in {"token", "_cookie_names"} or value is None or value == "":
                continue
            cookie_key = str(key)
            cookie_val = str(value)
            if _is_useful_cookie(cookie_key, cookie_val):
                cookies[cookie_key] = cookie_val

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

import json
import os
import time
from typing import Any

TOKEN_PREFIX = "oauth2v2_int_"
TOKEN_TTL_SECONDS = 10 * 60 * 60


def extract_bearer_cookie_metadata(cookies: list[dict[str, Any]]) -> dict[str, Any]:
    for cookie in cookies:
        name = str(cookie.get("name", ""))
        if name.startswith(TOKEN_PREFIX):
            return {
                "token": name[len(TOKEN_PREFIX):],
                "cookie_name": name,
                "expires": cookie.get("expires"),
                "domain": cookie.get("domain"),
                "path": cookie.get("path"),
            }
    return {
        "token": "",
        "cookie_name": "",
        "expires": None,
        "domain": "",
        "path": "",
    }

def extract_bearer_token_from_cookies(cookies: list[dict[str, Any]]) -> str:
    return str(extract_bearer_cookie_metadata(cookies).get("token", ""))


def extract_important_cookie_values(cookies: list[dict[str, Any]]) -> dict[str, str]:
    wanted = {
        "cf_clearance",
        "__cf_bm",
        "XSRF-TOKEN",
        "odesk_csrf_token",
        "_upwork_t",
        "visitor_id",
        "upwork_visitor",
        "oauth2_global_js_token",
    }
    out: dict[str, str] = {}
    for cookie in cookies:
        name = str(cookie.get("name", ""))
        value = str(cookie.get("value", ""))
        if name in wanted:
            out[name] = value
        if name.startswith(TOKEN_PREFIX):
            out[name] = value
    return out


def load_state(state_file: str) -> dict[str, Any]:
    if not os.path.exists(state_file):
        return {}
    with open(state_file, "r", encoding="utf-8") as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return {}


def save_state(state_file: str, state: dict[str, Any]) -> None:
    os.makedirs(os.path.dirname(state_file), exist_ok=True)
    with open(state_file, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=2)


def is_token_expired(state: dict[str, Any]) -> bool:
    issued_at = state.get("token_issued_at", 0)
    return (time.time() - issued_at) >= TOKEN_TTL_SECONDS

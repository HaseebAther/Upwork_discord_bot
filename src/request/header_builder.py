from typing import Any

def build_headers(bearer_token: str, xsrf_token: str) -> dict[str, str]:
    headers = {
        "accept": "application/json",
        "content-type": "application/json",
        "origin": "https://www.upwork.com",
        "referer": "https://www.upwork.com/nx/jobs/search/",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    }

    if bearer_token:
        headers["authorization"] = f"Bearer {bearer_token}"
    if xsrf_token:
        headers["x-odesk-csrf-token"] = xsrf_token

    return headers


def extract_xsrf_from_cookies(cookies: list[dict[str, Any]]) -> str:
    for cookie in cookies:
        if cookie.get("name") in {"XSRF-TOKEN", "odesk_csrf_token", "_upwork_t"}:
            return str(cookie.get("value", ""))
    return ""


def build_cookie_header(cookies: list[dict[str, Any]]) -> str:
    pairs: list[str] = []
    for cookie in cookies:
        name = str(cookie.get("name", "")).strip()
        value = str(cookie.get("value", "")).strip()
        if not name:
            continue
        pairs.append(f"{name}={value}")
    return "; ".join(pairs)

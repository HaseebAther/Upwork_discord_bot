from dataclasses import dataclass
from pathlib import Path

import cloudscraper
import requests

from src.auth.playwright_session import refresh_cookies_with_playwright
from src.auth.seleniumbase_session import refresh_cookies_with_seleniumbase
from src.upwork.capture_loader import load_capture_dicts


@dataclass
class FetchResult:
    status_code: int
    client_used: str
    response_text: str
    body: dict | None


def best_auth_token(cookies: dict, headers: dict) -> str | None:
    token_candidates = []
    auth_header = str(headers.get("authorization", ""))
    if auth_header.lower().startswith("bearer "):
        token_candidates.append(auth_header.split(" ", 1)[1].strip())

    token_candidates.extend([
        cookies.get("UniversalSearchNuxt_vt"),
        cookies.get("visitor_gql_token"),
    ])

    for token in token_candidates:
        if isinstance(token, str) and token.startswith("oauth2v2_"):
            return token
    return None


def normalize_headers(cookies: dict, headers: dict, visitor_mode: bool) -> dict:
    normalized = {str(k).lower(): str(v) for k, v in headers.items()}

    for key in (
        "authority",
        "method",
        "path",
        "scheme",
        "vnd-eo-parent-span-id",
        "vnd-eo-span-id",
        "vnd-eo-trace-id",
    ):
        normalized.pop(key, None)

    token = best_auth_token(cookies, normalized)
    if visitor_mode:
        normalized.pop("authorization", None)
    elif token:
        normalized["authorization"] = f"Bearer {token}"

    return normalized


def to_visitor_session(cookies: dict, headers: dict) -> tuple[dict, dict]:
    auth_cookie_prefixes = (
        "oauth",
        "_upw_ses",
        "_upw_id",
        "recognized",
        "company_last_accessed",
    )

    visitor_cookies = {
        str(k): v
        for k, v in cookies.items()
        if not str(k).lower().startswith(auth_cookie_prefixes)
    }

    visitor_headers = {str(k).lower(): str(v) for k, v in headers.items()}
    visitor_headers.pop("authorization", None)

    allowed_headers = {
        "accept",
        "accept-language",
        "content-type",
        "origin",
        "referer",
        "sec-fetch-dest",
        "sec-fetch-mode",
        "sec-fetch-site",
        "user-agent",
        "x-upwork-accept-language",
        "x-odesk-csrf-token",
    }
    visitor_headers = {k: v for k, v in visitor_headers.items() if k in allowed_headers}

    return visitor_cookies, visitor_headers


def post_with_requests(url: str, params: dict, cookies: dict, headers: dict, payload: dict) -> requests.Response:
    return requests.post(url, params=params, cookies=cookies, headers=headers, json=payload, timeout=40)


def post_with_cloudscraper(url: str, params: dict, cookies: dict, headers: dict, payload: dict) -> requests.Response:
    scraper = cloudscraper.create_scraper(browser={"browser": "chrome", "platform": "windows", "mobile": False})
    return scraper.post(url, params=params, cookies=cookies, headers=headers, json=payload, timeout=40)


def is_cloudflare_challenge(response: requests.Response) -> bool:
    if response.status_code != 403:
        return False
    preview = response.text[:1200].lower()
    return "challenge - upwork" in preview or "cf-challenge" in preview or "cloudflare" in preview


def merge_cookie_updates(base: dict, updates: dict) -> dict:
    merged = dict(base)
    for key, value in updates.items():
        if value:
            merged[key] = value
    return merged


def fetch_once(
    capture_file: Path,
    upwork_url: str,
    visitor_mode: bool = False,
    use_playwright_on_403: bool = True,
    use_seleniumbase_on_403: bool = True,
) -> FetchResult:
    data = load_capture_dicts(capture_file)
    cookies = data.get("cookies", {})
    headers = data.get("headers", {})
    params = data.get("params", {})
    payload = data.get("json_data", {})

    if not cookies or not payload:
        return FetchResult(
            status_code=0,
            client_used="none",
            response_text="Capture is incomplete. Need cookies + json_data at minimum.",
            body=None,
        )

    headers = normalize_headers(cookies, headers, visitor_mode)
    if visitor_mode:
        cookies, headers = to_visitor_session(cookies, headers)

    response = post_with_cloudscraper(upwork_url, params, cookies, headers, payload)
    client_used = "cloudscraper"

    if is_cloudflare_challenge(response):
        if use_playwright_on_403:
            refreshed = refresh_cookies_with_playwright("https://www.upwork.com/nx/search/jobs/")
            if refreshed:
                cookies = merge_cookie_updates(cookies, refreshed)
                response = post_with_cloudscraper(upwork_url, params, cookies, headers, payload)
                client_used = "cloudscraper+playwright-retry"

        if use_seleniumbase_on_403 and is_cloudflare_challenge(response):
            refreshed = refresh_cookies_with_seleniumbase("https://www.upwork.com/nx/search/jobs/")
            if refreshed:
                cookies = merge_cookie_updates(cookies, refreshed)
                response = post_with_cloudscraper(upwork_url, params, cookies, headers, payload)
                client_used = "cloudscraper+seleniumbase-retry"

    if response.status_code in {408, 502, 503, 504}:
        response = post_with_requests(upwork_url, params, cookies, headers, payload)
        client_used = "requests"

    try:
        body = response.json() if response.status_code == 200 else None
    except ValueError:
        body = None

    return FetchResult(
        status_code=response.status_code,
        client_used=client_used,
        response_text=response.text,
        body=body,
    )

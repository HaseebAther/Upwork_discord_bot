from dataclasses import dataclass
from pathlib import Path

import cloudscraper
import requests

from src.auth.seleniumbase_session import refresh_cookies_with_seleniumbase
from src.upwork.capture_loader import load_capture_dicts


@dataclass
class FetchResult:
    status_code: int
    client_used: str
    response_text: str
    body: dict | None

#dynamic Allocation of Search QUERY 
def apply_query_override(payload: dict, user_query: str | None) -> dict:
    if not user_query:
        return payload

    updated = dict(payload)
    variables = dict(updated.get("variables", {}))
    request_variables = dict(variables.get("requestVariables", {}))
    request_variables["userQuery"] = user_query
    variables["requestVariables"] = request_variables
    updated["variables"] = variables
    return updated


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


def safe_post_with_cloudscraper(url: str, params: dict, cookies: dict, headers: dict, payload: dict) -> tuple[requests.Response | None, str | None]:
    try:
        return post_with_cloudscraper(url, params, cookies, headers, payload), None
    except requests.RequestException as exc:
        return None, f"cloudscraper request failed: {exc}"


def safe_post_with_requests(url: str, params: dict, cookies: dict, headers: dict, payload: dict) -> tuple[requests.Response | None, str | None]:
    try:
        return post_with_requests(url, params, cookies, headers, payload), None
    except requests.RequestException as exc:
        return None, f"requests fallback failed: {exc}"


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
    user_query: str | None = None,
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

    payload = apply_query_override(payload, user_query)

    headers = normalize_headers(cookies, headers, visitor_mode)
    if visitor_mode:
        cookies, headers = to_visitor_session(cookies, headers)

    response, error = safe_post_with_cloudscraper(upwork_url, params, cookies, headers, payload)
    client_used = "cloudscraper"

    if response is None:
        fallback_response, fallback_error = safe_post_with_requests(upwork_url, params, cookies, headers, payload)
        if fallback_response is None:
            return FetchResult(
                status_code=0,
                client_used="none",
                response_text=f"{error}\n{fallback_error}",
                body=None,
            )
        response = fallback_response
        client_used = "requests"

    if is_cloudflare_challenge(response):
        if use_seleniumbase_on_403:
            refreshed = refresh_cookies_with_seleniumbase("https://www.upwork.com/nx/search/jobs/")
            if refreshed:
                cookies = merge_cookie_updates(cookies, refreshed)
                # After refresh, re-align headers with new cookies
                headers = normalize_headers(cookies, headers, visitor_mode)
                retried, retry_error = safe_post_with_cloudscraper(upwork_url, params, cookies, headers, payload)
                if retried is not None:
                    response = retried
                    client_used = "cloudscraper+seleniumbase-retry"
                else:
                    return FetchResult(
                        status_code=0,
                        client_used="cloudscraper+seleniumbase-retry",
                        response_text=retry_error or "cloudscraper retry failed",
                        body=None,
                    )

    if response.status_code in {408, 502, 503, 504}:
        fallback_response, fallback_error = safe_post_with_requests(upwork_url, params, cookies, headers, payload)
        if fallback_response is None:
            return FetchResult(
                status_code=0,
                client_used="requests",
                response_text=fallback_error or "requests fallback failed",
                body=None,
            )
        response = fallback_response
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


def build_search_url(query: str | None = None) -> str:
    """Build Upwork job search URL for browser navigation."""
    base_url = "https://www.upwork.com/nx/search/jobs/"
    if query:
        return f"{base_url}?q={query.replace(' ', '+')}"
    return base_url


def fetch_from_capture_data(
    capture_data: dict,
    upwork_url: str,
    user_query: str | None = None,
    visitor_mode: bool = False,
    use_seleniumbase_on_403: bool = True,
) -> FetchResult:
    """
    Fetch jobs from capture data dict (used by polling loop).
    Wrapper around fetch_once() that accepts pre-loaded capture data.
    """
    cookies = capture_data.get("cookies", {})
    headers = capture_data.get("headers", {})
    params = capture_data.get("params", {})
    payload = capture_data.get("json_data", {})

    if not cookies or not payload:
        return FetchResult(
            status_code=0,
            client_used="none",
            response_text="Capture data incomplete. Need cookies + json_data.",
            body=None,
        )

    payload = apply_query_override(payload, user_query)
    headers = normalize_headers(cookies, headers, visitor_mode)
    
    if visitor_mode:
        cookies, headers = to_visitor_session(cookies, headers)

    response, error = safe_post_with_cloudscraper(upwork_url, params, cookies, headers, payload)
    client_used = "cloudscraper"

    if response is None:
        fallback_response, fallback_error = safe_post_with_requests(upwork_url, params, cookies, headers, payload)
        if fallback_response is None:
            return FetchResult(
                status_code=0,
                client_used="none",
                response_text=f"{error}\n{fallback_error}",
                body=None,
            )
        response = fallback_response
        client_used = "requests"

    if is_cloudflare_challenge(response):

        if use_seleniumbase_on_403 and is_cloudflare_challenge(response):
            refreshed = refresh_cookies_with_seleniumbase("https://www.upwork.com/nx/search/jobs/")
            if refreshed:
                cookies = merge_cookie_updates(cookies, refreshed)
                retried, retry_error = safe_post_with_cloudscraper(upwork_url, params, cookies, headers, payload)
                if retried is not None:
                    response = retried
                    client_used = "cloudscraper+seleniumbase-retry"

    if response.status_code in {408, 502, 503, 504}:
        fallback_response, fallback_error = safe_post_with_requests(upwork_url, params, cookies, headers, payload)
        if fallback_response is None:
            return FetchResult(
                status_code=0,
                client_used="requests",
                response_text=fallback_error or "requests fallback failed",
                body=None,
            )
        response = fallback_response
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

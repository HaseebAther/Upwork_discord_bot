"""SeleniumBase helpers for one-time Cloudflare/session cookie refresh."""

from __future__ import annotations

import time
from urllib.parse import urlencode
from typing import Dict


def post_graphql_with_seleniumbase(
    graphql_url: str,
    params: dict,
    payload: dict,
    search_url: str,
    timeout_seconds: int = 35,
) -> tuple[int, str]:
    """Run GraphQL POST from a real browser context after opening Upwork pages."""
    try:
        from seleniumbase import SB
    except Exception as exc:
        return 0, f"SeleniumBase not available: {exc}"

    full_url = graphql_url
    if params:
        query = urlencode({str(k): str(v) for k, v in params.items()}, doseq=True)
        if query:
            full_url = f"{graphql_url}?{query}"

    try:
        with SB(uc=True, headless=True) as sb:
            sb.open(search_url)
            sb.wait_for_element_present("body", timeout=timeout_seconds)
            sb.open("https://www.upwork.com/")
            sb.wait_for_element_present("body", timeout=timeout_seconds)
            sb.sleep(1)

            result = sb.execute_script(
                """
                const url = arguments[0];
                const body = arguments[1];
                const xhr = new XMLHttpRequest();
                xhr.open('POST', url, false);
                xhr.setRequestHeader('accept', '*/*');
                xhr.setRequestHeader('content-type', 'application/json');
                xhr.send(JSON.stringify(body));
                return {status: xhr.status, text: xhr.responseText || ''};
                """,
                full_url,
                payload,
            )

            if isinstance(result, dict):
                status = int(result.get("status", 0) or 0)
                text = str(result.get("text", "") or "")
                return status, text
            return 0, "Unexpected browser script result"
    except BaseException as exc:
        return 0, f"SeleniumBase browser post failed: {exc}"


def refresh_cookies_with_seleniumbase(url: str, timeout_seconds: int = 40) -> Dict[str, str]:
    """
    Open browser with SeleniumBase, visit homepage + search page, extract cookies + tokens from storage.
    Extract tokens from localStorage/sessionStorage (where Upwork stores real bearer token).
    """
    try:
        from seleniumbase import SB
    except Exception as exc:
        print(f"SeleniumBase not available: {exc}")
        return {}

    result = {}
    try:
        # uc=True uses undetected-chromedriver. headless=False for debugging visibility.
        with SB(uc=True, headless=False) as sb:
            # Step 1: Visit homepage first to initialize session
            print("[1] Visiting Upwork homepage...")
            sb.open("https://www.upwork.com/")
            sb.sleep(3)

            # Step 2: Visit job search to trigger token generation
            print("[2] Visiting job search page...")
            sb.open(url)
            sb.sleep(5)

            # Step 3: Poll for token up to 40 seconds (they check localStorage/sessionStorage!)
            print("[3] Polling for tokens in browser storage...")
            token = None
            for poll_iter in range(timeout_seconds):
                try:
                    # Extract from localStorage
                    local_storage = sb.execute_script(
                        "return Object.assign({}, window.localStorage);"
                    ) or {}
                    # Extract from sessionStorage
                    session_storage = sb.execute_script(
                        "return Object.assign({}, window.sessionStorage);"
                    ) or {}
                except Exception:
                    local_storage = {}
                    session_storage = {}

                # Get cookies
                browser_cookies = sb.get_cookies()
                cookie_map = {c["name"]: c["value"] for c in browser_cookies}

                # Extract token from all sources
                token = _extract_token_from_storage(local_storage, session_storage, cookie_map)
                if token:
                    print(f"[✓] Token found after {poll_iter + 1} seconds")
                    result["token"] = token
                    result["cookies"] = browser_cookies
                    break

                sb.sleep(1)

            # Step 4: If token not found, retry with different search query
            if not token:
                print("[4] Token not found in first pass, trying alternate search...")
                sb.open("https://www.upwork.com/nx/search/jobs/?q=python&sort=recency")
                sb.sleep(4)

                for poll_iter in range(20):
                    try:
                        local_storage = sb.execute_script(
                            "return Object.assign({}, window.localStorage);"
                        ) or {}
                        session_storage = sb.execute_script(
                            "return Object.assign({}, window.sessionStorage);"
                        ) or {}
                    except Exception:
                        local_storage = {}
                        session_storage = {}

                    browser_cookies = sb.get_cookies()
                    cookie_map = {c["name"]: c["value"] for c in browser_cookies}

                    token = _extract_token_from_storage(local_storage, session_storage, cookie_map)
                    if token:
                        print(f"[✓] Token found on retry after {poll_iter + 1} seconds")
                        result["token"] = token
                        result["cookies"] = browser_cookies
                        break
                    sb.sleep(1)

            if not token:
                print("[-] Token not found after all attempts")
                return {}

            # Build final result dict with cookies
            for item in result.get("cookies", []):
                name = item.get("name")
                value = item.get("value")
                if name and value:
                    result[str(name)] = str(value)

    except BaseException as exc:
        print(f"SeleniumBase refresh failed: {exc}")
        return {}

    key_names = ["cf_clearance", "__cf_bm", "visitor_gql_token", "UniversalSearchNuxt_vt", "XSRF-TOKEN"]
    present = [name for name in key_names if name in result]
    print(f"SeleniumBase captured {len(result)} items; key cookies present: {present}")
    return result


def _extract_token_from_storage(local_storage: dict, session_storage: dict, cookie_map: dict) -> str | None:
    """Extract bearer token from localStorage, sessionStorage, or cookies (in priority order)."""
    
    # Priority token keys to check
    priority_keys = [
        "oauth2_global_js_token",
        "oauth2v2_global_js_token",
        "visitor_gql_token",
        "visitor_token",
        "UniversalSearchNuxt_vt",
    ]

    # Check each key in priority order
    for key in priority_keys:
        for store in (local_storage, session_storage):
            val = store.get(key)
            if val:
                print(f"  [Token] Found in {key}")
                return str(val).strip().strip('"').strip("'")

    # Fuzzy scan for JWT-like tokens
    for store in (local_storage, session_storage):
        for k, v in store.items():
            if not v:
                continue
            s = str(v)
            if (s.startswith("oauth2v2_") or s.startswith("eyJ") and len(s) > 100):
                print(f"  [Token] Found via fuzzy scan: {k}")
                return s

    # Check cookies as fallback
    for cookie_key in ("oauth2_global_js_token", "UniversalSearchNuxt_vt", "visitor_gql_token"):
        val = cookie_map.get(cookie_key)
        if val:
            print(f"  [Token] Found in cookie: {cookie_key}")
            return val

    return None

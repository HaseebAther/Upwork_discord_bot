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

    result: Dict[str, str] = {}

    def collect_browser_cookies(sb) -> list[dict]:
        """
        Collect the broadest cookie set available:
        1) selenium get_cookies() for current context
        2) CDP Network.getAllCookies() for full browser jar (includes httpOnly/path/domain scoped cookies)
        """
        merged: dict[tuple[str, str, str], dict] = {}

        try:
            for c in sb.get_cookies() or []:
                key = (str(c.get("name", "")), str(c.get("domain", "")), str(c.get("path", "/")))
                merged[key] = c
        except Exception:
            pass

        try:
            # Ensure cookie domain contexts are warmed.
            sb.open("https://www.upwork.com/")
            sb.sleep(1)
            cdp_res = sb.driver.execute_cdp_cmd("Network.getAllCookies", {})
            for c in (cdp_res or {}).get("cookies", []):
                normalized = {
                    "name": c.get("name"),
                    "value": c.get("value"),
                    "domain": c.get("domain"),
                    "path": c.get("path", "/"),
                    "secure": c.get("secure"),
                    "httpOnly": c.get("httpOnly"),
                    "expires": c.get("expires"),
                }
                key = (
                    str(normalized.get("name", "")),
                    str(normalized.get("domain", "")),
                    str(normalized.get("path", "/")),
                )
                merged[key] = normalized
        except Exception:
            pass

        return list(merged.values())

    def merge_storage_candidates(local_storage: dict, session_storage: dict) -> None:
        """
        Capture potentially relevant auth/session values from browser storage.
        We keep keys that commonly contain auth/session tokens and also token-like values.
        """
        for store in (local_storage or {}, session_storage or {}):
            if not isinstance(store, dict):
                continue
            for key, value in store.items():
                k = str(key or "").strip()
                if not k:
                    continue
                v = str(value or "").strip()
                if not v:
                    continue
                k_lower = k.lower()
                looks_relevant_key = any(
                    marker in k_lower
                    for marker in ("token", "oauth", "visitor", "xsrf", "csrf", "nuxt", "upwork")
                )
                looks_relevant_value = (
                    v.startswith("oauth2v2_")
                    or v.startswith("oauth2v2_int_")
                    or (v.startswith("eyJ") and len(v) > 60)
                )
                if looks_relevant_key or looks_relevant_value:
                    result[k] = v
    try:
        # uc=True uses undetected-chromedriver. headless=True for background operation (no visible window)
        with SB(uc=True, headless=True) as sb:
            # Step 1: Visit homepage first to initialize session
            print("[1] Visiting Upwork homepage...")
            sb.open("https://www.upwork.com/")
            sb.sleep(2)

            # Step 2: Visit job search to trigger token generation
            print("[2] Visiting job search page...")
            sb.open(url)
            sb.sleep(3)

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
                browser_cookies = collect_browser_cookies(sb)
                cookie_map = {c["name"]: c["value"] for c in browser_cookies}

                # Keep additional storage tokens/keys for session completeness
                merge_storage_candidates(local_storage, session_storage)

                # Extract primary token from all sources
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
                sb.sleep(2)

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

                    browser_cookies = collect_browser_cookies(sb)
                    cookie_map = {c["name"]: c["value"] for c in browser_cookies}

                    merge_storage_candidates(local_storage, session_storage)
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
            cookie_names: list[str] = []
            for item in result.get("cookies", []):
                name = item.get("name")
                value = item.get("value")
                if name and value:
                    cookie_name = str(name)
                    result[cookie_name] = str(value)
                    cookie_names.append(cookie_name)
            # Used by merge layer to avoid treating storage keys as cookies.
            result["_cookie_names"] = cookie_names
            
            # Remove the raw cookies list after extracting individual cookies
            if "cookies" in result:
                del result["cookies"]

    except BaseException as exc:
        print(f"SeleniumBase refresh failed: {exc}")
        return {}

    key_names = ["cf_clearance", "__cf_bm", "visitor_gql_token", "UniversalSearchNuxt_vt", "XSRF-TOKEN"]
    present = [name for name in key_names if name in result]
    print(f"SeleniumBase captured {len(result)} items; key cookies/tokens present: {present}")
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

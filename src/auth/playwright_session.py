"""Playwright helpers for one-time Cloudflare/session cookie refresh."""

from __future__ import annotations

from typing import Dict


def refresh_cookies_with_playwright(url: str, timeout_seconds: int = 25) -> Dict[str, str]:
    """
    Open a Playwright Chromium session and return cookies from that browser context.

    Use this only as 403 recovery. Do not call on every polling cycle.
    """
    try:
        from playwright.sync_api import sync_playwright
    except Exception as exc:
        print(f"Playwright not available: {exc}")
        return {}

    cookies: Dict[str, str] = {}
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(
                user_agent=(
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/146.0.0.0 Safari/537.36"
                )
            )
            page = context.new_page()
            page.goto(url, timeout=timeout_seconds * 1000, wait_until="domcontentloaded")
            page.wait_for_timeout(3500)
            for item in context.cookies():
                name = item.get("name")
                value = item.get("value")
                if name and value:
                    cookies[str(name)] = str(value)
            context.close()
            browser.close()
    except BaseException as exc:
        print(f"Playwright refresh failed (non-fatal): {exc}")
        return {}

    print(f"Playwright captured {len(cookies)} cookies")
    return cookies

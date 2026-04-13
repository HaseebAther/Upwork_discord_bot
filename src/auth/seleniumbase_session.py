"""SeleniumBase helpers for one-time Cloudflare/session cookie refresh."""

from __future__ import annotations

from typing import Dict


def refresh_cookies_with_seleniumbase(url: str, timeout_seconds: int = 25) -> Dict[str, str]:
    """
    Open a real browser context with SeleniumBase and return cookies from that session.

    Use this only as 403 recovery. Do not call on every polling cycle.
    """
    try:
        from seleniumbase import SB
    except Exception as exc:
        print(f"SeleniumBase not available: {exc}")
        return {}

    cookies: Dict[str, str] = {}
    try:
        # uc=True uses undetected-chromedriver mode for tougher anti-bot pages.
        with SB(uc=True, headless=True) as sb:
            sb.open(url)
            sb.sleep(4)
            sb.wait_for_element_present("body", timeout=timeout_seconds)
            for item in sb.driver.get_cookies():
                name = item.get("name")
                value = item.get("value")
                if name and value:
                    cookies[str(name)] = str(value)
    except BaseException as exc:
        print(f"SeleniumBase refresh failed (non-fatal): {exc}")
        return {}

    print(f"SeleniumBase captured {len(cookies)} cookies")
    return cookies

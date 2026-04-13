from src.auth.cookie_store import load_cookies
from src.auth.token_manager import extract_bearer_token_from_cookies
from src.request.header_builder import build_headers, extract_xsrf_from_cookies


def mask(value: str, keep: int = 8) -> str:
    if not value:
        return ""
    if len(value) <= keep * 2:
        return "*" * len(value)
    return f"{value[:keep]}...{value[-keep:]}"


def main() -> None:
    cookies_file = "data/cookies.json"
    cookies = load_cookies(cookies_file)

    bearer_token = extract_bearer_token_from_cookies(cookies)
    xsrf_token = extract_xsrf_from_cookies(cookies)
    headers = build_headers(bearer_token=bearer_token, xsrf_token=xsrf_token)

    print("=== Module 1: Auth Check ===")
    print(f"Cookies file: {cookies_file}")
    print(f"Cookies loaded: {len(cookies)}")
    print(f"Bearer token found: {bool(bearer_token)}")
    print(f"XSRF token found: {bool(xsrf_token)}")

    if bearer_token:
        print(f"Bearer token (masked): {mask(bearer_token)}")
    if xsrf_token:
        print(f"XSRF token (masked): {mask(xsrf_token)}")

    print("\nHeader preview:")
    for key in ("accept", "content-type", "origin", "referer", "authorization", "x-odesk-csrf-token"):
        if key in headers:
            val = headers[key]
            if key in {"authorization", "x-odesk-csrf-token"}:
                val = mask(val)
            print(f"- {key}: {val}")


if __name__ == "__main__":
    main()

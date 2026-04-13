import json

from src.auth.cookie_store import load_cookies
from src.auth.token_manager import (
    extract_bearer_cookie_metadata,
    extract_important_cookie_values,
)
from src.request.header_builder import (
    build_cookie_header,
    build_headers,
    extract_xsrf_from_cookies,
)


def mask(value: str, keep: int = 8) -> str:
    if not value:
        return ""
    if len(value) <= keep * 2:
        return "*" * len(value)
    return f"{value[:keep]}...{value[-keep:]}"


def masked_dict(data: dict[str, str]) -> dict[str, str]:
    return {k: mask(v) for k, v in data.items()}


def build_preview_payload() -> dict:
    return {
        "operationName": "VisitorJobSearch",
        "variables": {
            "input": {
                "query": "python automation",
                "pagination": {"offset": 0, "limit": 20},
            }
        },
        "query": "query VisitorJobSearch($input: VisitorJobSearchInput!) { visitorJobSearch(input: $input) { edges { node { id title } } } }",
    }


def main() -> None:
    cookies_file = "data/cookies.json"
    graphql_url = "https://www.upwork.com/api/graphql/v1?alias=visitorJobSearch"

    cookies = load_cookies(cookies_file)
    bearer_meta = extract_bearer_cookie_metadata(cookies)
    bearer_token = str(bearer_meta.get("token", ""))
    xsrf_token = extract_xsrf_from_cookies(cookies)

    headers = build_headers(bearer_token=bearer_token, xsrf_token=xsrf_token)
    headers["cookie"] = build_cookie_header(cookies)

    important = extract_important_cookie_values(cookies)
    payload = build_preview_payload()

    safe_headers = dict(headers)
    if "authorization" in safe_headers:
        safe_headers["authorization"] = mask(safe_headers["authorization"])
    if "x-odesk-csrf-token" in safe_headers:
        safe_headers["x-odesk-csrf-token"] = mask(safe_headers["x-odesk-csrf-token"])
    if "cookie" in safe_headers:
        safe_headers["cookie"] = f"{len(cookies)} cookies loaded"

    print("=== Module 1.1: Complete Request Preview ===")
    print(f"Cookies file: {cookies_file}")
    print(f"Cookies loaded: {len(cookies)}")
    print(f"Bearer token found: {bool(bearer_token)}")
    print(f"XSRF token found: {bool(xsrf_token)}")
    print(f"Cloudflare cookies found: {('cf_clearance' in important) or ('__cf_bm' in important)}")

    print("\nToken metadata:")
    print(json.dumps({
        "cookie_name": bearer_meta.get("cookie_name", ""),
        "expires": bearer_meta.get("expires"),
        "domain": bearer_meta.get("domain", ""),
        "path": bearer_meta.get("path", ""),
        "token_masked": mask(bearer_token),
    }, indent=2))

    print("\nImportant cookies (masked):")
    print(json.dumps(masked_dict(important), indent=2))

    print("\nRequest preview:")
    print(json.dumps({
        "url": graphql_url,
        "method": "POST",
        "headers": safe_headers,
        "payload": payload,
    }, indent=2))


if __name__ == "__main__":
    main()

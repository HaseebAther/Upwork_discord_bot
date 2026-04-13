import json
from pathlib import Path

from src.formatting.response_formatter import format_response
from src.upwork import fetch_once


CAPTURE_FILE = Path("data/cookies.py")
UPWORK_URL = "https://www.upwork.com/api/graphql/v1"
VISITOR_MODE = False


def main() -> None:
    if not CAPTURE_FILE.exists():
        print("Capture file not found: data/cookies.py")
        return

    print("=== Module 2: One-Shot GraphQL Fetch (Project Integrated) ===")
    print(f"Visitor mode: {VISITOR_MODE}")

    result = fetch_once(
        capture_file=CAPTURE_FILE,
        upwork_url=UPWORK_URL,
        visitor_mode=VISITOR_MODE,
        use_playwright_on_403=True,
        use_seleniumbase_on_403=True,
    )

    print(f"Client used: {result.client_used}")
    print(f"Status: {result.status_code}")

    if result.status_code == 401:
        print("Auth appears expired/invalid. Re-capture once and keep same cookies/tokens until next 401.")
        print("Do not rotate cookies on every run; rotate only on 401.")
        return

    if result.status_code != 200:
        print("Response preview:")
        print(result.response_text[:500])
        return

    if result.body is None:
        print("200 but response is not JSON")
        print(result.response_text)
        return

    print("Top-level keys:", list(result.body.keys()))

    formatted_jobs = format_response(result.body)
    print("Formatted jobs:", len(formatted_jobs))

    if formatted_jobs:
        print("all formatted jobs:")
        for job in formatted_jobs:
            print(json.dumps(job, indent=2))


if __name__ == "__main__":
    main()

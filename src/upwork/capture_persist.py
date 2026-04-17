"""Write Upwork capture dicts back to data/cookies.py (Python module format)."""

from pathlib import Path


def save_capture_to_py_file(path: Path, capture: dict) -> None:
    """Persist cookies, headers, params, and json_data in the format load_capture_dicts expects."""
    cookies = capture.get("cookies", {})
    headers = capture.get("headers", {})
    params = capture.get("params", {})
    json_data = capture.get("json_data", {})

    header = (
        '"""\n'
        "Upwork session capture — updated automatically on session refresh.\n"
        '"""\n\n'
    )
    body = (
        f"cookies = {repr(cookies)}\n\n"
        f"headers = {repr(headers)}\n\n"
        f"params = {repr(params)}\n\n"
        f"json_data = {repr(json_data)}\n"
    )
    path.write_text(header + body, encoding="utf-8")

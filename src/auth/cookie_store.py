import json
import os
from typing import Any


def load_cookies(cookies_file: str) -> list[dict[str, Any]]:
    if not os.path.exists(cookies_file):
        return []

    with open(cookies_file, "r", encoding="utf-8") as f:
        try:
            data = json.load(f)
            if isinstance(data, list):
                return data
        except json.JSONDecodeError:
            return []
    return []


def save_cookies(cookies_file: str, cookies: list[dict[str, Any]]) -> None:
    os.makedirs(os.path.dirname(cookies_file), exist_ok=True)
    with open(cookies_file, "w", encoding="utf-8") as f:
        json.dump(cookies, f, indent=2)

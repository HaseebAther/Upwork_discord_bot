import threading
import time
from urllib.parse import urlencode

import requests

from src.auth.seleniumbase_session import refresh_cookies_with_seleniumbase


class ManagedUpworkSession:

    def __init__(self, refresh_interval_hours: int = 9):
        self.session = requests.Session()
        self.refresh_interval_seconds = max(1, int(refresh_interval_hours)) * 3600
        self.last_refresh = 0.0
        self.last_force_refresh = 0.0
        self.min_force_refresh_interval_seconds = 60
        self._lock = threading.Lock()

        self.session.headers.update(
            {
                "accept": "*/*",
                "accept-language": "en-US,en;q=0.9",
                "content-type": "application/json",
                "origin": "https://www.upwork.com",
                "referer": "https://www.upwork.com/nx/search/jobs/",
                "user-agent": (
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/147.0.0.0 Safari/537.36"
                ),
                "x-upwork-accept-language": "en-US",
            }
        )

    def needs_refresh(self) -> bool:
        return (time.time() - self.last_refresh) > self.refresh_interval_seconds

    def refresh_if_needed(self) -> bool:
        if self.needs_refresh():
            return self.refresh(force=False)
        return True

    def force_refresh(self) -> bool:
        now = time.time()
        if (now - self.last_force_refresh) < self.min_force_refresh_interval_seconds:
            return False
        self.last_force_refresh = now
        return self.refresh(force=True)

    def refresh(self, force: bool = False) -> bool:
        with self._lock:
            if not force and not self.needs_refresh():
                return True
            refreshed = refresh_cookies_with_seleniumbase("https://www.upwork.com/nx/search/jobs/")
            if not refreshed:
                return False

            cookie_names = refreshed.get("_cookie_names") or []
            self.session.cookies.clear()
            for key in cookie_names:
                if key in refreshed and refreshed.get(key):
                    self.session.cookies.set(str(key), str(refreshed.get(key)))

            token = str(refreshed.get("token", "")).strip()
            if token:
                if token.lower().startswith("bearer "):
                    token = token[7:].strip()
                self.session.headers["Authorization"] = f"Bearer {token}"

            if not self.validate():
                return False

            self.last_refresh = time.time()
            return True

    def validate(self) -> bool:
        url = "https://www.upwork.com/api/graphql/v1?alias=visitorJobSearch"
        payload = {
            "query": """
            query VisitorJobSearch($requestVariables: VisitorJobSearchV1Request!) {
                search {
                    universalSearchNuxt {
                        visitorJobSearchV1(request: $requestVariables) {
                            paging { total offset count }
                            results { id title }
                        }
                    }
                }
            }
            """,
            "variables": {"requestVariables": {"userQuery": "python", "paging": {"offset": 0, "count": 1}}},
        }
        try:
            resp = self.session.post(url, json=payload, timeout=20)
            if resp.status_code != 200:
                return False
            data = resp.json()
            return isinstance(data, dict) and "errors" not in data
        except Exception:
            return False

    def post_graphql(self, graphql_url: str, params: dict, payload: dict, timeout: int = 40) -> requests.Response:
        full_url = graphql_url
        if params:
            query = urlencode({str(k): str(v) for k, v in params.items()}, doseq=True)
            if query:
                full_url = f"{graphql_url}?{query}"
        return self.session.post(full_url, json=payload, timeout=timeout)

import argparse
from collections import deque
import json
import time
from pathlib import Path

from src.auth.seleniumbase_session import refresh_cookies_with_seleniumbase
from src.formatting.response_formatter import format_response
from src.notifications import post_jobs_to_discord, resolve_discord_webhook_url
from src.storage import SQLiteStore
from src.upwork.job_search_client import build_search_url, fetch_from_capture_data, merge_cookie_updates
from src.upwork.capture_loader import load_capture_dicts
from src.auth.token_manager import load_state, save_state


CAPTURE_FILE = Path("data/cookies.py")
STATE_FILE = Path("data/polling_state.json")
DB_FILE = Path("data/runtime.db")
UPWORK_URL = "https://www.upwork.com/api/graphql/v1"


def print_job(job: dict) -> None:
    print(json.dumps(job, indent=2))


def load_runtime_capture(capture_file: Path, state_file: Path) -> dict:
    base_capture = load_capture_dicts(capture_file)
    state = load_state(str(state_file))

    if not state:
        return base_capture

    runtime_capture = dict(base_capture)
    for key in ("cookies", "headers", "params", "json_data"):
        if key in state and isinstance(state.get(key), dict):
            runtime_capture[key] = dict(state[key])

    if isinstance(state.get("seen_job_ids"), list):
        runtime_capture["seen_job_ids"] = list(state["seen_job_ids"])

    return runtime_capture


def persist_runtime_capture(state_file: Path, capture: dict) -> None:
    state = {
        "cookies": capture.get("cookies", {}),
        "headers": capture.get("headers", {}),
        "params": capture.get("params", {}),
        "json_data": capture.get("json_data", {}),
        "seen_job_ids": capture.get("seen_job_ids", []),
        "updated_at": time.time(),
    }
    save_state(str(state_file), state)


def refresh_runtime_cookies(capture: dict, query: str | None, state_file: Path) -> bool:
    refreshed = refresh_cookies_with_seleniumbase(build_search_url(query))
    if not refreshed:
        return False

    capture["cookies"] = merge_cookie_updates(capture.get("cookies", {}), refreshed)
    persist_runtime_capture(state_file, capture)
    return True


def main() -> None:
    parser = argparse.ArgumentParser(description="Long-running Upwork polling loop")
    parser.add_argument("--query", default=None, help="Override Upwork search query")
    parser.add_argument("--interval", type=int, default=180, help="Seconds between polls")
    parser.add_argument("--discord-webhook-url", default=None, help="Discord webhook URL (or set DISCORD_WEBHOOK_URL)")
    parser.add_argument("--discord-max-posts", type=int, default=5, help="Max new jobs to post per poll")
    parser.add_argument("--startup-refresh", action="store_true", default=True, help="Refresh cookies at startup")
    parser.add_argument("--no-startup-refresh", dest="startup_refresh", action="store_false", help="Skip startup refresh")
    parser.add_argument("--capture-file", default=str(CAPTURE_FILE), help="Path to the capture file")
    parser.add_argument("--state-file", default=str(STATE_FILE), help="Path to persistent runtime state")
    parser.add_argument("--db-file", default=str(DB_FILE), help="Path to SQLite runtime database")
    args = parser.parse_args()

    capture_file = Path(args.capture_file)
    state_file = Path(args.state_file)
    db_file = Path(args.db_file)

    if not capture_file.exists():
        print(f"Capture file not found: {capture_file}")
        return

    capture = load_runtime_capture(capture_file, state_file)
    store = SQLiteStore(db_file)
    store.init_schema()
    discord_webhook_url = resolve_discord_webhook_url(args.discord_webhook_url)

    if discord_webhook_url:
        print("Discord posting enabled")
    else:
        print("Discord posting disabled (no webhook URL provided)")

    if args.startup_refresh:
        print("Refreshing cookies at startup...")
        if refresh_runtime_cookies(capture, args.query, state_file):
            print("Startup refresh complete")
        else:
            print("Startup refresh skipped or failed; continuing with existing capture")

    query_key = args.query or ""
    cached_ids = store.load_recent_job_ids(query_key, limit=500)
    recent_job_ids = set(cached_ids)
    recent_job_order = deque(cached_ids, maxlen=500)
    if cached_ids:
        print(f"Loaded {len(cached_ids)} cached job ids for query '{query_key}'")
    else:
        print(f"No cached job ids for query '{query_key}'. Starting fresh.")

    print("Starting polling loop. Press Ctrl+C to stop.")

    try:
        while True:
            run_id = store.start_poll_run(args.query)
            result = fetch_from_capture_data(
                capture_data=capture,
                upwork_url=UPWORK_URL,
                user_query=args.query,
                use_seleniumbase_on_403=True,
            )

            print(f"Status: {result.status_code} | Client: {result.client_used}")
            jobs_seen_count = 0
            new_jobs_count = 0
            error_text = ""

            if result.status_code == 200 and result.body is not None:
                formatted_jobs = format_response(result.body)
                jobs_seen_count = len(formatted_jobs)
                new_jobs = []
                for job in formatted_jobs:
                    job_id = str(job.get("id", "")).strip()
                    if not job_id:
                        continue

                    is_new = job_id not in recent_job_ids
                    store.upsert_job(query_key, job)

                    if is_new:
                        new_jobs.append(job)
                        recent_job_ids.add(job_id)
                        recent_job_order.append(job_id)

                while len(recent_job_ids) > 500 and recent_job_order:
                    oldest_id = recent_job_order.popleft()
                    if oldest_id in recent_job_ids and oldest_id not in recent_job_order:
                        recent_job_ids.remove(oldest_id)

                store.save_recent_job_ids(query_key, list(recent_job_order))

                new_jobs_count = len(new_jobs)
                if new_jobs:
                    print(f"New jobs found: {len(new_jobs)}")
                    for job in new_jobs:
                        print_job(job)

                    posted = post_jobs_to_discord(
                        webhook_url=discord_webhook_url,
                        jobs=new_jobs,
                        query=args.query,
                        max_posts=args.discord_max_posts,
                    )
                    if posted["attempted"] > 0:
                        print(
                            "Discord posts: "
                            f"attempted={posted['attempted']} "
                            f"sent={posted['sent']} failed={posted['failed']}"
                        )
                else:
                    print(f"No new jobs. Total formatted jobs: {len(formatted_jobs)}")

                persist_runtime_capture(state_file, capture)

            elif result.status_code in {401, 403}:
                print("Auth or challenge failure detected. Refreshing cookies and retrying next loop...")
                if refresh_runtime_cookies(capture, args.query, state_file):
                    print("Reauth complete")
                else:
                    print("Reauth failed; keeping existing state")
                error_text = "Auth/challenge failure"

            else:
                error_text = result.response_text[:500]
                print(error_text)

            store.finish_poll_run(
                run_id=run_id,
                status_code=result.status_code,
                jobs_seen_count=jobs_seen_count,
                new_jobs_count=new_jobs_count,
                client_used=result.client_used,
                error_text=error_text,
            )

            time.sleep(max(5, args.interval))

    except KeyboardInterrupt:
        print("Polling loop stopped by user")


if __name__ == "__main__":
    main()
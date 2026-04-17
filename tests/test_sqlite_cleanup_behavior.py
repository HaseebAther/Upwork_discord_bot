import sqlite3
import time
from pathlib import Path

from src.storage.sqlite_store import SQLiteStore


def test_sqlite_cleanup_deletes_old_rows(tmp_path: Path):
    db = tmp_path / "runtime.db"
    store = SQLiteStore(db)
    store.init_schema()

    # Insert one recent row via normal path
    store.upsert_job("q1", {"id": "new1", "title": "new"})

    # Insert one old row by editing timestamps directly
    old_ts = time.time() - (30 * 24 * 3600)
    with sqlite3.connect(db) as conn:
        conn.execute(
            "INSERT OR REPLACE INTO jobs (job_id, query, title, payload_json, first_seen_at, last_seen_at, seen_count) VALUES (?, ?, ?, ?, ?, ?, 1)",
            ("old1", "q1", "old", "{}", old_ts, old_ts),
        )
        conn.execute(
            "INSERT OR REPLACE INTO poll_runs (id, query, started_at, finished_at, status_code, jobs_seen_count, new_jobs_count, client_used, error_text) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (1, "q1", old_ts, old_ts, 200, 1, 0, "cloudscraper", ""),
        )
        conn.execute(
            "INSERT OR REPLACE INTO job_id_cache (query, job_ids_json, updated_at) VALUES (?, ?, ?)",
            ("q1", '["old1"]', old_ts),
        )
        conn.commit()

    stats = store.cleanup_old_records(jobs_max_age_days=14, poll_runs_max_age_days=14)
    assert stats["jobs_deleted"] >= 1
    assert stats["poll_runs_deleted"] >= 1
    assert stats["job_id_cache_deleted"] >= 1

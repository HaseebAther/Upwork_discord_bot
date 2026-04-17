import json
import sqlite3
import time
from pathlib import Path
from typing import Any


class SQLiteStore:
    def __init__(self, db_path: Path) -> None:
        self.db_path = db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.execute("PRAGMA journal_mode=WAL;")
        conn.execute("PRAGMA synchronous=NORMAL;")
        return conn

    def init_schema(self) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS jobs (
                    job_id TEXT NOT NULL,
                    query TEXT NOT NULL,
                    title TEXT,
                    payload_json TEXT NOT NULL,
                    first_seen_at REAL NOT NULL,
                    last_seen_at REAL NOT NULL,
                    seen_count INTEGER NOT NULL DEFAULT 1,
                    PRIMARY KEY (job_id, query)
                );
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS job_id_cache (
                    query TEXT PRIMARY KEY,
                    job_ids_json TEXT NOT NULL,
                    updated_at REAL NOT NULL
                );
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS poll_runs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    query TEXT,
                    started_at REAL NOT NULL,
                    finished_at REAL,
                    status_code INTEGER,
                    jobs_seen_count INTEGER,
                    new_jobs_count INTEGER,
                    client_used TEXT,
                    error_text TEXT
                );
                """
            )

    def load_recent_job_ids(self, query: str, limit: int = 500) -> list[str]:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT job_ids_json FROM job_id_cache WHERE query = ?",
                (query,),
            ).fetchone()
            if row is not None:
                try:
                    cached_ids = json.loads(str(row[0]))
                    if isinstance(cached_ids, list):
                        return [str(job_id) for job_id in cached_ids if str(job_id).strip()]
                except Exception:
                    pass

            rows = conn.execute(
                """
                SELECT job_id
                FROM jobs
                WHERE query = ?
                ORDER BY last_seen_at DESC
                LIMIT ?
                """,
                (query, limit),
            ).fetchall()
            job_ids = [str(row[0]) for row in rows if str(row[0]).strip()]
            if job_ids:
                self.save_recent_job_ids(query, job_ids)
            return job_ids

    def save_recent_job_ids(self, query: str, job_ids: list[str]) -> None:
        compact_ids = [str(job_id) for job_id in job_ids if str(job_id).strip()]
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO job_id_cache (query, job_ids_json, updated_at)
                VALUES (?, ?, ?)
                ON CONFLICT(query) DO UPDATE SET
                    job_ids_json = excluded.job_ids_json,
                    updated_at = excluded.updated_at
                """,
                (query, json.dumps(compact_ids, separators=(",", ":")), time.time()),
            )

    def start_poll_run(self, query: str | None) -> int:
        with self._connect() as conn:
            cur = conn.execute(
                "INSERT INTO poll_runs (query, started_at) VALUES (?, ?)",
                (query or "", time.time()),
            )
            return int(cur.lastrowid)

    def finish_poll_run(
        self,
        run_id: int,
        status_code: int,
        jobs_seen_count: int,
        new_jobs_count: int,
        client_used: str,
        error_text: str = "",
    ) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                UPDATE poll_runs
                SET finished_at = ?, status_code = ?, jobs_seen_count = ?,
                    new_jobs_count = ?, client_used = ?, error_text = ?
                WHERE id = ?
                """,
                (
                    time.time(),
                    status_code,
                    jobs_seen_count,
                    new_jobs_count,
                    client_used,
                    error_text[:1000],
                    run_id,
                ),
            )

    def upsert_job(self, query: str, job: dict[str, Any]) -> bool:
        job_id = str(job.get("id", "")).strip()
        if not job_id:
            return False

        now = time.time()
        payload_json = json.dumps(job, separators=(",", ":"), ensure_ascii=True)
        title = str(job.get("title", ""))

        with self._connect() as conn:
            row = conn.execute(
                "SELECT seen_count FROM jobs WHERE job_id = ? AND query = ?",
                (job_id, query),
            ).fetchone()

            if row is None:
                conn.execute(
                    """
                    INSERT INTO jobs (job_id, query, title, payload_json, first_seen_at, last_seen_at, seen_count)
                    VALUES (?, ?, ?, ?, ?, ?, 1)
                    """,
                    (job_id, query, title, payload_json, now, now),
                )
                return True

            conn.execute(
                """
                UPDATE jobs
                SET title = ?, payload_json = ?, last_seen_at = ?, seen_count = seen_count + 1
                WHERE job_id = ? AND query = ?
                """,
                (title, payload_json, now, job_id, query),
            )
            return False

    def cleanup_old_records(self, jobs_max_age_days: int = 14, poll_runs_max_age_days: int = 14) -> dict[str, int]:
        """Delete stale rows to keep DB size bounded for long-running bots."""
        now = time.time()
        jobs_cutoff = now - (max(1, jobs_max_age_days) * 24 * 3600)
        poll_cutoff = now - (max(1, poll_runs_max_age_days) * 24 * 3600)
        with self._connect() as conn:
            jobs_deleted = conn.execute(
                "DELETE FROM jobs WHERE last_seen_at < ?",
                (jobs_cutoff,),
            ).rowcount
            polls_deleted = conn.execute(
                "DELETE FROM poll_runs WHERE started_at < ?",
                (poll_cutoff,),
            ).rowcount
            cache_deleted = conn.execute(
                "DELETE FROM job_id_cache WHERE updated_at < ?",
                (jobs_cutoff,),
            ).rowcount
        return {
            "jobs_deleted": int(jobs_deleted or 0),
            "poll_runs_deleted": int(polls_deleted or 0),
            "job_id_cache_deleted": int(cache_deleted or 0),
        }

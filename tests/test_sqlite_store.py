from pathlib import Path
from src.storage.sqlite_store import SQLiteStore


def test_sqlite_cleanup_old_records(tmp_path: Path):
    db = tmp_path / "runtime.db"
    store = SQLiteStore(db)
    store.init_schema()
    store.upsert_job("q1", {"id": "1", "title": "a"})
    stats = store.cleanup_old_records(jobs_max_age_days=14, poll_runs_max_age_days=14)
    assert "jobs_deleted" in stats
    assert "poll_runs_deleted" in stats

import os
import time
from typing import Any

import requests


DISCORD_CONTENT_LIMIT = 2000
DEFAULT_TIMEOUT_SECONDS = 20


def resolve_discord_webhook_url(cli_value: str | None = None) -> str | None:
    value = (cli_value or os.getenv("DISCORD_WEBHOOK_URL") or "").strip()
    return value or None


def _safe_text(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip()


def _job_url(job_id: str) -> str:
    clean_id = job_id.strip()
    if not clean_id:
        return ""
    if clean_id.startswith("http://") or clean_id.startswith("https://"):
        return clean_id
    if clean_id.startswith("~"):
        return f"https://www.upwork.com/jobs/{clean_id}"
    return f"https://www.upwork.com/jobs/~{clean_id}"


def format_job_message(job: dict[str, Any], query: str | None = None) -> str:
    title = _safe_text(job.get("title")) or "Untitled job"
    job_id = _safe_text(job.get("id"))
    job_type = _safe_text(job.get("job_type")) or "unknown"
    budget = _safe_text(job.get("budget_display")) or "not specified"
    publish_time = _safe_text(job.get("publish_time")) or "unknown"
    preview = _safe_text(job.get("description_preview"))
    skills = job.get("skills") if isinstance(job.get("skills"), list) else []
    skill_text = ", ".join(_safe_text(skill) for skill in skills if _safe_text(skill))
    skill_text = skill_text or "none listed"

    lines = [
        "New Upwork job found",
        f"Query: {query or '(default)'}",
        f"Title: {title}",
        f"Type: {job_type}",
        f"Budget: {budget}",
        f"Published: {publish_time}",
        f"Skills: {skill_text}",
    ]

    if preview:
        lines.append(f"Preview: {preview}")

    url = _job_url(job_id)
    if url:
        lines.append(f"Link: {url}")

    message = "\n".join(lines)
    if len(message) > DISCORD_CONTENT_LIMIT:
        message = message[: DISCORD_CONTENT_LIMIT - 3] + "..."
    return message


def send_discord_webhook(webhook_url: str, content: str, timeout_seconds: int = DEFAULT_TIMEOUT_SECONDS) -> tuple[bool, str]:
    payload = {"content": content}

    try:
        response = requests.post(webhook_url, json=payload, timeout=timeout_seconds)
    except requests.RequestException as exc:
        return False, f"request failed: {exc}"

    if response.status_code in {200, 204}:
        return True, "ok"

    if response.status_code == 429:
        retry_after_seconds = 1.0
        try:
            data = response.json()
            retry_after_seconds = float(data.get("retry_after", 1.0))
        except Exception:
            pass

        time.sleep(max(0.25, retry_after_seconds))
        try:
            retry_response = requests.post(webhook_url, json=payload, timeout=timeout_seconds)
        except requests.RequestException as exc:
            return False, f"retry failed: {exc}"

        if retry_response.status_code in {200, 204}:
            return True, "ok_after_retry"

        return False, f"status {retry_response.status_code}: {retry_response.text[:300]}"

    return False, f"status {response.status_code}: {response.text[:300]}"


def post_jobs_to_discord(
    webhook_url: str | None,
    jobs: list[dict[str, Any]],
    query: str | None,
    max_posts: int = 5,
) -> dict[str, int]:
    if not webhook_url or not jobs:
        return {"attempted": 0, "sent": 0, "failed": 0}

    allowed = max(0, max_posts)
    selected_jobs = jobs[:allowed] if allowed else []

    sent = 0
    failed = 0

    for job in selected_jobs:
        message = format_job_message(job, query=query)
        ok, _detail = send_discord_webhook(webhook_url, message)
        if ok:
            sent += 1
        else:
            failed += 1

    return {"attempted": len(selected_jobs), "sent": sent, "failed": failed}

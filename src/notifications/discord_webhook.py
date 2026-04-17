import os
import time
from typing import Any

import requests

from src.notifications.discord_formatter import JobEmbed, extract_full_job_data
from src.notifications.channel_manager import (
    JobChannelManager,
    ChannelNameGenerator,
    ThreadNameGenerator,
)


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
    """Format job message using the new Upwork-like formatter."""
    embed = JobEmbed(job, query=query)
    message = embed.format_compact_message()
    
    if len(message) > DISCORD_CONTENT_LIMIT:
        message = message[: DISCORD_CONTENT_LIMIT - 3] + "..."
    
    return message


def format_job_thread_message(job: dict[str, Any]) -> str:
    """Format detailed message for thread posting."""
    embed = JobEmbed(job)
    message = embed.format_detail_message()
    
    if len(message) > DISCORD_CONTENT_LIMIT:
        # Split into multiple messages if needed
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
    """
    Post new jobs to Discord.
    
    Enhanced version that:
    - Uses improved Upwork-like formatting
    - Tracks job-to-channel mappings
    - Handles jobs appearing in multiple queries
    - Returns posting statistics
    """
    if not webhook_url or not jobs:
        return {"attempted": 0, "sent": 0, "failed": 0}

    allowed = max(0, max_posts)
    selected_jobs = jobs[:allowed] if allowed else []

    # Initialize channel manager
    channel_manager = JobChannelManager()

    sent = 0
    failed = 0
    new_channels = 0
    reposted_to_queries = 0

    for job in selected_jobs:
        job_id = str(job.get("id", ""))
        
        # Check if job already has a channel (appeared in different query)
        is_new_job = channel_manager.is_job_new(job_id)
        
        if is_new_job:
            # New job - create channel mapping
            channel_name = ChannelNameGenerator.from_job(job)
            channel_manager.register_job_channel(job_id, channel_name, query=query)
            new_channels += 1
        else:
            # Job appearing in multiple queries
            channel_manager.register_job_channel(job_id, "", query=query)  # Update query tracking
            reposted_to_queries += 1
        
        # Format and send message
        message = format_job_message(job, query=query)
        ok, _detail = send_discord_webhook(webhook_url, message)
        if ok:
            sent += 1
        else:
            failed += 1

    return {
        "attempted": len(selected_jobs),
        "sent": sent,
        "failed": failed,
        "new_channels": new_channels,
        "reposted_to_queries": reposted_to_queries,
    }


def post_job_details_to_thread(
    webhook_url: str | None,
    job: dict[str, Any],
) -> tuple[bool, str]:
    """
    Post detailed job information to a thread.
    Includes full description, skills, and additional details.
    """
    if not webhook_url or not job:
        return False, "No webhook or job data"

    message = format_job_thread_message(job)
    return send_discord_webhook(webhook_url, message)


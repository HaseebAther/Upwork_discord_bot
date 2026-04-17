"""Discord channel management for per-job channels."""

import os
from typing import Optional
from pathlib import Path
import json
from datetime import datetime


class JobChannelManager:
    """
    Manages mapping between jobs and Discord channels.
    Handles channel creation tracking and job-to-channel associations.
    """

    def __init__(self, store_file: Path | str = Path("data/job_channels.json")):
        self.store_file = Path(store_file)
        self.store_file.parent.mkdir(parents=True, exist_ok=True)
        self._load_mappings()

    def _load_mappings(self) -> None:
        """Load channel mappings from file."""
        if self.store_file.exists():
            try:
                with open(self.store_file, "r") as f:
                    data = json.load(f)
                    self.job_channels = data.get("job_channels", {})  # job_id -> channel_name
                    self.queries_with_jobs = data.get("queries_with_jobs", {})  # job_id -> [query1, query2, ...]
            except Exception as e:
                print(f"Warning: Could not load channel mappings: {e}")
                self.job_channels = {}
                self.queries_with_jobs = {}
        else:
            self.job_channels = {}
            self.queries_with_jobs = {}

    def _save_mappings(self) -> None:
        """Save channel mappings to file."""
        try:
            with open(self.store_file, "w") as f:
                json.dump({
                    "job_channels": self.job_channels,
                    "queries_with_jobs": self.queries_with_jobs,
                    "updated_at": datetime.now().isoformat(),
                }, f, indent=2)
        except Exception as e:
            print(f"Warning: Could not save channel mappings: {e}")

    def register_job_channel(
        self,
        job_id: str,
        channel_name: str,
        query: str | None = None
    ) -> bool:
        """
        Register a job-to-channel mapping.
        
        Args:
            job_id: Upwork job ID
            channel_name: Discord channel name (e.g., "web-dev-job-123456")
            query: Query that found this job (for tracking overlaps)
        
        Returns:
            True if new channel, False if already registered
        """
        is_new = job_id not in self.job_channels
        
        self.job_channels[job_id] = channel_name
        
        if query:
            if job_id not in self.queries_with_jobs:
                self.queries_with_jobs[job_id] = []
            if query not in self.queries_with_jobs[job_id]:
                self.queries_with_jobs[job_id].append(query)
        
        self._save_mappings()
        return is_new

    def get_job_channel(self, job_id: str) -> str | None:
        """Get channel name for a job."""
        return self.job_channels.get(job_id)

    def get_job_queries(self, job_id: str) -> list[str]:
        """Get all queries that found this job."""
        return self.queries_with_jobs.get(job_id, [])

    def is_job_new(self, job_id: str) -> bool:
        """Check if job is new (not in any channel yet)."""
        return job_id not in self.job_channels

    def get_all_job_ids(self) -> list[str]:
        """Get all tracked job IDs."""
        return list(self.job_channels.keys())

    def get_jobs_for_query(self, query: str) -> list[str]:
        """Get all jobs found for a specific query."""
        return [
            job_id for job_id, queries in self.queries_with_jobs.items()
            if query in queries
        ]

    def clear_old_entries(self, keep_recent: int = 1000) -> int:
        """Keep only the most recent job entries."""
        if len(self.job_channels) <= keep_recent:
            return 0
        
        # This is a simple implementation - could be improved with timestamps
        removed = 0
        job_ids = list(self.job_channels.keys())
        
        for job_id in job_ids[keep_recent:]:
            del self.job_channels[job_id]
            if job_id in self.queries_with_jobs:
                del self.queries_with_jobs[job_id]
            removed += 1
        
        self._save_mappings()
        return removed


class ChannelNameGenerator:
    """Generate safe Discord channel names."""

    @staticmethod
    def sanitize(text: str, max_length: int = 30) -> str:
        """
        Sanitize text for Discord channel names.
        Rules: lowercase, 2-100 chars, alphanumerics and hyphens only.
        """
        # Lowercase
        text = text.lower()
        
        # Keep only alphanumerics and spaces
        text = "".join(c if c.isalnum() or c == " " else "" for c in text)
        
        # Replace spaces with hyphens
        text = "-".join(text.split())
        
        # Remove duplicate hyphens
        while "--" in text:
            text = text.replace("--", "-")
        
        # Trim length
        text = text[:max_length].strip("-")
        
        return text

    @staticmethod
    def from_job(job: dict, include_id: bool = True) -> str:
        """
        Generate channel name from job data.
        Example: "woocommerce-speed-optimization-2044484480719877725"
        """
        title = job.get("title", "job")
        job_id = str(job.get("id", ""))
        
        # Use first few words of title
        title_words = title.split()[:3]
        title_slug = "-".join(title_words)
        title_slug = ChannelNameGenerator.sanitize(title_slug, max_length=40)
        
        # Add job ID for uniqueness
        if include_id and job_id:
            channel_name = f"{title_slug}-{job_id}"
        else:
            channel_name = title_slug
        
        # Final sanitization and length limit
        channel_name = ChannelNameGenerator.sanitize(channel_name, max_length=100)
        
        # Ensure minimum length (Discord requires 2-100 chars, we use at least 3)
        if len(channel_name) < 2:
            channel_name = f"job-{job_id}" if job_id else "job-unknown"
        
        return channel_name


class ThreadNameGenerator:
    """Generate thread names for job discussions."""

    @staticmethod
    def from_job(job: dict) -> str:
        """
        Generate thread name from job data.
        Example: "Woocommerce Speed Optimization - $100 - Fixed"
        """
        title = job.get("title", "Untitled Job")
        budget = job.get("budget_display", "Budget TBD")
        job_type = job.get("job_type", "").replace("_", " ")
        
        # Limit thread name to 100 chars
        thread_name = f"{title} - {budget}"
        
        if len(thread_name) > 100:
            thread_name = thread_name[:97] + "..."
        
        return thread_name

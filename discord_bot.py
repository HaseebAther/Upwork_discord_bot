"""Discord bot runner for Upwork polling with multi-query support."""

import asyncio
from collections import deque
import concurrent.futures
import copy
import json
import os
import random
import re
import threading
import time
from pathlib import Path
from datetime import datetime

import discord
from discord.ext import commands

from src.auth.session_coordinator import refresh_capture_file
from src.discord_bot.bot import UpworkBot
from src.upwork.job_search_client import fetch_from_capture_data
from src.formatting.response_formatter import format_response
from src.storage import SQLiteStore
from src.upwork.capture_loader import load_capture_dicts
from src.logging_config import setup_logging, get_logger


class UpworkBotRunner:
    """Main bot runner that manages Discord bot and polling loop."""

    def __init__(self):
        """Initialize the bot runner."""
        self.bot: commands.Bot | None = None
        self.upwork_cog: UpworkBot | None = None
        self.polling_thread: threading.Thread | None = None
        self.should_stop = False
        self.logger = get_logger("discord_bot")
        self.bot_loop: asyncio.AbstractEventLoop | None = None
        self.auth_preflight_query = os.getenv("AUTH_PREFLIGHT_QUERY", "python")
        self.auth_preflight_enabled = os.getenv("AUTH_PREFLIGHT_ENABLED", "false").strip().lower() in {"1", "true", "yes", "on"}
        self.relevance_filter_enabled = os.getenv("RELEVANCE_FILTER_ENABLED", "true").strip().lower() in {"1", "true", "yes", "on"}
        self.query_token_min_len = int(os.getenv("QUERY_TOKEN_MIN_LEN", "3"))
        self.query_stop_words = {
            "and", "or", "the", "a", "an", "for", "to", "of", "in", "on", "with",
            "from", "by", "at", "is", "are", "be", "as",
        }

    async def initialize_bot(self) -> None:
        """Initialize the Discord bot."""
        token = os.getenv("DISCORD_BOT_TOKEN", "").strip()
        if not token:
            self.logger.error("DISCORD_BOT_TOKEN not set in .env")
            raise ValueError("DISCORD_BOT_TOKEN required")

        intents = discord.Intents.default()
        intents.message_content = True
        intents.members = True
        self.bot = commands.Bot(command_prefix="!", intents=intents)
        self.bot_loop = asyncio.get_event_loop()  # Store the bot's event loop

        @self.bot.event
        async def on_ready() -> None:
            """Called when bot is ready."""
            # Simple logging, no messages sent
            if not hasattr(self, '_on_ready_logged'):
                self.logger.info("Bot logged in as %s", self.bot.user)
                self.logger.info("Watching %d guild(s)", len(self.bot.guilds))
                self.logger.info("Bot is ready and waiting for commands")
                self.logger.info("Use !help_upwork to see available commands")
                self._on_ready_logged = True

        # Add Upwork cog (remove old one first to prevent duplicates)
        if "UpworkBot" in self.bot.cogs:
            await self.bot.remove_cog("UpworkBot")
            self.logger.info("Removed old UpworkBot cog")
        
        self.upwork_cog = UpworkBot(self.bot)
        await self.bot.add_cog(self.upwork_cog)
        self.logger.info("Upwork commands loaded")

    def polling_loop_thread(self) -> None:
        """Run polling loop in background thread."""
        try:
            self.polling_loop()
        except Exception as e:
            self.logger.error(f"Polling loop error: {e}", exc_info=True)

    def polling_loop(self) -> None:
        """Polling loop that runs in background."""
        if not self.upwork_cog:
            self.logger.error("Upwork cog not initialized")
            return

        capture_file = Path("data/cookies.py")
        state_file = Path("data/polling_state.json")
        db_file = Path("data/runtime.db")
        upwork_url = "https://www.upwork.com/api/graphql/v1"

        if not capture_file.exists():
            self.logger.error(f"Capture file not found: {capture_file}")
            return

        store = SQLiteStore(db_file)
        store.init_schema()
        seen_cache_limit = int(os.getenv("SEEN_CACHE_LIMIT", "800"))
        failure_backoff_threshold = int(os.getenv("FAILURE_BACKOFF_THRESHOLD", "6"))
        raw_dump_sample_every = int(os.getenv("RAW_DUMP_SAMPLE_EVERY", "30"))
        quiet_step_seconds = int(os.getenv("QUIET_MODE_STEP_SECONDS", "30"))
        quiet_max_seconds = int(os.getenv("QUIET_MODE_MAX_SECONDS", "300"))
        jobs_retention_days = int(os.getenv("JOBS_RETENTION_DAYS", "14"))
        poll_runs_retention_days = int(os.getenv("POLL_RUNS_RETENTION_DAYS", "14"))
        channel_validate_every_polls = int(os.getenv("CHANNEL_VALIDATE_EVERY_POLLS", "3"))
        error_retry_min_seconds = int(os.getenv("ERROR_RETRY_MIN_SECONDS", "2"))
        error_retry_max_seconds = int(os.getenv("ERROR_RETRY_MAX_SECONDS", "5"))
        max_concurrent_fetches = int(os.getenv("MAX_CONCURRENT_FETCHES", "3"))

        self.logger.info("=" * 60)
        self.logger.info("UPWORK POLLING LOOP STARTED")
        self.logger.info("=" * 60)
        self.logger.info("Job posts go to Discord channels via the bot (not webhooks).")
        cleanup_stats = store.cleanup_old_records(
            jobs_max_age_days=jobs_retention_days,
            poll_runs_max_age_days=poll_runs_retention_days,
        )
        self.logger.info("DB cleanup stats: %s", cleanup_stats)

        # Cookie refresh strategy
        last_refresh_time = time.time()
        refresh_interval = random.randint(8 * 3600, 10 * 3600)  # 8-10 hours in seconds
        next_refresh_time = last_refresh_time + refresh_interval
        print(f"🍪 Cookies loaded. Next refresh in {refresh_interval // 3600} hours")
        
        # Keep track of seen jobs per query in bounded memory structures:
        # - set for O(1) lookup
        # - deque for oldest-id eviction
        seen_jobs_by_query: dict[str, set[str]] = {}
        seen_jobs_order_by_query: dict[str, deque[str]] = {}
        
        # Initialize seen jobs from database for all queries
        print("📦 Loading seen jobs from database...")
        for query in self.upwork_cog.queries.keys():
            recent_ids = store.load_recent_job_ids(query, limit=500)
            trimmed_ids = [str(x) for x in recent_ids if str(x).strip()][:seen_cache_limit]
            seen_jobs_by_query[query] = set(trimmed_ids)
            seen_jobs_order_by_query[query] = deque(trimmed_ids, maxlen=seen_cache_limit)
            print(f"  ✓ Loaded {len(recent_ids)} seen jobs for '{query}'")

        poll_count = 0
        consecutive_failures = 0
        quiet_mode_level = 0
        while not self.should_stop:
            if not self.upwork_cog.polling_active:
                time.sleep(5)
                continue

            active_queries = self.upwork_cog.get_active_queries()
            if not active_queries:
                print("⏸️  No active queries, waiting...")
                time.sleep(10)
                continue

            poll_count += 1
            poll_new_jobs = 0
            poll_had_fetch_error = False
            poll_post_failures = 0
            self.logger.info(f"[Poll #{poll_count}] {time.strftime('%Y-%m-%d %H:%M:%S')}")
            self.logger.info(f"Active queries: {active_queries}")

            # Validate/recreate channels CONCURRENTLY for all active queries
            do_channel_validation = (poll_count % max(1, channel_validate_every_polls)) == 1
            if do_channel_validation:
                print("🔗 Validating channels for all queries...")
            channel_futures = {}
            if do_channel_validation:
                for query in active_queries:
                    future = asyncio.run_coroutine_threadsafe(
                        self._ensure_channel_exists(query),
                        self.bot_loop
                    )
                    channel_futures[query] = future
            
            # Collect results (will wait if not ready yet)
            validated_channels = {}
            if do_channel_validation:
                for query, future in channel_futures.items():
                    try:
                        validated_channels[query] = future.result(timeout=10)
                    except Exception as e:
                        print(f"⚠️ Channel validation failed for '{query}': {e}")
                        validated_channels[query] = None
            else:
                # Fast path: reuse saved channel mapping/cached channel object.
                for query in active_queries:
                    channel_id = self.upwork_cog.query_channels.get(query)
                    validated_channels[query] = self.bot.get_channel(channel_id) if channel_id else None

            try:
                shared_capture = load_capture_dicts(capture_file)
                print("✓ Session capture loaded (shared across all queries this poll)")
            except Exception as e:
                print(f"❌ Failed to load capture: {e}")
                self.logger.error(f"Failed to load capture: {e}")
                time.sleep(30)
                continue

            # Auth/session preflight on first poll and periodic intervals.
            if self.auth_preflight_enabled and (poll_count == 1 or (poll_count % 50 == 0)):
                try:
                    preflight = fetch_from_capture_data(
                        capture_data=shared_capture,
                        upwork_url=upwork_url,
                        user_query=self.auth_preflight_query,
                        use_seleniumbase_on_403=True,
                        capture_path=capture_file,
                    )
                    self.logger.info(
                        "Auth preflight query='%s' status=%s client=%s",
                        self.auth_preflight_query,
                        preflight.status_code,
                        preflight.client_used,
                    )
                except Exception as e:
                    self.logger.warning("Auth preflight failed: %s", e)

            # Proactive session refresh once per poll round (not per keyword)
            if time.time() >= next_refresh_time:
                print(f"🔄 Scheduled cookie refresh (every {refresh_interval // 3600} hours)...")
                self.logger.info("Running scheduled cookie refresh")
                try:
                    if refresh_capture_file(capture_file):
                        shared_capture = load_capture_dicts(capture_file)
                        print("✅ Session capture refreshed on disk and reloaded")
                        last_refresh_time = time.time()
                        refresh_interval = random.randint(8 * 3600, 10 * 3600)
                        next_refresh_time = last_refresh_time + refresh_interval
                        print(f"🍪 Next refresh in {refresh_interval // 3600} hours")
                    else:
                        print("⚠️ Scheduled refresh did not obtain new session data")
                except Exception as e:
                    print(f"⚠️ Scheduled refresh failed: {e}")
                    self.logger.error(f"Scheduled cookie refresh failed: {e}")

            for query in active_queries:
                if query not in seen_jobs_by_query:
                    seen_jobs_by_query[query] = set()
                    seen_jobs_order_by_query[query] = deque(maxlen=seen_cache_limit)

            # Fetch queries concurrently (bounded worker pool).
            fetch_results: dict[str, tuple] = {}
            with concurrent.futures.ThreadPoolExecutor(max_workers=max(1, max_concurrent_fetches)) as executor:
                future_map = {
                    executor.submit(
                        self._fetch_query_once,
                        query,
                        copy.deepcopy(shared_capture),
                        capture_file,
                        upwork_url,
                    ): query
                    for query in active_queries
                }
                for future in concurrent.futures.as_completed(future_map):
                    query = future_map[future]
                    try:
                        fetch_results[query] = future.result()
                    except Exception as e:
                        fetch_results[query] = (None, False, [], e)

            # Process results in main thread (DB, cache, posting).
            for query in active_queries:
                result, graphql_has_errors, formatted_jobs, fetch_error = fetch_results.get(query, (None, False, [], None))
                if fetch_error is not None:
                    poll_had_fetch_error = True
                    print(f"❌ ERROR polling '{query}': {fetch_error}")
                    self.logger.error(f"Error polling '{query}': {fetch_error}", exc_info=True)
                    continue

                if result is None:
                    poll_had_fetch_error = True
                    continue

                print(f"✓ Got response: Status {result.status_code} | Client: {result.client_used}")
                self.logger.info(f"Query '{query}': Status {result.status_code} | Client: {result.client_used}")

                if result.status_code == 403:
                    poll_had_fetch_error = True
                    self.logger.warning(
                        "Query '%s' still 403 after shared refresh path — session may be blocked.",
                        query,
                    )

                if graphql_has_errors:
                    poll_had_fetch_error = True
                    self.logger.warning(
                        "Query '%s' returned GraphQL errors: %s",
                        query,
                        result.body.get("errors") if isinstance(result.body, dict) else None,
                    )
                    print(f"⚠️ GraphQL errors for '{query}'. Check data/raw_api_response.json")

                if result.status_code != 200:
                    poll_had_fetch_error = True
                    continue

                # Save raw response only on anomalies or periodic sampling.
                if isinstance(result.body, dict) and (graphql_has_errors or (poll_count % raw_dump_sample_every == 0)):
                    with open("data/raw_api_response.json", "w", encoding="utf-8") as f:
                        json.dump(result.body, f, indent=2)
                    print("💾 Raw API response saved to: data/raw_api_response.json")

                print(f"📊 Total jobs found: {len(formatted_jobs)}")
                new_jobs = []

                for job in formatted_jobs:
                    job_id = str(job.get("id", "")).strip()
                    if not job_id:
                        continue
                    if not self._job_relevance_match(job, query):
                        self.logger.debug(
                            "Filtered non-relevant job for query '%s': %s",
                            query,
                            job.get("title", "N/A"),
                        )
                        continue

                    # Always store in DB (for history)
                    store.upsert_job(query, job)
                    
                    # Check if job is in seen cache
                    if job_id not in seen_jobs_by_query[query]:
                        # New job! Add to both cache and list for posting
                        seen_jobs_by_query[query].add(job_id)
                        seen_jobs_order_by_query[query].append(job_id)
                        if len(seen_jobs_by_query[query]) > seen_cache_limit:
                            # Evict oldest entries from set while deque tracks order.
                            while len(seen_jobs_by_query[query]) > seen_cache_limit and seen_jobs_order_by_query[query]:
                                oldest = seen_jobs_order_by_query[query].popleft()
                                seen_jobs_by_query[query].discard(oldest)
                        new_jobs.append(job)

                if new_jobs:
                    poll_new_jobs += len(new_jobs)
                    print(f"✨ NEW JOBS: {len(new_jobs)} | Posting to Discord...")
                    self.logger.info(f"Found {len(new_jobs)} new jobs in query '{query}'")
                    
                    # Use pre-validated channel (from concurrent check earlier)
                    channel = validated_channels.get(query)
                    
                    if channel:
                        post_future = asyncio.run_coroutine_threadsafe(
                            self._post_jobs_batch(channel, new_jobs[:5]),
                            self.bot_loop,
                        )
                        ok_count, fail_count = post_future.result(timeout=30)
                        poll_post_failures += fail_count
                        self.logger.info(
                            "Posted %d/%d jobs to #%s",
                            ok_count,
                            min(5, len(new_jobs)),
                            channel.name,
                        )
                    else:
                        print(f"⚠️ Channel not available for query '{query}'")
                        self.logger.warning(f"Channel not available for query '{query}'")
                else:
                    self.logger.debug(f"No new jobs for query '{query}'")

            # Failure cooldown to avoid hammering during prolonged outages.
            if poll_had_fetch_error:
                consecutive_failures += 1
            else:
                consecutive_failures = 0

            if consecutive_failures >= failure_backoff_threshold:
                cooldown_s = random.randint(
                    min(error_retry_min_seconds, error_retry_max_seconds),
                    max(error_retry_min_seconds, error_retry_max_seconds),
                )
                self.logger.warning(
                    "Consecutive failures=%d reached threshold; cooling down for %ds",
                    consecutive_failures,
                    cooldown_s,
                )
                time.sleep(cooldown_s)
                continue

            # Quiet-mode interval: if no new jobs, back off gradually; reset on activity.
            if poll_had_fetch_error:
                # Fast retry window on fetch/session errors (user-tunable, defaults 2-5s).
                sleep_time = random.randint(
                    min(error_retry_min_seconds, error_retry_max_seconds),
                    max(error_retry_min_seconds, error_retry_max_seconds),
                )
                quiet_mode_level = 0
            else:
                if poll_new_jobs == 0:
                    quiet_mode_level = min(quiet_mode_level + 1, max(1, quiet_max_seconds // max(1, quiet_step_seconds)))
                else:
                    quiet_mode_level = 0

                dynamic_quiet_extra = min(quiet_mode_level * quiet_step_seconds, max(0, quiet_max_seconds - self.upwork_cog.polling_interval))
                sleep_time = self.upwork_cog.polling_interval + dynamic_quiet_extra
            self.logger.info(
                "Poll summary: new_jobs=%d fetch_error=%s post_failures=%d quiet_level=%d consecutive_failures=%d next_sleep=%ds",
                poll_new_jobs,
                poll_had_fetch_error,
                poll_post_failures,
                quiet_mode_level,
                consecutive_failures,
                sleep_time,
            )
            print(f"⏰ Next poll in {sleep_time}s...\n")
            self.logger.debug(f"Next poll in {sleep_time}s...")
            for i in range(sleep_time):
                if self.should_stop:
                    break
                time.sleep(1)

        self.logger.info("=" * 60)
        self.logger.info("POLLING LOOP STOPPED")
        self.logger.info("=" * 60)

    async def _send_embed_to_channel(self, channel, embed):
        """Send an embed to a Discord channel and return created message."""
        return await channel.send(embed=embed)

    def _query_keywords(self, query: str) -> list[str]:
        """Extract meaningful query keywords for AND-based relevance checks."""
        words = re.findall(r"[a-z0-9]+", str(query).lower())
        return [
            w for w in words
            if len(w) >= max(1, self.query_token_min_len) and w not in self.query_stop_words
        ]

    def _job_relevance_match(self, job: dict, query: str) -> bool:
        """
        Require all meaningful query tokens to exist in job title/description/skills.
        Example: query='saas development' => both 'saas' and 'development' must appear.
        """
        if not self.relevance_filter_enabled:
            return True

        keywords = self._query_keywords(query)
        if not keywords:
            return True

        title = str(job.get("title") or "").lower()
        desc = str(job.get("description_preview") or job.get("full_description") or "").lower()
        skills = " ".join(str(s).lower() for s in (job.get("skills") or []))
        searchable = f"{title} {desc} {skills}"
        return all(k in searchable for k in keywords)

    def _fetch_query_once(self, query: str, capture_data: dict, capture_file: Path, upwork_url: str):
        """Single-query fetch worker used by thread pool."""
        print(f"\n🔍 SEARCHING: '{query}'...")
        print(f"⏳ Fetching from Upwork for '{query}'...")
        result = fetch_from_capture_data(
            capture_data=capture_data,
            upwork_url=upwork_url,
            user_query=query,
            use_seleniumbase_on_403=True,
            capture_path=capture_file,
        )
        graphql_has_errors = (
            result.status_code == 200
            and isinstance(result.body, dict)
            and bool(result.body.get("errors"))
        )
        formatted_jobs = format_response(result.body) if result.status_code == 200 and result.body else []
        return result, graphql_has_errors, formatted_jobs, None

    def _build_job_embed(self, job: dict) -> discord.Embed:
        title = job.get("title", "N/A")
        budget_display = job.get("budget_display") or "Not specified"
        skills = ", ".join(job.get("skills", [])[:5]) if job.get("skills") else "Not specified"
        description = (job.get("description_preview") or "").strip() or "No description in feed (GraphQL may omit it)."
        job_id = job.get("id", "")
        job_type = job.get("job_type", "").title() if job.get("job_type") else "Job"
        job_url = job.get("job_url")

        embed = discord.Embed(
            title=f"💼 {title}",
            description=description[:4096] if description else None,
            color=discord.Color.green(),
            url=job_url if job_url else None,
        )
        embed.add_field(name="📋 Type", value=job_type, inline=True)
        embed.add_field(name="💰 Budget", value=budget_display, inline=True)
        embed.add_field(name="🛠️ Skills", value=skills, inline=False)
        if job_url:
            link_block = f"[Open job posting]({job_url})"
        else:
            link_block = "Job link unavailable (missing `ciphertext` in API response)."
        embed.add_field(name="🔗 Upwork", value=link_block, inline=False)
        embed.set_footer(text=f"Job ID: {job_id}")
        return embed

    async def _post_single_job(self, channel, job: dict, semaphore: asyncio.Semaphore) -> bool:
        async with semaphore:
            try:
                embed = self._build_job_embed(job)
                sent_message = await self._send_embed_to_channel(channel, embed)
                await self._post_job_details_thread(sent_message, dict(job))
                self.logger.info("Posted job to #%s: %s", channel.name, job.get("title", "N/A"))
                print(f"✅ Posted: {job.get('title', 'N/A')}")
                return True
            except Exception as e:
                self.logger.error("Failed to post job: %s", e)
                print(f"❌ Failed to post job: {e}")
                return False

    async def _post_jobs_batch(self, channel, jobs: list[dict]) -> tuple[int, int]:
        """
        Post multiple jobs concurrently (bounded) to reduce sequential delay.
        """
        max_concurrent_posts = int(os.getenv("MAX_CONCURRENT_POSTS", "3"))
        semaphore = asyncio.Semaphore(max(1, max_concurrent_posts))
        tasks = [self._post_single_job(channel, job, semaphore) for job in jobs]
        results = await asyncio.gather(*tasks, return_exceptions=False)
        ok_count = sum(1 for r in results if r)
        fail_count = len(results) - ok_count
        return ok_count, fail_count

    async def _post_job_details_thread(self, message, job: dict) -> None:
        """Create one thread per job and post full details."""
        try:
            title = str(job.get("title") or "Job Details").strip()[:80] or "Job Details"
            thread = await message.create_thread(
                name=f"{title} - details",
                auto_archive_duration=1440,
            )
        except Exception as e:
            self.logger.warning("Failed creating thread for job %s: %s", job.get("id"), e)
            return

        details_lines = [
            f"**Title:** {job.get('title') or 'N/A'}",
            f"**Job ID:** `{job.get('id') or 'N/A'}`",
            f"**Type:** {str(job.get('job_type') or 'UNKNOWN').title()}",
            f"**Budget:** {job.get('budget_display') or 'Not specified'}",
            f"**Skills:** {', '.join(job.get('skills', [])[:20]) if job.get('skills') else 'Not specified'}",
        ]
        job_url = job.get("job_url")
        if job_url:
            details_lines.append(f"**Link:** {job_url}")
        details_lines.extend(
            [
                "",
                "**Full Description:**",
                (job.get("full_description") or job.get("description_preview") or "No description available.").strip(),
            ]
        )

        content = "\n".join(details_lines).strip()
        if not content:
            return

        chunk_size = 1900
        for start in range(0, len(content), chunk_size):
            await thread.send(content[start : start + chunk_size])

    async def _ensure_channel_exists(self, query: str) -> discord.TextChannel | None:
        """Ensure channel exists for query - validate or recreate if needed."""
        try:
            # Try to get existing channel
            channel = await self.upwork_cog.get_query_channel(query)
            if channel:
                return channel
            
            # Channel doesn't exist, recreate it
            print(f"  🔄 Recreating channel for '{query}'...")
            guild = self.bot.guilds[0] if self.bot.guilds else None
            if not guild:
                return None
            
            channel_name = self.upwork_cog.sanitize_channel_name(query)
            new_channel = await guild.create_text_channel(
                channel_name,
                topic=f"Upwork jobs for: {query}"
            )
            self.upwork_cog.query_channels[query] = new_channel.id
            self.upwork_cog.save_channels()
            print(f"  ✅ Channel recreated: #{channel_name}")
            return new_channel
        except Exception as e:
            print(f"  ❌ Channel validation failed for '{query}': {e}")
            return None

    async def run(self) -> None:
        """Run the bot."""
        try:
            self.logger.info("Initializing bot...")
            await self.initialize_bot()
            self.logger.info("Bot initialized successfully")

            # Start polling thread
            self.logger.info("Starting polling thread...")
            self.polling_thread = threading.Thread(
                target=self.polling_loop_thread, daemon=True
            )
            self.polling_thread.start()
            self.logger.info("Polling thread started")

            # Start bot
            self.logger.info("Starting Discord bot...")
            token = os.getenv("DISCORD_BOT_TOKEN")
            await self.bot.start(token)
        except KeyboardInterrupt:
            self.logger.info("Shutting down...")
            self.should_stop = True
            if self.polling_thread and self.polling_thread.is_alive():
                self.polling_thread.join(timeout=5)
            if self.bot:
                await self.bot.close()
        except Exception as e:
            self.logger.critical(f"Fatal error: {e}", exc_info=True)
            raise


async def main() -> None:
    """Main entry point."""
    # Load .env
    from dotenv import load_dotenv

    env_file = Path(__file__).parent / ".env"
    if env_file.exists():
        load_dotenv(env_file)

    # Configure logging early so all modules write to same handlers.
    log_level = os.getenv("LOG_LEVEL", "INFO")
    log_dir = Path(os.getenv("LOG_DIR", "logs"))
    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = log_dir / f"polling_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
    setup_logging(
        log_level=log_level,
        log_file=log_file,
        console_output=True,
        cleanup_retention_days=int(os.getenv("LOG_RETENTION_DAYS", "10")),
    )
    # Child loggers (e.g., "discord_bot") should inherit handlers from configured logger.
    get_logger("discord_bot").setLevel(get_logger("upwork_bot").level)

    runner = UpworkBotRunner()
    await runner.run()


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())

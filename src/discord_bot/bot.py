"""Discord bot for Upwork job scraper with multi-query polling."""

import asyncio
import json
import re
from pathlib import Path
from typing import Optional

import discord
from discord.ext import commands, tasks


class UpworkBot(commands.Cog, name="UpworkBot"):
    """Discord bot for managing Upwork job polling."""

    QUERIES_FILE = Path("data/queries.json")
    CHANNELS_FILE = Path("data/query_channels.json")
    ALIASES_FILE = Path("data/query_aliases.json")
    DEFAULT_QUERY_ALIASES = {
        "python": {
            "python",
            "python3",
            "py",
            "py3",
        },
        "react": {
            "react",
            "reactjs",
            "react js",
            "react-js",
        },
        "web development": {
            "web",
            "web dev",
            "web develope",
            "web developer",
            "web development",
        },
    }

    def __init__(self, bot: commands.Bot):
        """Initialize the bot cog."""
        self.bot = bot
        self.polling_active = False
        self.polling_task: Optional[asyncio.Task] = None
        self.query_aliases = self._load_query_aliases()
        self.load_channels()
        self.load_queries()

    def load_queries(self) -> None:
        """Load active search queries from file."""
        if self.QUERIES_FILE.exists():
            try:
                with open(self.QUERIES_FILE) as f:
                    data = json.load(f)
                    self.queries = data.get("queries", {})
                    self.polling_interval = data.get("polling_interval", 180)
            except Exception:
                self.queries = {"web dev": True}
                self.polling_interval = 180
        else:
            self.queries = {"web dev": True}
            self.polling_interval = 180
        before_queries = dict(self.queries)
        before_channels = dict(self.query_channels)
        self._canonicalize_query_state()
        if self.queries != before_queries:
            self.save_queries()
        if self.query_channels != before_channels:
            self.save_channels()

    def _load_query_aliases(self) -> dict[str, set[str]]:
        """
        Load alias groups from data/query_aliases.json and merge with defaults.
        File shape:
        {
          "python": ["python", "py", "python3", "py3"],
          "react": ["react", "reactjs", "react js", "react-js"]
        }
        """
        aliases: dict[str, set[str]] = {
            k: set(v) for k, v in self.DEFAULT_QUERY_ALIASES.items()
        }
        if not self.ALIASES_FILE.exists():
            return aliases

        try:
            with open(self.ALIASES_FILE, encoding="utf-8") as f:
                payload = json.load(f)
            if isinstance(payload, dict):
                for canonical, values in payload.items():
                    c = str(canonical).strip().lower()
                    if not c:
                        continue
                    raw_list = values if isinstance(values, list) else []
                    merged_values = {str(x).strip().lower() for x in raw_list if str(x).strip()}
                    merged_values.add(c)
                    aliases[c] = aliases.get(c, set()) | merged_values
        except Exception:
            # Keep defaults if user file is malformed.
            pass

        return aliases

    @staticmethod
    def _compact_query(text: str) -> str:
        """Lowercase and remove non-alphanumeric chars for fuzzy alias matching."""
        return re.sub(r"[^a-z0-9]+", "", text.lower())

    @staticmethod
    def _clean_query_text(query: str) -> str:
        """Normalize user-provided query text before alias matching."""
        clean = str(query).strip().lower()
        # Users often send quoted phrases via Discord, e.g. "wordpress".
        if len(clean) >= 2 and clean[0] == clean[-1] and clean[0] in {"'", '"', "`"}:
            clean = clean[1:-1].strip()
        clean = re.sub(r"\s+", " ", clean)
        # Normalize common typos seen in channel/query names.
        typo_map = {
            "developement": "development",
            "developepr": "developer",
        }
        for wrong, right in typo_map.items():
            clean = clean.replace(wrong, right)
        return clean

    def _normalize_query(self, query: str) -> tuple[str, str | None]:
        """Normalize aliases to one canonical query key."""
        clean_query = self._clean_query_text(query)

        for canonical, aliases in self.query_aliases.items():
            if clean_query == canonical or clean_query in aliases:
                return canonical, clean_query

        compact = self._compact_query(clean_query)
        for canonical, aliases in self.query_aliases.items():
            canonical_compact = self._compact_query(canonical)
            if compact == canonical_compact:
                return canonical, clean_query
            for alias in aliases:
                if compact == self._compact_query(alias):
                    return canonical, clean_query
        return clean_query, None

    def _canonicalize_query_state(self) -> None:
        """
        Merge persisted legacy/alias keys into canonical keys.
        This keeps old data files compatible after alias rules change.
        """
        merged_queries: dict[str, bool] = {}
        merged_channels: dict[str, int] = {}

        for key, enabled in self.queries.items():
            canonical, _ = self._normalize_query(str(key))
            merged_queries[canonical] = bool(enabled) or merged_queries.get(canonical, False)

        for key, channel_id in self.query_channels.items():
            canonical, _ = self._normalize_query(str(key))
            if canonical not in merged_channels:
                merged_channels[canonical] = channel_id

        self.queries = merged_queries
        self.query_channels = merged_channels

    def load_channels(self) -> None:
        """Load query to channel mappings."""
        if self.CHANNELS_FILE.exists():
            try:
                with open(self.CHANNELS_FILE) as f:
                    self.query_channels = json.load(f)
            except Exception:
                self.query_channels = {}
        else:
            self.query_channels = {}

    def save_queries(self) -> None:
        """Save active search queries to file."""
        self.QUERIES_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(self.QUERIES_FILE, "w") as f:
            json.dump(
                {
                    "queries": self.queries,
                    "polling_interval": self.polling_interval,
                },
                f,
                indent=2,
            )

    def save_channels(self) -> None:
        """Save query to channel mappings."""
        self.CHANNELS_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(self.CHANNELS_FILE, "w") as f:
            json.dump(self.query_channels, f, indent=2)
    
    def sanitize_channel_name(self, text: str) -> str:
        """Convert text to valid Discord channel name."""
        # Replace spaces with hyphens, remove special chars
        name = text.lower().replace(" ", "-")
        name = "".join(c for c in name if c.isalnum() or c == "-")
        # Discord channel names: 2-100 chars, lowercase, alphanumeric + hyphens
        name = name.strip("-")[:100]
        if len(name) < 2:
            name = "jobs"
        return name

    def _channel_name_to_query_text(self, channel_name: str) -> str:
        """Approximate query text from a Discord channel name."""
        return str(channel_name).strip().lower().replace("-", " ")

    def _is_channel_alias_match(self, query: str, channel_name: str) -> bool:
        """
        Check if a channel name is equivalent to the query under alias normalization.
        Example: query='reactjs' and channel='react-js' -> True.
        """
        channel_query_text = self._channel_name_to_query_text(channel_name)
        query_canonical, _ = self._normalize_query(query)
        channel_canonical, _ = self._normalize_query(channel_query_text)
        if query_canonical == channel_canonical:
            return True
        return self._compact_query(query) == self._compact_query(channel_query_text)

    def _find_alias_channel(self, guild: discord.Guild, query: str) -> Optional[discord.TextChannel]:
        """Find an existing guild channel that matches query aliases/canonical form."""
        for channel in guild.channels:
            if isinstance(channel, discord.TextChannel) and self._is_channel_alias_match(query, channel.name):
                return channel
        return None

    def get_active_queries(self) -> list[str]:
        """Get list of active (enabled) queries."""
        return [q for q, enabled in self.queries.items() if enabled]

    async def get_query_channel(self, query: str) -> Optional[discord.TextChannel]:
        """Get the Discord channel for a query."""
        if query not in self.query_channels:
            return None
        
        channel_id = self.query_channels[query]
        # Try to get from bot's cache first
        channel = self.bot.get_channel(channel_id)
        if channel:
            return channel
        
        # Otherwise try to fetch from Discord
        try:
            channel = await self.bot.fetch_channel(channel_id)
            return channel
        except:
            return None

    async def on_ready(self) -> None:
        """Bot ready event."""
        print(f"✓ Bot logged in as {self.bot.user}")
        print(f"✓ Watching over {len(self.bot.guilds)} guild(s)")

    @commands.command(name="query_add")
    async def query_add(self, ctx: commands.Context, *, query: str) -> None:
        """Add a new search query and create a channel. Usage: !query_add web development"""
        if len(query.strip()) < 2:
            await ctx.send("❌ Query must be at least 2 characters")
            return

        clean_query, alias_used = self._normalize_query(query)
        channel_name = self.sanitize_channel_name(clean_query)
        
        # Check if query already exists
        if clean_query in self.queries:
            self.queries[clean_query] = True
            self.save_queries()
            
            # Auto-start polling if not already running
            if not self.polling_active:
                self.polling_active = True
                alias_note = f"\nℹ️ Normalized `{alias_used}` -> `{clean_query}`" if alias_used and alias_used != clean_query else ""
                await ctx.send(
                    f"✓ Re-enabled query: `{clean_query}`{alias_note}\n🔍 **Polling started automatically!** Searching for jobs now..."
                )
            else:
                alias_note = f"\nℹ️ Normalized `{alias_used}` -> `{clean_query}`" if alias_used and alias_used != clean_query else ""
                await ctx.send(f"✓ Re-enabled query: `{clean_query}`{alias_note}\n🔄 Already polling - will search for this query")
            return

        # Create new channel for this query
        try:
            # Check if channel already exists
            existing_channel = discord.utils.get(ctx.guild.channels, name=channel_name)
            if not existing_channel:
                # Alias-aware fallback: reuse equivalent channel title if already present
                existing_channel = self._find_alias_channel(ctx.guild, clean_query)
            if not existing_channel:
                # Create new channel
                channel = await ctx.guild.create_text_channel(
                    channel_name,
                    topic=f"Upwork jobs for: {clean_query}"
                )
                await channel.send(f"🎯 **New Search Channel**\nSearching for: `{clean_query}`")
                self.query_channels[clean_query] = channel.id
                self.save_channels()
                alias_note = f"\nℹ️ Normalized `{alias_used}` -> `{clean_query}`" if alias_used and alias_used != clean_query else ""
                await ctx.send(f"✓ Added query: `{clean_query}`{alias_note}\n📍 Created channel: #{channel_name}")
            else:
                # Channel exists, just map it
                self.query_channels[clean_query] = existing_channel.id
                self.save_channels()
                alias_note = f"\nℹ️ Normalized `{alias_used}` -> `{clean_query}`" if alias_used and alias_used != clean_query else ""
                await ctx.send(f"✓ Added query: `{clean_query}`{alias_note}\n📍 Using existing channel: #{channel_name}")
        except discord.Forbidden:
            await ctx.send("❌ I don't have permission to create channels. Please give me channel management permissions.")
            return
        except Exception as e:
            await ctx.send(f"❌ Error creating channel: {str(e)}")
            return

        # Add query to list
        self.queries[clean_query] = True
        self.save_queries()
        
        # Auto-start polling if not already running
        if not self.polling_active:
            self.polling_active = True
            await ctx.send("🔍 **Polling started automatically!** Searching for jobs now...")

    @commands.command(name="query_remove")
    async def query_remove(self, ctx: commands.Context, *, query: str) -> None:
        """Remove/disable a search query. Usage: !query_remove web development"""
        clean_query, alias_used = self._normalize_query(query)
        if clean_query not in self.queries:
            await ctx.send(f"❌ Query not found: `{clean_query}`")
            return

        self.queries[clean_query] = False
        self.save_queries()
        alias_note = f"\nℹ️ Normalized `{alias_used}` -> `{clean_query}`" if alias_used and alias_used != clean_query else ""
        await ctx.send(f"✓ Disabled query: `{clean_query}`{alias_note}")

    @commands.command(name="query_list")
    async def query_list(self, ctx: commands.Context) -> None:
        """List all queries (enabled/disabled)."""
        if not self.queries:
            await ctx.send("No queries configured")
            return

        lines = ["**Active Queries:**"]
        for query, enabled in self.queries.items():
            status = "✓ ON" if enabled else "✗ OFF"
            lines.append(f"`{status}` - {query}")

        lines.append(f"\n**Polling Interval:** {self.polling_interval}s")
        await ctx.send("\n".join(lines))

    @commands.command(name="polling_status")
    async def polling_status(self, ctx: commands.Context) -> None:
        """Check polling status with detailed info."""
        status = "🟢 RUNNING" if self.polling_active else "🔴 STOPPED"
        active = self.get_active_queries()
        
        # Count total jobs from database
        total_jobs = 0
        try:
            from src.storage import SQLiteStore
            store = SQLiteStore(Path("data/runtime.db"))
            from pathlib import Path
            total_jobs = len(store.load_recent_job_ids("", limit=1000))
        except:
            total_jobs = 0
        
        # Build detailed status message
        embed = discord.Embed(title="📊 Polling Status", color=discord.Color.green() if self.polling_active else discord.Color.red())
        embed.add_field(name="Status", value=status, inline=False)
        embed.add_field(name="Active Queries", value=str(len(active)), inline=True)
        embed.add_field(name="Polling Interval", value=f"{self.polling_interval}s", inline=True)
        embed.add_field(name="Total Jobs Cached", value=str(total_jobs), inline=True)
        
        if active:
            embed.add_field(
                name="Queries",
                value="\n".join([f"• {q}" for q in active]),
                inline=False
            )
        
        embed.set_footer(text="Use !help_upwork for all commands")
        await ctx.send(embed=embed)

    @commands.command(name="polling_start")
    async def polling_start(self, ctx: commands.Context) -> None:
        """Start the polling loop."""
        if self.polling_active:
            await ctx.send("⚠️ Polling already running")
            return

        active = self.get_active_queries()
        if not active:
            await ctx.send("❌ No active queries. Use `!query_add` first")
            return

        self.polling_active = True
        await ctx.send(f"🟢 **Polling started** with {len(active)} queries")
        # The actual polling is managed by module3_polling_loop with this flag

    @commands.command(name="polling_stop")
    async def polling_stop(self, ctx: commands.Context) -> None:
        """Stop the polling loop."""
        if not self.polling_active:
            await ctx.send("⚠️ Polling not running")
            return

        self.polling_active = False
        await ctx.send("🔴 **Polling stopped**")

    @commands.command(name="interval_set")
    async def interval_set(self, ctx: commands.Context, seconds: int) -> None:
        """Set polling interval in seconds. Usage: !interval_set 120"""
        if seconds < 20:
            await ctx.send("❌ Interval must be at least 20 seconds")
            return

        self.polling_interval = seconds
        self.save_queries()
        await ctx.send(f"✓ Polling interval set to {seconds} seconds")

    @commands.command(name="help_upwork")
    async def help_upwork(self, ctx: commands.Context) -> None:
        """Show available commands."""
        embed = discord.Embed(
            title="🤖 Upwork Bot Commands",
            description="Control the bot via Discord directly!",
            color=discord.Color.blue()
        )
        
        embed.add_field(
            name="📝 Query Management",
            value=(
                "`!query_add <query>` - Add search query\n"
                "`!query_remove <query>` - Remove/disable query\n"
                "`!query_list` - Show all queries"
            ),
            inline=False
        )
        
        embed.add_field(
            name="🔄 Polling Control",
            value=(
                "`!polling_start` - Start polling\n"
                "`!polling_stop` - Stop polling\n"
                "`!polling_status` - Check status"
            ),
            inline=False
        )
        
        embed.add_field(
            name="⚙️ Configuration",
            value="`!interval_set <seconds>` - Set polling interval",
            inline=False
        )
        
        embed.set_footer(text="Example: !query_add 'WordPress Developer'")
        await ctx.send(embed=embed)


def setup_bot(token: str) -> commands.Bot:
    """Create and configure the Discord bot."""
    intents = discord.Intents.default()
    intents.message_content = True
    bot = commands.Bot(command_prefix="!", intents=intents)

    @bot.event
    async def on_ready() -> None:
        """Called when bot is ready."""
        print(f"✓ Bot logged in as {bot.user}")

    async def load_cogs() -> None:
        """Load bot cogs."""
        await bot.add_cog(UpworkBot(bot))

    asyncio.create_task(load_cogs())
    return bot

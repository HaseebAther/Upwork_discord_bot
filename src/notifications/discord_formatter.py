"""Discord embed formatter that replicates Upwork's job display."""

from datetime import datetime
from typing import Any, Optional
import json


class JobEmbed:
    """Build Discord embeds similar to Upwork job listings."""

    def __init__(self, job: dict[str, Any], query: str | None = None):
        self.job = job
        self.query = query
        self.job_id = str(job.get("id", "unknown"))
        self.title = str(job.get("title", "Untitled Job"))
        self.description = str(job.get("description_preview", ""))
        self.job_type = str(job.get("job_type", "UNKNOWN"))
        self.budget_display = str(job.get("budget_display", "Not specified"))
        self.budget_type = str(job.get("budget_type", "unspecified"))
        self.publish_time = str(job.get("publish_time", ""))
        self.skills = job.get("skills", []) if isinstance(job.get("skills"), list) else []

    def get_upwork_url(self) -> str:
        """Generate Upwork job URL (uses cipherText slug, not numeric GraphQL id)."""
        direct = self.job.get("job_url")
        if direct:
            return str(direct)
        ct = self.job.get("ciphertext") or self.job.get("cipherText")
        if ct:
            s = str(ct).strip()
            if s.startswith("http"):
                return s
            path = s if s.startswith("~") else f"~{s}"
            return f"https://www.upwork.com/jobs/{path}"
        return ""

    def get_color(self) -> int:
        """Get color based on job type and budget."""
        if self.budget_type == "fixed":
            return 0x14A085  # Upwork green
        elif self.budget_type == "hourly":
            return 0x4A7BA7  # Upwork blue
        else:
            return 0x999999  # Gray

    def build_embed(self) -> dict[str, Any]:
        """Build Discord embed (for future use if switching to bot)."""
        return {
            "title": self.title[:256],
            "description": self.description[:4096],
            "url": self.get_upwork_url(),
            "color": self.get_color(),
            "fields": [
                {"name": "Job Type", "value": self.format_job_type(), "inline": True},
                {"name": "Budget", "value": self.budget_display, "inline": True},
                {"name": "Skills", "value": self.format_skills(), "inline": False},
            ] + ([{"name": "Query", "value": self.query, "inline": True}] if self.query else []),
            "footer": {"text": f"Job ID: {self.job_id}"},
            "timestamp": self.publish_time,
        }

    def format_job_type(self) -> str:
        """Format job type for display."""
        type_map = {
            "FIXED": "✓ Fixed Price",
            "HOURLY": "⏱ Hourly",
            "NTC": "TBD",
        }
        return type_map.get(self.job_type, f"• {self.job_type}")

    def format_skills(self) -> str:
        """Format skills for display."""
        if not self.skills:
            return "No skills listed"
        
        # Limit to 10 skills, join with commas
        displayed_skills = self.skills[:10]
        skills_text = ", ".join(str(s).strip() for s in displayed_skills if s)
        
        if len(self.skills) > 10:
            return f"{skills_text}, +{len(self.skills) - 10} more"
        
        return skills_text if skills_text else "No skills listed"

    def format_compact_message(self) -> str:
        """Format compact message for webhook posting."""
        lines = [
            f"**{self.title}**",
            "",
            f"🏷️ **Type:** {self.format_job_type()}",
            f"💰 **Budget:** {self.budget_display}",
        ]
        
        if self.skills:
            lines.append(f"🛠️ **Skills:** {self.format_skills()}")
        
        if self.query:
            lines.append(f"🔍 **Query:** {self.query}")
        
        if self.description:
            lines.append(f"\n📝 **Description:**\n{self.description}")
        
        url = self.get_upwork_url()
        if url:
            lines.append(f"\n[View on Upwork]({url})")
        
        return "\n".join(lines)

    def format_detail_message(self) -> str:
        """Format detailed message for threads."""
        job_type_full = {
            "FIXED": "Fixed Price",
            "HOURLY": "Hourly",
            "NTC": "To Be Determined",
        }.get(self.job_type, self.job_type)
        
        lines = [
            f"**Job Details for:** {self.title}",
            "",
            f"**Job ID:** `{self.job_id}`",
            f"**Type:** {job_type_full}",
            f"**Budget:** {self.budget_display}",
            f"**Published:** {self.publish_time}",
            "",
            f"**Skills Required:**",
        ]
        
        if self.skills:
            for i, skill in enumerate(self.skills, 1):
                lines.append(f"  {i}. {skill}")
        else:
            lines.append("  • No skills listed")
        
        job_url = self.job.get("job_url") or self.get_upwork_url()
        lines.extend(
            [
                "",
                f"**Description:**",
                f"{self.description}",
                "",
                f"**Links:**",
            ]
        )
        if job_url:
            lines.append(f"• [View Full Job]({job_url})")
        else:
            lines.append("• (Job URL needs `ciphertext` from API — see formatter)")
        
        return "\n".join(lines)


def get_channel_name_from_job(job: dict[str, Any]) -> str:
    """
    Generate a safe Discord channel name from job title and ID.
    Channel names: 15-100 characters, lowercase, hyphens/underscores.
    """
    title = str(job.get("title", "job")).lower()
    job_id = str(job.get("id", ""))
    
    # Keep only alphanumeric and hyphens
    safe_title = "".join(c if c.isalnum() or c == " " else "" for c in title)
    safe_title = "-".join(safe_title.split())[:30]  # Limit to 30 chars
    
    # Add job ID for uniqueness
    channel_name = f"{safe_title}-{job_id}"[:100]
    
    return channel_name.lower().strip("-")


def get_thread_name_from_job(job: dict[str, Any]) -> str:
    """Generate a thread name for detailed job discussion."""
    title = str(job.get("title", "job"))
    budget = str(job.get("budget_display", ""))
    
    # Create thread name like: "Job Title - $1000 - Fixed"
    thread_name = f"{title} - {budget}"[:100]
    
    return thread_name


def extract_full_job_data(item: dict[str, Any]) -> dict[str, Any]:
    """
    Extract all available job data including raw fields.
    This preserves complete information for storage and threads.
    """
    job_tile = item.get("jobTile", {}) if isinstance(item, dict) else {}
    job_data = job_tile.get("job", {}) if isinstance(job_tile, dict) else {}
    
    return {
        "id": item.get("id") or job_data.get("id"),
        "title": item.get("title", ""),
        "description": item.get("description", ""),
        "full_description": item.get("description", ""),  # Keep full description
        "job_type": job_data.get("jobType"),
        "skills": [
            skill.get("prettyName") or skill.get("prefLabel", "")
            for skill in item.get("ontologySkills", []) if isinstance(skill, dict)
        ],
        "publish_time": job_data.get("publishTime", ""),
        "create_time": job_data.get("createTime", ""),
        "contractor_tier": job_data.get("contractorTier", ""),
        "fixed_price": job_data.get("fixedPriceAmount", {}).get("amount") if isinstance(job_data.get("fixedPriceAmount"), dict) else None,
        "fixed_currency": job_data.get("fixedPriceAmount", {}).get("isoCurrencyCode") if isinstance(job_data.get("fixedPriceAmount"), dict) else None,
        "hourly_min": job_data.get("hourlyBudgetMin"),
        "hourly_max": job_data.get("hourlyBudgetMax"),
        "raw_data": item,  # Store raw for reference
    }

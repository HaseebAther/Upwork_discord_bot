import re
from typing import Any

HIGHLIGHT_START = "H^"
HIGHLIGHT_END = "^H"


def clean_highlight_markup(text: str) -> str:
    if not text:
        return ""
    return text.replace(HIGHLIGHT_START, "").replace(HIGHLIGHT_END, "")


def normalize_text(text: str) -> str:
    clean = clean_highlight_markup(text)
    return re.sub(r"\s+", " ", clean).strip()


def _extract_results(body: dict[str, Any]) -> list[dict[str, Any]]:
    data = body.get("data", {}) if isinstance(body, dict) else {}
    search = data.get("search", {}) if isinstance(data, dict) else {}
    universal = search.get("universalSearchNuxt", {}) if isinstance(search, dict) else {}
    visitor = universal.get("visitorJobSearchV1", {}) if isinstance(universal, dict) else {}
    results = visitor.get("results", []) if isinstance(visitor, dict) else []
    return results if isinstance(results, list) else []


def format_job(item: dict[str, Any]) -> dict[str, Any]:
    job_tile = item.get("jobTile", {}) if isinstance(item, dict) else {}
    job_data = job_tile.get("job", {}) if isinstance(job_tile, dict) else {}

    title = normalize_text(str(item.get("title", "")))
    description = normalize_text(str(item.get("description", "")))

    skills_raw = item.get("ontologySkills", []) if isinstance(item, dict) else []
    skills: list[str] = []
    if isinstance(skills_raw, list):
        for skill in skills_raw:
            if not isinstance(skill, dict):
                continue
            name = skill.get("prettyName") or skill.get("prefLabel") or ""
            if name:
                skills.append(normalize_text(str(name)))

    fixed_price = job_data.get("fixedPriceAmount", {}) if isinstance(job_data, dict) else {}

    return {
        "id": item.get("id") or job_data.get("id"),
        "title": title,
        "description_preview": description[:280],
        "job_type": job_data.get("jobType"),
        "hourly_budget_min": job_data.get("hourlyBudgetMin"),
        "hourly_budget_max": job_data.get("hourlyBudgetMax"),
        "fixed_budget": fixed_price.get("amount") if isinstance(fixed_price, dict) else None,
        "fixed_budget_currency": fixed_price.get("isoCurrencyCode") if isinstance(fixed_price, dict) else None,
        "publish_time": job_data.get("publishTime"),
        "create_time": job_data.get("createTime"),
        "skills": skills,
    }


def format_response(body: dict[str, Any]) -> list[dict[str, Any]]:
    results = _extract_results(body)
    formatted: list[dict[str, Any]] = []
    for item in results:
        if isinstance(item, dict):
            formatted.append(format_job(item))
    return formatted

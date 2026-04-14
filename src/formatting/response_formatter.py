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


def _as_text_or_none(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text if text else None


def _build_budget_fields(job_data: dict[str, Any], fixed_price: dict[str, Any]) -> tuple[str, str | None]:
    fixed_amount = _as_text_or_none(fixed_price.get("amount")) if isinstance(fixed_price, dict) else None
    currency = _as_text_or_none(fixed_price.get("isoCurrencyCode")) if isinstance(fixed_price, dict) else None

    hourly_min = _as_text_or_none(job_data.get("hourlyBudgetMin"))
    hourly_max = _as_text_or_none(job_data.get("hourlyBudgetMax"))

    if fixed_amount:
        if currency:
            return "fixed", f"{fixed_amount} {currency}"
        return "fixed", fixed_amount

    if hourly_min and hourly_max:
        return "hourly", f"{hourly_min}-{hourly_max}/hr"
    if hourly_min:
        return "hourly", f"from {hourly_min}/hr"
    if hourly_max:
        return "hourly", f"up to {hourly_max}/hr"

    return "unspecified", None


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
    budget_type, budget_display = _build_budget_fields(job_data, fixed_price)

    return {
        "id": item.get("id") or job_data.get("id"),
        "title": title,
        "description_preview": description[:280],
        "job_type": job_data.get("jobType"),
        "budget_type": budget_type,
        "budget_display": budget_display,
        "hourly_budget_min": _as_text_or_none(job_data.get("hourlyBudgetMin")),
        "hourly_budget_max": _as_text_or_none(job_data.get("hourlyBudgetMax")),
        "fixed_budget": _as_text_or_none(fixed_price.get("amount")) if isinstance(fixed_price, dict) else None,
        "fixed_budget_currency": _as_text_or_none(fixed_price.get("isoCurrencyCode")) if isinstance(fixed_price, dict) else None,
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

from src.formatting.response_formatter import upwork_job_urls, format_job


def test_upwork_job_urls_from_ciphertext():
    view, apply = upwork_job_urls("~022044961869610508366")
    assert view == "https://www.upwork.com/jobs/~022044961869610508366"
    assert apply == "https://www.upwork.com/jobs/~022044961869610508366/apply"


def test_format_job_extracts_link_and_skills():
    item = {
        "id": "123",
        "title": "React dev",
        "description": "Build dashboard",
        "ontologySkills": [{"prefLabel": "React"}],
        "jobTile": {
            "job": {
                "id": "123",
                "ciphertext": "~000123",
                "jobType": "FIXED",
                "fixedPriceAmount": {"amount": "100", "isoCurrencyCode": "USD"},
            }
        },
    }
    out = format_job(item)
    assert out["job_url"] == "https://www.upwork.com/jobs/~000123"
    assert out["skills"] == ["React"]
    assert out["budget_display"] == "$100 USD"

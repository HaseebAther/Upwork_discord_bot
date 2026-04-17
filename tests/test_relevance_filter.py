from discord_bot import UpworkBotRunner


def _runner(enabled: bool = True):
    r = UpworkBotRunner()
    r.relevance_filter_enabled = enabled
    r.query_token_min_len = 3
    r.query_stop_words = {
        "and", "or", "the", "a", "an", "for", "to", "of", "in", "on", "with",
        "from", "by", "at", "is", "are", "be", "as",
    }
    return r


def test_query_keywords_strips_stopwords_and_short_words():
    r = _runner(True)
    assert r._query_keywords("the AI in saas development") == ["saas", "development"]


def test_relevance_requires_all_query_keywords():
    r = _runner(True)
    query = "saas development"
    job_bad = {
        "title": "Lead Generation in SaaS",
        "description_preview": "Find leads for SaaS startup",
        "skills": ["Sales", "SaaS"],
    }
    job_good = {
        "title": "SaaS development engineer",
        "description_preview": "Build and development work for SaaS platform",
        "skills": ["Python", "SaaS"],
    }
    assert r._job_relevance_match(job_bad, query) is False
    assert r._job_relevance_match(job_good, query) is True


def test_relevance_filter_can_be_disabled():
    r = _runner(False)
    query = "saas development"
    job = {
        "title": "Lead Generation in SaaS",
        "description_preview": "No dev keyword",
        "skills": ["Sales"],
    }
    assert r._job_relevance_match(job, query) is True

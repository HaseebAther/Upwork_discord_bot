from src.discord_bot.bot import UpworkBot


def _bot_for_tests():
    b = UpworkBot.__new__(UpworkBot)
    b.query_aliases = {
        "python": {"python", "python3", "py", "py3"},
        "react": {"react", "reactjs", "react js", "react-js"},
    }
    return b


def test_clean_query_text_strips_quotes_and_typos():
    assert UpworkBot._clean_query_text('"web developement"') == "web development"


def test_normalize_query_aliases():
    b = _bot_for_tests()
    canonical, original = b._normalize_query("Py3")
    assert canonical == "python"
    assert original == "py3"


def test_channel_alias_match():
    b = _bot_for_tests()
    assert b._is_channel_alias_match("reactjs", "react-js") is True

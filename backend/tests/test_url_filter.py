import re

import pytest

from app.core.url_filter import compile_url_filter, validate_url_pattern


def test_none_keeps_everything():
    keep = compile_url_filter(None)
    assert keep("https://x/en/betting/promo") is True


def test_include_filter():
    keep = compile_url_filter(r"/en/(news|lists)/")
    assert keep("https://x/en/news/a") is True
    assert keep("https://x/en/lists/b") is True
    assert keep("https://x/en/betting/c") is False


def test_exclude_filter_with_bang_prefix():
    keep = compile_url_filter(r"!/betting/")
    assert keep("https://x/en/betting/c") is False
    assert keep("https://x/en/news/a") is True


def test_validate_accepts_include_and_exclude():
    validate_url_pattern(r"/en/(news|lists)/")
    validate_url_pattern(r"!/betting/")


def test_validate_rejects_invalid_body():
    with pytest.raises(re.error):
        validate_url_pattern("[unclosed(")

    with pytest.raises(re.error):
        validate_url_pattern("![unclosed(")

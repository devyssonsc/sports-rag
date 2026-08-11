import re

from collections.abc import Callable


def compile_url_filter(pattern: str | None) -> Callable[[str], bool]:
    """Build a predicate that decides whether a URL should be kept.

    - ``None`` / empty  -> keep every URL.
    - starts with ``!``  -> exclude filter: keep URLs that do NOT match the rest.
    - otherwise          -> include filter: keep URLs that match.

    Matching uses ``re.search``, so the pattern may match anywhere in the URL.
    """
    if not pattern:
        return lambda url: True

    if pattern.startswith("!"):
        compiled = re.compile(pattern[1:])
        return lambda url: compiled.search(url) is None

    compiled = re.compile(pattern)
    return lambda url: compiled.search(url) is not None


def validate_url_pattern(pattern: str) -> None:
    """Validate the regex body of ``pattern`` (ignoring a leading ``!``).

    Raises ``re.error`` if the body is not a valid regular expression.
    """
    body = pattern[1:] if pattern.startswith("!") else pattern
    re.compile(body)

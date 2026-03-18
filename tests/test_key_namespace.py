import re

import pytest

from app.services.key_namespace import extract_prefix, validate_namespaced_key, validate_prefix


def test_validate_namespaced_key_accepts_namespace_format() -> None:
    assert validate_namespaced_key("user:1") == "user:1"
    assert validate_namespaced_key("team:user:1") == "team:user:1"


@pytest.mark.parametrize(
    ("key", "message"),
    [
        ("user", "key must use namespace format (<prefix>:<name>)"),
        (":1", "prefix must include at least one namespace segment"),
        ("user:", "key must include a name after the namespace prefix"),
        ("user::1", "prefix cannot contain empty namespace segments"),
        ("user name:1", "key cannot contain whitespace"),
    ],
)
def test_validate_namespaced_key_rejects_invalid_format(key: str, message: str) -> None:
    with pytest.raises(ValueError, match=re.escape(message)):
        validate_namespaced_key(key)


def test_extract_prefix_returns_namespace_prefix() -> None:
    assert extract_prefix("user:1") == "user:"
    assert extract_prefix("team:user:1") == "team:user:"


@pytest.mark.parametrize(
    ("prefix", "message"),
    [
        ("", "prefix is required"),
        ("user", "prefix must end with ':'"),
        (":", "prefix must include at least one namespace segment"),
        ("user::", "prefix cannot contain empty namespace segments"),
        ("user profile:", "prefix cannot contain whitespace"),
    ],
)
def test_validate_prefix_rejects_invalid_prefix(prefix: str, message: str) -> None:
    with pytest.raises(ValueError, match=re.escape(message)):
        validate_prefix(prefix)

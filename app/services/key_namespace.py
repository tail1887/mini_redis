def _contains_whitespace(value: str) -> bool:
    return any(char.isspace() for char in value)


def validate_prefix(prefix: str) -> str:
    if not prefix:
        raise ValueError("prefix is required")
    if _contains_whitespace(prefix):
        raise ValueError("prefix cannot contain whitespace")
    if not prefix.endswith(":"):
        raise ValueError("prefix must end with ':'")

    namespace = prefix[:-1]
    if not namespace:
        raise ValueError("prefix must include at least one namespace segment")
    if any(not segment for segment in namespace.split(":")):
        raise ValueError("prefix cannot contain empty namespace segments")

    return prefix


def validate_namespaced_key(key: str) -> str:
    if not key:
        raise ValueError("key is required")
    if _contains_whitespace(key):
        raise ValueError("key cannot contain whitespace")
    if ":" not in key:
        raise ValueError("key must use namespace format (<prefix>:<name>)")

    prefix, name = key.rsplit(":", 1)
    if not name:
        raise ValueError("key must include a name after the namespace prefix")

    validate_prefix(f"{prefix}:")
    return key


def extract_prefix(key: str) -> str:
    validate_namespaced_key(key)
    prefix, _ = key.rsplit(":", 1)
    return f"{prefix}:"

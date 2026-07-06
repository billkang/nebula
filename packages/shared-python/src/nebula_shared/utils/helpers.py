def version_tuple(version_str: str) -> tuple[int, ...]:
    """Parse a semver string into a sortable tuple.

    Example: "1.2.3" -> (1, 2, 3)
    """
    return tuple(int(part) for part in version_str.split("."))

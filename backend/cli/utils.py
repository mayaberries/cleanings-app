def fix_mojibake(value: str) -> str:
    """
    Works around a locale quirk (see LANG check in README): when the
    terminal's locale isn't UTF-8-aware, stdin decodes unrepresentable
    bytes using the 'surrogateescape' error handler, producing lone
    surrogate code points that look fine in the terminal but crash when
    httpx tries to UTF-8-encode them into a request body. Round-tripping
    through surrogateescape recovers the original bytes if they were
    valid UTF-8 to begin with.
    """
    try:
        return value.encode("utf-8", "surrogateescape").decode("utf-8")
    except UnicodeDecodeError:
        return value

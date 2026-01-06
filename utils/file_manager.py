import os


def ensure_file(path: str):
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    if not os.path.exists(path):
        with open(path, "w", encoding="utf-8") as f:
            f.write("")


def append_line_safe(path: str, text: str):
    ensure_file(path)
    with open(path, "a", encoding="utf-8") as f:
        f.write(text)
        if not text.endswith("\n"):
            f.write("\n")


def append_text(path: str, text: str):
    """Append text without forcing newline."""
    ensure_file(path)
    with open(path, "a", encoding="utf-8") as f:
        f.write(text)


def clear_file(path: str):
    ensure_file(path)
    with open(path, "w", encoding="utf-8") as f:
        f.write("")


def read_all_text(path: str) -> str:
    try:
        ensure_file(path)
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    except Exception as e:
        return f"<error reading file: {e}>"

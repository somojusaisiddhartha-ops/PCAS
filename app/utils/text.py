import re


WHITESPACE_PATTERN = re.compile(r"\s+")
NON_ALPHANUM_PATTERN = re.compile(r"[^a-z0-9\s]")


def normalize_text(text: str) -> str:
    lowered = text.lower()
    stripped = NON_ALPHANUM_PATTERN.sub(" ", lowered)
    compact = WHITESPACE_PATTERN.sub(" ", stripped)
    return compact.strip()


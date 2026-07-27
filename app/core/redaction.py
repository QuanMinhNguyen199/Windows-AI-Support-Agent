import re


_MAC_ADDRESS = re.compile(r"(?i)\b(?:[0-9a-f]{2}[-:]){5}[0-9a-f]{2}\b")
_WINDOWS_USER_PATH = re.compile(r"(?i)([a-z]:\\users\\)[^\\\r\n]+")
_SECRET_ASSIGNMENT = re.compile(
    r"(?i)\b(password|passwd|token|api[_-]?key|secret)\s*[:=]\s*([^\s,;]+)"
)


def redact_text(value: str) -> str:
    value = _MAC_ADDRESS.sub("[MAC_REDACTED]", value)
    value = _WINDOWS_USER_PATH.sub(r"\1[USER]", value)
    return _SECRET_ASSIGNMENT.sub(r"\1=[REDACTED]", value)

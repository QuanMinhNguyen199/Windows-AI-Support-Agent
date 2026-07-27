import re


_NO_PACKAGE_MARKERS = (
    "no installed package found",
    "no package found matching",
    "không tìm thấy gói",
)
_VERSION = re.compile(r"\b(?:v)?\d+(?:\.\d+){1,3}(?:[-+._a-z0-9]*)?\b", re.IGNORECASE)


def winget_reports_installed(output: str, package_id: str) -> bool:
    lowered = output.casefold()
    if any(marker in lowered for marker in _NO_PACKAGE_MARKERS):
        return False
    return package_id.casefold() in lowered


def extract_version(output: str, package_id: str | None = None) -> str | None:
    lines = [line.strip() for line in output.splitlines() if line.strip()]
    if package_id:
        package_lower = package_id.casefold()
        lines = [line for line in lines if package_lower in line.casefold()] or lines
    for line in lines:
        matches = _VERSION.findall(line)
        if matches:
            return matches[-1].removeprefix("v")
    return None

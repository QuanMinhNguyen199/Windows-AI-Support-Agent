import json
from pathlib import Path

from app.config import BASE_DIR
from app.core.text_normalization import normalize_vietnamese
from app.models.chat import Intent, IntentDecision, RouterSource
from app.services.software_catalog import SoftwareCatalog


DEFAULT_EXAMPLES_PATH = BASE_DIR.parent / "data" / "processed" / "intent_examples.json"

_INTENT_PRIORITY = (
    Intent.INSTALLATION_TROUBLESHOOTING,
    Intent.INTERNET_CONNECTION_ISSUE,
    Intent.NETWORK_SPEED_TEST,
    Intent.SLOW_NETWORK_DIAGNOSIS,
    Intent.WIFI_DIAGNOSIS,
    Intent.DNS_DIAGNOSIS,
    Intent.PACKET_LOSS_DIAGNOSIS,
    Intent.SOFTWARE_INSTALLATION,
    Intent.SOFTWARE_CHECK,
    Intent.SOFTWARE_UPDATE,
    Intent.SOFTWARE_RECOMMENDATION,
    Intent.NETWORK_STATUS,
    Intent.SYSTEM_INFORMATION,
    Intent.HELP,
    Intent.GREETING,
)

_SOFTWARE_ALIASES = {
    "visual studio code": "vscode",
    "vs code": "vscode",
    "vscode": "vscode",
    "node js": "nodejs",
    "node.js": "nodejs",
    "nodejs": "nodejs",
    "7 zip": "7zip",
    "7zip": "7zip",
    "libre office": "libreoffice",
    "libreoffice": "libreoffice",
    "firefox": "firefox",
    "python": "python",
    "git": "git",
    "ollama": "ollama",
    "vlc": "vlc",
    "speedtest": "speedtest",
    "speed test": "speedtest",
    "google chrome": "chrome",
    "chrome": "chrome",
    "adobe reader": "adobe-reader",
    "acrobat reader": "adobe-reader",
    "sumatra pdf": "sumatrapdf",
    "sumatrapdf": "sumatrapdf",
    "zoom": "zoom",
    "microsoft teams": "teams",
    "teams": "teams",
    "spotify": "spotify",
    "power toys": "powertoys",
    "powertoys": "powertoys",
    "everything": "everything",
    "notepad++": "notepad-plus-plus",
    "notepad plus plus": "notepad-plus-plus",
    "github desktop": "github-desktop",
    "postman": "postman",
    "windows terminal": "windows-terminal",
    "onlyoffice": "onlyoffice",
}

_INJECTION_MARKERS = (
    "bo qua moi quy tac",
    "bo qua chi dan",
    "ignore previous",
    "ignore system",
    "chay cmd",
    "chay powershell",
    "tu xac nhan",
    "tu dong xac nhan",
)


class RuleBasedIntentRouter:
    def __init__(
        self,
        *,
        examples_path: Path = DEFAULT_EXAMPLES_PATH,
        catalog: SoftwareCatalog | None = None,
    ) -> None:
        payload = json.loads(examples_path.read_text(encoding="utf-8"))
        self.examples = {
            Intent(intent): tuple(normalize_vietnamese(value) for value in values)
            for intent, values in payload.items()
        }
        self.catalog = catalog or SoftwareCatalog()

    def route(self, message: str) -> IntentDecision:
        normalized = normalize_vietnamese(message)
        if self.is_prompt_injection(normalized):
            return IntentDecision(
                intent=Intent.FALLBACK,
                confidence=0.95,
                reason="Phát hiện nội dung cố gắng thay đổi quy tắc an toàn.",
                source=RouterSource.RULE_BASED,
            )
        scores: dict[Intent, float] = {}
        for intent in _INTENT_PRIORITY:
            matches = [
                phrase
                for phrase in self.examples.get(intent, ())
                if phrase and self._contains_phrase(normalized, phrase)
            ]
            if matches:
                scores[intent] = max(1.0 + len(phrase.split()) * 0.15 for phrase in matches)

        intent = max(
            _INTENT_PRIORITY,
            key=lambda item: (scores.get(item, 0), -_INTENT_PRIORITY.index(item)),
        )
        score = scores.get(intent, 0)
        if score == 0:
            intent = Intent.FALLBACK
        software_id = self.extract_software_id(normalized)
        confidence = min(0.98, 0.45 + score / 2.5) if score else 0.2
        return IntentDecision(
            intent=intent,
            confidence=confidence,
            software_id=software_id,
            reason="Khớp rule/phrase đã kiểm duyệt." if score else "Không có rule đủ mạnh.",
            source=RouterSource.RULE_BASED,
        )

    def extract_software_id(self, message: str) -> str | None:
        normalized = normalize_vietnamese(message)
        for alias in sorted(_SOFTWARE_ALIASES, key=len, reverse=True):
            if self._contains_phrase(normalized, alias):
                software_id = _SOFTWARE_ALIASES[alias]
                try:
                    self.catalog.get(software_id)
                except ValueError:
                    continue
                return software_id
        return None

    @staticmethod
    def is_prompt_injection(message: str) -> bool:
        normalized = normalize_vietnamese(message)
        return any(marker in normalized for marker in _INJECTION_MARKERS)

    @staticmethod
    def _contains_phrase(text: str, phrase: str) -> bool:
        return f" {phrase} " in f" {text} "

import json
from pathlib import Path

from app.config import BASE_DIR
from app.models.software import SoftwareCatalogFile, SoftwareEntry, SoftwareSummary


DEFAULT_CATALOG_PATH = BASE_DIR.parent / "data" / "processed" / "software_catalog.json"


class SoftwareCatalogError(ValueError):
    """Raised when a software ID is absent from the reviewed catalog."""


class SoftwareCatalog:
    def __init__(self, path: Path = DEFAULT_CATALOG_PATH) -> None:
        payload = json.loads(path.read_text(encoding="utf-8"))
        self._entries = SoftwareCatalogFile.model_validate(payload).software

    def list(self) -> list[SoftwareSummary]:
        return [
            self._summary(software_id, entry)
            for software_id, entry in sorted(
                self._entries.items(),
                key=lambda item: (
                    item[1].display_rank,
                    item[1].display_name.casefold(),
                ),
            )
        ]

    def get(self, software_id: str) -> SoftwareEntry:
        normalized = software_id.strip().casefold()
        try:
            return self._entries[normalized]
        except KeyError as exc:
            raise SoftwareCatalogError(
                f"Phần mềm không nằm trong catalog: {software_id}"
            ) from exc

    def summary(self, software_id: str) -> SoftwareSummary:
        normalized = software_id.strip().casefold()
        return self._summary(normalized, self.get(normalized))

    @property
    def entries(self) -> dict[str, SoftwareEntry]:
        return dict(self._entries)

    @staticmethod
    def _summary(software_id: str, entry: SoftwareEntry) -> SoftwareSummary:
        return SoftwareSummary(
            id=software_id,
            display_name=entry.display_name,
            description=entry.description,
            publisher=entry.publisher,
            category=entry.category,
            audience=entry.audience,
            advanced_group=entry.advanced_group,
            display_rank=entry.display_rank,
            winget_id=entry.winget_id,
            license_note=entry.license_note,
        )

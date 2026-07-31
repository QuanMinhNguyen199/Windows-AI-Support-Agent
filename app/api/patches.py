import json
from functools import lru_cache
from pathlib import Path

from fastapi import APIRouter

from app.config import BASE_DIR
from app.models.patches import PatchNotesFile, PatchRelease

router = APIRouter(prefix="/api/patches", tags=["patches"])
PATCH_NOTES_PATH = BASE_DIR.parent / "data" / "processed" / "patch_notes.json"


@lru_cache
def load_patch_notes(path: Path = PATCH_NOTES_PATH) -> PatchNotesFile:
    payload = json.loads(path.read_text(encoding="utf-8"))
    return PatchNotesFile.model_validate(payload)


@router.get("", response_model=list[PatchRelease])
def list_patches() -> list[PatchRelease]:
    return load_patch_notes().releases


@router.get("/latest", response_model=PatchRelease)
def latest_patch() -> PatchRelease:
    return load_patch_notes().releases[0]

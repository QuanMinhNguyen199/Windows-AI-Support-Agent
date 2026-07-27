from pathlib import Path

from app.config import BASE_DIR


PROMPTS_DIR = BASE_DIR.parent / "prompts"


class PromptService:
    def __init__(self, root: Path = PROMPTS_DIR) -> None:
        self.root = root.resolve()

    def load(self, relative_path: str) -> str:
        path = (self.root / relative_path).resolve()
        if self.root not in path.parents:
            raise ValueError("Prompt path nằm ngoài prompts directory.")
        return path.read_text(encoding="utf-8").strip()

from app.core.model_selection import select_ollama_model


GIB = 1024**3


def test_select_small_model_for_low_memory() -> None:
    assert select_ollama_model(6 * GIB) == "qwen3:0.6b"


def test_select_balanced_model_for_normal_memory() -> None:
    assert select_ollama_model(8 * GIB) == "qwen3:1.7b"
    assert select_ollama_model(15 * GIB) == "qwen3:1.7b"


def test_select_fast_quality_model_for_high_memory() -> None:
    assert select_ollama_model(16 * GIB) == "qwen3:4b"

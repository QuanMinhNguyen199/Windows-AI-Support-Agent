import re
import unicodedata


_NON_WORD = re.compile(r"[^a-z0-9+#]+")


def normalize_vietnamese(value: str) -> str:
    lowered = value.casefold().replace("wi-fi", "wifi").replace("đ", "d")
    decomposed = unicodedata.normalize("NFD", lowered)
    without_marks = "".join(
        character
        for character in decomposed
        if unicodedata.category(character) != "Mn"
    )
    return " ".join(_NON_WORD.sub(" ", without_marks).split())

import unicodedata
import re


def normalize_tag_to_filename(tag: str) -> str:
    text = str(tag).strip().lower()
    text = unicodedata.normalize("NFD", text)
    text = "".join(ch for ch in text if unicodedata.category(ch) != "Mn")
    text = text.replace("&", "and")
    text = re.sub(r"[ /-]+", "_", text)
    text = re.sub(r"[^a-z0-9_]", "", text)
    text = re.sub(r"_+", "_", text)
    text = text.strip("_")
    return text
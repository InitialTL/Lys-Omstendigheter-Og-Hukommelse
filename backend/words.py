"""Fixed, reviewable stimulus lists. They are deliberately NOT machine translated.

Pilot material only. Validate phonotactic similarity and item difficulty before the study.
"""
from __future__ import annotations
import re
import unicodedata

# word, target key.  Each list has 10 distinct five-letter nonsense words.
LISTS: tuple[tuple[tuple[str, str], ...], ...] = (
    (("navor", "chair"), ("pelum", "key"), ("tarek", "apple"),
     ("mivon", "bicycle"), ("sorel", "lamp"), ("darum", "book"),
     ("fepik", "spoon"), ("lonet", "window"), ("vusar", "shoe"),
     ("kemol", "cup")),
    (("ravel", "clock"), ("porem", "bridge"), ("tusik", "flower"),
     ("kadon", "table"), ("melur", "pencil"), ("fivan", "door"),
     ("jorum", "basket"), ("vesak", "mirror"), ("lunet", "bottle"),
     ("sopir", "hat")),
    (("domir", "umbrella"), ("falek", "candle"), ("suvon", "towel"),
     ("nupel", "plate"), ("pavir", "glove"), ("lorum", "ladder"),
     ("tesik", "pillow"), ("vamer", "fork"), ("pulos", "scissors"),
     ("regan", "camera")),
)

# Display labels and accepted variants for exact, deterministic scoring.
TARGETS: dict[str, dict[str, tuple[str, ...]]] = {
    "chair": {"nb": ("stol",), "en": ("chair",)},
    "key": {"nb": ("nøkkel", "nokkel"), "en": ("key",)},
    "apple": {"nb": ("eple",), "en": ("apple",)},
    "bicycle": {"nb": ("sykkel",), "en": ("bicycle", "bike",)},
    "lamp": {"nb": ("lampe",), "en": ("lamp",)},
    "book": {"nb": ("bok",), "en": ("book",)},
    "spoon": {"nb": ("skje",), "en": ("spoon",)},
    "window": {"nb": ("vindu",), "en": ("window",)},
    "shoe": {"nb": ("sko",), "en": ("shoe",)},
    "cup": {"nb": ("kopp",), "en": ("cup", "mug")},
    "clock": {"nb": ("klokke",), "en": ("clock",)},
    "bridge": {"nb": ("bro", "bru"), "en": ("bridge",)},
    "flower": {"nb": ("blomst",), "en": ("flower",)},
    "table": {"nb": ("bord",), "en": ("table",)},
    "pencil": {"nb": ("blyant",), "en": ("pencil",)},
    "door": {"nb": ("dør", "dor"), "en": ("door",)},
    "basket": {"nb": ("kurv",), "en": ("basket",)},
    "mirror": {"nb": ("speil",), "en": ("mirror",)},
    "bottle": {"nb": ("flaske",), "en": ("bottle",)},
    "hat": {"nb": ("hatt",), "en": ("hat",)},
    "umbrella": {"nb": ("paraply",), "en": ("umbrella",)},
    "candle": {"nb": ("stearinlys", "lys"), "en": ("candle",)},
    "towel": {"nb": ("håndkle", "handkle"), "en": ("towel",)},
    "plate": {"nb": ("tallerken",), "en": ("plate",)},
    "glove": {"nb": ("hanske",), "en": ("glove",)},
    "ladder": {"nb": ("stige",), "en": ("ladder",)},
    "pillow": {"nb": ("pute",), "en": ("pillow",)},
    "fork": {"nb": ("gaffel",), "en": ("fork",)},
    "scissors": {"nb": ("saks",), "en": ("scissors",)},
    "camera": {"nb": ("kamera",), "en": ("camera",)},
}


def normalize(value: str) -> str:
    value = unicodedata.normalize("NFKD", value.strip().casefold())
    value = "".join(c for c in value if not unicodedata.combining(c))
    value = re.sub(r"[^a-z0-9æøå]+", " ", value).strip()
    return re.sub(r"\s+", " ", value)


def learning_pairs(list_id: int, language: str) -> list[dict[str, str]]:
    return [{"word": word.upper(), "meaning": TARGETS[key][language][0]}
            for word, key in LISTS[list_id]]


def recall_words(list_id: int) -> list[str]:
    return [word.upper() for word, _ in LISTS[list_id]]


def grade(list_id: int, language: str, answers: list[str]) -> tuple[int, list[bool]]:
    correct = [normalize(answer) in {
        normalize(variant) for variant in TARGETS[key][language]
    } for (_, key), answer in zip(LISTS[list_id], answers)]
    return sum(correct), correct


assert len(LISTS) == 3 and all(len(list_) == 10 for list_ in LISTS)
assert len({word for row in LISTS for word, _ in row}) == 30

"""Fixed, auditable stimuli. Each pilot list has ten distinct pronounceable nonwords.

These nonwords are designed to reduce *obvious* semantic cues, not to eliminate
mnemonics. Validate language-specific accidental meanings and list difficulty
with a multilingual pilot before conducting the definitive study.
"""
from __future__ import annotations
import re
import unicodedata

LANGUAGES = ("nb", "en", "sv", "de", "fr", "es")

# Five-letter, mostly consonant-vowel pseudowords, with no embedded object names.
# A change in stimuli constitutes a new version of the experimental protocol.
LISTS: tuple[tuple[tuple[str, str], ...], ...] = (
    (("zevup", "chair"), ("fekuz", "key"), ("vuzem", "apple"),
     ("jopiz", "bicycle"), ("zunef", "lamp"), ("kivez", "book"),
     ("puzek", "spoon"), ("vezop", "window"), ("zivuk", "shoe"),
     ("fuzep", "cup")),
    (("vakez", "clock"), ("zepik", "bridge"), ("kuzav", "flower"),
     ("zefuk", "table"), ("pazev", "pencil"), ("juzek", "door"),
     ("zopuv", "basket"), ("vezik", "mirror"), ("fuzak", "bottle"),
     ("zikip", "hat")),
    (("vuzop", "umbrella"), ("pezuk", "candle"), ("zifek", "towel"),
     ("kozev", "plate"), ("jafuz", "glove"), ("zuvik", "ladder"),
     ("pezav", "pillow"), ("vizuk", "fork"), ("fekiz", "scissors"),
     ("zokep", "camera")),
)

# The first label is displayed; all supplied variants count as correct.
# Fully reviewed, fixed vocabulary is preferable to live machine translation.
TARGETS: dict[str, dict[str, tuple[str, ...]]] = {
    "chair": {"nb": ("stol",), "en": ("chair",), "sv": ("stol",), "de": ("Stuhl",), "fr": ("chaise",), "es": ("silla",)},
    "key": {"nb": ("nøkkel", "nokkel"), "en": ("key",), "sv": ("nyckel",), "de": ("Schlüssel",), "fr": ("clé", "clef"), "es": ("llave",)},
    "apple": {"nb": ("eple",), "en": ("apple",), "sv": ("äpple",), "de": ("Apfel",), "fr": ("pomme",), "es": ("manzana",)},
    "bicycle": {"nb": ("sykkel",), "en": ("bicycle", "bike"), "sv": ("cykel",), "de": ("Fahrrad", "Rad"), "fr": ("vélo", "bicyclette"), "es": ("bicicleta", "bici")},
    "lamp": {"nb": ("lampe",), "en": ("lamp",), "sv": ("lampa",), "de": ("Lampe",), "fr": ("lampe",), "es": ("lámpara", "lampara")},
    "book": {"nb": ("bok",), "en": ("book",), "sv": ("bok",), "de": ("Buch",), "fr": ("livre",), "es": ("libro",)},
    "spoon": {"nb": ("skje",), "en": ("spoon",), "sv": ("sked",), "de": ("Löffel",), "fr": ("cuillère", "cuillere"), "es": ("cuchara",)},
    "window": {"nb": ("vindu",), "en": ("window",), "sv": ("fönster",), "de": ("Fenster",), "fr": ("fenêtre", "fenetre"), "es": ("ventana",)},
    "shoe": {"nb": ("sko",), "en": ("shoe",), "sv": ("sko",), "de": ("Schuh",), "fr": ("chaussure",), "es": ("zapato",)},
    "cup": {"nb": ("kopp",), "en": ("cup", "mug"), "sv": ("kopp",), "de": ("Tasse", "Becher"), "fr": ("tasse",), "es": ("taza",)},
    "clock": {"nb": ("klokke",), "en": ("clock",), "sv": ("klocka",), "de": ("Uhr",), "fr": ("horloge",), "es": ("reloj",)},
    "bridge": {"nb": ("bro", "bru"), "en": ("bridge",), "sv": ("bro",), "de": ("Brücke",), "fr": ("pont",), "es": ("puente",)},
    "flower": {"nb": ("blomst",), "en": ("flower",), "sv": ("blomma",), "de": ("Blume",), "fr": ("fleur",), "es": ("flor",)},
    "table": {"nb": ("bord",), "en": ("table",), "sv": ("bord",), "de": ("Tisch",), "fr": ("table",), "es": ("mesa",)},
    "pencil": {"nb": ("blyant",), "en": ("pencil",), "sv": ("blyertspenna", "penna"), "de": ("Bleistift",), "fr": ("crayon",), "es": ("lápiz", "lapiz")},
    "door": {"nb": ("dør", "dor"), "en": ("door",), "sv": ("dörr",), "de": ("Tür",), "fr": ("porte",), "es": ("puerta",)},
    "basket": {"nb": ("kurv",), "en": ("basket",), "sv": ("korg",), "de": ("Korb",), "fr": ("panier",), "es": ("cesta", "canasta")},
    "mirror": {"nb": ("speil",), "en": ("mirror",), "sv": ("spegel",), "de": ("Spiegel",), "fr": ("miroir",), "es": ("espejo",)},
    "bottle": {"nb": ("flaske",), "en": ("bottle",), "sv": ("flaska",), "de": ("Flasche",), "fr": ("bouteille",), "es": ("botella",)},
    "hat": {"nb": ("hatt",), "en": ("hat",), "sv": ("hatt",), "de": ("Hut",), "fr": ("chapeau",), "es": ("sombrero",)},
    "umbrella": {"nb": ("paraply",), "en": ("umbrella",), "sv": ("paraply",), "de": ("Regenschirm",), "fr": ("parapluie",), "es": ("paraguas",)},
    "candle": {"nb": ("stearinlys", "lys"), "en": ("candle",), "sv": ("stearinljus", "ljus"), "de": ("Kerze",), "fr": ("bougie",), "es": ("vela",)},
    "towel": {"nb": ("håndkle", "handkle"), "en": ("towel",), "sv": ("handduk",), "de": ("Handtuch",), "fr": ("serviette",), "es": ("toalla",)},
    "plate": {"nb": ("tallerken",), "en": ("plate",), "sv": ("tallrik",), "de": ("Teller",), "fr": ("assiette",), "es": ("plato",)},
    "glove": {"nb": ("hanske",), "en": ("glove",), "sv": ("handske",), "de": ("Handschuh",), "fr": ("gant",), "es": ("guante",)},
    "ladder": {"nb": ("stige",), "en": ("ladder",), "sv": ("stege",), "de": ("Leiter",), "fr": ("échelle", "echelle"), "es": ("escalera",)},
    "pillow": {"nb": ("pute",), "en": ("pillow",), "sv": ("kudde",), "de": ("Kissen",), "fr": ("oreiller",), "es": ("almohada",)},
    "fork": {"nb": ("gaffel",), "en": ("fork",), "sv": ("gaffel",), "de": ("Gabel",), "fr": ("fourchette",), "es": ("tenedor",)},
    "scissors": {"nb": ("saks",), "en": ("scissors",), "sv": ("sax",), "de": ("Schere",), "fr": ("ciseaux",), "es": ("tijeras",)},
    "camera": {"nb": ("kamera",), "en": ("camera",), "sv": ("kamera",), "de": ("Kamera",), "fr": ("appareil photo",), "es": ("cámara", "camara")},
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
assert all(set(labels) == set(LANGUAGES) for labels in TARGETS.values())

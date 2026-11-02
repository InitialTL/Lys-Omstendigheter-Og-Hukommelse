"""Fixed, auditable stimuli. Each pilot list has eight distinct pronounceable nonwords.

These nonwords are designed to reduce *obvious* semantic cues, not to eliminate
mnemonics. Validate language-specific accidental meanings and list difficulty
with a multilingual pilot before conducting the definitive study.
"""
from __future__ import annotations
import re
import unicodedata

LANGUAGES = ("nb", "en", "sv", "de", "fr", "es", "it", "pt", "nl", "da", "pl", "ro")

# Visibly and phonologically distinct pseudowords. This is a new pilot
# protocol, not a validated normed psychometric test. Do not mix V2.2 scores.
LISTS: tuple[tuple[tuple[str, str], ...], ...] = (
    (("maviko", "chair"), ("tulena", "key"), ("boremi", "apple"),
     ("nupasi", "bicycle"), ("kevora", "lamp"), ("falitu", "book"),
     ("sedani", "spoon"), ("pumelo", "window")),
    (("dovika", "clock"), ("nemaru", "bridge"), ("kasipo", "flower"),
     ("reluna", "table"), ("tofeni", "pencil"), ("bajero", "door"),
     ("visaku", "basket"), ("lomeri", "mirror")),
    (("terupo", "umbrella"), ("mikaso", "candle"), ("foneli", "towel"),
     ("razuki", "plate"), ("benavo", "glove"), ("sufari", "ladder"),
     ("peliko", "pillow"), ("votema", "fork")),
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


# Additional study languages. Labels below are pilot vocabulary, not validated
# against native-speaker difficulty. No remote translation API is called.
_ADDITIONAL_LABELS = {
    'chair': (('sedia',), ('cadeira',), ('stoel',), ('stol',), ('krzesło',), ('scaun',)),
    'key': (('chiave',), ('chave',), ('sleutel',), ('nøgle',), ('klucz',), ('cheie',)),
    'apple': (('mela',), ('maçã',), ('appel',), ('æble',), ('jabłko',), ('măr',)),
    'bicycle': (('bicicletta','bici'), ('bicicleta',), ('fiets',), ('cykel',), ('rower',), ('bicicletă',)),
    'lamp': (('lampada',), ('lâmpada',), ('lamp',), ('lampe',), ('lampa',), ('lampă',)),
    'book': (('libro',), ('livro',), ('boek',), ('bog',), ('książka',), ('carte',)),
    'spoon': (('cucchiaio',), ('colher',), ('lepel',), ('ske',), ('łyżka',), ('lingură',)),
    'window': (('finestra',), ('janela',), ('raam',), ('vindue',), ('okno',), ('fereastră',)),
    'clock': (('orologio',), ('relógio',), ('klok',), ('ur',), ('zegar',), ('ceas',)),
    'bridge': (('ponte',), ('ponte',), ('brug',), ('bro',), ('most',), ('pod',)),
    'flower': (('fiore',), ('flor',), ('bloem',), ('blomst',), ('kwiat',), ('floare',)),
    'table': (('tavolo',), ('mesa',), ('tafel',), ('bord',), ('stół',), ('masă',)),
    'pencil': (('matita',), ('lápis',), ('potlood',), ('blyant',), ('ołówek',), ('creion',)),
    'door': (('porta',), ('porta',), ('deur',), ('dør',), ('drzwi',), ('ușă',)),
    'basket': (('cesto',), ('cesto',), ('mand',), ('kurv',), ('kosz',), ('coș',)),
    'mirror': (('specchio',), ('espelho',), ('spiegel',), ('spejl',), ('lustro',), ('oglindă',)),
    'umbrella': (('ombrello',), ('guarda-chuva',), ('paraplu',), ('paraply',), ('parasol',), ('umbrelă',)),
    'candle': (('candela',), ('vela',), ('kaars',), ('stearinlys',), ('świeca',), ('lumânare',)),
    'towel': (('asciugamano',), ('toalha',), ('handdoek',), ('håndklæde',), ('ręcznik',), ('prosop',)),
    'plate': (('piatto',), ('prato',), ('bord',), ('tallerken',), ('talerz',), ('farfurie',)),
    'glove': (('guanto',), ('luva',), ('handschoen',), ('handske',), ('rękawiczka',), ('mănușă',)),
    'ladder': (('scala',), ('escada',), ('ladder',), ('stige',), ('drabina',), ('scară',)),
    'pillow': (('cuscino',), ('travesseiro',), ('kussen',), ('pude',), ('poduszka',), ('pernă',)),
    'fork': (('forchetta',), ('garfo',), ('vork',), ('gaffel',), ('widelec',), ('furculiță',)),
}
for _key, _items in _ADDITIONAL_LABELS.items():
    TARGETS[_key].update(dict(zip(LANGUAGES[6:], _items)))


def normalize(value: str) -> str:
    value = unicodedata.normalize("NFKD", value.strip().casefold())
    value = "".join(c for c in value if not unicodedata.combining(c))
    value = re.sub(r"[^a-z0-9æøå]+", " ", value).strip()
    return re.sub(r"\s+", " ", value)


def learning_pairs(list_id: int, language: str, order: list[int] | None = None) -> list[dict[str, str]]:
    items = LISTS[list_id]
    return [{"word": items[i][0].upper(), "meaning": TARGETS[items[i][1]][language][0]}
            for i in (order if order is not None else range(len(items)))]


def recall_words(list_id: int, order: list[int] | None = None) -> list[str]:
    items = LISTS[list_id]
    return [items[i][0].upper() for i in (order if order is not None else range(len(items)))]


def grade(list_id: int, language: str, answers: list[str], order: list[int] | None = None) -> tuple[int, list[bool]]:
    items = LISTS[list_id]
    indices = order if order is not None else list(range(len(items)))
    if len(answers) != len(items) or sorted(indices) != list(range(len(items))):
        raise ValueError('Invalid answer count or recall ordering')
    correct = [normalize(answer) in {
        normalize(variant) for variant in TARGETS[items[i][1]][language]
    } for i, answer in zip(indices, answers)]
    return sum(correct), correct


def answer_review(list_id: int, language: str, answers: list[str], order: list[int]) -> list[dict]:
    _, graded = grade(list_id, language, answers, order)
    items = LISTS[list_id]
    return [{"word": items[i][0].upper(), "answer": answer,
             "expected": TARGETS[items[i][1]][language][0], "correct": okay}
            for i, answer, okay in zip(order, answers, graded)]


assert len(LISTS) == 3 and all(len(list_) == 8 for list_ in LISTS)
assert len({word for row in LISTS for word, _ in row}) == 24
# All actual stimuli must have a validated label entry for every study language.
assert all(set(TARGETS[key]) == set(LANGUAGES) for row in LISTS for _,key in row)

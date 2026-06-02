"""
Ukrainian NLP — pymorphy3 lemmatisation + spaCy NER.

Lemmatisation collapses declined/conjugated forms into one base lemma:
  "україні", "україну", "україни" → "україна"

Sentiment uses stem-prefix matching (no lemmatisation needed there because
the stems are short enough to catch all forms).

Entity extraction uses spaCy uk_core_news_sm:
  PER  — persons       (Зеленський, Путін)
  ORG  — organisations (НАТО, ЄС, Газпром)
  LOC  — locations     (Київ, Харків)
  GPE  — geo-political (Україна, Росія, США)
"""
import re
from collections import Counter
from functools import lru_cache

try:
    import pymorphy3
    # Ukrainian morphological analyser (pymorphy3-dicts-uk must be installed)
    _MORPH = pymorphy3.MorphAnalyzer(lang='uk')
    _LEMMATISE_AVAILABLE = True
except Exception:
    _MORPH = None
    _LEMMATISE_AVAILABLE = False

# spaCy NER — loaded lazily on first call to avoid startup cost
_NLP = None
_NLP_LOADED = False

def _get_nlp():
    global _NLP, _NLP_LOADED
    if _NLP_LOADED:
        return _NLP
    try:
        import spacy
        _NLP = spacy.load("uk_core_news_sm", disable=["parser", "senter"])
        # Increase max_length for long texts
        _NLP.max_length = 2_000_000
    except Exception:
        _NLP = None
    _NLP_LOADED = True
    return _NLP

# Entity labels we care about for news analysis
_ENTITY_LABELS = {"PER", "ORG", "LOC", "GPE", "MISC"}

# ---------------------------------------------------------------------------
# Stopwords
# ---------------------------------------------------------------------------

STOPWORDS = {
    "і", "в", "на", "з", "до", "за", "що", "як", "але", "або", "та", "по",
    "від", "про", "це", "той", "він", "вона", "вони", "ми", "ви", "не", "а",
    "у", "із", "під", "над", "між", "через", "тому", "тоді", "коли", "якщо",
    "свого", "його", "після", "при", "які", "який", "яка", "яке", "яких",
    "також", "лише", "тільки", "вже", "ще", "навіть", "саме", "однак",
    "адже", "бо", "щоб", "хоча", "поки", "поки", "зокрема", "зараз",
    "нині", "сьогодні", "вчора", "завтра", "тут", "там", "так", "ні",
    # common news-filler words (lemmatised forms)
    "понад",          # більше ніж / more than
    "терміново",      # breaking-news prefix
    "новий",          # нові/нова/нового → lemma новий
    "увесь", "весь",  # all
    "стати", "бути",  # became / be
    "може", "мати",   # can / has
    "року", "рік",    # year (very frequent in dates)
    "млн", "млрд", "тис",  # числові скорочення
    "the", "a", "an", "is", "are", "was", "were", "be", "been", "this",
    "that", "with", "from", "have", "will", "for", "not", "but",
}

# ---------------------------------------------------------------------------
# Sentiment stems  (prefix of 4–6 chars catches most declined/conjugated forms)
# ---------------------------------------------------------------------------

# Each tuple: (min_stem_length, stem_prefix)
# We match token.startswith(prefix) AND len(token) >= min_len to avoid
# short false-positive matches.

NEGATIVE_STEMS: list[tuple[int, str]] = [
    # casualties / violence
    (5, "загиб"),   # загибель, загиблих, загибли
    (5, "смерт"),   # смерть, смерті, смертей
    (5, "жертв"),   # жертва, жертви, жертвам, жертвувати
    (5, "пораН"),   # поранений, поранених — normalised below
    (5, "поран"),
    (5, "вбит"),    # вбитий, вбито, вбили
    (4, "вбив"),    # вбивство, вбивець
    # attacks / war
    (4, "атак"),    # атака, атаки, атакував, атакували
    (6, "обстріл"), # обстріл, обстрілу, обстрілів
    (4, "удар"),    # удар, удару, ударів, ударний
    (4, "дрон"),    # дрон, дрони, дронів, дроновий
    (5, "ракет"),   # ракета, ракети, ракетний, ракетних
    (5, "вибух"),   # вибух, вибухів, вибуховий
    (6, "терорис"), # терорист, терористи
    (6, "терорис"),
    (5, "терор"),   # теракт, тероризм
    (5, "теракт"),
    (5, "окупа"),   # окупація, окупант
    # crisis / problems
    (4, "криз"),    # криза, кризи, кризовий
    (6, "падіння"),
    (5, "падін"),
    (5, "втрат"),   # втрата, втрати, втрачено
    (5, "збитк"),   # збиток, збитків
    (5, "загроз"),  # загроза, загрозу
    (8, "катастроф"),
    (5, "небезп"),  # небезпека, небезпечний
    (5, "скорот"),  # скорочення, скоротили
    (5, "штраф"),
    (6, "санкці"),  # санкція, санкцій
    (7, "загостр"), # загострення
    (5, "конфлі"),  # конфлікт
    (5, "погірш"),  # погіршення
    (6, "протест"),
    (5, "страйк"),
    (5, "банкру"),  # банкрутство
    (5, "дефол"),   # дефолт
    (5, "пожеж"),   # пожежа, пожежі
    (5, "повінь"),
    (6, "повені"),
    (4, "смог"),
    (5, "арешт"),   # арешт, заарештован
    (8, "заарешт"),
    (4, "суд"),     # суд, судять — neutral/slightly negative in news
    (6, "звинув"),  # звинувачення
    (5, "корупц"),  # корупція
    (6, "хабар"),
    (4, "зниж"),    # зниження, знизилися (econ)
    (5, "дефіц"),   # дефіцит
    (5, "боргу"),
    (4, "борг"),
    (4, "криз"),
]

POSITIVE_STEMS: list[tuple[int, str]] = [
    (6, "відновл"),  # відновлення, відновлено, відновлюється
    (6, "зростан"),  # зростання, зростає
    (6, "зростає"),
    (5, "зріст"),
    (6, "перемог"),  # перемога, перемоги, перемогли
    (5, "успіх"),
    (7, "підтримк"), # підтримка
    (6, "підтрим"),
    (6, "допомог"),  # допомога, допомоги, допомогли
    (5, "допома"),
    (6, "розвит"),   # розвиток, розвитку, розвивати
    (6, "покращ"),   # покращення, покращити, покращилось
    (6, "збільш"),   # збільшення, збільшено, збільшилось
    (6, "позитив"),
    (8, "досягнен"), # досягнення
    (7, "досягну"),  # досягнуто
    (5, "інвест"),   # інвестиція, інвестиції, інвестував
    (4, "угод"),     # угода, угоди, угодою (can be positive)
    (7, "звільнен"), # звільнення (prisoners)
    (6, "обміняли"), # обмін полоненими
    (5, "обмін"),    # обмін полоненими
    (6, "відкрит"),  # відкриття
    (6, "запуск"),   # запуск нового
    (5, "гранти"),
    (5, "грант"),
    (6, "рекорд"),
    (5, "прибут"),   # прибуток, прибутковий
    (5, "виграш"),
    (6, "виграли"),
    (5, "мирни"),    # мирний, мирні переговори
    (5, "примир"),   # примирення
    (5, "реформ"),   # реформа, реформи
    (5, "модерн"),   # модернізація
    (5, "зниженн"),  # зниження цін (positive for consumers)
    (5, "здешев"),   # здешевлення
    (4, "рост"),     # ріст (може бути і рос., але часто позитив)
    (7, "покращив"),
]

# De-duplicate stems by converting to set of unique values
_seen: set[str] = set()
_NEGATIVE_STEMS: list[tuple[int, str]] = []
for _pair in NEGATIVE_STEMS:
    if _pair[1] not in _seen:
        _seen.add(_pair[1])
        _NEGATIVE_STEMS.append(_pair)
NEGATIVE_STEMS = _NEGATIVE_STEMS

_seen = set()
_POSITIVE_STEMS: list[tuple[int, str]] = []
for _pair in POSITIVE_STEMS:
    if _pair[1] not in _seen:
        _seen.add(_pair[1])
        _POSITIVE_STEMS.append(_pair)
POSITIVE_STEMS = _POSITIVE_STEMS


# ---------------------------------------------------------------------------
# Core helpers
# ---------------------------------------------------------------------------

def _tokenise(text: str) -> list[str]:
    """Lowercase + keep only Cyrillic/Latin tokens ≥ 3 chars."""
    return re.findall(r'[а-яіїєёa-z]{3,}', text.lower())


@lru_cache(maxsize=8192)
def _lemma(token: str) -> str:
    """Return lemma for token; falls back to token itself if unavailable."""
    if _MORPH is None:
        return token
    parses = _MORPH.parse(token)
    if parses:
        return parses[0].normal_form
    return token


def _matches_stems(token: str, stems: list[tuple[int, str]]) -> bool:
    for min_len, prefix in stems:
        if len(token) >= min_len and token.startswith(prefix):
            return True
    return False


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def extract_keywords(text: str, top_n: int = 5) -> list[str]:
    """
    Tokenise → lemmatise → filter stopwords → top_n by frequency.
    Lemmatisation ensures "україні"/"україни"/"україну" all count as "україна".
    """
    raw_tokens = [t for t in _tokenise(text) if len(t) >= 4]
    lemmas = [_lemma(t) for t in raw_tokens]
    filtered = [l for l in lemmas if l not in STOPWORDS and len(l) >= 4]
    freq = Counter(filtered)
    return [w for w, _ in freq.most_common(top_n)]


def sentiment_score(text: str) -> float:
    """
    Returns float in [-1, 1].
    Stem-prefix matching handles declined/conjugated Ukrainian word forms.
    """
    tokens = _tokenise(text)
    pos = sum(1 for t in tokens if _matches_stems(t, POSITIVE_STEMS))
    neg = sum(1 for t in tokens if _matches_stems(t, NEGATIVE_STEMS))
    total = pos + neg
    if total == 0:
        return 0.0
    return round((pos - neg) / total, 2)


try:
    from langdetect import detect as _ld_detect
    from langdetect import DetectorFactory
    DetectorFactory.seed = 0          # deterministic results
    _LANGDETECT_AVAILABLE = True
except Exception:
    _LANGDETECT_AVAILABLE = False


def detect_language(text: str) -> str:
    """
    Two-stage language detector for Ukrainian/Russian news titles.

    Stage 1 — Unicode character heuristic (fast, zero-cost):
      Ukrainian-only: ї (U+0457), є (U+0454), ґ (U+0491), і (U+0456)
      Russian-only:   ы (U+044B), э (U+044D), ъ (U+044A)

    Stage 2 — langdetect n-gram model (slower, handles ambiguous titles):
      Used only when Stage 1 returns "unknown".

    rbc.ua published in Russian until ~Feb 2022, then switched to Ukrainian.
    """
    if not text or not text.strip():
        return "unknown"
    t = text.lower()

    # Stage 1: distinctive-character heuristic
    uk_strong = t.count("ї") + t.count("є") + t.count("ґ")
    uk_soft   = t.count("і")
    ru_strong = t.count("ы") + t.count("э") + t.count("ъ")

    if uk_strong > 0:
        return "uk"
    if ru_strong > 0 and uk_soft == 0:
        return "ru"
    if uk_soft > 0:
        return "uk"

    # Stage 2: n-gram model for ambiguous titles
    if _LANGDETECT_AVAILABLE:
        try:
            lang = _ld_detect(text)
            if lang == "uk":
                return "uk"
            if lang == "ru":
                return "ru"
        except Exception:
            pass

    return "unknown"


def extract_entities(text: str) -> list[dict]:
    """
    Run spaCy NER on text, return deduplicated entities.
    Each entity: {"text": "Зеленський", "label": "PER"}
    Falls back to [] if spaCy is unavailable.
    """
    nlp = _get_nlp()
    if nlp is None or not text.strip():
        return []
    doc = nlp(text[:500])  # titles are short; cap to avoid overhead
    seen: set[str] = set()
    result: list[dict] = []
    for ent in doc.ents:
        if ent.label_ not in _ENTITY_LABELS:
            continue
        key = ent.text.strip().lower()
        if len(key) < 2 or key in seen:
            continue
        seen.add(key)
        result.append({"text": ent.text.strip(), "label": ent.label_})
    return result


def analyze(title: str, description: str) -> dict:
    text = f"{title} {description}"
    return {
        "keywords": extract_keywords(text),
        "sentiment_score": sentiment_score(text),
        "word_count": len(text.split()),
        "entities": extract_entities(text),
        "lang": detect_language(title),  # use title only — more reliable signal
    }

"""Conservative title-only taxonomy for comics and sticker albums."""
import re
from functools import lru_cache

def norm(title):
    return re.sub(r"\s+", " ", str(title or "").casefold()).strip()

@lru_cache(maxsize=100000)
def classify(category_id, title):
    t = norm(title)
    if str(category_id) == "141755":
        brands = [("Panini",r"\bpanini\b"),("Topps",r"\btopps\b"),("Merlin",r"\bmerlin\b"),("Calciatori",r"\bcalciatori\b")]
        brand = next((b for b,p in brands if re.search(p,t)), "Non identificato")
        families = [
            ("Mondiali calcio",r"world cup|coppa del mondo|mondiali|fifa world"),
            ("Europei calcio",r"euro 20\d\d|europei|uefa euro"),
            ("Calciatori",r"calciatori|serie a|campionato italiano"),
            ("NBA / Basket",r"nba|basket|jordan"),
            ("Olimpiadi",r"olimpiad|olympic"),
            ("Pokémon",r"pokemon|pokémon"),
        ]
        family = next((b for b,p in families if re.search(p,t)), "Altri album e figurine")
        year = re.search(r"\b(19[5-9]\d|20[0-2]\d)(?:\s*[/\-]\s*(?:\d{2}|20\d{2}))?\b",t)
        model = year.group(0) if year else "Anno / edizione non identificato"
        return brand, family, model
    if str(category_id) == "63":
        series = [
            ("Dylan Dog",r"\bdylan\s*dog\b"),
            ("Tex",r"\btex\b|tex willer"),
            ("Diabolik",r"\bdiabolik\b"),
            ("Zagor",r"\bzagor\b"),
            ("Martin Mystère",r"martin myst"),
            ("Topolino",r"\btopolino\b"),
            ("Spider-Man",r"spider.?man|uomo ragno"),
            ("Batman",r"\bbatman\b"),
            ("Manga",r"\bmanga\b|one piece|dragon ball|naruto"),
        ]
        family = next((b for b,p in series if re.search(p,t)), "Altri fumetti")
        publishers = [
            ("Sergio Bonelli",r"bonelli|dylan dog|zagor|martin myst|\btex\b"),
            ("Panini",r"\bpanini\b"),
            ("Marvel",r"\bmarvel\b|spider.?man"),
            ("DC Comics",r"dc comics|\bbatman\b"),
            ("Disney",r"\bdisney\b|\btopolino\b"),
            ("Astorina",r"\bastorina\b|diabolik"),
        ]
        brand = next((b for b,p in publishers if re.search(p,t)), "Editore non identificato")
        issue = re.search(r"\b(?:n(?:umero|um)?\.?|#)\s*(\d{1,4})\b", t)
        model = "N. " + issue.group(1) if issue else "Numero non identificato"
        return brand, family, model
    return "Non identificato", "Altri prodotti", "Modello non identificato"

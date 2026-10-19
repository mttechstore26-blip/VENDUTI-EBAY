"""Conservative commercial model recognition for kitchen eBay listings."""
import re

KNOWN = [
 ("AquaTru", "Classic AT2020", r"\baquatru\b.*\bat2020\b"),
 ("Illy", "Francis Francis X7", r"\b(?:illy|francis)\b.*\bx7\b"),
 ("Typhur", "Dome 2", r"\btyphur\b.*\bdome\s*2\b"),
 ("Super Angel", "Pro", r"\bsuper angel\b.*\bpro\b"),
 ("Super Angel", "Deluxe", r"\bsuper angel\b.*\bdeluxe\b"),
 ("White Mountain", "69204", r"\bwhite mountain\b.*\b69204\b"),
 ("Royal Prestige", "Plancha quadrata", r"\broyal prestige\b.*\bplancha\b"),
 ("Hawos", "Billy 100", r"\bhawos\b.*\bbilly\s*100\b"),
 ("Instant Pot", "Duo", r"\binstant pot\b.*\bduo\b"),
 ("Magimix", "Cook Expert", r"\bmagimix\b.*\bcook expert\b"),
 ("Magimix", "5200 XL", r"\bmagimix\b.*\b5200\s*xl\b"),
 ("Omega", "J8006", r"\bomega\b.*\bj8006\b"),
 ("Hurom", "H400", r"\bhurom\b.*\bh400\b"),
 ("Nutribullet", "Pro 900", r"\bnutribullet\b.*\b(?:pro\s*)?900\b"),
 ("PopSmith", "The Popper", r"\bpopsmith\b.*\bpopper\b"),
 ("VEVOR", "Gelatiera compressore 2 L", r"\bvevor\b.*\bgelatiera\b.*\b2\s*l\b"),
]
BRANDS = [
 "AquaTru", "Illy", "PopSmith", "Typhur", "Chantal", "White Mountain",
 "Royal Prestige", "VEVOR", "Super Angel", "Hawos", "Eureka", "Rocket",
 "La Marzocco", "Rancilio", "Omega", "Hurom", "Nutribullet", "Instant Pot",
 "Miele", "Ankarsrum", "Bialetti", "Moulinex", "Krups", "Bamix",
 "Magimix", "KRUVE", "Café"
]
# No assumptions about model from a generic noun, voltage, capacity, colour or year.
EXPLICIT_CODE = re.compile(r"\b(?:AT|X|SCM|BES|BEM|KSM|VM|NS|NP|SL|NC|DZ|DCF|TSF|KBGV|G5-NG|J)\s*[- ]?\d{2,6}[A-Z0-9-]*\b",re.I)

def normalized_model(row):
    title = str(row.get("title") or "")
    lower = title.casefold()
    brand = str(row.get("Brand / Editore") or "Non identificato")
    model = str(row.get("Modello / Edizione") or "Modello non identificato")
    for b, m, pattern in KNOWN:
        if re.search(pattern, lower, re.I):
            return f"{b} {m}"
    if brand == "Non identificato":
        brand = next((b for b in BRANDS if re.search(r"(?<!\w)"+re.escape(b)+r"(?!\w)",title,re.I)), brand)
    invalid = {"modello non identificato","rosso","rossa","robot","attacchi","attacco","attachments","royal","slice","camper","robusto","ice cream","bianco","nera","nero","epicurean"}
    if model.casefold() not in invalid and re.search(r"\d",model):
        return f"{brand} {model}".strip() if brand != "Non identificato" else f"Modello {model}"
    if brand != "Non identificato":
        match = EXPLICIT_CODE.search(title)
        if match:
            return f"{brand} {re.sub(r'[\s-]+','',match.group()).upper()}"
        return f"{brand} — modello non specificato"
    return "Modello non identificato (titolo insufficiente)"

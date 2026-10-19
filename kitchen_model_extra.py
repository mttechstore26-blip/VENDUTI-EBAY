"""Conservative commercial model recognition for kitchen eBay listings."""
import re

KNOWN = [
 ("Mr. Coffee", "BVMC-EL1", r"\b(?:mr\.?\s*coffee|cafe latte)\b.*\bbvmc[- ]?el1\b"),
 ("Whirlpool", "WMC2005YD", r"\bwhirlpool\b.*\bwmc2005yd\b"),
 ("Joyoung", "M6-L20S", r"\bjoyoung\b.*\bm6[- ]?l20s\b"),
 ("Siemens", "TW91100 Porsche Design", r"\bsiemens\b.*\btw\s*91100\b"),
 ("Enagic", "LeveLuk SD501", r"\b(?:enagic|kangen|leveluk)\b.*\bsd501\b"),
 ("Dualit", "Classic D4BMH", r"\bdualit\b.*\bd4bmh\b"),
 ("National", "SD-1801", r"\bnational\b.*\bsd[- ]?1801\b"),
 ("SodaStream", "E-Terra", r"\bsodastream\b.*\be[- ]?terra\b"),
 ("Ronic", "Original 20", r"\bronic\b.*\boriginal\s*20\b"),
 ("Timemore", "Sculptor 078S", r"\btimemore\b.*\b078s\b"),
 ("Revolution Cooking", "R180S", r"\brevolution cooking\b.*\br180s\b"),
 ("VillaWare", "Grand Wrap 5955", r"\bvillaware\b.*\b5955\b"),
 ("iCucina", "BL3445", r"\bicucina\b.*\bbl3445\b"),
 ("Tribest", "Green Star GS-3000", r"\b(?:green star|tribest)\b.*\bgs[- ]?3000\b"),
 ("Bluevua", "RO100ROPOT", r"\bbluevua\b.*\bro100ropot\b"),
 ("Waterdrop", "WD-A2", r"\bwaterdrop\b.*\bwd[- ]?a2\b"),
 ("LEM", "1158", r"\blem products\b.*\b1158\b"),
 ("Sharp", "R-1M50", r"\bsharp\b.*\br[- ]?1m50\b"),
 ("Bellman", "CX25S", r"\bbellman\b.*\bcx25s\b"),
 ("Cuckoo", "CRP Series", r"\bcuckoo\b.*\bcrp[- ]?[a-z0-9]+\b"),
 ("Bodum", "Bistro 11659", r"\bbodum\b.*\b11659\b"),
 ("All American", "915", r"\ball american\b.*\b915\b"),
 ("All American", "910", r"\ball american\b.*\b910\b"),
 ("Schnitzer", "Cerealo", r"\bschnitzer\b.*\bcerealo\b"),
 ("Chemex", "Classic", r"\bchemex\b.*\bclassic\b"),
 ("Dito Sama", "K35", r"\bdito sama\b.*\bk35\b"),
 ("Gourmia", "Soft Serve Maker", r"\bgourmia\b.*\bsoft serve\b"),
 ("Air Water Life", "Aqua-Ionizer Deluxe 9.0", r"\bair water life\b.*\b(?:deluxe\s*)?9\.0\b"),
 ("Joy Resolve", "Barisieur", r"\bjoy resolve\b.*\bbarisieur\b"),
 ("Grain Master", "Whisper Mill 2000", r"\b(?:grain master|whisper mill)\b.*\b2000\b"),
 ("T-Fal", "Actifry 2 in 1", r"\b(?:t-fal|tefal|tfal)\b.*\bactifry\b.*\b2\s*in\s*1\b"),
 ("Pure Water", "Mini Classic", r"\bpure water\b.*\bmini classic\b"),
 ("Café", "Bellissimo", r"\bcaff[eè]\b.*\bbellissimo\b"),

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
    # SMEG: normalize color/market suffixes only, never combine different generations.
    # Demo codes are retained as supplied, not assumed equivalent to retail models.
    if re.search(r"\bsmeg\b", lower):
        demo = re.search(r"\b(?:smk|sek|scj|scg|scm)[-\s]?[a-z]{2}\d{2,3}\b", lower, re.I)
        if demo:
            return "SMEG " + demo.group(0).upper().replace(" ", "")
        retail = re.search(r"\b(?:blf|smf|cgf|bcc|sjf|mgf|cjf|dcf|klf|tsf|ecf|bcl|pbf|hbf|bgb|mff|cpm|bml|bccc)\s*0?[1-9]\d?(?:[a-z]{2,5})?(?:us|uk|eu|it)?\b", lower, re.I)
        if retail:
            family = re.match(r"[a-z]+0?[1-9]\d?", retail.group(0), re.I)
            if family:
                return "SMEG " + family.group(0).upper()
        if "bollitore" in lower and "tostapane" in lower:
            return "SMEG Kit bollitore + tostapane (codici non indicati)"
        descriptions = [
            ("SMEG Bollitore (codice non indicato)", r"bollitore|kettle"),
            ("SMEG Tostapane (codice non indicato)", r"tostapane|toaster"),
            ("SMEG Macchina caffè filtro (codice non indicato)", r"caff[eè].*(?:goccia|filtro)|drip coffee"),
            ("SMEG Macchina espresso (codice non indicato)", r"espresso"),
            ("SMEG Macinacaffè (codice non indicato)", r"macinacaff"),
            ("SMEG Frullatore (codice non indicato)", r"frullator|blender"),
            ("SMEG Impastatrice (codice non indicato)", r"impastatrice|mixer da appoggio"),
            ("SMEG Spremiagrumi (codice non indicato)", r"spremiagrum"),
        ]
        for name, pat in descriptions:
            if re.search(pat, lower):
                return name
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

"""Precise, conservative taxonomy for eBay category 171485 (tablets and e-readers).

Identities are derived from seller titles only: never infer a generation from a
generic product name. Product state is a separate comparability dimension.
"""
import re
import unicodedata


def _norm(value):
    value = unicodedata.normalize("NFKC", str(value or "")).casefold()
    return re.sub(r"[\u2010-\u2015]", "-", value)


def _hit(text, pattern):
    return bool(re.search(pattern, text, re.I))


# Most specific before generic. Numeric model IDs are accepted only in contexts
# where the supplier uses those IDs as unambiguous product identifiers.
KOBO = (
    (r"\blibra\s*colou?r\b|\bn428\b", "Libra", "Kobo Libra Colour"),
    (r"\bclara\s*colou?r\b|\bn367\b", "Clara", "Kobo Clara Colour"),
    (r"\bclara\s*bw\b|\bn365b?\b|\bp365\b", "Clara", "Kobo Clara BW"),
    (r"\belipsa\s*2e\b|\bn605\b", "Elipsa", "Kobo Elipsa 2E"),
    (r"\bclara\s*2e\b|\bn506\b", "Clara", "Kobo Clara 2E"),
    (r"\blibra\s*2\b|\bn418\b", "Libra", "Kobo Libra 2"),
    (r"\blibra\s*h[2z0]o\b|\bn873\b|\bn783\b", "Libra", "Kobo Libra H2O"),
    (r"\belipsa\b|\bn604\b", "Elipsa", "Kobo Elipsa"),
    (r"\bsage\b|\bn778k?\b", "Sage", "Kobo Sage"),
    (r"\bforma\b|\bn782\b", "Forma", "Kobo Forma"),
    (r"\bclara\s*hd\b|\bn249\b", "Clara", "Kobo Clara HD"),
    (r"\baura\s*h2o\s*(?:edition\s*2|2)\b|\bn867\b", "Aura", "Kobo Aura H2O Edition 2"),
    (r"\baura\s*one\b|\bn709\b", "Aura", "Kobo Aura ONE"),
    (r"\baura\s*(?:edition\s*)?2\b|\bn236\b", "Aura", "Kobo Aura Edition 2"),
    (r"\bnia\b|\bn306\b", "Nia", "Kobo Nia"),
)

POCKETBOOK = (
    (r"\binkpad\s*color\s*3\b|\bpb743k3\b", "InkPad", "PocketBook InkPad Color 3"),
    (r"\binkpad\s*color\s*2\b|\bpb743c\b", "InkPad", "PocketBook InkPad Color 2"),
    (r"\binkpad\s*color\b|\bpb741\b", "InkPad", "PocketBook InkPad Color"),
    (r"\binkpad\s*4\b|\bpb743g\b", "InkPad", "PocketBook InkPad 4"),
    (r"\binkpad\s*3\s*pro\b|\bpb740-2\b", "InkPad", "PocketBook InkPad 3 Pro"),
    (r"\binkpad\s*3\b|\bpb740\b", "InkPad", "PocketBook InkPad 3"),
    (r"\binkpad\s*eo\b", "InkPad", "PocketBook InkPad Eo"),
    (r"\binkpad\s*x\s*pro\b|\bpb1040d\b", "InkPad", "PocketBook InkPad X Pro"),
    (r"\binkpad\s*x\b|\bpb1040\b", "InkPad", "PocketBook InkPad X"),
    (r"\bera\s*color\b|\bpb700k3\b", "Era", "PocketBook Era Color"),
    (r"\bera\s*lite\b|\bpb710\b", "Era", "PocketBook Era Lite"),
    (r"\bera\b|\bpb700\b", "Era", "PocketBook Era"),
    (r"\bverse\s*pro\s*color\b", "Verse", "PocketBook Verse Pro Color"),
    (r"\bverse\s*pro\b|\bpb634\b", "Verse", "PocketBook Verse Pro"),
    (r"\bverse\s*lite\b|\bpb619\b", "Verse", "PocketBook Verse Lite"),
    (r"\bverse\b|\bpb629\b", "Verse", "PocketBook Verse"),
    (r"\btouch\s*hd\s*3\b|\bpb632\b", "Touch", "PocketBook Touch HD 3"),
    (r"\btouch\s*lux\s*5\b|\bpb628\b", "Touch", "PocketBook Touch Lux 5"),
)

BOOX = (
    (r"\bnote\s*air\s*4\s*c\b", "Note Air", "BOOX Note Air 4 C"),
    (r"\bnote\s*air\s*3\s*c\b", "Note Air", "BOOX Note Air 3 C"),
    (r"\bnote\s*air\s*3\b", "Note Air", "BOOX Note Air 3"),
    (r"\bnote\s*air\s*2\s*plus\b", "Note Air", "BOOX Note Air 2 Plus"),
    (r"\bnote\s*air\s*2\b", "Note Air", "BOOX Note Air 2"),
    (r"\bgo\s*color\s*7\s*(?:gen\s*(?:ii|2)|gen2)\b|\bgo\s*color\s*7\s*2\b", "Go", "BOOX Go Color 7 Gen II"),
    (r"\bgo\s*color\s*7\b", "Go", "BOOX Go Color 7"),
    (r"\bgo\s*10\.3\b", "Go", "BOOX Go 10.3"),
    (r"\bgo\s*7\b", "Go", "BOOX Go 7"),
    (r"\bpalma\s*2\b|\bpalma2\b", "Palma", "BOOX Palma 2"),
    (r"\bpalma\b", "Palma", "BOOX Palma"),
    (r"\btab\s*ultra\s*c\s*pro\b", "Tab", "BOOX Tab Ultra C Pro"),
    (r"\btab\s*ultra\s*c\b", "Tab", "BOOX Tab Ultra C"),
    (r"\btab\s*mini\s*c\b", "Tab", "BOOX Tab Mini C"),
    (r"\bpage\b", "Page", "BOOX Page"),
    (r"\bleaf\s*2\b", "Leaf", "BOOX Leaf 2"),
    (r"\bleaf\b", "Leaf", "BOOX Leaf"),
    (r"\bpoke\s*5\b", "Poke", "BOOX Poke 5"),
    (r"\bnova\s*air\s*c\b", "Nova", "BOOX Nova Air C"),
    (r"\bnova\s*air\b", "Nova", "BOOX Nova Air"),
)

SAMSUNG = (
    (r"\b(?:galaxy\s*)?tab\s*active\s*3\b|\bsm[- ]?t575\b", "Galaxy Tab Active", "Samsung Galaxy Tab Active3"),
    (r"\b(?:galaxy\s*)?tab\s*a11\b|\bsm[- ]?x130\b", "Galaxy Tab A", "Samsung Galaxy Tab A11"),
    (r"\b(?:galaxy\s*)?tab\s*s10\s*ultra\b", "Galaxy Tab S", "Samsung Galaxy Tab S10 Ultra"),
    (r"\b(?:galaxy\s*)?tab\s*s10\s*fe\s*\+", "Galaxy Tab S FE", "Samsung Galaxy Tab S10 FE+"),
    (r"\b(?:galaxy\s*)?tab\s*s10\s*fe\b", "Galaxy Tab S FE", "Samsung Galaxy Tab S10 FE"),
    (r"\b(?:galaxy\s*)?tab\s*s10\s*\+", "Galaxy Tab S", "Samsung Galaxy Tab S10+"),
    (r"\b(?:galaxy\s*)?tab\s*s9\s*ultra\b", "Galaxy Tab S", "Samsung Galaxy Tab S9 Ultra"),
    (r"\b(?:galaxy\s*)?tab\s*s9\s*fe\s*\+", "Galaxy Tab S FE", "Samsung Galaxy Tab S9 FE+"),
    (r"\b(?:galaxy\s*)?tab\s*s9\s*fe\b", "Galaxy Tab S FE", "Samsung Galaxy Tab S9 FE"),
    (r"\b(?:galaxy\s*)?tab\s*s9\s*\+", "Galaxy Tab S", "Samsung Galaxy Tab S9+"),
    (r"\b(?:galaxy\s*)?tab\s*s9\b", "Galaxy Tab S", "Samsung Galaxy Tab S9"),
    (r"\b(?:galaxy\s*)?tab\s*s8\s*ultra\b", "Galaxy Tab S", "Samsung Galaxy Tab S8 Ultra"),
    (r"\b(?:galaxy\s*)?tab\s*s8\s*\+", "Galaxy Tab S", "Samsung Galaxy Tab S8+"),
    (r"\b(?:galaxy\s*)?tab\s*s8\b", "Galaxy Tab S", "Samsung Galaxy Tab S8"),
    (r"\b(?:galaxy\s*)?tab\s*s7\s*fe\b", "Galaxy Tab S FE", "Samsung Galaxy Tab S7 FE"),
    (r"\b(?:galaxy\s*)?tab\s*s7\s*\+", "Galaxy Tab S", "Samsung Galaxy Tab S7+"),
    (r"\b(?:galaxy\s*)?tab\s*s7\b", "Galaxy Tab S", "Samsung Galaxy Tab S7"),
    (r"\b(?:galaxy\s*)?tab\s*s6\s*lite\b.*\b2024\b", "Galaxy Tab S Lite", "Samsung Galaxy Tab S6 Lite (2024)"),
    (r"\b(?:galaxy\s*)?tab\s*s6\s*lite\b", "Galaxy Tab S Lite", "Samsung Galaxy Tab S6 Lite"),
    (r"\b(?:galaxy\s*)?tab\s*a9\s*\+", "Galaxy Tab A", "Samsung Galaxy Tab A9+"),
    (r"\b(?:galaxy\s*)?tab\s*a9\b", "Galaxy Tab A", "Samsung Galaxy Tab A9"),
    (r"\b(?:galaxy\s*)?tab\s*a8\b", "Galaxy Tab A", "Samsung Galaxy Tab A8"),
    (r"\b(?:galaxy\s*)?tab\s*a7\s*lite\b", "Galaxy Tab A", "Samsung Galaxy Tab A7 Lite"),
    (r"\b(?:galaxy\s*)?tab\s*a7\b", "Galaxy Tab A", "Samsung Galaxy Tab A7"),
)

TOLINO = (
    (r"\bvision\s*color\b", "Vision", "Tolino Vision Color"),
    (r"\bvision\s*6\b", "Vision", "Tolino Vision 6"),
    (r"\bvision\s*5\b", "Vision", "Tolino Vision 5"),
    (r"\bvision\s*4\s*hd\b", "Vision", "Tolino Vision 4 HD"),
    (r"\bshine\s*color\b", "Shine", "Tolino Shine Color"),
    (r"\bshine\s*5\b", "Shine", "Tolino Shine 5"),
    (r"\bshine\s*4\b", "Shine", "Tolino Shine 4"),
    (r"\bepos\s*3\b", "Epos", "Tolino Epos 3"),
    (r"\bepos\s*2\b", "Epos", "Tolino Epos 2"),
)

RUGGED = (
    ("DOOGEE", "T", r"\bt30\s*pro\b", "DOOGEE T30 Pro"),
    ("i.safe", "IS", r"\bis930[.]?1\b", "i.safe IS930.1"),
    ("Xplore", "Rugged", r"\bix101b1\b", "Xplore iX101B1"),
    ("OUKITEL", "RT", r"\brt2\b", "OUKITEL RT2"),
    ("Dell", "Latitude 2-in-1", r"\blatitude\s*5290\b", "Dell Latitude 5290 2-in-1"),
    ("Dell", "Venue", r"\bvenue\s*11\s*pro\s*7139\b", "Dell Venue 11 Pro 7139"),
    ("Fujitsu", "Stylistic", r"\bstylistic\s*q738\b", "Fujitsu Stylistic Q738"),
)

OTHER = (
    ("Lenovo", "Tab P", r"\btab\s*p12\s*pro\b", "Lenovo Tab P12 Pro"),
    ("Lenovo", "Tab P", r"\btab\s*p12\b", "Lenovo Tab P12"),
    ("Lenovo", "Tab P", r"\btab\s*p11\s*pro\s*(?:gen\s*)?2\b", "Lenovo Tab P11 Pro Gen 2"),
    ("Lenovo", "Tab P", r"\btab\s*p11\s*pro\b", "Lenovo Tab P11 Pro"),
    ("Lenovo", "Tab P", r"\btab\s*p11\s*(?:gen\s*)?2\b", "Lenovo Tab P11 Gen 2"),
    ("Lenovo", "Tab P", r"\btab\s*p11\b", "Lenovo Tab P11"),
    ("Lenovo", "Tab M", r"\btab\s*m11\b", "Lenovo Tab M11"),
    ("Lenovo", "Tab M", r"\btab\s*m10\s*plus\s*(?:gen\s*)?3\b", "Lenovo Tab M10 Plus Gen 3"),
    ("Lenovo", "Tab M", r"\btab\s*m10\s*plus\b", "Lenovo Tab M10 Plus"),
    ("Lenovo", "Tab M", r"\btab\s*m10\b|\blenovo\s*m10\s*hd\b", "Lenovo Tab M10"),
    ("Lenovo", "Legion", r"\blegion\s*y700\b", "Lenovo Legion Y700"),
    ("Microsoft", "Surface Go", r"\bsurface\s*go\s*4\b", "Microsoft Surface Go 4"),
    ("Microsoft", "Surface Go", r"\bsurface\s*go\s*3\b", "Microsoft Surface Go 3"),
    ("Microsoft", "Surface Go", r"\bsurface\s*go\s*2\b", "Microsoft Surface Go 2"),
    ("Microsoft", "Surface Go", r"\bsurface\s*go\b", "Microsoft Surface Go (1ª gen.)"),
    ("Microsoft", "Surface Pro", r"\bsurface\s*pro\s*9\b", "Microsoft Surface Pro 9"),
    ("Microsoft", "Surface Pro", r"\bsurface\s*pro\s*8\b", "Microsoft Surface Pro 8"),
    ("Microsoft", "Surface Pro", r"\bsurface\s*pro\s*7\s*(?:\+|plus)(?=\W|$)", "Microsoft Surface Pro 7+"),
    ("Microsoft", "Surface Pro", r"\bsurface\s*pro\s*7\b", "Microsoft Surface Pro 7"),
    ("Microsoft", "Surface Pro", r"\bsurface\s*pro\s*6\b", "Microsoft Surface Pro 6"),
    ("Xiaomi", "Pad", r"\bpad\s*6s\s*pro\b", "Xiaomi Pad 6S Pro"),
    ("Xiaomi", "Pad", r"\bpad\s*6\s*pro\b", "Xiaomi Pad 6 Pro"),
    ("Xiaomi", "Pad", r"\bpad\s*6\b", "Xiaomi Pad 6"),
    ("Xiaomi", "Pad", r"\bpad\s*5\b", "Xiaomi Pad 5"),
    ("Xiaomi", "Redmi Pad", r"\bredmi\s*pad\s*pro\b", "Xiaomi Redmi Pad Pro"),
    ("Xiaomi", "Redmi Pad", r"\bredmi\s*pad\s*se\b", "Xiaomi Redmi Pad SE"),
    ("Xiaomi", "Redmi Pad", r"\bredmi\s*pad\b", "Xiaomi Redmi Pad"),
    ("Huawei", "MatePad", r"\bmatepad\s*11\.5\b", "Huawei MatePad 11.5"),
    ("Huawei", "MatePad", r"\bmatepad\s*11\b", "Huawei MatePad 11"),
    ("Huawei", "MatePad", r"\bmatepad\s*pro\b", "Huawei MatePad Pro"),
    ("Huawei", "MatePad", r"\bmatepad\b", "Huawei MatePad (generazione non specificata)"),
    ("Amazon", "Fire", r"\bfire\s*hd\s*10\s*plus\b", "Amazon Fire HD 10 Plus"),
    ("Amazon", "Fire", r"\bfire\s*hd\s*10\b", "Amazon Fire HD 10"),
    ("Amazon", "Fire", r"\bfire\s*hd\s*8\b", "Amazon Fire HD 8"),
    ("Amazon", "Fire", r"\bfire\s*7\b", "Amazon Fire 7"),
    ("reMarkable", "reMarkable", r"\bpaper\s*pro\b", "reMarkable Paper Pro"),
    ("reMarkable", "reMarkable", r"\bremarkable\s*2\b", "reMarkable 2"),
    ("reMarkable", "reMarkable", r"\bremarkable\s*1\b", "reMarkable 1"),
)


def _apple(text):
    if not _hit(text, r"\bipad\b|\ba(?:2[0-9]{3}|3[0-9]{3})\b"):
        return None
    size = None
    if _hit(text, r"\b12[.,]9\b"): size = "12.9"
    elif _hit(text, r"\b11(?:[.,]0)?\s*(?:pollici|inch|\"|”)?\b"): size = "11"
    elif _hit(text, r"\b10[.,]5\b"): size = "10.5"
    # Prefer official Apple identifiers over ambiguous seller generation shorthand.
    IDs = (
        (r"\ba335[456]\b", "iPad", "iPad (A16, 2025)"),
        (r"\ba2696\b|\ba2757\b|\ba2777\b", "iPad", "iPad 10ª gen. (2022)"),
        (r"\ba260[2345]\b", "iPad", "iPad 9ª gen. (2021)"),
        (r"\ba2270\b|\ba2428\b|\ba2429\b|\ba2430\b", "iPad", "iPad 8ª gen. (2020)"),
        (r"\ba2197\b|\ba2200\b|\ba2198\b", "iPad", "iPad 7ª gen. (2019)"),
        (r"\ba2993\b|\ba2995\b|\ba2996\b", "iPad mini", "iPad mini (A17 Pro, 2024)"),
        (r"\ba2567\b|\ba2568\b|\ba2569\b", "iPad mini", "iPad mini 6ª gen. (2021)"),
        (r"\ba2588\b|\ba2589\b|\ba2591\b", "iPad Air", "iPad Air 5ª gen. (M1, 2022)"),
        (r"\ba2316\b|\ba2324\b|\ba2325\b|\ba2072\b", "iPad Air", "iPad Air 4ª gen. (2020)"),
    )
    for pattern, fam, model in IDs:
        if _hit(text, pattern): return ("Apple", fam, model)
    # Apple's 11-inch and 12.9-inch iPad Pro generation numbering differs.
    proid = (
        (r"\ba1980\b|\ba2013\b|\ba1934\b|\ba1979\b", 'iPad Pro 11" 1ª gen. (2018)'),
        (r"\ba1876\b|\ba2014\b|\ba1895\b|\ba1983\b", 'iPad Pro 12.9" 3ª gen. (2018)'),
    )
    for pattern,model in proid:
        if _hit(text,pattern): return ("Apple","iPad Pro",model)
    mini = _hit(text, r"\bipad\s*mini\b")
    air = _hit(text, r"\bipad\s*air\b")
    pro = _hit(text, r"\bipad\s*pro\b")
    if mini:
        fam = "iPad mini"
        if _hit(text, r"\ba17\s*pro\b|\b2024\b"): model = "iPad mini (A17 Pro, 2024)"
        elif _hit(text, r"\b(?:6(?:th)?|sesta|6[ªa])\s*(?:gen|generazione)\b|\b2021\b|\bipad\s*mini\s*6\b"): model = "iPad mini 6ª gen. (2021)"
        elif _hit(text, r"\b(?:5(?:th)?|quinta|5[ªa])\s*(?:gen|generazione)\b|\b2019\b"): model = "iPad mini 5ª gen. (2019)"
        elif _hit(text, r"\b(?:4(?:th)?|quarta|4[ªa])\s*(?:gen|generazione)\b"): model = "iPad mini 4ª gen."
        else: model = "iPad mini — generazione da verificare"
    elif air:
        fam = "iPad Air"
        gen = re.search(r"\b([3456])(?:st|nd|rd|th|[ªa])?\s*\.?\s*(?:gen|generazione)\b", text)
        chip = re.search(r"\bm([1234])\b", text)
        if chip:
            model = f"iPad Air {size + chr(34) + ' ' if size else ''}M{chip.group(1)}"
        elif gen: model = f"iPad Air {gen.group(1)}ª gen." 
        else: model = "iPad Air — generazione da verificare"
    elif pro:
        fam = "iPad Pro"
        gen = re.search(r"\b([1-6])(?:st|nd|rd|th|[ªa])?\s*\.?\s*(?:gen|generazione)\b", text)
        chip = re.search(r"\bm([1234])\b", text)
        if chip: model = f"iPad Pro {size + chr(34) + ' ' if size else ''}M{chip.group(1)}"
        elif gen and size: model = f"iPad Pro {size}{chr(34)} {gen.group(1)}ª gen."
        elif size == "11" and _hit(text,r"\b2018\b"): model = 'iPad Pro 11" 1ª gen. (2018)'
        elif size == "12.9" and _hit(text,r"\b2018\b"): model = 'iPad Pro 12.9" 3ª gen. (2018)'
        else: model = "iPad Pro — taglia/generazione da verificare"
    else:
        fam = "iPad"
        gen = re.search(r"\b(7|8|9|10|11)(?:st|nd|rd|th|[ªa])?\s*\.?\s*(?:gen|generazione)\b", text)
        if _hit(text, r"\ba16\b") or (gen and gen.group(1) == "11"):
            model = "iPad (A16, 2025)"
        elif gen: model = f"iPad {gen.group(1)}ª gen." + {"9":" (2021)","8":" (2020)","7":" (2019)","10":" (2022)"}.get(gen.group(1),"")
        elif _hit(text, r"\bipad\s*10\b") and not _hit(text, r"\b10[.,]2\b"): model = "iPad 10ª gen. (2022)"
        elif _hit(text, r"\bipad\s*9\b"): model = "iPad 9ª gen. (2021)"
        else: model = "iPad — generazione da verificare"
    return ("Apple", fam, model)


def _kindle(text):
    if not _hit(text, r"\bkindle\b|\bcolorsoft\b"): return None
    if _hit(text, r"\bcolorsoft\b"): return ("Amazon", "Kindle Colorsoft", "Kindle Colorsoft Signature" if _hit(text, r"signature") else "Kindle Colorsoft")
    if _hit(text, r"\b(?:scribe)\b"):
        if _hit(text, r"\b2024\b|\b(?:2|seconda)\s*(?:gen|generazione)\b"):
            return ("Amazon", "Kindle Scribe", "Kindle Scribe (2024)")
        if _hit(text, r"\b2022\b|\b(?:1|prima)\s*(?:gen|generazione)\b"):
            return ("Amazon", "Kindle Scribe", "Kindle Scribe (2022)")
        return ("Amazon", "Kindle Scribe", "Kindle Scribe — versione da verificare")
    if _hit(text, r"\boasis\b"):
        label = "Kindle Oasis 10ª gen. (2019)" if _hit(text,r"\b10(?:th|[ªa])?\s*(?:gen|generazione)\b") else "Kindle Oasis — generazione da verificare"
        return ("Amazon", "Kindle Oasis", label)
    if _hit(text, r"\bpaper\s*white\b|\bpaperwhite\b"):
        family = "Kindle Paperwhite"
        if _hit(text, r"\b(?:12(?:th)?|12[ªa])\s*(?:gen|generazione)?\b|\b2024\b"): gen = "12ª gen. (2024)"
        elif _hit(text, r"\b(?:11(?:th)?|11[ªa])\s*(?:gen|generazione)?\b|\b2021\b"): gen = "11ª gen. (2021)"
        elif _hit(text, r"\b(?:10(?:th)?|10[ªa])\s*(?:gen|generazione)?\b|\b2018\b"): gen = "10ª gen. (2018)"
        elif _hit(text, r"\b(?:7(?:th)?|7[ªa])\s*(?:gen|generazione)\b"): gen = "7ª gen."
        else: gen = "generazione da verificare"
        prefix = "Kindle Paperwhite Signature Edition" if _hit(text, r"\bsignature\b|\bse\b") else "Kindle Paperwhite"
        return ("Amazon", family, f"{prefix} {gen}")
    gen = re.search(r"\b(10|11|12)(?:th|[ªa])?\s*(?:gen|generazione)\b", text)
    model = "Kindle base " + (gen.group(1) + "ª gen." if gen else "— generazione da verificare")
    return ("Amazon", "Kindle base", model)


def _status(text):
    if _hit(text, r"\b(?:lotto|lot|stock|[2-9]\s*(?:pezzi|pcs))\b"):
        return "⚠️ Lotto / più dispositivi"
    if _hit(text, r"\b(?:ic[l]?oud\s*lock|activation\s*lock|mdm|frp|account\s*lock|bloccato|bloccata|locked|blacklisted|guasto|guasta|difettoso|difettosa|not\s*working|non\s*funzionante|for\s*parts|spares\s*or\s*repair|defekt|broken|schermo\s*rotto|display\s*rotto)\b"):
        return "⚠️ Guasto / bloccato"
    if _hit(text, r"\b(?:cover|custodia|case|housse|copertina|pellicola|screen\s*protector|proteggi\s*schermo|ricambio|replacement|spare\s*part|tastiera|keyboard|folio|pencil|stylus|stilo|penna|caricabatterie|charger|solo\s*scatola|empty\s*box)\b") and not _hit(text, r"\b(?:con|inclus[oa]|insieme|with|plus|\+)\s*(?:pen|pencil|stylus|stilo|custodia|case|cover|tastiera|keyboard)\b"):
        return "⚠️ Accessorio / ricambio"
    if _hit(text, r"\b(?:touch\s*dell\s*latitude|hp\s*elitebook\s*830)\b"):
        return "⚠️ Computer portatile / fuori categoria"
    return "Usato — stato da verificare"


def _configuration(text, model, status):
    """Keep price-sensitive tablet configurations separate when seller states them."""
    if status.startswith("⚠️") or "verificare" in model: return model
    values = []
    # GB/TB; ignore RAM-labelled values and screen sizes.
    for m in re.finditer(r"\b(32|64|128|256|512)\s*gb\b|\b([12])\s*tb\b", text):
        prefix = text[max(0,m.start()-12):m.start()]
        if re.search(r"\b(?:ram|memory\s*ram)\s*:?\s*$", prefix): continue
        val = (m.group(1) + " GB") if m.group(1) else (m.group(2) + " TB")
        values.append(val)
    if values and len(set(values)) == 1:
        model += " · " + values[-1]
    if _hit(text, r"\b(?:5g|4g|lte|cellular|sim|wi[\s-]?fi\s*\+\s*cellular)\b"):
        model += " · Cellular"
    elif _hit(text, r"\bwi[\s-]?fi(?:\s*only)?\b") and not model.startswith(
            ("Kindle ", "Kobo ", "PocketBook ", "BOOX ", "reMarkable ", "Tolino ")):
        # Wi-Fi is standard on these e-readers: do not split identical models
        # just because one seller included Wi-Fi in the title.
        model += " · Wi-Fi"
    return model


def classify_tablet(title):
    """Return (brand, family, exact model/configuration, state)."""
    t = _norm(title)
    status = _status(t)
    result = None
    # Brand gates prevent short model names e.g. Page, Sage and Fire from
    # swallowing unrelated products.
    if _hit(t, r"\bkobo\b"): 
        result = next((("Kobo", family, model) for pat,family,model in KOBO if _hit(t,pat)), ("Kobo","Kobo eReader","Kobo — modello da identificare"))
    elif _hit(t, r"\bpocket[\s-]?book\b"):
        result = next((("PocketBook", family, model) for pat,family,model in POCKETBOOK if _hit(t,pat)), ("PocketBook","PocketBook eReader","PocketBook — modello da identificare"))
    elif _hit(t, r"\b(?:onyx|boox)\b"):
        result = next((("BOOX", family, model) for pat,family,model in BOOX if _hit(t,pat)), ("BOOX","BOOX eReader","BOOX — modello da identificare"))
    elif _hit(t, r"\btolino\b"):
        result = next((("Tolino", family, model) for pat,family,model in TOLINO if _hit(t,pat)), ("Tolino","Tolino eReader","Tolino — modello da identificare"))
    elif _hit(t, r"\b(?:samsung|galaxy\s*tab)\b"):
        result = next((("Samsung", family, model) for pat,family,model in SAMSUNG if _hit(t,pat)), ("Samsung","Galaxy Tab","Samsung Galaxy Tab — modello da identificare"))
    elif _hit(t, r"\bipad\b|\ba(?:2[0-9]{3}|3[0-9]{3})\b"):
        result = _apple(t)
    elif _hit(t, r"\bkindle\b|\bcolorsoft\b"):
        result = _kindle(t)
    else:
        for brand, family, pattern, model in RUGGED:
            if _hit(t,pattern):
                result = (brand,family,model)
                break
        for brand in ("Lenovo","Microsoft","Xiaomi","Huawei","Amazon","reMarkable"):
            if result is not None: break
            if _hit(t,rf"\b{brand}\b") or (brand=="Microsoft" and _hit(t,r"\bsurface\b")) or (brand=="reMarkable" and _hit(t,r"\bremarkable\b")) or (brand=="Xiaomi" and _hit(t,r"\bredmi\b")) or (brand=="Amazon" and _hit(t,r"\bfire\s*(?:hd\s*)?\d+\b")):
                result = next(((b,f,m) for b,f,pat,m in OTHER if b==brand and _hit(t,pat)), (brand,brand+" Tablet",brand+" — modello da identificare"))
                break
    if result is None:
        return ("Non identificato","Tablet / eReader non identificato","Modello da identificare",status)
    brand,family,model = result
    if brand == "Amazon" and family == "Kindle base" and _hit(t, r"\bsignature\b"):
        status = "⚠️ Modello Kindle ambiguo"
    if status == "⚠️ Accessorio / ricambio" and _hit(
            t, r"(?:\+|\bcon\b|\bwith\b)\s*(?:pen\b|pencil\b|stylus\b|stilo\b|custodia\b|case\b|cover\b|tastiera\b|keyboard\b)"):
        status = "Usato — accessorio incluso da verificare"
    if len(set(m.group(0).replace(" ","") for m in re.finditer(r"\b(?:32|64|128|256|512)\s*gb\b",t))) > 1 and _hit(t,r"\b(?:o|oppure|or)\b"):
        status = "⚠️ Varianti memoria alternative"
    return (brand,family,_configuration(t,model,status),status)

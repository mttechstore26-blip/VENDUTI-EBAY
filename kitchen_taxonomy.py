"""Classification for eBay kitchen category 20667. Titles are evidence, not proof of completeness."""
import re
from functools import lru_cache

def match(pattern, text):
    return bool(re.search(pattern, text, re.I))

@lru_cache(maxsize=100000)
def classify_kitchen(title):
    t = re.sub(r"\s+", " ", str(title or "").casefold()).strip()
    brands = [
        ("KitchenAid", r"kitchen\s*-?\s*aid"), ("Vitamix", r"vita\s*-?\s*mix"),
        ("Breville", r"\bbreville\b"), ("Sage", r"\bsage\b"),
        ("Ninja", r"\bninja\b"), ("Vorwerk", r"\bvorwerk\b|\bbimby\b|\bthermomix\b"),
        ("SMEG", r"\bsmeg\b"), ("Zojirushi", r"zojirushi"),
        ("Philips", r"\bphilips\b"), ("De'Longhi", r"de.?longhi|delonghi"),
        ("Gaggia", r"\bgaggia\b"), ("Champion", r"\bchampion\b"),
        ("Blendtec", r"blendtec|k.tec"), ("Kenwood", r"\bkenwood\b"),
        ("Bosch", r"\bbosch\b"), ("Cuisinart", r"cuisinart"),
        ("Technivorm", r"technivorm|moccamaster"), ("Panasonic", r"panasonic"),
        ("Braun", r"\bbraun\b"), ("Jura", r"\bjura\b"),
        ("Keurig", r"\bkeurig\b"), ("Nespresso", r"nespresso"),
        ("Aarke", r"\baarke\b"), ("Tribest", r"tribest|greenstar"),
        ("Flair", r"\bflair\b"), ("La Pavoni", r"la pavoni"),
        ("Eureka", r"\beureka\b"), ("Baratza", r"baratza"),
        ("1Zpresso", r"1zpresso"), ("Fellow", r"\bfellow\b"),
        ("Waring", r"\bwaring\b"), ("Silvercrest", r"silvercrest|monsieur cuisine"),
        ("Cuckoo", r"\bcuckoo\b"), ("Kuvings", r"kuvings"),
        ("Mockmill", r"mockmill"), ("Oster", r"\boster\b"),
        ("GE", r"\bge\b.*(?:opal|profile|brew|coffee)"),
        ("Black & Decker", r"black\s*(?:&|and)\s*decker"),
        ("Saladmaster", r"saladmaster"), ("Magic Mill", r"magic mill"),
        ("VacMaster", r"vacmaster"), ("Nutrimill", r"nutrimill"),
        ("Shark", r"\bshark\b"), ("Crock-Pot", r"crock.?pot"),
        ("Instant Pot", r"instant pot"), ("Saeco", r"\\bsaeco\\b"),
        ("Krups", r"\\bkrups\\b"), ("Lavazza", r"\\blavazza\\b"),
        ("Baratza", r"baratza"), ("Weston", r"\\bweston\\b"),
        ("WonderMill", r"wondermill|whisper mill"), ("Yum Asia", r"yumasia"),
        ("Tchibo", r"tchibo"), ("AEG", r"\\baeg\\b"),
        ("Russell Hobbs", r"russell hobbs"), ("GE", r"\\bge\\b"),
    ]
    brand = next((b for b, p in brands if match(p, t)), "Non identificato")

    # A set may include a bowl/lid: these words alone MUST NOT imply a parts listing.
    parts_only = r"\b(?:solo\s+(?:motore|base|ciotola|coperchio|caraffa|vaso|ricambi|accessori|pannello|scheda)|only\s+(?:base|motor|bowl|jar|lid|parts)|motor\s+base\s+only|replacement\s+(?:part|bowl|jar|lid|motor)|ricambio|ricambi|spare\s+parts?|scheda\s+(?:elettronica|madre)|control\s+board|display\s+board|inverter\s+board|pannello\s+comandi|per\s+pezzi|for\s+parts|non\s+funzionante|not\s+working|broken)\b"
    accessories = r"\b(?:accessorio\s+(?:per|di)|accessori\s+(?:per|di)|attachment\s+for|attachments?\s+only|solo\s+accessori|frusta\s+per|gancio\s+per|coperchio\s+per|ciotola\s+per|bowl\s+for|jar\s+for|tamper\s+for|filtro\s+di\s+ricambio|kit\s+(?:accessori|ricambi))\b"
    incomplete = r"\b(?:senza\s+(?:ciotola|caraffa|coperchio|motore|accessori)|missing\s+(?:bowl|jar|lid|motor|parts)|incomplet[oa]|da\s+riparare|da\s+testare|untested|non\s+testato|as.is)\b"
    # Explicit standalone components often missing the word "ricambio".
    components = r"\b(?:scheda (?:alimentazione|pc|di controllo|elettronica)|display board|digitron|control panel|pannello di controllo|porta completa|scheda madre|power board|microonde.*(?:scheda|pannello)|(?:wb27x|wb07x|de92-|eax\d|ebr\d|adc\d{6,})[a-z0-9-]*)\b"
    if match(components, t):
        condition = "Ricambio / non funzionante"
    elif match(r"\b(?:dispositivo base|unità base|unita base|base unit)\b", t):
        condition = "Incompleto / da verificare"
    elif match(parts_only, t):
        condition = "Ricambio / non funzionante"
    elif match(accessories, t):
        condition = "Accessorio"
    elif match(incomplete, t):
        condition = "Incompleto / da verificare"
    else:
        # Titles seldom prove all parts are included: prefer cautious wording.
        condition = "Apparecchio presumibilmente completo"

    groups = [
        ("Multicooker / pentole elettriche", r"instant pot|multicooker|multi.cooker|multifornello|slow cooker|fornello lento|pentola elettrica|speedi|sf301|rockcrok"),
        ("Affettatrici / tritacarne", r"affettatrice|tritacarne|meat slicer|meat grinder"),
        ("Gelatiere / bevande ghiacciate", r"gelatiera|creami|slushi|slushie|soft serve"),
        ("Gasatori acqua", r"infizz|aarke|soda maker|acqua spumante|carbonator"),
        ("Girarrosti", r"girarrosto|rotisserie"),

        ("Robot da cucina / Bimby", r"bimby|thermomix|monsieur cuisine|robot da cucina|food processor"),
        ("Impastatrici / planetarie", r"stand mixer|mixer da appoggio|miscelatore con supporto|miscelatore stand|impastatrice|planetaria|kitchenaid.*(?:artisan|classic|professional|ksm|k45|k5ss|quart)"),
        ("Macchine espresso", r"espresso|barista|bambino|gaggia|jura|lattissima|dedica|francis francis|microcimbali"),
        ("Macchine caffè / filtro / capsule", r"caffettiera|macchina da caff|macchina caff|nespresso|keurig|senseo|moccamaster|grind.*brew|truebrew|pour over|coffee maker"),
        ("Macinacaffè / macinacereali", r"macinacaff|macina farina|macina grani|grain mill|coffee grinder|mockmill"),
        ("Frullatori / blender", r"frullator|blender|vitamix|blendtec|turboblend"),
        ("Estrattori / centrifughe / spremiagrumi", r"spremiagrum|juicer|estrattore|centrifug|pressa a freddo|greenstar"),
        ("Cuociriso", r"cuociriso|scaldariso|rice cooker|neuro fuzzy|micom"),
        ("Friggitrici ad aria / forni", r"friggitrice ad aria|air fryer|smart oven|forno|\bdz550\b"),
        ("Gelatiere / bevande ghiacciate", r"gelatiera|creami|slushi|slushie|soft serve"),
        ("Bollitori / tè", r"bollitore|tea maker|tea kettle"),
        ("Sottovuoto / confezionatrici", r"sottovuoto|vacuum sealer"),
        ("Macchine per pane / pasta", r"macchina del pane|home bakery|pasta maker|macchina per pasta"),
        ("Tostapane / waffle / popcorn", r"tostapane|toaster|waffle|popcorn"),
        ("Griglie / piastre / padelle", r"griglia|grill|plancha|padella elettrica"),
        ("Filtrazione / gasatura acqua", r"osmosi|ionizzatore|distillatore acqua|carbonator|purificazione"),
        ("Microonde", r"microonde|microwave"),
    ]
    family = next((n for n, p in groups if match(p, t)), "Altri elettrodomestici cucina")
    if condition == "Accessorio":
        family = "Accessori per elettrodomestici"
    elif condition == "Ricambio / non funzionante":
        family = "Ricambi / apparecchi non funzionanti"

    model = "Modello non identificato"
    # Require recognizable manufacturer prefixes, with boundary guards against
    # dimensions, prices, year and generic capacity/voltage numbers.
    extra_models = [
        r"\\b(?:KM0\\d{2}|KM\\d{3,4}|SFCM[- ]?CR\\d{2}|ENV\\d{3}[A-Z]?|ES\\d{3}|SF\\d{3}|WM\\d{4}|KST\\d{4}[A-Z]*|BB[- ]?P(?:AC|DC)\\d{2}[A-Z]*|KLF\\d{2}|TSF\\d{2}[A-Z]*|AE\\d{4}|K[- ]?3500|KSM\\d{2,5}[A-Z]*|K5[- ]?A|BB[- ]?PDC20BA|BB[- ]?PAC20|K5SSWH|TPU\\d{5}|BB[- ]?PDC20|WB\\d{2}X\\d{4,6}|WP\\d{7}|KBGV\\w{2,8})\\b",
        r"\\b(?:Professional 750|Professional 600|Cooking Chef Major|Luxe Caf[eé] Premier|Talea Giro|Encore ESP|Ode Brew|Lagom P64|Virtuoso Plus|Barista Express|Barista Touch)\\b",
    ]
    for pat in extra_models:
        hit = re.search(pat, t, re.I)
        if hit:
            model = re.sub(r"\\s+", " ", hit.group(0)).upper()
            break

    rules = [
        (r"\bg5\s*-?\s*ng\s*-?\s*853s\b", "G5-NG-853S"),
        (r"\btm\s*-?\s*(31|5|6|7)\b", None),
        (r"\b(?:bes|ksm|k45ss|k5ss|vm|nc|dz|np|ns|nw|crp|bta|bdc|klf|dcf|tsf|kmx|mum|skms|kvc|sov|hd|hr|cam|ec|bco|dgb|ksc|kbgv)[-\s]?[a-z0-9]{3,12}\b", None),
        (r"\b(?:a2300|a2500|a3300|a3500|5200|7500)\b", None),
    ]
    for pat, canonical in rules:
        m = re.search(pat, t, re.I)
        if m:
            model = canonical or re.sub(r"[\s-]+", "", m.group(0)).upper()
            if model.startswith("TM") and re.fullmatch(r"TM(?:31|5|6|7)", model):
                pass
            break
    if model == "Modello non identificato":
        labels = [
            ("Barista Touch", r"barista touch"), ("Barista Express", r"barista express"),
            ("Bambino Plus", r"bambino plus"), ("Bambino", r"\bbambino\b"),
            ("Artisan", r"\bartisan\b"), ("Professional 5 Plus", r"professional 5 plus"),
            ("CREAMi", r"\bcreami\b"), ("Neuro Fuzzy", r"neuro fuzzy"),
            ("KBGV Select", r"kbgv select"),
        ]
        model = next((n for n,p in labels if match(p,t)), model)
    return brand, family, model, condition

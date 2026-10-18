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
        # Serie specifiche prima dei raggruppamenti generici.
        specific = [
            ("FIFA 365", r"fifa\\s*365"),
            ("Dylan Dog", r"dylan\\s*dog"),
            ("Harry Potter", r"harry\\s*potter"),
            ("Corto Maltese", r"corto\\s*maltese"),
            ("I Simpson", r"simpsons|\\bsimpson\\b"),
            ("Flintstones", r"flintstones|bedrock bowl"),
            ("Principessa Sissi", r"principessa sissi"),
            ("Amici Cucciolotti", r"amici cucciolotti"),
            ("One Piece", r"one\\s*piece"),
            ("Tour de France / Ciclismo", r"tour de france|eddy merckx|ciclosport|ciclismo"),
            ("Champions League / UCL", r"champions league|champions of europe|\\bucc\\b|\\buefa\\b.*(?:champions|club)"),
            ("FIFA World Cup / Mondiali", r"world\\s*cup|\\bwc\\b|\\bwm\\b|\\bmundial\\w*\\b|mondial\\w*|south africa 2010|qatar 2022|mexico 70|mexico 86|argentina 78|espa(?:na|ña) 82|usa 94|france 98|russia 2018|germany 2006|brasil 2014|m[üu]nchen\\s*74|korea japan 2002|fifa cup 2026|coppa del mondo"),
            ("Europei calcio", r"\\beuro(?:pa)?\\s*(?:80|84|96|200[048]|201[26]|202[048])\\b|\\buefa\\s*euro|campionato europeo"),
            ("Calciatori / Campionati", r"supercalcio|\\bcalciatori\\b|campionato italiano|serie\\s*[a-c]\\b|foot france|la liga|\\bvoetbal\\b|divisione\\s*[12]"),
            ("Sport / Campioni dello sport", r"campioni(?:ssimi)? dello sport|olympia|giochi olimpici|olimpiad|olympic|\\bmunchen\\s*72"),
            ("WWE / Wrestling", r"\\bwwe\\b|smackdown"),
            ("X-Files", r"x[ -]?files?"),
        ]
        family = next((b for b,p in specific if re.search(p,t)), None)
        if family is None:
            family = next((b for b,p in families if re.search(p,t)), None)
        # Se non riconosciamo la serie, distinguiamo il formato dell'articolo.
        if family is None:
            formats = [
                ("Box / display / bustine", r"\\bbox\\b|display|bustina|\\bpacks?\\b|confezioni|packet"),
                ("Card autografate / certificate", r"\\bpsa\\b|\\bcgc\\b|autograph|\\bauto\\b|rookie|\\bcard\\b|\\bcarta\\b"),
                ("Figurine singole / lotti", r"figurina|figurine|\\bstickers?\\b|adesiv\\w*|\\blotto\\b"),
                ("Album e set completi", r"\\balbum\\b|\\bset completo\\b|raccolta completa"),
            ]
            family = next((b for b,p in formats if re.search(p,t)), "Altri album e figurine")

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
            ("Alan Ford",r"\balan ford\b"),
            ("Wolverine",r"\bwolverine\b"),
            ("X-Men",r"x[ -]?men|nuovi mutanti|new mutants|reign of x"),
            ("Fantastici Quattro",r"fantastic four|fantastici quattro"),
            ("Avengers",r"\bavengers\b"),
            ("Superman",r"\bsuperman\b|\bsuperboy\b"),
            ("Wonder Woman",r"wonder woman"),
            ("Lanterna Verde",r"lanterna verde|green lantern"),
            ("Flash",r"flash comics|\bflash\s*#"),
            ("Spawn",r"\bspawn\b"),
            ("Invincible",r"\binvincible\b"),
            ("Star Wars",r"star wars"),
            ("Iron Man",r"iron man"),
            ("Thor",r"\bthor\b"),
            ("Hulk / She-Hulk",r"she[ -]?hulk|incredible hulk"),
            ("Daredevil",r"\bdaredevil\b"),
            ("Deadpool",r"\bdeadpool\b"),
            ("Doctor Strange",r"doctor strange"),
            ("Conan",r"\bconan\b"),
            ("Berserk",r"\bberserk\b"),
            ("Jujutsu Kaisen",r"jujutsu kaisen"),
            ("Vinland Saga",r"vinland saga"),
            ("Nausicaä",r"nausicaa|nausicaä"),
            ("Boruto",r"\bboruto\b"),
            ("Rat-Man",r"rat[ -]?man"),
            ("Ken Parker",r"ken parker"),
            ("Sandman",r"\bsandaman\b|\bsandman\b"),
            ("Teenage Mutant Ninja Turtles",r"teenage mutant ninja turtles|ninja turtles"),
            ("Judge Dredd / 2000 AD",r"judge dredd|2000 ad"),
            ("World of Warcraft",r"world of warcraft"),
            ("Transformers",r"\btransformers\b"),
            ("Sonic",r"sonic the hedgehog"),
            ("G.I. Joe",r"g\.?i\.? joe"),
            ("Hellboy",r"\bhellboy\b"),
            ("Moon Knight",r"moon knight"),
            ("The Punisher",r"\bpunisher\b"),
            ("Predator",r"\bpredator\b"),
            ("Doctor Doom",r"doctor doom"),
            ("Carnage",r"\bcarnage\b"),
            ("Silver Surfer",r"silver surfer"),
            ("Secret Wars",r"secret wars?|guerre segrete"),
            ("Horror / EC",r"house of secrets|haunt of fear|weird fantasy|weird science|ghostly haunts|ghost manor"),
            ("Fumetto originale / tavole",r"planche|dessin original|arte originale|copertina originale|schizzo originale"),
            ("Omnibus / raccolte Marvel",r"\bmarvel\b.*omnibus"),
            ("Altri manga",r"\bmanga\b|higurashi|ichi the killer|fragrant flower"),
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

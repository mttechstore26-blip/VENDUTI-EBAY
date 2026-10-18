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
            ("FIFA 365", r"fifa\s*365"),
            ("Dylan Dog", r"dylan\s*dog"),
            ("Harry Potter", r"harry\s*potter"),
            ("Corto Maltese", r"corto\s*maltese"),
            ("I Simpson", r"simpsons|\bsimpson\b"),
            ("Flintstones", r"flintstones|bedrock bowl"),
            ("Principessa Sissi", r"principessa sissi"),
            ("Amici Cucciolotti", r"amici cucciolotti"),
            ("One Piece", r"one\s*piece"),
            ("Tour de France / Ciclismo", r"tour de france|eddy merckx|ciclosport|ciclismo"),
            ("Champions League / UCL", r"champions league|champions of europe|\bucc\b|\buefa\b.*(?:champions|club)"),
            ("FIFA World Cup / Mondiali", r"world\s*cup|\bwc\b|\bwm\b|\bmundial\w*\b|mondial\w*|south africa 2010|qatar 2022|mexico 70|mexico 86|argentina 78|espa(?:na|ña) 82|usa 94|france 98|russia 2018|germany 2006|brasil 2014|m[üu]nchen\s*74|korea japan 2002|fifa cup 2026|coppa del mondo"),
            ("Europei calcio", r"\beuro(?:pa)?\s*(?:80|84|96|200[048]|201[26]|202[048])\b|\buefa\s*euro|campionato europeo"),
            ("Calciatori / Campionati", r"supercalcio|\bcalciatori\b|campionato italiano|serie\s*[a-c]\b|foot france|la liga|\bvoetbal\b|divisione\s*[12]"),
            ("Sport / Campioni dello sport", r"campioni(?:ssimi)? dello sport|olympia|giochi olimpici|olimpiad|olympic|\bmunchen\s*72"),
            ("WWE / Wrestling", r"\bwwe\b|smackdown"),
            ("X-Files", r"x[ -]?files?"),
        ]
        # Mondiali: separa le edizioni senza confondere il numero di una figurina con l'annata.
        editions = [
            (1970, "Messico", r"mexic[oa]|messico|m[eé]xico"),
            (1974, "Germania Ovest", r"west germany|germania|deutschland|m[üu]nchen|munich"),
            (1978, "Argentina", r"argentina"),
            (1982, "Spagna", r"spagna|espa[ñn]a|spain"),
            (1986, "Messico", r"mexic[oa]|messico|m[eé]xico"),
            (1990, "Italia", r"italia|italy"),
            (1994, "USA", r"usa|united states"),
            (1998, "Francia", r"france|francia"),
            (2002, "Corea/Giappone", r"korea|japan|corea|giappone"),
            (2006, "Germania", r"germany|germania|deutschland"),
            (2010, "Sudafrica", r"south africa|sudafrica"),
            (2014, "Brasile", r"brazil|brasil[ei]?"),
            (2018, "Russia", r"russia"),
            (2022, "Qatar", r"qatar|quatar"),
            (2026, "USA/Canada/Messico", r"world cup|mondial|fifa|mexico|messico"),
        ]
        cup_context = bool(re.search(r"world\s*cup|coppa del mondo|mondial\w*|mundial\w*|\bwc\b|\bwm\b|\bfifa\b|calciatori", t))
        world_family = None
        for year_n, host, host_pattern in editions:
            short = str(year_n)[-2:]
            has_host = bool(re.search(r"\b(?:" + host_pattern + r")\b", t))
            year_match = bool(re.search(r"(?<!\d)" + str(year_n) + r"(?!\d)", t))
            shorthand = bool(re.search(r"(?<!\d)" + short + r"(?!\d)", t))
            # Two-digit shorthand only counts alongside host and/or World Cup wording.
            if (has_host and (year_match or shorthand)) or (year_match and cup_context):
                world_family = f"Mondiali {year_n} — {host}"
                break
        if world_family is not None:
            family = world_family
        else:
            family = next((b for b,p in specific if re.search(p,t)), None)
        if family is None:
            family = next((b for b,p in families if re.search(p,t)), None)
        # Se non riconosciamo la serie, distinguiamo il formato dell'articolo.
        if family is None:
            formats = [
                ("Box / display / bustine", r"\bbox\b|display|bustina|\bpacks?\b|confezioni|packet"),
                ("Card autografate / certificate", r"\bpsa\b|\bcgc\b|autograph|\bauto\b|rookie|\bcard\b|\bcarta\b"),
                ("Figurine singole / lotti", r"figurina|figurine|\bstickers?\b|adesiv\w*|\blotto\b"),
                ("Album e set completi", r"\balbum\b|\bset completo\b|raccolta completa"),
            ]
            family = next((b for b,p in formats if re.search(p,t)), "Altri album e figurine")

        year = re.search(r"\b(19[5-9]\d|20[0-2]\d)(?:\s*[/\-]\s*(?:\d{2}|20\d{2}))?\b",t)
        model = year.group(0) if year else "Anno / edizione non identificato"
        return brand, family, model
    if str(category_id) == "220":
        patterns = [
            ("LEGO", "LEGO Star Wars", r"\blego\b.*\bstar wars\b"),
            ("LEGO", "LEGO Technic", r"\blego\b.*\btechnic\b"),
            ("LEGO", "LEGO City", r"\blego\b.*\bcity\b"),
            ("LEGO", "LEGO", r"\blego\b|\bduplo\b"),
            ("Mattel", "Hot Wheels", r"hot\s*wheels"),
            ("Mattel", "Barbie", r"\bbarbie\b"),
            ("Mattel", "Masters of the Universe", r"masters of the universe|\bmotu\b|he.man"),
            ("Hasbro", "Transformers", r"\btransformers\b"),
            ("Hasbro", "Star Wars action figure", r"star wars.*(?:figure|action|hasbro|kenner)"),
            ("Hasbro", "G.I. Joe", r"g\.?i\.?\s*joe"),
            ("Bandai", "Gundam / Gunpla", r"\bgundam\b|\bgunpla\b"),
            ("Bandai", "Dragon Ball", r"dragon\s*ball"),
            ("Nintendo", "Pokémon", r"pok[eé]mon"),
            ("Nintendo", "Super Mario", r"super\s*mario"),
            ("Funko", "Funko Pop", r"\bfunko\b|\bpop\s*!"),
            ("Playmobil", "Playmobil", r"\bplaymobil\b"),
            ("Schleich", "Schleich", r"\bschleich\b"),
            ("Bruder", "Bruder", r"\bbruder\b"),
            ("Tamiya", "Tamiya", r"\btamiya\b"),
            ("Revell", "Revell", r"\brevell\b"),
            ("Bburago", "Bburago", r"\bbburago\b|\bburago\b"),
            ("Maisto", "Maisto", r"\bmaisto\b"),
            ("Minichamps", "Minichamps", r"\bminichamps\b"),
            ("AUTOart", "AUTOart", r"\bautoart\b"),
            ("IXO", "IXO Models", r"\bixo\b"),
            ("Hornby", "Trenini Hornby", r"\bhornby\b"),
            ("Märklin", "Trenini Märklin", r"\bm[aä]rklin\b"),
            ("Roco", "Trenini Roco", r"\broco\b"),
            ("Scalextric", "Piste Scalextric", r"\bscalextric\b"),
        ]
        brand, family = next(((brand, family) for brand, family, pattern in patterns if re.search(pattern, t)), (None, None))
        if family is None:
            general = [
                ("Modellini auto / moto", r"modellin\w*.*(?:auto|ferrari|porsche|lamborghini|moto)|\bdiecast\b"),
                ("Modellismo ferroviario", r"trenino|locomotiva|ferromodellismo|scala\s*h0\b"),
                ("Aerei / navi / kit", r"aeromodellismo|modellino.*(?:aereo|nave)|\bkit\s*model"),
                ("Action figure", r"action\s*figure|\bfigurine?\s*articolat"),
                ("Bambole", r"\bbambol[ae]\b|\bdoll\b"),
                ("Giochi da tavolo", r"gioco da tavolo|board\s*game"),
                ("Giocattoli radiocomandati", r"radiocomandat|\brc\b"),
            ]
            family = next((name for name, pattern in general if re.search(pattern, t)), "Altri giocattoli e modellismo")
            brand = "Non identificato"
        match = re.search(r"\b(?:set|art\.?|cod\.?|mod\.?|n\.?|no\.?)\s*[:#-]?\s*(\d{4,7})\b", t)
        model = match.group(1) if match else "Modello non identificato"
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
        more_series = [
            ("LOW", r"\blow\b.*(?:remender|tocchini|image comics)"),
            ("Infinity Gauntlet / Guanto dell’Infinito", r"guanto dell.infinito|infinity gauntlet|\bthanos\b"),
            ("Marvel Premiere", r"marvel premiere"),
            ("Teen Titans", r"teen titans|tales of the teen titans|\bcyborg\b.*titans"),
            ("Darkstalkers", r"darkstalkers|morrigan.*udon"),
            ("The Metabarons", r"metabarons|metabaroni"),
            ("MAD Magazine", r"\bmad archives\b|\bmad magazine\b"),
            ("Hot Rods and Racing Cars", r"hot rods|auto da corsa.*fumetto"),
            ("Rachel Rising", r"rachel rising"),
            ("Ghost-Spider / Spider-Gwen", r"ghost.spider|spider.gwen"),
            ("Don Rosa / Zio Paperone", r"don rosa|zio paperone"),
            ("Ultra Gash Inferno", r"ultra gash|suehiro maruo"),
            ("Sehelenex / Thrilling", r"sehelenex|thrilling super fumetti"),
            ("Hawkman", r"\bhawkman\b"),
            ("Lupo mannaro di notte", r"lupo mannaro di notte|werewolf by night"),
            ("Hitman / Agente 47", r"agente 47|nascita del sicario"),
            ("Gaston Lagaffe", r"\bgaston\b"),
            ("Frankenstein", r"frankenstein"),
            ("Amazing Adult Fantasy", r"amazing adult fantasy"),
            ("Spider-Ham", r"spider.ham"),
            ("Strange Tales", r"strange tales"),
            ("Dracula", r"\bdracula\b"),
            ("Justice League", r"justice league|jla\b"),
            ("Lady Death", r"lady death"),
            ("Robin / Tim Drake", r"tim drake|\brobin\b"),
            ("Tarzan", r"\btarzan\b"),
            ("Nick Fury", r"nick fury|s\.?h\.?i\.?e\.?l\.?d"),
            ("Scooby Apocalypse", r"scooby apocalypse"),
            ("Czarface", r"czarface"),
            ("Marvel Zero", r"marvel zero"),
            ("Über", r"\buber\b.*(?:gillen|avatar|fumett)"),
            ("Crossed", r"\bcrossed\b"),
            ("Captain Marvel", r"captain marvel"),
            ("World’s Finest", r"world.s finest"),
            ("The Eternals", r"\beternals\b"),
            ("Super Mario Bros", r"super mario bros"),
            ("Chevalier Ardent", r"chevalier ardent"),
            ("Blueberry", r"\bblueberry\b.*(?:navajos|t\.?\s*5)"),
            ("Stillwater", r"\bstillwater\b"),
            ("Il Mercenario", r"il mercenario|\bsegrelles\b"),
            ("Ice Cream Man", r"ice cream man"),
            ("Doctor Peculiar", r"doctor peculiar"),
            ("Something Is Killing the Children", r"\bsiktc\b|something is killing the children"),
            ("Weird Western Tales", r"weird western tales"),
            ("Haunted / Charlton", r"\bhaunted\b.*(?:charlton|sutton)"),
        ]
        family = next((name for name, pattern in more_series if re.search(pattern, t)), None)
        if family is None:
            family = next((name for name, pattern in series if re.search(pattern, t)), None)
        if family is None:
            other_types = [
                ("Statue / busti / action figure", r"statua|statue|\bbusto\b|action figure|\bfigure\b"),
                ("Tavole / cel / disegni originali", r"\bcellulo\b|\bcel\b|d[eé]cor original|\bdessin\b|arte originale|copertina.*dipinta"),
                ("Lotti misti / varianti", r"scatola.*fumetti|\blotto\b.*(?:fumetti|variant)|copertin[ae] variant"),
                ("Libri e materiale non fumettistico", r"problemi di fisica|\birodov\b|t.shirt|maglietta|supporto acrilico"),
            ]
            family = next((name for name, pattern in other_types if re.search(pattern, t)), "Altri fumetti")

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

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
    if str(category_id) == "101376":
        families = [
            ("Furga", "Furga — vintage", r"\bfurga\b"),
            ("Lenci", "Lenci — vintage", r"\blenci\b"),
            ("Sebino", "Cicciobello / Sebino vintage", r"cicciobello|\bsebino\b"),
            ("Migliorati", "Migliorati — vintage", r"\bmigliorati\b"),
            ("Mattel", "Barbie — vintage / collezione", r"\bbarbie\b"),
            ("Mattel", "Monster High", r"monster high|draculaura|frankie stein"),
            ("MGA", "Bratz", r"\bbratz\b"),
            ("Galoob", "Polly Pocket vintage", r"polly pocket"),
            ("Mattel", "Rainbow Brite / Iridella", r"rainbow brite|iridella"),
            ("Ideal", "Bambole Ideal", r"\bideal\b"),
            ("Ratti", "Ratti — vintage", r"\bratti\b"),
            ("Famosa", "Famosa / Nancy vintage", r"\bfamosa\b|\bnancy\b"),
            ("Hasbro", "My Little Pony vintage", r"my little pony|\bmlp\b"),
            ("Vari", "Bambole di porcellana", r"porcellana|porcelain|bisque"),
            ("Vari", "Bambole antiche / celluloide", r"celluloide|celluloid|antique doll"),
            ("Vari", "Bambole di pezza", r"bambol[ae] di pezza|rag doll"),
            ("Vari", "Lotti misti di bambole", r"\blotto\b|collezione.*bambol"),
            ("Vari", "Accessori / vestiti / ricambi", r"solo vestito|solo abito|only clothes|accessori|ricambi|parti di ricambio"),
        ]
        brand, family = next(((b, name) for b, name, pat in families if re.search(pat, t)),
                             ("Non identificato", "Altre bambole vintage"))
        year = re.search(r"(?<!\d)(19[3-9]\d|20[0-2]\d)(?!\d)", t)
        model = year.group(1) if year else "Modello non identificato"
        return brand, family, model
    if str(category_id) in ("717", "233", "183446"):
        if str(category_id) == "183446":
            # Priorità: accessori / minifigure / imballaggi non sono set completi.
            # Successivamente riconosci il tema LEGO anche quando manca il nome della linea.
            groups = [
                ("LEGO", "LEGO — solo scatole / imballaggi", r"\b(?:solo\s+(?:imballaggio|scatola|box)|only\s+box|empty\s+box|scatola\s+vuota)\b"),
                ("LEGO", "LEGO Minifigure / personaggi", r"\b(?:minifigur\w*|cmf|personaggi\s+lego|copricapo|prototype|prototipo)\b"),
                ("LEGO", "LEGO BrickLink Designer Program", r"bricklink|\b9100\d{2}\b"),
                ("LEGO", "LEGO Ninjago", r"ninjago|spinjitzu|\bzane\b.*(?:lego|9563)"),
                ("LEGO", "LEGO Super Mario / Mario Kart", r"super mario|mario kart|bowser|\b7139[15]\b|\b71438\b|\b40787\b"),
                ("LEGO", "LEGO Castle / Kingdoms", r"\bcastle\b|kingdoms|cavalieri|castello.*(?:lego|king)|\b(?:375|6090|6098|6080|70403)\b"),
                ("LEGO", "LEGO Pirates", r"pirates|pirati|black seas barracuda|eldorado|cross bone clipper|\b(?:6285|6250|6276|6261)\b"),
                ("LEGO", "LEGO Treni / Ferrovia", r"ferrovia|locomotiva|treno|santa fe|monorail|railway|\b(?:7740|7750|10020|10022)\b"),
                ("LEGO", "LEGO Space / Classic Space", r"\b(?:ufo|classic space|interstellar starfighter)\b|\b6979\b"),
                ("LEGO", "LEGO Star Wars", r"star wars|tie fighter|y.wing"),
                ("LEGO", "LEGO Technic", r"\btechnic\b|\b42174\b"),
                ("LEGO", "LEGO Speed Champions", r"speed champions|\b75913\b"),
                ("LEGO", "LEGO Architecture", r"architecture|notre dame|farnsworth|neuschwanstein|piramide.*giza|\b(?:21009|21027|21058|21061|21063)\b"),
                ("LEGO", "LEGO Art", r"\blego art\b|\b31212\b|via lattea|milchstra"),
                ("LEGO", "LEGO Ideas", r"\bideas?\b|willy wonka|apollo saturn|\b(?:21360|92176)\b"),
                ("LEGO", "LEGO Icons / Creator Expert", r"\bicons?\b|creator expert|titanic|winter village|\b(?:10294|10199)\b"),
                ("LEGO", "LEGO The Lord of the Rings / Hobbit", r"lord of the rings|\blotr\b|hobbit|orthanc|elrond|moria|lake.town|\b(?:10237|79006|79013|9473)\b"),
                ("LEGO", "LEGO The Legend of Zelda", r"zelda|deku tree|\b77092\b"),
                ("LEGO", "LEGO Disney / Pixar", r"\bdisney\b|pixar|toy story|topolino|minnie|bella e.*bestia|\b(?:43179|43263|43301)\b"),
                ("LEGO", "LEGO Marvel", r"\bmarvel\b|avengers|iron man|lex luthor|\b(?:76125|76097)\b"),
                ("LEGO", "LEGO Batman / DC", r"\bbatman\b|\bbatmobile\b|\bdc comics\b|\btumbler\b|\b(?:76240|76112|76328)\b"),
                ("LEGO", "LEGO Harry Potter", r"harry potter|gringotts|\b40598\b"),
                ("LEGO", "LEGO Minecraft", r"minecraft|\b21137\b"),
                ("LEGO", "LEGO Jurassic World", r"jurassic|t.rex|\b(?:76956|75929)\b"),
                ("LEGO", "LEGO Indiana Jones", r"indiana jones|\b7197\b"),
                ("LEGO", "LEGO One Piece", r"one piece|\b75646\b"),
                ("LEGO", "LEGO Bionicle", r"bionicle|lhikan|\b8811\b"),
                ("LEGO", "LEGO Dimensions", r"\bdimensions\b|portal adventure time"),
                ("LEGO", "LEGO Horizon", r"\bhorizon\b|tallneck|\b76989\b"),
                ("LEGO", "LEGO Teenage Mutant Ninja Turtles", r"ninja turtles|shellraiser|\btmnt\b|\b79104\b"),
                ("LEGO", "LEGO Avatar", r"\bavatar\b|tulkun|\b75579\b"),
                ("LEGO", "LEGO DUPLO", r"\bduplo\b"),
                ("LEGO", "LEGO City / Town", r"\bcity\b|classic town|legoland town|cargo center|strada principale|\b(?:6391|10041)\b"),
                ("LEGO", "LEGO Education / WeDo", r"\bwedo\b|\beducation\b"),
                ("LEGO", "LEGO Seasonal / Esclusivi", r"\bseasonal\b|capodanno cinese|calendario dell.avvento|\b(?:80101|4002023)\b"),
                ("LEGO", "LEGO vintage / lotti misti", r"\bvintage\b|lotto.*lego|legoland.*\blotto\b|collezione.*lego"),
                ("LEGO", "LEGO — altri set", r"\blego\b"),
                ("Playmobil", "Playmobil", r"\bplaymobil\b"),
                ("Meccano", "Meccano", r"\bmeccano\b"),
                ("K'NEX", "K'NEX", r"\bk.?nex\b"),
            ]
            fallback = "Altre costruzioni"
        elif str(category_id) == "717":
            # Distingue marchio, serie e materiale: un'auto in ghisa non è un set western.
            # Alcuni marchi realizzano diverse famiglie, quindi ordine specifico -> generale.
            groups = [
                ("Marx", "Marx — playset Western / Fort Apache", r"\bmarx\b.*(?:fort apache|fort dearborn|western|johnny west|roy rogers|bar.m.ranch|navarone|best of the west|marxman|usaf|play\s?set.*(?:military|farm))|(?:fort apache|johnny west|marxman).*marx"),
                ("Marx", "Marx — giocattoli in latta", r"\bmarx\b.*(?:tin|latta|wind.?up|frizione|punto.*litograf|litho|midget racer|popeye)"),
                ("Marx", "Marx — altri giocattoli", r"\b(?:marx|louis marx)\b"),
                ("Arcade", "Arcade — auto / camion / trattori in ghisa", r"\barcade\b.*(?:ghisa|cast iron|auto|trattor|camion|dumper|motore|bus|fire|fordson)|(?:trattore|auto).*arcade"),
                ("Hubley", "Hubley — veicoli in ghisa", r"\bhubley\b.*(?:ghisa|cast iron|auto|camion|motocic|vigil|zephyr|fire|dray|carro)"),
                ("AC Williams", "AC Williams — veicoli in ghisa", r"\bac\.?\s*williams\b|a\.c\.\s*williams"),
                ("Kenton", "Kenton — veicoli in ghisa", r"\bkenton\b"),
                ("Technofix", "Technofix — piste e giocattoli meccanici", r"\btechnofix\b|\btechnofix\b"),
                ("Masudaya", "Masudaya — latta giapponese / robot", r"\bmasudaya\b"),
                ("Bandai", "Bandai — latta / vintage", r"\bbandai\b"),
                ("Nomura", "Nomura TN — latta giapponese", r"\bnomura\b|\bnomura tn\b"),
                ("Yonezawa", "Yonezawa — latta giapponese", r"\byonezawa\b"),
                ("Schuco", "Schuco — auto e modellini vintage", r"\bschuco\b"),
                ("Marklin", "Märklin — giocattoli / vapore vintage", r"\b(?:marklin|märklin)\b"),
                ("Mamod", "Mamod — motori a vapore", r"\bmamod\b"),
                ("Fleischmann", "Fleischmann — vapore vintage", r"\bfleischmann\b"),
                ("Polly Pocket", "Polly Pocket vintage", r"polly pocket"),
                ("Schoenhut", "Schoenhut — bambole / circo in legno", r"\bschoenhut\b"),
                ("Rushton", "Rushton — peluche / gomma vintage", r"\brushton\b"),
                ("Steiff", "Steiff — peluche vintage", r"\bsteiff\b"),
                ("Ledra", "Ledra / Ledraplastic — pupazzi in gomma", r"\bledra\b|ledraplastic"),
                ("Ideal", "Ideal — giocattoli meccanici / Mr. Machine", r"\bideal\b.*(?:mr\.?\s*machine|fix.it|giocattol)|\bmr\.?\s*machine\b"),
                ("ERTL", "ERTL — mezzi agricoli e figure", r"\bertl\b"),
                ("Britains", "Britains — soldatini / figure in piombo", r"\bbritains\b"),
                ("Remco", "Remco — playset / elettronici", r"\bremco\b"),
                ("Kingdam", "Kingdam — robot / Diaclone", r"\bkingdam\b"),
                ("Takara", "Takara — Diaclone / Transformers", r"\btakara\b|\bdiaclone\b"),
                ("Mattel", "Mattel — She-Ra / Masters of the Universe", r"\bshe.ra\b|masters of the universe|\bmotu\b"),
                ("Mattel", "Mattel — Thingmaker / Fright Factory", r"\bthingmaker\b|fright factory"),
                ("Mattel", "Mattel — Barbie vintage", r"\bbarbie\b"),
                ("MEGO", "MEGO — personaggi TV e film", r"\bmego\b"),
                ("Kenner", "Star Wars / Kenner vintage", r"star wars|\bkenner\b"),
                ("Hartland", "Lone Ranger / Western", r"lone ranger|\bhartland\b"),
                ("Evel Knievel", "Evel Knievel — Stunt Cycle", r"evel knievel|stunt cycle"),
                ("Madballs", "Madballs / Trash Head / Slime Ball", r"\bmadballs?\b|trash head|slime ball|spitball"),
                ("Beyblade", "Beyblade vintage", r"\bbeyblade\b"),
                ("Disney", "Disney / Hanna-Barbera vintage", r"\bdisney\b|hanna.barbera|flintstone|banana splits|sneezly|popeye|winnie the pooh"),
                ("Schylling", "Schylling — giochi vintage", r"\bschylling\b"),
                ("J. Chein", "Chein — giocattoli in latta", r"\bchein\b"),
                ("Distler", "Distler — giocattoli in latta", r"\bdistler\b"),
                ("Lehmann", "Lehmann — giocattoli meccanici", r"\blehmann?\b"),
                ("Ingap", "INGAP — giocattoli in latta", r"\bingap\b"),
                ("Rosbro", "Rosbro — giocattoli vintage", r"\brosbro\b"),
                ("Schuco", "Schuco — giocattoli vintage", r"\bschuco\b"),
                ("Vari", "Bambole / ventriloqui vintage", r"\b(?:ventriloqu|slappy|bambola|bambole|doll|manichino)\b"),
                ("Vari", "Giocattoli in latta / wind-up", r"\b(?:latta|tin toy|tin.litho|litograf|wind.?up|avvolgibil)\b"),
                ("Vari", "Giocattoli / veicoli in ghisa", r"\bghisa\b|cast iron"),
                ("Vari", "Peluche / pupazzi in gomma", r"\b(?:peluche|plush|gomma|rubber|squeak)\b"),
                ("Vari", "Playset / fortini / ranch vintage", r"\bplay.?set\b|fortino|ranch|fort apache"),
                ("Vari", "Auto / camion vintage", r"\b(?:auto|camion|trattore|automobile|batmobile|jeep|motocicletta)\b"),
                ("Vari", "Robot / spazio vintage", r"\b(?:robot|ufo|disco volante|space tank|missil)\b"),
                ("Vari", "Trottole / giroscopi", r"\b(?:trottol|spinning top|giroscop|beyblade)\b"),
                ("Vari", "Teatri / marionette / burattini", r"\b(?:teatro|marionett|burattin)\b"),
                ("Vari", "Soldatini / figure militari", r"\b(?:soldatin|artiglier|guerrier|figurin)\b"),
                ("Vari", "Giochi e puzzle vintage", r"\b(?:puzzle|gioco dadi|board game|flipper|destrezza)\b"),
                ("Vari", "Giocattoli a pedali / cavalcabili", r"\b(?:pedali|triciclo|bicicletta)\b"),
                ("Vari", "Aerei / navi / treni giocattolo", r"\b(?:aereo|locomotiva|treno|navale|barca)\b"),
                ("Vari", "Accessori / documentazione / ricambi", r"\b(?:catalogo|wishbook|manuale|ricambi|for parts|restauro|solo scatola)\b"),
            ]
            fallback = "Altri giocattoli d'epoca"
        else:
            groups = [
                ("Hasbro", "Monopoly", r"\bmonopoly\b"),
                ("Hasbro", "Risiko", r"\brisiko\b|\brisk\b"),
                ("Hasbro", "Cluedo", r"\bcluedo\b|\bclue\b"),
                ("Mattel", "UNO", r"\buno\b.*(?:carte|gioco|card)"),
                ("Ravensburger", "Ravensburger", r"ravensburger"),
                ("Asmodee", "Catan", r"\bcatan\b|coloni di catan"),
                ("Asmodee", "Dixit", r"\bdixit\b"),
                ("Asmodee", "Ticket to Ride", r"ticket to ride"),
                ("Giochi Uniti", "Carcassonne", r"\bcarcassonne\b"),
                ("Games Workshop", "Warhammer", r"\bwarhammer\b"),
                ("Nintendo", "Pokémon giochi da tavolo", r"pokemon.*(?:gioco da tavolo|board game)"),
                ("Vari", "Scacchi", r"\bscacchi\b|\bchess\b"),
            ]
            fallback = "Altri giochi di società"
        brand, family = next(((brand, family) for brand, family, pat in groups if re.search(pat, t)), ("Non identificato", fallback))
        code = re.search(r"(?<!\\d)(\\d{4,6})(?!\\d)", t) if brand == "LEGO" else re.search(r"\\b(?:set|art\\.?|cod\\.?|mod\\.?)\\s*[:#-]?\\s*(\\d{4,7})\\b", t)
        model = code.group(1) if code else "Modello non identificato"
        if brand == "LEGO" and model == "Modello non identificato":
            lego_set = re.search(r"(?<!\d)(\d{5})(?!\d)", t)
            if lego_set:
                model = lego_set.group(1)
        return brand, family, model
    if str(category_id) == "63":
        series = [
            ("Amazing Spider-Man", r"\bamazing\s+spider[ -]?man\b|\b(?:asm)\s*#?\s*\d"),
            ("Absolute Batman", r"\babsolute\s+batman\b"),
            ("Detective Comics", r"\bdetective\s+comics\b"),
            ("Action Comics", r"\baction\s+comics\b"),
            ("Uncanny X-Men", r"\buncanny\s+x[ -]?men\b"),
            ("Ultimate Spider-Man", r"\bultimate\s+spider[ -]?man\b"),
            ("Dylan Dog Speciale", r"\bdylan\s+dog\s+speciale\b"),
            ("Tex Gigante", r"\btex\s+gigante\b"),
            ("Tex Willer", r"\btex\s+willer\b"),
            ("Topolino Libretto", r"\btopolino\b.*\blibretto\b"),
            ("Diabolik Originale", r"\bdiabolik\b.*\boriginale\b"),
            ("One Piece", r"\bone\s+piece\b"),
            ("Dragon Ball", r"\bdragon\s+ball\b"),
            ("Naruto", r"\bnaruto\b"),
            ("Dragonero", r"\bdragonero\b"),
            ("Nathan Never", r"\bnathan\s+never\b"),
            ("Julia", r"\bjulia\b.*(?:bonelli|fumett|n\.?\s*\d)"),
            ("Lupo Alberto", r"\blupo\s+alberto\b"),
            ("Corto Maltese", r"\bcorto\s+maltese\b"),
            ("Asterix", r"\basterix\b"),
            ("Lucky Luke", r"\blucky\s+luke\b"),
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
        family = next((name for name, pattern in series if re.search(pattern, t)), None)
        if family is None:
            family = next((name for name, pattern in more_series if re.search(pattern, t)), None)
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
        # The edition model combines explicit clues only: never infer publication
        # year or issue number from unrelated prices, CGC grades, or seller IDs.
        issue = re.search(
            r"(?<!\w)(?:n(?:umero|um)?\.?|n°|nº|nr\.?|issue|#)\s*(\d{1,4})(?!\d)", t
        )
        if issue is None:
            # Bare numbers are acceptable only directly after a known series
            # name, not after "lotto", "cgc", "vol", or an ISBN.
            label = re.search(
                r"(?:amazing\s+spider[ -]?man|absolute\s+batman|detective\s+comics|"
                r"action\s+comics|dylan\s+dog|tex\s+willer|topolino|diabolik|"
                r"zagor|batman|spider[ -]?man|one\s+piece)\s+(\d{1,4})\b", t
            )
            issue = label
        # Accept four-digit years only; don't confuse them with numbered issues.
        year = re.search(r"(?<!\d)(?:19[3-9]\d|20[0-2]\d)(?!\d)", t)
        details = []
        if issue:
            details.append("N. " + str(int(issue.group(1))))
        if year:
            details.append("Anno " + year.group(0))
        editions = [
            ("Prima stampa", r"\bprima\s+stampa\b|\bfirst\s+print(?:ing)?\b|\b1st\s+print\b"),
            ("Ristampa", r"\bristampa\b|\breprint\b|\bsecond\s+print(?:ing)?\b|\b2nd\s+print\b"),
            ("Variant cover", r"\bvariant\b|\bcover\s+[b-z]\b"),
            ("Autografato", r"\bautografat[oaie]?\b|\bfirmat[oaie]?\b|\bsigned\b|\bsignature\b"),
            ("CGC", r"\bcgc\b"),
            ("CBCS", r"\bcbcs\b"),
            ("Omnibus", r"\bomnibus\b"),
            ("Lotto", r"\blotto\b|\blot\b|\bcollezione\b|\bblocco\b"),
        ]
        details.extend(label for label, pat in editions if re.search(pat, t))
        model = " · ".join(details) if details else "Numero / anno non identificati"
        return brand, family, model

    if str(category_id) == "20667":
        # Titoli eBay anche tradotti: brand, tipologia e codice modello quando esplicito.
        brands = [
            ("KitchenAid", r"kitchen\s?aid"), ("Vitamix", r"vita[ -]?mix"),
            ("Breville", r"\bbreville\b"), ("Sage", r"\bsage\b"),
            ("Ninja", r"\bninja\b"), ("Vorwerk", r"vorwerk|\bbimby\b|thermomix"),
            ("SMEG", r"\bsmeg\b"), ("Zojirushi", r"zojirushi"),
            ("Philips", r"\bphilips\b"), ("De'Longhi", r"de.?longhi|delonghi"),
            ("Gaggia", r"\bgaggia\b"), ("Champion", r"\bchampion\b"),
            ("Blendtec", r"blendtec|k.tec"), ("Kenwood", r"\bkenwood\b"),
            ("Bosch", r"\bbosch\b"), ("Cuisinart", r"cuisinart"),
            ("Technivorm", r"technivorm|moccamaster"), ("Saladmaster", r"saladmaster"),
            ("Panasonic", r"panasonic"), ("Braun", r"\bbraun\b"),
            ("Jura", r"\bjura\b"), ("Keurig", r"\bkeurig\b"),
            ("Nespresso", r"nespresso"), ("Aarke", r"\baarke\b"),
            ("Tribest", r"tribest|greenstar"), ("Flair", r"\bflair\b"),
            ("La Pavoni", r"la pavoni"), ("Eureka", r"\beureka\b"),
            ("Baratza", r"baratza"), ("1Zpresso", r"1zpresso"),
            ("Fellow", r"\bfellow\b"), ("Magic Mill", r"magic mill"),
            ("Waring", r"waring"), ("White Mountain", r"white mountain"),
            ("Mr. Coffee", r"mr\.? coffee"), ("Silvercrest", r"silvercrest|monsieur cuisine"),
            ("Cuckoo", r"cuckoo"), ("Kuvings", r"kuvings"),
            ("Nama", r"\bnama\b"), ("Joyoung", r"joyoung"),
            ("Mockmill", r"mockmill"), ("Schnitzer", r"schnitzer"),
            ("NutriMill", r"nutrimill"), ("Oster", r"\boster\b"),
            ("GE", r"\bge\b.*(?:opal|profile|brew)"),
            ("VacMaster", r"vacmaster"), ("Multivac", r"multivac"),
            ("Typhur", r"typhur"), ("AquaTru", r"aquatru"),
            ("Bluevua", r"bluevua"), ("Enagic", r"enagic|kangen"),
            ("LEVO", r"\blevo\b"), ("LEМ", r"\blem products\b"),
            ("Black & Decker", r"black\s*(?:&|and)\s*decker"),
            ("Ronic", r"\bronic\b"), ("National", r"\bnational\b"),
            ("Bodum", r"\bbodum\b"), ("Sharp", r"\bsharp\b"),
            ("Whirlpool", r"whirlpool"), ("Samsung", r"samsung"),
            ("LG", r"\blg\b"), ("Siemens", r"siemens"),
            ("Kruve", r"kruve"), ("Chemex", r"chemex"),
        ]
        brand = next((name for name, pat in brands if re.search(pat, t)), "Non identificato")
        accessory = re.search(r"\b(?:scheda|pannello|display board|control board|inverter|ricambio|replacement|solo motore|base solo|motor base only|only base|porta completa|barattolo|caraffa di ricambio|coperchio|only bowl|senza ciotola|senza coperchio|solo sezione motore|attacco miscelatore|inserti filtro|setaccio)\b", t)
        if accessory:
            family = "Accessori / ricambi / componenti"
        else:
            families = [
                ("Robot da cucina / Bimby", r"bimby|thermomix|monsieur cuisine|robot da cucina|food processor|robot cook"),
                ("Impastatrici / planetarie", r"mixer da appoggio|stand mixer|miscelatore|impastatrice|kitchenaid.*(?:artisan|classic|ultra power|ksm|k45|k5ss|quart)|chef elite|\bkmix\b"),
                ("Macchine espresso", r"espresso|barista|bambino|gaggia|jura|lattissima|dedica duo|francis francis|microcimbali"),
                ("Macchine caffè / filtro / capsule", r"caffettiera|macchina da caff|macchina caff|nespresso|keurig|senseo|moccamaster|grind.*brew|truebrew|pour over"),
                ("Macinacaffè / macinacereali", r"macinacaff|smerigliatrice|macina farina|macina grani|mulino|grain mill|mockmill"),
                ("Frullatori / blender", r"frullator|blender|vitamix|blendtec|turboblend"),
                ("Estrattori / centrifughe / spremiagrumi", r"spremiagrum|juicer|estrattore|centrifug|pressa a freddo|greenstar"),
                ("Cuociriso", r"cuociriso|scaldariso|rice cooker|neuro fuzzy|micom|induzione.*riso"),
                ("Friggitrici ad aria / forni", r"friggitrice ad aria|air fryer|smart oven|forno|\bdz550\b"),
                ("Gelatiere / bevande ghiacciate", r"gelatiera|creami|slushi|slushie|congelatore gelato|soft serve"),
                ("Bollitori / tè", r"bollitore|macchina per t[eè]|tea maker"),
                ("Sottovuoto / confezionatrici", r"sottovuoto|vacuum sealer|sigillante"),
                ("Macchine per pane / pasta", r"macchina del pane|macchina per il pane|home bakery|pasta maker|noodle maker|macchina per pasta"),
                ("Tostapane / waffle / popcorn", r"tostapane|waffle|cialda.*belga|popcorn|popper"),
                ("Griglie / piastre / padelle", r"griglia|grill|plancha|padella elettrica|pentola elettrica"),
                ("Filtrazione / gasatura acqua", r"filtrazione acqua|osmosi|ionizzatore|distillatore acqua|carbonator|purificazione"),
                ("Microonde", r"microonde"),
                ("Altri elettrodomestici cucina", r"."),
            ]
            family = next((name for name, pat in families if re.search(pat, t)), "Altri elettrodomestici cucina")
        # Evita di scambiare voltaggio/capacità con il codice modello.
        known = [
            r"g5[- ]ng[- ]853s", r"\btm\s?(?:31|5|6|7)\b",
            r"\b(?:bes|ksm|k45ss|k5ss|vm|nc|dz|tb|ep|np|ns|nw|crp|bta|bdc|klf|dcf|tsf|kmx|mum|gse|skms|fs|fg|hb|cf|ft|sl|kvc|sov|ice|tpu|hd|hr|cam|ec|bco|dgb|ksc|btm|at|ro|sv|kbgv)[- ]?[a-z0-9]{3,15}\b",
        ]
        model = "Modello non identificato"
        for pat in known:
            m = re.search(pat, t, re.I)
            if m:
                model = m.group(0).upper()
                break
        if model == "Modello non identificato":
            for name, pat in [
                ("5200", r"\b5200\b"), ("7500", r"\b7500\b"),
                ("A2300", r"\ba2300\b"), ("A2500", r"\ba2500\b"),
                ("Barista Express", r"barista express"),
                ("Barista Touch", r"barista touch"),
                ("Bambino Plus", r"bambino plus"), ("Bambino", r"\bbambino\b"),
                ("Artisan", r"artisan"), ("CREAMi", r"creami"),
                ("Neuro Fuzzy", r"neuro fuzzy"), ("KBGV Select", r"kbgv select"),
            ]:
                if re.search(pat, t):
                    model = name
                    break
        return brand, family, model
    return "Non identificato", "Altri prodotti", "Modello non identificato"

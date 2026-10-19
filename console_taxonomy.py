"""Model-oriented console classification including retro, special editions and PC handhelds.

Order matters: specific hardware precedes generic families. No model guesses from
color/storage alone. A sale is never dropped merely because it cannot be recognized.
"""
import re

MODELS = [
 ("ASUS","ROG Xbox Ally X",r"\brog\s*xbox\s*ally\s*x\b"),
 ("ASUS","ROG Xbox Ally",r"\brog\s*xbox\s*ally\b"),
 ("ASUS","ROG Ally X",r"\brog\s*ally\s*x\b"),
 ("ASUS","ROG Ally",r"\brog\s*ally\b"),
 ("AYN","Thor Max",r"\bayn\s*thor\s*max\b|\bthor\s*max\b"),
 ("AYN","Thor Pro",r"\bayn\s*thor\s*pro\b|\bthor\s*pro\b"),
 ("AYN","Thor",r"\bayn\s*thor\b"),
 ("AYN","Odin 3 Ultra",r"\b(?:ayn\s*)?odin\s*3\s*ultra\b"),
 ("AYN","Odin 3 Max",r"\b(?:ayn\s*)?odin\s*3\s*max\b"),
 ("AYN","Odin 3 Pro",r"\b(?:ayn\s*)?odin\s*3\s*pro\b"),
 ("AYN","Odin 3",r"\b(?:ayn\s*)?odin\s*3\b"),
 ("AYN","Odin 2 Portal",r"\bodin\s*2\s*portal\b"),
 ("AYN","Odin 2 Mini",r"\bodin\s*2\s*mini\b"),
 ("AYN","Odin 2",r"\bodin\s*2\b"),
 ("AYN","Odin",r"\bayn\s*odin\b"),
 ("Nintendo","New 3DS XL",r"\bnew\s*nintendo\s*3ds\s*(?:xl|ll)\b|\bnew\s*3ds\s*(?:xl|ll)\b|\bnuov[ao]\s*3ds\s*(?:xl|ll)\b"),
 ("Nintendo","New 2DS XL",r"\b(?:new\s*)?(?:nintendo\s*)?2ds\s*(?:xl|ll)\b"),
 ("Nintendo","New 3DS",r"\b(?:new|nuov[ao])\s*(?:nintendo\s*)?3ds\b"),
 ("Nintendo","3DS XL",r"\b(?:nintendo\s*)?3ds\s*(?:xl|ll)\b|\b3dsxl\b"),
 ("Nintendo","2DS",r"\b(?:nintendo\s*)?2ds\b"),
 ("Nintendo","3DS",r"\b(?:nintendo\s*)?3ds\b"),
 ("Nintendo","DSi XL",r"\b(?:nintendo\s*)?dsi\s*(?:xl|ll)\b"),
 ("Nintendo","DSi",r"\b(?:nintendo\s*)?dsi\b"),
 ("Nintendo","DS Lite",r"\b(?:nintendo\s*)?ds\s*lite\b"),
 ("Nintendo","DS",r"\bnintendo\s*ds\b"),
 ("Nintendo","Game Boy Micro",r"\b(?:game\s*boy|gameboy)\s*micro\b"),
 ("Nintendo","Game Boy Advance SP",r"\b(?:game\s*boy|gameboy|gba)\s*advance\s*sp\b|\bgba\s*sp\b|\bags[- ]?0(?:01|101)\b"),
 ("Nintendo","Game Boy Advance",r"\b(?:game\s*boy|gameboy)\s*advance\b|\bgba\b"),
 ("Nintendo","Game Boy Color",r"\b(?:game\s*boy|gameboy)\s*colou?r\b|\bgbc\b"),
 ("Nintendo","Game Boy Pocket",r"\b(?:game\s*boy|gameboy)\s*pocket\b"),
 ("Nintendo","Game Boy",r"\b(?:game\s*boy|gameboy)\b"),
 ("Nintendo","Game & Watch",r"\bgame\s*(?:&|and)\s*watch\b|\bpanorama\s*screen\b|\bdonkey\s*kong\s*jr\.?\s*tabletop\b"),
 ("Nintendo","GameCube",r"\bgame\s*cube\b|\bgamecube\b|\bdol[- ]?10[01]\b"),
 ("Nintendo","Nintendo 64",r"\bnintendo\s*64\b|\bn64\b"),
 ("Nintendo","Super Nintendo / SNES",r"\bsnes\b|\bsuper\s*nintendo\b|\bsuper\s*famicom\b"),
 ("Nintendo","Famicom / NES",r"\bfamicom\b|\bnes\b|\bnintendo entertainment system\b"),
 ("Nintendo","Wii U",r"\bwii\s*u\b|\bwiiu\b"),
 ("Nintendo","Wii",r"\bwii\b"),
 ("Sony","PlayStation 3 (PS3)",r"\bplaystation\s*3\b|\bps3\b|\bcech[a-z0-9-]{3,}\b|\bdecha00a\b"),
 ("Sony","PlayStation 2 (PS2)",r"\bplaystation\s*2\b|\bplaystation2\b|\bps2\b|\bdtl[- ]?h30000\b"),
 ("Sony","PlayStation 1 (PS1)",r"\bplaystation\s*(?:1|one)\b|\bps1\b|\bpsx\b"),
 ("Sony","PS Vita TV / PlayStation TV",r"\bpstv\b|\bps\s*vita\s*tv\b|\bplaystation\s*tv\b"),
 ("Sony","PS Vita",r"\bps\s*vita\b|\bplaystation\s*vita\b|\bpch[- ]?\d{4}\b"),
 ("Sony","PSP Go",r"\bpsp\s*go\b|\bpsp[- ]?n1000\b"),
 ("Sony","PSP",r"\bpsp\b|\bplaystation\s*portable\b"),
 ("Microsoft","Xbox 360",r"\bxbox\s*360\b"),
 ("Microsoft","Xbox One S",r"\bxbox\s*one\s*s\b"),
 ("Microsoft","Xbox One",r"\bxbox\s*one\b"),
 ("Microsoft","Original Xbox",r"\boriginal\s*xbox\b|\bxbox\s*(?:original|classic|halo special|crystal edition)\b"),
 ("SEGA","Game Gear",r"\bgame\s*gear\b"),
 ("SEGA","Genesis Nomad",r"\bgenesis\s*nomad\b|\bsega\s*nomad\b"),
 ("SEGA","Sega CDX / Multi-Mega",r"\bsega\s*(?:genesis\s*)?cdx\b|\bmulti[\s-]*mega\b"),
 ("SEGA","Sega CD / Mega-CD",r"\bsega\s*cd\b|\bmegacd\b|\bmega\s*cd\b"),
 ("SEGA","Genesis / Mega Drive",r"\bgenesis\b|\bmega\s*drive\b|\bmegadrive\b"),
 ("SEGA","Dreamcast",r"\bdreamcast\b"),
 ("SEGA","Saturn",r"\bsega\s*saturn\b"),
 ("SEGA","Master System",r"\bmaster\s*system\b"),
 ("NEC","PC Engine LT",r"\bpc\s*engine\s*lt\b"),
 ("NEC","SuperGrafx",r"\bsuper\s*grafx\b|\bsupergrafx\b"),
 ("NEC","PC Engine Duo",r"\bpc\s*engine\s*duo\b"),
 ("NEC","TurboGrafx-16",r"\bturbografx\b|\bturbo\s*grafx\b"),
 ("NEC","PC Engine",r"\bpc\s*engine\b"),
 ("SNK","Neo Geo CD",r"\bneo\s*geo\s*cd\b"),
 ("SNK","Neo Geo AES",r"\bneo\s*geo\s*aes\b|\bneo[- ]?0\b"),
 ("SNK","Neo Geo Pocket",r"\bneo\s*geo\s*pocket\b"),
 ("Atari","Jaguar",r"\batari\s*jaguar\b"),
 ("Atari","Lynx II",r"\batari\s*lynx\s*(?:ii|2)\b"),
 ("Atari","Lynx",r"\batari\s*lynx\b"),
 ("Atari","7800",r"\batari\s*7800\b"),
 ("Atari","5200",r"\batari\s*5200\b"),
 ("Atari","2600",r"\batari\s*2600\b"),
 ("Panasonic","3DO FZ-1",r"\b3do\b.*\bfz[- ]?1\b"),
 ("Panasonic","3DO",r"\b3do\b"),
 ("Fairchild","Channel F",r"\bfairchild\s*channel\s*f\b"),
 ("APF","M-1000",r"\bapf\s*m[- ]?1000\b"),
 ("Commodore","C64 Games System",r"\bcommodore\s*64\s*gs\b|\bc64\s*gs\b"),
 ("Valve","Steam Machine",r"\bsteam\s*machine\b"),
 ("MSI","Claw",r"\bmsi\s*claw\b"),
 ("AYANEO","AYANEO 3",r"\bayaneo\s*3\b"),
 ("AYANEO","AYANEO",r"\bayaneo\b"),
 ("GPD","WIN Max 2",r"\bgpd\s*win\s*max\s*2\b"),
 ("GPD","WIN Mini",r"\bgpd\s*win\s*mini\b"),
 ("GPD","WIN 4",r"\bgpd\s*win\s*4\b"),
 ("GPD","WIN",r"\bgpd\s*win\b"),
 ("OneXPlayer","OneXFly",r"\bonexfly\b"),
 ("OneXPlayer","Apex",r"\bonexplayer\s*apex\b"),
 ("OneXPlayer","OneXPlayer 2 Pro",r"\bonexplayer\s*2\s*pro\b"),
 ("OneXPlayer","OneXPlayer",r"\bonexplayer\b"),
 ("Analogue","Pocket",r"\banalogue\s*pocket\b|\btasca\s*analogica\b"),
 ("Panic","Playdate",r"\bplaydate\b"),
 ("Anbernic","RG557",r"\brg557\b"),
 ("Anbernic","Anbernic",r"\banbernic\b"),
 ("Blaze","Evercade",r"\bevercade\b"),
 ("Mattel","Intellivision",r"\bintellivision\b"),
 ("Coleco","ColecoVision",r"\bcolecovision\b"),
 ("GCE","Vectrex",r"\bvectrex\b"),
 ("Apple/Bandai","Pippin",r"\bpippin\b"),
]
# Distinguish editions as separate filterable labels without splitting a platform
# on color alone. Console sale vs peripheral should be reviewed.
EDITIONS=[
 ("Hyrule Edition",r"\bhyrule\b"),("SNES Edition",r"\b(?:snes|super nintendo|super famicom)\s*edition\b"),
 ("Fire Emblem Edition",r"\bfire emblem\b"),("Zelda Edition",r"\bzelda\b"),
 ("Pokemon Edition",r"\bpok[eé]mon\b"),("Galaxy Edition",r"\bgalaxy edition\b"),
 ("Halo Edition",r"\bhalo\b.*\bedition\b"),("Gears of War Edition",r"\bgears of war\b.*\bedition\b"),
]
def classify_console(title):
    t=re.sub(r"\s+"," ",str(title or "").casefold())
    suspicious = r"\b(?:solo\s+scatola|empty box|box only|controller only|solo controller|senza console|for parts|per ricambi|non funzionante|guasta|broken|figure|figura\s+(?:in\s+)?pvc|action figure|scheda madre|motherboard|monitor|display replacement|scheda di acquisizione|capture card|cartridge only|cartuccia gioco|game only|solo gioco)\b"
    if re.search(suspicious,t):
        state="Non console / ricambio / da verificare"
    elif re.search(r"\b(?:lotto|bundle|con giochi|2 console|due console)\b",t):
        state="Bundle / da verificare"
    else:
        state="Console presumibilmente completa"
    # Earlier patterns; more specific new cases override ambiguous defaults.
    for brand,model,pat in MODELS:
        if re.search(pat,t):
            edition=next((label for label,expr in EDITIONS if re.search(expr,t)),None)
            if edition and model in ("New 3DS XL","3DS XL","Game Boy Advance SP","Original Xbox","Xbox 360"):
                model += " — "+edition
            return brand,"Console",model,state
    return "Non identificato","Console","Modello non identificato",state

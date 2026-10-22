"""Classify sold digital cameras by exact model and item configuration."""
import re

MODELS = (
    ("Canon", "PowerShot", r"\bsx700\s*hs\b", "Canon PowerShot SX700 HS"),
    ("Canon", "PowerShot", r"\bsx710\s*hs\b", "Canon PowerShot SX710 HS"),
    ("Canon", "PowerShot", r"\bsx260\s*hs\b", "Canon PowerShot SX260 HS"),
    ("Canon", "PowerShot", r"\bsx50\s*hs\b", "Canon PowerShot SX50 HS"),
    ("Canon", "PowerShot", r"\bsx200\s*is\b", "Canon PowerShot SX200 IS"),
    ("Canon", "PowerShot", r"\ba2300\b", "Canon PowerShot A2300"),
    ("Canon", "PowerShot", r"\ba630\b", "Canon PowerShot A630"),
    ("Canon", "PowerShot", r"\bs90\b", "Canon PowerShot S90"),
    ("Canon", "PowerShot", r"\bg9\b", "Canon PowerShot G9"),
    ("Canon", "IXUS", r"\b160\b", "Canon IXUS 160"),
    ("Canon", "IXUS", r"\b150\b", "Canon IXUS 150"),
    ("Canon", "IXUS", r"\b155\b", "Canon IXUS 155"),
    ("Canon", "IXUS", r"\b220\s*hs\b", "Canon IXUS 220 HS"),
    ("Canon", "IXUS", r"\b265\s*hs\b", "Canon IXUS 265 HS"),
    ("Canon", "IXUS", r"\b275\s*hs\b", "Canon IXUS 275 HS"),
    ("Canon", "EOS", r"\b5d\s*mark\s*ii\b", "Canon EOS 5D Mark II"),
    ("Canon", "EOS", r"\b6d\b", "Canon EOS 6D"),
    ("Canon", "EOS", r"\b350d\b", "Canon EOS 350D"),
    ("Canon", "EOS M", r"\bm50\s*mark\s*ii\b", "Canon EOS M M50 Mark II"),
    ("Canon", "EOS M", r"\bm50\b", "Canon EOS M M50"),
    ("Canon", "EOS M", r"\bm10\b", "Canon EOS M M10"),
    ("Canon", "EOS M", r"\bm3\b", "Canon EOS M M3"),
    ("Nikon", "Reflex", r"\bd7100\b", "Nikon D7100"),
    ("Nikon", "Reflex", r"\bd7000\b", "Nikon D7000"),
    ("Nikon", "Reflex", r"\bd700\b", "Nikon D700"),
    ("Nikon", "Reflex", r"\bd3100\b", "Nikon D3100"),
    ("Nikon", "Reflex", r"\bd5100\b", "Nikon D5100"),
    ("Nikon", "Coolpix", r"\bp310\b", "Nikon Coolpix P310"),
    ("Nikon", "Coolpix", r"\bp7000\b", "Nikon Coolpix P7000"),
    ("Nikon", "Coolpix", r"\bs9500\b", "Nikon Coolpix S9500"),
    ("Nikon", "Coolpix", r"\bs9600\b", "Nikon Coolpix S9600"),
    ("Nikon", "Coolpix", r"\bb700\b", "Nikon Coolpix B700"),
    ("Nikon", "Coolpix", r"\b995\b", "Nikon Coolpix 995"),
    ("Nikon", "Coolpix", r"\bsq\b", "Nikon Coolpix SQ"),
    ("Nikon", "Nikon 1", r"\baw1\b", "Nikon Nikon 1 AW1"),
    ("Nikon", "Nikon 1", r"\bj4\b", "Nikon Nikon 1 J4"),
    ("Nikon", "Nikon 1", r"\bj1\b", "Nikon Nikon 1 J1"),
    ("Sony", "Cyber-shot", r"\bdsc[-\s]?w810\b", "Sony Cyber-shot DSC-W810"),
    ("Sony", "Cyber-shot", r"\bdsc[-\s]?w120\b", "Sony Cyber-shot DSC-W120"),
    ("Sony", "Cyber-shot", r"\bdsc[-\s]?wx350\b", "Sony Cyber-shot DSC-WX350"),
    ("Sony", "Cyber-shot", r"\bdsc[-\s]?wx300\b", "Sony Cyber-shot DSC-WX300"),
    ("Sony", "Cyber-shot", r"\bdsc[-\s]?hx400v\b", "Sony Cyber-shot DSC-HX400V"),
    ("Sony", "Cyber-shot", r"\bdsc[-\s]?hx50v\b", "Sony Cyber-shot DSC-HX50V"),
    ("Sony", "Cyber-shot", r"\bdsc[-\s]?hx9v\b", "Sony Cyber-shot DSC-HX9V"),
    ("Sony", "Cyber-shot", r"\bdsc[-\s]?rx10\b", "Sony Cyber-shot DSC-RX10"),
    ("Sony", "Cyber-shot", r"\bdsc[-\s]?t10\b", "Sony Cyber-shot DSC-T10"),
    ("Sony", "Alpha", r"\ba7\s*ii\b", "Sony Alpha A7 II"),
    ("Sony", "Alpha", r"\ba290\b", "Sony Alpha A290"),
    ("Sony", "Alpha", r"\ba5000\b", "Sony Alpha A5000"),
    ("Sony", "NEX", r"\bnex[-\s]?f3\b", "Sony NEX NEX-F3"),
    ("Sony", "NEX", r"\bnex[-\s]?3n\b", "Sony NEX NEX-3N"),
    ("Panasonic", "Lumix", r"\btz57\b", "Panasonic Lumix TZ57"),
    ("Panasonic", "Lumix", r"\bfz300\b", "Panasonic Lumix FZ300"),
    ("Panasonic", "Lumix", r"\bfz82\b", "Panasonic Lumix FZ82"),
    ("Panasonic", "Lumix", r"\bgh4\b", "Panasonic Lumix GH4"),
    ("Panasonic", "Lumix", r"\bg6\b", "Panasonic Lumix G6"),
    ("Panasonic", "Lumix", r"\blf1\b", "Panasonic Lumix LF1"),
    ("Olympus", "PEN", r"\be[-\s]?pl3\b", "Olympus PEN E-PL3"),
    ("Olympus", "Tough", r"\btg[-\s]?6\b", "Olympus Tough TG-6"),
    ("Olympus", "Tough", r"\btg[-\s]?870\b", "Olympus Tough TG-870"),
    ("Olympus", "Stylus", r"\bsp[-\s]?100ee\b", "Olympus Stylus SP-100EE"),
    ("Fujifilm", "FinePix", r"\bs2\s*pro\b", "Fujifilm FinePix S2 Pro"),
    ("Fujifilm", "FinePix", r"\bs5\s*pro\b", "Fujifilm FinePix S5 Pro"),
    ("Fujifilm", "FinePix", r"\bm603\b", "Fujifilm FinePix M603"),
    ("Fujifilm", "FinePix", r"\bhs30\s*exr\b", "Fujifilm FinePix HS30 EXR"),
    ("Fujifilm", "X", r"\bxf1\b", "Fujifilm X XF1"),
    ("Pentax", "K", r"\bk[-\s]?30\b", "Pentax K K-30"),
    ("Pentax", "K", r"\bk[-\s]?s1\b", "Pentax K K-S1"),
    ("Samsung", "NX", r"\bnx1000\b", "Samsung NX NX1000"),
    ("Samsung", "NX", r"\bnx1100\b", "Samsung NX NX1100"),
    ("Samsung", "NX", r"\bnx2000\b", "Samsung NX NX2000"),
    ("Samsung", "WB", r"\bwb350f\b", "Samsung WB WB350F"),
    ("Samsung", "WB", r"\bwb5500\b", "Samsung WB WB5500"),
    ("Insta360", "Ace", r"\bace\s*pro\s*2\b", "Insta360 Ace Ace Pro 2"),
    ("Insta360", "Ace", r"\bace\s*pro\b", "Insta360 Ace Ace Pro"),
    ("Insta360", "X", r"\bx4\s*air\b", "Insta360 X X4 Air"),
    ("GoPro", "HERO", r"\bhero11\s*black\b", "GoPro HERO HERO11 Black"),
    ("GoPro", "MAX", r"\bmax\b", "GoPro MAX MAX"),
    ("Apple", "QuickTake", r"\bquicktake\s*200\b", "Apple QuickTake QuickTake 200"),
    ("Sigma", "DP", r"\bdp1\b", "Sigma DP DP1"),
    ("Canon", "EOS", r"\b(?:eos\s*)?(?:1300d|rebel\s*t6)\b", "Canon EOS 1300D / Rebel T6"),
    ("Canon", "EOS", r"\b(?:eos\s*)?2000d\b", "Canon EOS 2000D"),
    ("Canon", "EOS", r"\b(?:eos\s*)?1200d\b", "Canon EOS 1200D"),
    ("Canon", "EOS", r"\b(?:eos\s*)?(?:750d|rebel\s*t6i)\b", "Canon EOS 750D"),
    ("Canon", "EOS", r"\b(?:eos\s*)?800d\b", "Canon EOS 800D"),
    ("Canon", "EOS", r"\b(?:eos\s*)?700d\b", "Canon EOS 700D"),
    ("Canon", "EOS", r"\b(?:eos\s*)?600d\b", "Canon EOS 600D"),
    ("Canon", "EOS", r"\b(?:eos\s*)?250d\b", "Canon EOS 250D"),
    ("Canon", "EOS", r"\b(?:eos\s*)?100d\b", "Canon EOS 100D"),
    ("Canon", "EOS", r"\b(?:eos\s*)?40d\b", "Canon EOS 40D"),
    ("Canon", "EOS", r"\b(?:eos\s*)?7d\b", "Canon EOS 7D"),
    ("Canon", "EOS", r"\b(?:eos\s*)?5d\s*(?:classic|mki|mark\s*i)?\b", "Canon EOS 5D (versione da verificare)"),
    ("Canon", "IXUS", r"\b(?:ixus|ixy|elph)\s*(?:105|210\s*is)\b", "Canon IXUS 105"),
    ("Canon", "IXUS", r"\b(?:ixus\s*120\s*is|ixy\s*220\s*is|elph\s*sd940\s*is)\b", "Canon IXUS 120 IS"),
    ("Canon", "PowerShot", r"\b(?:powershot\s*)?g\s*11\b", "Canon PowerShot G11"),
    ("Nikon", "Reflex", r"\bd\s*3300\b", "Nikon D3300"),
    ("Nikon", "Reflex", r"\bd\s*3400\b", "Nikon D3400"),
    ("Nikon", "Reflex", r"\bd\s*3500\b", "Nikon D3500"),
    ("Nikon", "Reflex", r"\bd\s*3200\b", "Nikon D3200"),
    ("Nikon", "Reflex", r"\bd\s*5300\b", "Nikon D5300"),
    ("Nikon", "Reflex", r"\bd\s*5600\b", "Nikon D5600"),
    ("Nikon", "Reflex", r"\bd\s*5000\b", "Nikon D5000"),
    ("Nikon", "Reflex", r"\bd\s*200\b", "Nikon D200"),
    ("Nikon", "Reflex", r"\bd\s*90\b", "Nikon D90"),
    ("Nikon", "Coolpix", r"\b(?:coolpix\s*)?aw\s*120\b", "Nikon Coolpix AW120"),
    ("Nikon", "Coolpix", r"\b(?:coolpix\s*)?s\s*6600\b", "Nikon Coolpix S6600"),
    ("Nikon", "Coolpix", r"\b(?:coolpix\s*)?s\s*3500\b", "Nikon Coolpix S3500"),
    ("Sony", "NEX", r"\b(?:alpha\s*)?nex[-\s]?6\b", "Sony NEX-6"),
    ("Sony", "NEX", r"\b(?:alpha\s*)?nex[-\s]?7\b", "Sony NEX-7"),
    ("Sony", "Alpha", r"\b(?:alpha\s*|a\s*)?6000\b", "Sony Alpha A6000"),
    ("Sony", "Alpha", r"\b(?:alpha\s*|a\s*)?6300\b", "Sony Alpha A6300"),
    ("Sony", "Cyber-shot", r"\b(?:dsc[-\s]?)?f\s*828\b", "Sony Cyber-shot DSC-F828"),
    ("Sony", "Cyber-shot", r"\b(?:dsc[-\s]?)?w\s*830\b", "Sony Cyber-shot DSC-W830"),
    ("Sony", "Cyber-shot", r"\b(?:dsc[-\s]?)?hx\s*350\b", "Sony Cyber-shot DSC-HX350"),
    ("Sony", "Cyber-shot", r"\b(?:dsc[-\s]?)?rx\s*100\s*(?:m[2-7]|ii|iii|iv|v|vi|vii)?\b", "Sony RX100 (versione da verificare)"),
    ("Panasonic", "Lumix", r"\b(?:dmc[-\s]?)?lx\s*2\b", "Panasonic Lumix LX2"),
    ("Panasonic", "Lumix", r"\b(?:dmc[-\s]?)?lx\s*3\b", "Panasonic Lumix LX3"),
    ("Panasonic", "Lumix", r"\b(?:dmc[-\s]?)?fz\s*1000\b", "Panasonic Lumix FZ1000"),
    ("Olympus", "PEN", r"\b(?:pen\s*)?e[-\s]?pl\s*8\b", "Olympus PEN E-PL8"),
    ("Olympus", "Stylus", r"\b(?:stylus\s*)?sh[-\s]?2\b", "Olympus Stylus SH-2"),
    ("Sigma", "SD", r"\bsd\s*quattro\b", "Sigma SD Quattro"),
    ("GoPro", "HERO", r"\bhero\s*12\b", "GoPro HERO12 Black"),
)
def classify_camera(title):
    t = str(title or "").casefold()
    brand = next((b for b in ("Canon","Nikon","Sony","Panasonic","Fujifilm","Olympus","Pentax","Kodak","Sigma","GoPro","Samsung","Insta360","Apple") if b.casefold() in t), "Non identificato")
    if re.search(r"\b(?:solo\s+obiettivo|obiettivo\s+solo|lens\s+only|ricambi|for\s+parts|defekt|non\s+funzionante|guasta|guasto)\b", t):
        return brand, "Ricambi e accessori", "Prodotto da verificare", "Guasto / accessori"
    model, family = "Modello da identificare", "Fotocamere digitali"
    for b, group, pattern, name in MODELS:
        if b.casefold() not in t and not (b == "Fujifilm" and re.search(r"\bfuji\b",t)):
            continue
        if re.search(pattern, t, re.I):
            brand, family, model = b, group, name
            break
    if re.search(r"\b(?:solo\s+corpo|corpo\s+macchina|body\s+only|body\s+reflex|solo\s+body)\b", t):
        state = "Solo corpo"
    else:
        # Multiple distinct lens focal ranges in the seller title are a
        # stronger signal than a generic "kit" or a list of accessories.
        lenses = set(re.findall(r"\b\d{2,3}\s*[-–]\s*\d{2,3}\s*(?:mm)?\b", t))
        plural = bool(re.search(r"\b(?:due|2|tre|3|quattro|4)\s+(?:obiettiv\w*|lenti|lens\w*)\b|\b(?:obiettiv\w*|lenti|lenses)\s*[x×]\s*[234]\b", t))
        if plural or len(lenses) >= 2:
            state = "Kit con più obiettivi"
        elif len(lenses) == 1 or re.search(r"\b(?:kit\s+con\s+(?:un\s+)?obiettiv\w*|con\s+(?:un\s+)?obiettiv\w*|\+\s*obiettiv\w*)\b", t):
            state = "Kit con un obiettivo"
        else:
            state = "Dotazione non specificata"
    return brand, family, model, state

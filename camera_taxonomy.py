"""Classify sold digital cameras by exact model and item configuration."""
import re

MODELS = (
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
    brand = next((b for b in ("Canon","Nikon","Sony","Panasonic","Fujifilm","Olympus","Pentax","Kodak","Sigma","GoPro") if b.casefold() in t), "Non identificato")
    if re.search(r"\b(?:solo\s+obiettivo|obiettivo\s+solo|lens\s+only|ricambi|for\s+parts|defekt|non\s+funzionante|guasta|guasto)\b", t):
        return brand, "Ricambi e accessori", "Prodotto da verificare", "Guasto / accessori"
    model, family = "Modello da identificare", "Fotocamere digitali"
    for b, group, pattern, name in MODELS:
        if re.search(pattern, t, re.I):
            brand, family, model = b, group, name
            break
    if re.search(r"\b(?:solo\s+corpo|corpo\s+macchina|body\s+only|body\s+reflex|solo\s+body)\b", t):
        state = "Solo corpo"
    elif re.search(r"\b(?:18[-\s]?55|55[-\s]?250|18[-\s]?105|18[-\s]?200|kit\s+con|con\s+obiettiv|\+\s*obiettiv)\b", t):
        state = "Kit con obiettivo"
    else:
        state = "Configurazione da verificare"
    return brand, family, model, state

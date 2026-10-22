"""Conservative digital-camera brand/model grouping from listing titles."""
import re

MODELS = (
    ("Canon", r"\b(?:eos\s*)?(?:1300d|rebel\s*t6)\b", "Canon EOS 1300D / Rebel T6"),
    ("Canon", r"\b(?:eos\s*)?2000d\b", "Canon EOS 2000D"),
    ("Canon", r"\b(?:eos\s*)?1200d\b", "Canon EOS 1200D"),
    ("Canon", r"\b(?:eos\s*)?250d\b", "Canon EOS 250D"),
    ("Canon", r"\b(?:eos\s*)?700d\b", "Canon EOS 700D"),
    ("Canon", r"\b(?:eos\s*)?600d\b", "Canon EOS 600D"),
    ("Nikon", r"\bd\s*3500\b", "Nikon D3500"),
    ("Nikon", r"\bd\s*3400\b", "Nikon D3400"),
    ("Nikon", r"\bd\s*3300\b", "Nikon D3300"),
    ("Nikon", r"\bd\s*3200\b", "Nikon D3200"),
    ("Nikon", r"\bd\s*5600\b", "Nikon D5600"),
    ("Sony", r"\b(?:alpha\s*|a\s*)?6000\b", "Sony Alpha A6000"),
    ("Sony", r"\b(?:alpha\s*|a\s*)?6300\b", "Sony Alpha A6300"),
    ("Sony", r"\b(?:dsc[-\s]?)?rx100\s*(?:m[2-7]|ii|iii|iv|v|vi|vii)?\b", "Sony RX100 (versione da verificare)"),
    ("Panasonic", r"\b(?:lumix\s*)?dmc[-\s]?fz\s*1000\b", "Panasonic Lumix FZ1000"),
)
def classify_camera(title):
    t = str(title or "").casefold()
    brand = next((b for b in ("Canon","Nikon","Sony","Panasonic","Fujifilm","Olympus","Pentax","Kodak") if b.casefold() in t), "Non identificato")
    if re.search(r"\b(?:solo\s+obiettivo|obiettivo\s+solo|lens\s+only|ricambi|for\s+parts|defekt|non\s+funzionante|solo\s+corpo\s+guasto)\b", t):
        return brand, "Accessori / ricambi", "Non è una fotocamera completa", "Ricambi / accessori"
    for b,pat,model in MODELS:
        if re.search(pat,t,re.I):
            return b, "Fotocamere digitali", model, "Fotocamera (completezza da verificare)"
    return brand, "Fotocamere digitali", "Modello da identificare", "Fotocamera (modello da verificare)"

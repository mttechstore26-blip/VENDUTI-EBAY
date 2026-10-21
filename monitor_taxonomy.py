"""Brand, model and family classification for eBay Monitor category 80053."""
import re
from functools import lru_cache

@lru_cache(maxsize=50000)
def classify_monitor(title):
    t=re.sub(r"\s+"," ",str(title or "").casefold())
    if re.search(r"\brtx\s*3060\b|top performance 86cc|tpr minarelli",t):
        return ("Fuori categoria","Non è un monitor","Non applicabile","Fuori categoria")
    brands=[
        ("Apple",r"\bapple\b|\bcinema (?:hd )?display\b|\bthunderbolt display\b"),
        ("LG",r"\blg\b|\bultragear\b"),
        ("Samsung",r"\bsamsung\b|\bodyssey\b"),
        ("ASUS",r"\basus\b|\bro[g|g]\b|\btuf gaming\b|\bproart\b"),
        ("MSI",r"\bmsi\b"),
        ("AOC",r"\baoc\b|\bagon\b"),
        ("Dell",r"\bdell\b|\bultrasharp\b"),
        ("Acer",r"\bacer\b|\bpredator\b|\bnitro\b"),
        ("BenQ",r"\bbenq\b|\bmobiuz\b"),
        ("HP",r"\bhp\b|\bomen\b"),
        ("Philips",r"\bphilips\b"),
        ("Sony",r"\bsony\b"),
        ("Eizo",r"\beizo\b"),
        ("NEC",r"\bnec\b|\bmultisync\b"),
        ("Gigabyte",r"\bgigabyte\b"),
        ("Huawei",r"\bhuawei\b|\bmateview\b"),
        ("Xiaomi",r"\bxiaomi\b"),
        ("IBM",r"\bibm\b"),
        ("LaCie",r"\blacie\b"),
        ("Nokia",r"\bnokia\b"),
        ("Hannspree",r"\bhannspree\b"),
        ("Koorui",r"\bkoorui\b"),
        ("Barco",r"\bbarco\b"),
    ]
    brand=next((b for b,pat in brands if re.search(pat,t)),"Non identificato")
    if re.search(r"\b(?:crt|tubo catodico|electron22blue)\b",t):
        family="Monitor CRT / vintage"
    elif re.search(r"\b(?:medicale|grado medico|medical|radi(?:force|ology))\b",t):
        family="Monitor medicali"
    elif re.search(r"\b(?:vetrina negozio|digital signage|ultra luminoso)\b",t):
        family="Monitor commerciali / signage"
    elif re.search(r"\b(?:portatile|portable)\b",t):
        family="Monitor portatili"
    elif re.search(r"\b(?:qd[- ]?oled|woled|oled)\b",t):
        family="Monitor OLED / QD-OLED"
    elif brand=="Apple" and re.search(r"cinema|thunderbolt",t):
        family="Apple Cinema / Thunderbolt"
    elif re.search(r"\b(?:gaming|ultragear|odyssey|rog|tuf|predator|mobiuz|nitro|240hz|360hz|165hz|180hz|144hz)\b",t):
        family="Monitor gaming LCD"
    elif re.search(r"\b(?:ultrawide|ultra.?wide|21:9|3440x1440|curvo|curved)\b",t):
        family="Monitor ultrawide / curvi"
    elif re.search(r"\b(?:4k|uhd|3840x2160)\b",t):
        family="Monitor 4K / UHD"
    else:
        family="Monitor standard / professionali"
    # Model tokens are kept only when attached to identifiable manufacturers;
    # prevent bare dimensions, resolution and refresh rate from being models.
    pats=[
        r"\b(?:35WN65C|27GS75Q|32GN600|27GL850|34GN850|27GP850|32GN63T|34GP63AP|27GR93U|32UN500|29UB67|24MP88HV)[- ]?[A-Z]?\b",
        r"\b(?:A1407|A1083|M8536)\b",
        r"\b(?:C34G55TWWU|C27RG50|C32G53TQBU|U28R552UQ|U28E570|S27DG502|C24F390FHU)\b",
        r"\b(?:EX3210U|EL2870U|UP2516D|U2520D|S2721QSA|P2715Q|2007FPB)\b",
        r"\b(?:VG32VQ1BR|VG289Q1A|VG279QL1A|PG348Q|PA279CV|PB287Q|XG259QN|XG27AQ)\b",
        r"\b(?:345CQR|G27CQ4|MP271P|CQ27G4X|27M2N3201A|279P1|323E7QDAB|GO27Q24A|G34WQI|P242W|ZR30W|E27Q|E27\s*G5|HC322PPB)\b",
        r"\b(?:VG280K|UP2516D|L150|107E|447XPRO|LMD[- ]?2140MD|GS220|M32F|24FW)\b",
    ]
    models=[]
    for pat in pats:
        for x in re.findall(pat,t,re.I):
            model=re.sub(r"\s+","",x).upper()
            if model not in models:models.append(model)
    # Broad but guarded manufacturer-style codes for future arrivals.
    if not models and brand!="Non identificato":
        candidate=re.findall(r"\b(?=[a-z0-9-]{5,15}\b)(?=[a-z0-9-]*\d)[a-z]{1,5}\d{2,5}[a-z0-9-]{0,6}\b",t,re.I)
        models=[m.upper() for m in candidate if not re.search(r"(?:^HDR|^WQHD|^FHD|^UHD|^RTX|^HDMI)",m,re.I)][:1]
    model=models[0] if len(models)==1 else ("Più modelli / lotto" if len(models)>1 else "Modello non identificato")
    return brand,family,model,"Monitor / tipo da titolo"

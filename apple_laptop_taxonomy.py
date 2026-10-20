"""Conservative title-based Apple laptop taxonomy, four fields.
No inference of CPU, model year, SSD or condition where unmentioned.
"""
import re


# Intel MacBook Pro: distinguish year and screen because value changes strongly.
# A-numbers may span more than one year: never invent one from a chassis code.
INTEL_PRO_CHASSIS = {
 "a1278": ('13"', None), "a1286": ('15"', None),
 "a1297": ('17"', None), "a1398": ('15"', None),
 "a1425": ('13"', None), "a1502": ('13"', None),
 "a1706": ('13"', None), "a1708": ('13"', None),
 "a1989": ('13"', None), "a2159": ('13"', "2019"),
 "a2251": ('13"', "2020"), "a2289": ('13"', "2020"),
 "a2141": ('16"', "2019"), "a1990": ('15"', None),
 "a1707": ('15"', None), "a2442": ('14"', None),
}
def intel_pro_model(t, inches, yr):
    match = re.search(r'\b(a1\d{3}|a2\d{3}|a3\d{3})\b', t)
    chassis = match.group(1).lower() if match else ""
    mapping = INTEL_PRO_CHASSIS.get(chassis)
    if mapping:
        if inches and inches != mapping[0]:
            # Conflicting title information: show the uncertain label, not false precision.
            return "MacBook Pro Intel — dimensione da verificare (" + chassis.upper() + ")"
        inches = inches or mapping[0]
        yr = yr or mapping[1] or ""
    if not inches:
        raw = re.search(r'\b(13|15|16|17)(?:[,.][0-9])?\s*(?:inch|inches)\b|\b(?:macbook\s*pro|pro)\s*(13|15|16|17)(?=\b|\s)',t)
        if raw: inches = (raw.group(1) or raw.group(2)) + '"'
    if not yr and re.search(r'\b(?:4a|4°|fourth|4th)\s*(?:generazione|gen)\b',t):
        # Intel 4th generation alone does not establish Apple model year.
        pass
    model = "MacBook Pro Intel" + (" " + inches if inches else "")
    if yr: model += " (" + yr + ")"
    else: model += " — anno non specificato"
    if chassis and not yr:
        model += " · " + chassis.upper()
    # Mark screen-less / year-less titles honestly; retain chip and chassis in group.
    return model

def classify_apple_laptop(title):
    t = str(title or '').lower().replace('’', "'")
    has_apple = bool(re.search(r'\b(?:apple|macbook|mac book|a1\d{3}|a2\d{3}|a3\d{3})\b', t))
    if not has_apple:
        return "Altro marchio", "Fuori categoria Apple", "Non Apple / verificare", "Non Apple / verificare"
    # Older iBook models are distinct from MacBooks; use only explicit chassis codes.
    ibook = re.search(r"\bibook\s*(g3|g4)\b", t)
    if ibook:
        code = re.search(r"\b(m2453)\b", t)
        label = "Apple iBook " + ibook.group(1).upper() + (" " + code.group(1).upper() if code else "")
        condition = "⚠️ Lotto multiplo / da verificare" if re.search(r"\blotto\s*(?:di\s*)?[2-9]\d*\b", t) else "Portatile presumibilmente completo"
        return "Apple", "iBook", label, condition
    family = ("MacBook Neo" if re.search(r'\bmacbook\s*neo\b', t) else
              "MacBook Air" if re.search(r'\bmac\s*book\s*air\b|\bmacbook\s*air\b', t) else
              "MacBook Pro" if re.search(r'\bmac\s*book\s*pro\b|\bmacbook\s*pro\b', t) else
              "MacBook Retina 12" if re.search(r'\bmacbook\s*(?:retina\s*)?12\b', t) else
              "MacBook (generico)" if re.search(r'\bmac\s*book\b|\bmacbook\b', t) else
              "Apple laptop da verificare")
    if re.search(r'\b(?:m[1-5])\s*(?:max|ultra|pro)\b',t):
        m=re.search(r'\b(m[1-5])\s*(max|ultra|pro)\b',t)
        chip=m.group(1).upper()+' '+m.group(2).capitalize()
    else:
        m=re.search(r'\b(m[1-5])\b',t)
        chip=m.group(1).upper() if m else ("Intel" if re.search(r'\b(?:intel|core\s*(?:i[3579]|ultra)|i[3579](?:[-\s]?\d{3,5})?|\bi[3579]\b)\b',t) else "Chip non specificato")
    screen = re.search(r'\b(11|12|13|14|15|16|17)(?:[,.][036])?\s*(?:"|″|pollici|inch|inches|\bpol\b)',t)
    inches=screen.group(1)+'"' if screen else ""
    year = re.search(r'\b(20(?:0[6-9]|1[0-9]|2[0-6]))\b', t)
    yr=year.group(1) if year else ""
    ram = re.search(r'\b(4|8|12|16|18|24|32|36|48|64|96|128)\s*gb\s*(?:ram|unified|memoria)\b|\b(?:ram|memoria)\s*(4|8|12|16|18|24|32|36|48|64|96|128)\s*gb\b',t)
    memory=(next((g for g in ram.groups() if g),None)+'GB RAM') if ram else ""
    disk = re.search(r'\b(128|256|512)\s*gb\s*(?:ssd|storage|archiviazione)\b|\b([1248])\s*tb\s*(?:ssd|storage)\b',t)
    storage=(disk.group(1)+'GB SSD' if disk.group(1) else disk.group(2)+'TB SSD') if disk else ""
    if chip == "Chip non specificato" and yr and int(yr) < 2020:
        chip = "Intel"  # MacBook pre-Apple-Silicon model years
    # Pro models announced before the Apple Silicon transition are Intel;
    # 2020 remains ambiguous unless processor or Intel-only chassis is explicit.
    if family == "MacBook Pro" and chip == "Chip non specificato" and re.search(r'\b(?:a1706|a1707|a1708|a1989|a1990|a1398|a1502|a1425|a1286|a1297|a1278|a2141|a2159|a2251|a2289)\b',t):
        chip = "Intel"
    # Canonical commercial groups: do not split on optional year or size.
    # Keep ambiguous family/chip identities distinct rather than guessing.
    if family == "MacBook Air":
        # Distinguish Intel chassis and disclosed year without inferring an unknown year.
        air_code = re.search(r'\b(a(?:1237|1304|1369|1370|1465|1466|1932|2179|2337|2681|3113|3240))\b', t)
        if air_code and chip == "Chip non specificato" and air_code.group(1) not in ("a2337", "a2681", "a3113", "a3240"):
            chip = "Intel"
        model = "MacBook Air " + chip
        if chip == "Intel":
            if air_code:
                model += " " + air_code.group(1).upper()
            elif yr:
                model += " (" + yr + ")"
            elif inches:
                model += " " + inches + " — anno non specificato"
        elif inches == '15"' and chip in ("M2", "M3", "M4", "M5"):
            model += ' 15"'
    elif family == "MacBook Pro" and chip == "Intel":
        model = intel_pro_model(t, inches, yr)
    elif family == "MacBook Pro":
        model = "MacBook Pro " + chip
        if inches in ('14"', '16"'):
            model += " " + inches
        elif chip in ("M1", "M2") and inches == '13"':
            model += ' 13"'
    elif family == "MacBook Neo":
        model = "MacBook Neo"
    elif family == "MacBook Retina 12":
        model = "MacBook Retina 12"
    elif family == "MacBook (generico)":
        model = "MacBook non specificato · " + chip
    else:
        model = "Apple laptop da verificare · " + chip
    danger=r'\b(?:icloud\s*(?:lock|blocc)|activation\s*lock|blocco\s*attivazione|mdm|remote\s*management|gestione\s*remota|per\s*ricambi|for\s*parts|non\s*funzionante|non\s*si\s*accende|schermo\s*rotto|display\s*rotto|senza\s*audio|broken|faulty|guasto|scheda\s*madre|logic\s*board|solo\s*scatola|box\s*only)\b'
    if re.search(danger,t): status="⚠️ Blocco / guasto / ricambio: verificare"
    elif re.search(r'\b(?:da\s*testare|leggere\s*descrizione|difetto|problema|battery\s*service|batteria\s*da\s*sostituire)\b',t): status="⚠️ Condizioni da verificare"
    else: status="Portatile presumibilmente completo"
    if re.search(r"\b(?:lotto\s*(?:di\s*)?[2-9]\d*\s*(?:macbook|notebook|laptop|pc)|lot\s+of\s+[2-9]\d*\s*(?:macbooks|laptops))\b", t):
        status="⚠️ Lotto multiplo / non confrontabile con singolo portatile"
    return "Apple",family,model,status

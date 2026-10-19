"""Conservative title-based Apple laptop taxonomy, four fields.
No inference of CPU, model year, SSD or condition where unmentioned.
"""
import re

def classify_apple_laptop(title):
    t = str(title or '').lower().replace('’', "'")
    has_apple = bool(re.search(r'\b(?:apple|macbook|mac book|a1\d{3}|a2\d{3}|a3\d{3})\b', t))
    if not has_apple:
        return "Altro marchio", "Fuori categoria Apple", "Non Apple / verificare", "Non Apple / verificare"
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
        chip=m.group(1).upper() if m else ("Intel" if re.search(r'\b(?:intel|core\s*(?:i[3579]|ultra)|i[3579][-\s]?\d{3,5})\b',t) else "Chip non specificato")
    screen = re.search(r'\b(11|12|13|14|15|16|17)(?:[,.][036])?\s*(?:"|″|pollici|inch|inches|\bpol\b)',t)
    inches=screen.group(1)+'"' if screen else ""
    year = re.search(r'\b(20(?:0[6-9]|1[0-9]|2[0-6]))\b', t)
    yr=year.group(1) if year else ""
    ram = re.search(r'\b(4|8|12|16|18|24|32|36|48|64|96|128)\s*gb\s*(?:ram|unified|memoria)\b|\b(?:ram|memoria)\s*(4|8|12|16|18|24|32|36|48|64|96|128)\s*gb\b',t)
    memory=(next((g for g in ram.groups() if g),None)+'GB RAM') if ram else ""
    disk = re.search(r'\b(128|256|512)\s*gb\s*(?:ssd|storage|archiviazione)\b|\b([1248])\s*tb\s*(?:ssd|storage)\b',t)
    storage=(disk.group(1)+'GB SSD' if disk.group(1) else disk.group(2)+'TB SSD') if disk else ""
    # Canonical commercial groups: do not split on optional year or size.
    # Keep ambiguous family/chip identities distinct rather than guessing.
    if family == "MacBook Air":
        model = "MacBook Air " + chip
        if inches == '15"' and chip in ("M2", "M3", "M4", "M5"):
            model += ' 15"'
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
    return "Apple",family,model,status

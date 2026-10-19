"""Model-level grouping for used video game consoles."""
import re
def classify_console(title):
    t=str(title or "").lower()
    if re.search(r"\b(?:solo\s+scatola|empty box|box only|controller only|solo controller|senza console|for parts|per ricambi|non funzionante|guasta|broken)\b",t):
        state="Accessori / ricambi o da verificare"
    elif re.search(r"\b(?:lotto|bundle|con giochi|2 console|due console)\b",t):
        state="Bundle / da verificare"
    else:
        state="Console presumibilmente completa"
    patterns=[
        ("Sony","PlayStation 5 Pro",r"\bps5\s*pro\b|playstation\s*5\s*pro\b|\bcfi[- ]?70\d\d\b"),
        ("Sony","PlayStation 5 Slim Digital",r"(?:ps5|playstation\s*5).*slim.*digital|(?:ps5|playstation\s*5).*digital.*slim"),
        ("Sony","PlayStation 5 Slim",r"(?:ps5|playstation\s*5).*slim|\bcfi[- ]?20\d\d\b"),
        ("Sony","PlayStation 5 Digital",r"(?:ps5|playstation\s*5).*digital"),
        ("Sony","PlayStation 5 Standard",r"\bps5\b|playstation\s*5\b"),
        ("Sony","PlayStation 4 Pro",r"\bps4\s*pro\b|playstation\s*4\s*pro"),
        ("Sony","PlayStation 4 Slim",r"\bps4\s*slim\b|playstation\s*4\s*slim"),
        ("Sony","PlayStation 4",r"\bps4\b|playstation\s*4"),
        ("Microsoft","Xbox Series X",r"\bxbox\s*(?:series\s*)?x\b"),
        ("Microsoft","Xbox Series S",r"\bxbox\s*(?:series\s*)?s\b"),
        ("Microsoft","Xbox One X",r"\bxbox\s*one\s*x\b"),
        ("Nintendo","Switch 2",r"\bswitch\s*2\b"),
        ("Nintendo","Switch OLED",r"\bswitch\s*oled\b|\boled\s*switch\b"),
        ("Nintendo","Switch Lite",r"\bswitch\s*lite\b"),
        ("Nintendo","Switch",r"\bnintendo\s*switch\b|\bswitch\b"),
        ("Valve","Steam Deck OLED",r"\bsteam\s*deck\b.*\boled\b"),
        ("Valve","Steam Deck LCD",r"\bsteam\s*deck\b"),
        ("ASUS","ROG Ally X",r"\brog\s*ally\s*x\b"),
        ("ASUS","ROG Ally",r"\brog\s*ally\b"),
        ("Lenovo","Legion Go",r"\blegion\s*go\b"),
        ("Sony","PlayStation Portal",r"\bplaystation\s*portal\b|\bps\s*portal\b"),
    ]
    for brand,model,pat in patterns:
        if re.search(pat,t):
            return brand,"Console",model,state
    return "Non identificato","Console","Modello non identificato",state

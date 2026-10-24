"""Recognize actual coffee machines and non-machine components from eBay 38250."""
import re
from functools import lru_cache

@lru_cache(maxsize=100000)
def classify_coffee(title):
    s = re.sub(r"\s+", " ",str(title or "")).strip()
    t = s.casefold()
    brand_rules=[
      ("Sage",r"\bsage\b"),("Breville",r"\bbreville\b"),("De'Longhi",r"de.?longhi|delonghi"),
      ("Gaggia",r"gaggia"),("Saeco",r"saeco"),("Siemens",r"siemens"),
      ("Jura",r"\bjura\b"),("Miele",r"\bmiele\b"),("Faber",r"\bfaber\b"),
      ("KitchenAid",r"kitchen\s?aid"),("Nespresso",r"nespresso"),
      ("Philips",r"philips"),("Krups",r"\bkrups\b"),("SMEG",r"\bsmeg\b"),
      ("Lavazza",r"lavazza"),("Magimix",r"magimix"),("Ninja",r"\bninja\b"),
      ("Beko",r"\bbeko\b"),("Lelit",r"\blelit\b"),("Baratza",r"baratza"),
      ("Flair",r"\bflair\b"),("La Pavoni",r"la pavoni"),("Giannini",r"giannini"),
      ("Fellow",r"fellow"),("Franke",r"franke"),("Tchibo",r"tchibo"),
      ("HiBREW",r"hibrew"),("Grimac",r"grimac"),("Cecotec",r"cecotec"),
      ("Dualit",r"dualit"),("Bravilor Bonamat",r"bravilor"),("ROK",r"\brok\b"),
      ("Grundig",r"grundig"),("Amzchef",r"amzchef"),("DF54",r"\bdf54\b"),
    ]
    brand=next((name for name,pat in brand_rules if re.search(pat,t)), "Non identificato")
    if re.search(r"\b(?:scheda\s+(?:di\s+)?(?:controllo|alimentazione|potenza|elettronica)|control\s+board|power\s+print|pcb|gruppo\s+.*e61|beccuccio\s+automatico|pannello\s+kit|tamper\s+58mm|unit[aà]\s+di\s+infusione|alimentatore\s+scheda)\b",t):
        status="Ricambio / componente"
    elif re.search(r"\b(?:solo\s+unit[aà]\s+base|senza\s+(?:boccale|serbatoio|accessori)|non\s+funzionante|per\s+pezzi)\b",t):
        status="Incompleto / da verificare"
    elif re.search(r"\b(?:macinacaff[eè]|coffee grinder|grinder)\b",t) and not re.search(r"macchina\s+da\s+caff|macchina\s+caff|automatic|espresso",t):
        status="Accessorio / macinacaffè"
    else:
        status="Apparecchio presumibilmente completo"
    rules=[
       ("Sage / Breville Bambino Plus",r"\b(?:bambino plus|ses500[a-z0-9]*)\b"),
       ("Sage / Breville Barista Express",r"\bbarista express\b|\bbes870\w*\b"),
       ("De'Longhi Magnifica S",r"magnifica\s+s\b|\becam\s*20[.\s-]?116\b"),
       ("De'Longhi Magnifica Start",r"magnifica start"),
       ("De'Longhi Magnifica Evo",r"magnifica evo|\becam\s*290[.\s-]?21\b"),
       ("De'Longhi Dedica Arte EC885",r"dedica arte|\bec885\b"),
       ("Sage / Nespresso Creatista Plus",r"creatista plus|\bbne800"),
       ("Sage / Nespresso Vertuo Creatista",r"vertuo creatista|\bsve850"),
       ("Sage Precision Brewer",r"precision brewer|\bsdc400|\bsdc465"),
       ("Gaggia Classic",r"\bgaggia classic\b"),
       ("Gaggia Carezza Deluxe",r"carezza deluxe"),
       ("Saeco Xelsis SM7580",r"xelsis.*sm7580"),
       ("Saeco Incanto Deluxe",r"incanto de luxe"),
       ("Siemens EQ.9 Plus",r"eq[.\s-]*9\b"),
       ("Siemens EQ.6 Plus",r"eq[.\s-]*6\b"),
       ("Siemens EQ.500",r"eq[.\s-]*500\b"),
       ("Jura ENA 8",r"\bena\s*8\b"),
       ("Jura E8",r"\bjura\b.*\be8\b"),
       ("KitchenAid Artisan Nespresso 5KES0503",r"\b5kes0503\w*\b|\bkitchenaid\b.*\b(?:artisan|nespresso)\b"),
       ("Nespresso CitiZ & Milk",r"citiz\s*(?:&|and|\+)\s*milk|citiz.*\bmilk\b|\b(?:m196|c123)\b"),
       ("Nespresso CitiZ",r"\bcitiz\b|\b(?:m190|c111)\b"),
       ("Nespresso Lattissima One",r"\blattissima\s*one\b"),
       ("Nespresso Essenza Mini",r"\bessenza\s*mini\b"),
       ("Nespresso Pixie",r"\bpixie\b|\bd60\b"),
       ("Nespresso Zenius",r"\bzenius\b|\b9737n\b"),
       ("Nespresso Gemini CS100",r"\bgemini\s*cs\s*100\b"),
       ("Nespresso D300",r"\bd300\b"),
       ("Nespresso C190",r"\bc190\b"),
       ("Faber Pro Deluxe",r"faber.*pro deluxe"),
       ("Faber Pro Total",r"faber.*pro total"),
       ("Faber Slot",r"faber.*slot"),
       ("Ninja Luxe Café ES601",r"\bes601"),
       ("Ninja Luxe Café ES701",r"\bes701"),
       ("Philips Series 2200",r"philips.*(?:serie 2200|ep2224)"),
       ("Miele CM6310",r"cm\s*6310"),
       ("Miele CM7300",r"cm\s*7300"),
       ("SMEG CGF03",r"\bcgf03"),
       ("Lavazza EP2100",r"\bep\s*2100"),
       ("La Pavoni Europiccola",r"europiccola"),
       ("Fellow Aiden",r"fellow.*aiden"),
       ("HiBREW H10A",r"hibrew.*h10a"),
    ]
    model=next((m for m,p in rules if re.search(p,t)), None)
    if model is None:
        code=re.search(r"\b(?:ECAM|ESAM|EP|SES|BES|SNE|BNE|SVE|SM|CM|EC|SCG|PL|TQ|TE|CEG|KVA|MD|SDC|CGF|DF|ZN|EDG|B[VT]MC)[\s.-]*\d{2,5}[A-Z0-9.-]*\b",s,re.I)
        model=f"{brand} {code.group(0).upper()}" if code else f"{brand} — modello non specificato"
    family=("Ricambi / accessori" if status!="Apparecchio presumibilmente completo"
            else "Macinacaffè" if re.search(r"macinacaff|grinder",t) and not re.search(r"macchina.*caff|espresso",t)
            else "Macchine da caffè")
    return brand,family,model,status

"""Title-based taxonomy for used laptops: brand, family, canonical model, condition."""
import re

BRANDS=[
 ("Apple",r"\b(?:apple|mac\s*book|macbook)\b"),
 ("Lenovo",r"\b(?:lenovo|thinkpad|thinkbook|ideapad)\b"),
 ("HP",r"\b(?:hp|hewlett[\s-]*packard|elitebook|probook|zbook)\b"),
 ("Dell",r"\b(?:dell|latitude|inspiron)\b"),
 ("ASUS",r"\b(?:asus|vivobook|zenbook|expertbook|rog)\b"),
 ("Acer",r"\b(?:acer|aspire|travelmate|extensa)\b"),
 ("Microsoft",r"\b(?:microsoft|surface)\b"),
 ("Huawei",r"\b(?:huawei|matebook)\b"),
 ("Samsung",r"\b(?:samsung|galaxy\s*book)\b"),
 ("Fujitsu",r"\b(?:fujitsu|lifebook)\b"),
 ("Toshiba/Dynabook",r"\b(?:toshiba|dynabook|satellite|portege|port[eé]g[eé])\b"),
 ("MSI",r"\bmsi\b"),
 ("LG",r"\blg\s*gram\b"),("Chuwi",r"\bchuwi\b"),
 ("Sony",r"\b(?:sony|vaio)\b"),("Razer",r"\brazer\b"),
 ("Medion",r"\bmedion\b"),("Honor",r"\bhonor\b"),
 ("Panasonic",r"\b(?:panasonic|toughbook)\b")
]
FAMILIES={
 "Lenovo":["ThinkPad","ThinkBook","IdeaPad","Yoga","Legion","LOQ"],
 "HP":["EliteBook","ProBook","ZBook","Pavilion","Envy","Spectre","Omen","Victus","250","255","15","14","17"],
 "Dell":["Latitude","Inspiron","Precision","Vostro","XPS","G3","G5","G7"],
 "ASUS":["VivoBook","ZenBook","ExpertBook","ROG","TUF","Eee PC"],
 "Acer":["Aspire","TravelMate","Swift","Extensa","Nitro","Predator","Spin"],
 "Microsoft":["Surface Laptop Go","Surface Laptop","Surface Pro","Surface Go","Surface Book"],
 "Huawei":["MateBook D","MateBook X","MateBook"],
 "Samsung":["Galaxy Book","Notebook"],
 "Fujitsu":["Lifebook"],
 "Toshiba/Dynabook":["Portege","Satellite","Tecra"],
 "MSI":["Modern","Prestige","Katana","GF","GP","GE"],
 "Chuwi":["UBook","HeroBook","CoreBook"],
 "Sony":["VAIO"]
}
# Families whose numeric identifiers do not need the family name repeated.
NUMERIC={"HP":["250","255","14","15","17"],"Dell":["G3","G5","G7"]}
def classify_laptop(title):
 t=re.sub(r"[\u2010-\u2015_]+"," ",str(title or "").casefold())
 t=re.sub(r"\s+"," ",t)
 brand=next((b for b,p in BRANDS if re.search(p,t,re.I)),"Marchio non identificato")
 family="Portatile non identificato"
 model="Modello da identificare"
 if brand=="Apple":
  from apple_laptop_taxonomy import classify_apple_laptop
  b,f,m,status=classify_apple_laptop(title)
  return b,f,m,status
 for candidate in FAMILIES.get(brand,[]):
  if re.search(r"(?<!\w)"+re.escape(candidate).replace(r"\ ",r"\s*")+r"(?!\w)",t,re.I):
   family=candidate
   break
 if family=="Portatile non identificato" and brand!="Marchio non identificato":
  family=brand+" serie non identificata"
 if brand=="Lenovo":
  # T490s, L590, X1 Carbon, E14, T14 Gen 1; generic IdeaPad 3-15IML05.
  m=re.search(r"\b(?:thinkpad\s*)?(t\d{3,4}s?|x\d{3,4}s?|l\d{2,4}|e\d{2,4}|p\d{2,4}|x1\s*carbon|x1\s*yoga)\b",t)
  if m:
   family="ThinkPad"
   model="Lenovo ThinkPad "+m.group(1).upper().replace(" "," ")
   g=re.search(r"\bgen\s*([1-9])\b",t)
   if g and re.search(r"\b(?:[elpt]\d{2}|x1)\b",m.group(1)):model+=" Gen "+g.group(1)
  else:
   m=re.search(r"\b(?:thinkbook|ideapad|yoga|legion|loq)\s*([0-9a-z-]+(?:\s*gen\s*\d+)?)",t)
   if m: model="Lenovo "+family+" "+m.group(1).upper()
   else:
    m=re.search(r"\b(?:thinkpad\s*)?(x1\s*carbon)\b",t)
    if m: model="Lenovo ThinkPad X1 Carbon"
 elif brand=="HP":
  m=re.search(r"\b(elitebook|probook|zbook)\s*(?:folio\s*)?(\d{3,4})\s*(g\d{1,2})?\b",t)
  if m:
   family=m.group(1).title().replace("Elitebook","EliteBook").replace("Probook","ProBook").replace("Zbook","ZBook")
   model="HP "+family+" "+m.group(2)+(" "+m.group(3).upper() if m.group(3) else "")
  else:
   m=re.search(r"\b(250|255)\s*[- ]?\s*(g\d{1,2})\b",t)
   if m:family="HP "+m.group(1);model=family+" "+m.group(2).upper()
 elif brand=="Dell":
  m=re.search(r"\b(latitude|inspiron|vostro|precision|xps)\s*(?:e\s*)?(\d{3,5})(?:\s*(?:2\s*in\s*1))?",t)
  if m:family=m.group(1).title();model="Dell "+family+" "+m.group(2)
  else:
   m=re.search(r"\b(g[357])\s*(?:15\s*)?(\d{4})\b",t)
   if m:family="Dell "+m.group(1).upper();model=family+" "+m.group(2)
 elif brand=="Acer":
  m=re.search(r"\b(aspire|swift|travelmate|extensa|nitro|spin|predator)\s*([a-z]?\d{1,4}(?:[- ]\d{1,4}[a-z]*)?)\b",t)
  if m:family=m.group(1).title();model="Acer "+family+" "+m.group(2).upper().replace(" ","-")
 elif brand=="ASUS":
  m=re.search(r"\b(?:asus\s*)?(vivobook|zenbook|expertbook|tuf|rog)\s*([a-z]?\d{1,4}[a-z-]*)\b",t)
  if m: family=m.group(1).title();model="ASUS "+family+" "+m.group(2).upper()
  else:
   m=re.search(r"\b([a-z]{1,3}\d{3,4}[a-z]{0,3})\b",t)
   if m:model="ASUS "+m.group(1).upper()
 elif brand=="Microsoft":
  m=re.search(r"\bsurface\s*(laptop\s*go|laptop|pro|go|book)\s*(\d{1,2})?\b",t)
  if m:
   family="Surface "+m.group(1).title()
   model="Microsoft "+family+(" "+m.group(2) if m.group(2) else "")
 elif brand=="Huawei":
  m=re.search(r"\bmatebook\s*(d|x)?\s*(\d{2})?\b",t)
  if m:family="MateBook"+(" "+m.group(1).upper() if m.group(1) else "");model="Huawei "+family+(" "+m.group(2) if m.group(2) else "")
 elif brand=="Fujitsu":
  m=re.search(r"\blifebook\s*([a-z]\d{3,4})\b",t)
  if m:model="Fujitsu Lifebook "+m.group(1).upper()
 if model=="Modello da identificare" and brand!="Marchio non identificato":model=brand+" — modello da identificare"
 if re.search(r"\b(?:icloud\s*(?:lock|blocc)|mdm|remote\s*management|gestione\s*remota|bloccato|per\s*ricambi|for\s*parts|non\s*funzionante|non\s*si\s*accende|guast[oa]|rotto|broken|senza\s*audio|no\s*audio|solo\s*scatola|box\s*only)\b",t):
  status="⚠️ Bloccato / guasto / ricambi"
 elif re.search(r"\b(?:da\s*testare|leggi\s*descrizione|leggere\s*descrizione|difett[oi]|batteria\s*ko|battery\s*service|batteria\s*esausta|schermo\s*macchiato)\b",t):
  status="⚠️ Difetto / condizioni da verificare"
 else:status="Portatile presumibilmente completo"
 return brand,family,model,status

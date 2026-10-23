"""Render verified item-location country beside listing titles.
Never infer seller nationality from ebaySite, currency or username.
"""
import re

COUNTRIES = [
 ("🇮🇹","Italia",r"\b(?:italia|italy|italien|italie|italië)\b"),
 ("🇺🇸","Stati Uniti",r"\b(?:stati uniti|united states|usa|u\.s\.a\.|états-unis|vereinigte staaten)\b"),
 ("🇬🇧","Regno Unito",r"\b(?:united kingdom|regno unito|great britain|großbritannien|uk|england|scotland|wales)\b"),
 ("🇩🇪","Germania",r"\b(?:germany|germania|deutschland|allemagne)\b"),
 ("🇫🇷","Francia",r"\b(?:france|francia|frankreich)\b"),
 ("🇪🇸","Spagna",r"\b(?:spain|spagna|españa|espagne|spanien)\b"),
 ("🇳🇱","Paesi Bassi",r"\b(?:netherlands|paesi bassi|nederland|niederlande|olanda)\b"),
 ("🇧🇪","Belgio",r"\b(?:belgium|belgio|belgique|belgië|belgien)\b"),
 ("🇨🇭","Svizzera",r"\b(?:switzerland|svizzera|schweiz|suisse)\b"),
 ("🇦🇹","Austria",r"\b(?:austria|österreich)\b"),
 ("🇵🇱","Polonia",r"\b(?:poland|polonia|polska)\b"),
 ("🇨🇿","Repubblica Ceca",r"\b(?:czechia|czech republic|repubblica ceca|tschechien)\b"),
 ("🇵🇹","Portogallo",r"\b(?:portugal|portogallo)\b"),
 ("🇮🇪","Irlanda",r"\b(?:ireland|irlanda)\b"),
 ("🇸🇪","Svezia",r"\b(?:sweden|svezia|schweden)\b"),
 ("🇩🇰","Danimarca",r"\b(?:denmark|danimarca|dänemark)\b"),
 ("🇬🇷","Grecia",r"\b(?:grecia|greece|hellas|ellada|griechenland|grèce)\b"),
 ("🇧🇬","Bulgaria",r"\b(?:bulgaria|bulgarie)\b"),
 ("🇭🇷","Croazia",r"\b(?:croatia|croazia|hrvatska|kroatien)\b"),
 ("🇨🇾","Cipro",r"\b(?:cyprus|cipro|kypros|zypern)\b"),
 ("🇪🇪","Estonia",r"\b(?:estonia|estland|eesti)\b"),
 ("🇭🇺","Ungheria",r"\b(?:hungary|ungheria|magyarorszag|ungarn)\b"),
 ("🇱🇻","Lettonia",r"\b(?:latvia|lettonia|latvija|lettland)\b"),
 ("🇱🇹","Lituania",r"\b(?:lithuania|lituania|lietuva|litauen)\b"),
 ("🇱🇺","Lussemburgo",r"\b(?:luxembourg|lussemburgo|luxemburg)\b"),
 ("🇲🇹","Malta",r"\bmalta\b"),
 ("🇷🇴","Romania",r"\b(?:romania|roumanie|rumania|rumänien)\b"),
 ("🇸🇰","Slovacchia",r"\b(?:slovakia|slovacchia|slovensko|slowakei)\b"),
 ("🇸🇮","Slovenia",r"\b(?:slovenia|slovenija|slowenien)\b"),
 ("🇳🇴","Norvegia",r"\b(?:norway|norvegia|norwegen)\b"),
 ("🇫🇮","Finlandia",r"\b(?:finland|finlandia)\b"),
 ("🇨🇦","Canada",r"\b(?:canada|canadà)\b"),
 ("🇯🇵","Giappone",r"\b(?:japan|giappone|japon)\b"),
 ("🇨🇳","Cina",r"\b(?:china|cina|chine)\b"),
 ("🇦🇺","Australia",r"\b(?:australia)\b"),
]
def flag_for_location(location):
    if location is None or str(location).strip().lower() in ("","none","nan","null"):
        return "🏳️","Località non disponibile"
    location=str(location)
    for flag,country,pattern in COUNTRIES:
        if re.search(pattern,location,re.I):
            return flag, f"{country} · {location}"
    return "🏳️", f"Paese non identificato · {location}"

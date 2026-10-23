"""Strict item-location filter for the 27 EU member states.

Only an explicit country in SoldComps itemLocation qualifies. Missing or
ambiguous locations are excluded rather than guessed from ebaySite/currency.
"""
import re
import unicodedata

EU_COUNTRIES = {
    "austria", "osterreich", "belgium", "belgio", "belgique", "belgie",
    "bulgaria", "croatia", "croazia", "hrvatska", "cyprus", "cipro", "kypros",
    "czechia", "czech republic", "repubblica ceca", "tschechien", "cesko",
    "denmark", "danimarca", "danmark", "estonia", "estonia",
    "finland", "finlandia", "suomi", "france", "francia", "frankreich",
    "germany", "germania", "deutschland", "greece", "grecia", "hellas",
    "hungary", "ungheria", "magyarorszag", "ireland", "irlanda", "eire",
    "italy", "italia", "italien", "italie", "latvia", "lettonia", "latvija",
    "lithuania", "lituania", "lietuva", "luxembourg", "lussemburgo",
    "malta", "netherlands", "paesi bassi", "nederland", "niederlande", "olanda",
    "poland", "polonia", "polska", "portugal", "portogallo",
    "romania", "roumanie", "rumania", "slovakia", "slovacchia", "slovensko",
    "slovenia", "slovenija", "spain", "spagna", "espana", "espagne", "spanien",
    "sweden", "svezia", "sverige", "schweden",
}
NON_EU = {
    "united kingdom", "regno unito", "great britain", "england", "scotland",
    "wales", "northern ireland", "switzerland", "svizzera", "schweiz",
    "suisse", "norway", "norvegia", "norge", "norwegen", "united states",
    "stati uniti", "usa", "canada", "china", "cina", "japan", "giappone",
    "australia", "turkey", "turkiye", "turchia", "ukraine", "ucraina",
    "serbia", "albania", "iceland", "islanda",
}

def _normalize(location):
    value = unicodedata.normalize("NFKD", str(location or "").casefold())
    value = "".join(c for c in value if not unicodedata.combining(c))
    return re.sub(r"[^a-z]+", " ", value).strip()

def is_eu_location(location):
    value = _normalize(location)
    if not value:
        return False
    # A country must be identified, never infer from a town/city.
    # If contradictory country names appear, fail closed.
    matches = lambda words: any(re.search(r"(?<![a-z])" + re.escape(word) + r"(?![a-z])", value) for word in words)
    return matches(EU_COUNTRIES) and not matches(NON_EU)

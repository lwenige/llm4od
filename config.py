from rdflib import Namespace

from services.resources import load_license_map

THEME = Namespace("http://publications.europa.eu/resource/authority/data-theme/")
AVA = Namespace("http://publications.europa.eu/resource/authority/planned-availability/")

city_map = {
    "Aachen": "https://www.aachen.de",
    "Augsburg": "https://www.augsburg.de",
    "Berlin": "https://www.berlin.de",
    "Bielefeld": "https://www.bielefeld.de",
    "Bochum": "https://www.bochum.de",
    "Bonn": "https://www.bonn.de",
    "Braunschweig": "https://www.braunschweig.de",
    "Bremen": "https://www.bremen.de",
    "Chemnitz": "https://www.chemnitz.de",
    "Dortmund": "https://www.dortmund.de",
    "Dresden": "https://www.dresden.de",
    "Duisburg": "https://www.duisburg.de",
    "Düsseldorf": "https://www.duesseldorf.de",
    "Erfurt": "https://www.erfurt.de",
    "Essen": "https://www.essen.de",
    "Frankfurt am Main": "https://frankfurt.de",
    "Freiburg im Breisgau": "https://www.freiburg.de",
    "Gelsenkirchen": "https://www.gelsenkirchen.de",
    "Halle (Saale)": "https://halle.de",
    "Hamburg": "https://www.hamburg.de",
    "Hannover": "https://www.hannover.de",
    "Karlsruhe": "https://www.karlsruhe.de",
    "Kassel": "https://www.kassel.de",
    "Kiel": "https://www.kiel.de",
    "Köln": "https://www.stadt-koeln.de",
    "Krefeld": "https://www.krefeld.de",
    "Leipzig": "https://www.leipzig.de",
    "Lübeck": "https://www.luebeck.de",
    "Magdeburg": "https://www.magdeburg.de",
    "Mainz": "https://www.mainz.de",
    "Mannheim": "https://www.mannheim.de",
    "Mönchengladbach": "https://www.moenchengladbach.de",
    "München": "https://www.muenchen.de",
    "Münster": "https://www.muenster.de",
    "Nürnberg": "https://www.nuernberg.de",
    "Oberhausen": "https://www.oberhausen.de",
    "Rostock": "https://www.rostock.de",
    "Stuttgart": "https://www.stuttgart.de",
    "Wiesbaden": "https://www.wiesbaden.de",
    "Wuppertal": "https://www.wuppertal.de"
}

theme_map = {
    "Bildung, Kultur und Sport": THEME.EDUC,
    "Bevölkerung und Gesellschaft": THEME.SOCI,
    "Wissenschaft und Technologie": THEME.TECH,
    "Verkehr": THEME.TRAN,
    "Justiz, Rechtssystem und öffentliche Sicherheit": THEME.JUST,
    "Landwirtschaft, Fischerei, Forstwirtschaft und Nahrungsmittel": THEME.AGRI,
    "Wirtschaft und Finanzen": THEME.ECON,
    "Umwelt": THEME.ENVI,
    "Energie": THEME.ENER,
    "Regionen und Städte": THEME.REGI,
    "Gesundheit": THEME.HEAL,
    "Internationale Angelegenheiten": THEME.INTR,
    "Regierung und öffentlicher Sektor": THEME.GOVE,
}

availability_map = {
    "temporär": AVA.temporary,
    "experimentell": AVA.experimental,
    "verfügbar": AVA.available,
    "stabil": AVA.stable,
}

llm_map = {
    "Mistral Small 3.2": "mistralai/mistral-small-3.2-24b-instruct",
    "Llama 3.1 Instruct": "meta-llama/llama-3.1-70b-instruct",
    "GPT-5": "openai/gpt-5",
    "GPT-5-mini": "openai/gpt-5-mini",
}

license_map = load_license_map()
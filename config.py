from rdflib import Namespace

THEME = Namespace("http://publications.europa.eu/resource/authority/data-theme/")
AVA = Namespace("https://www.dcat-ap.de/def/plannedAvailability/1_0#")

city_map = {
    "Halle (Saale)": "https://www.halle.de",
    "Magdeburg": "https://www.magdeburg.de",
    "Dessau": "https://www.dessau.de",
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
import streamlit as st
from streamlit_searchbox import st_searchbox
from rdflib import Namespace
from streamlit_tags import st_tags
from rdflib import Graph, SKOS, RDF
from tantivy import Index, SchemaBuilder
from models.dataset import Dataset
from services.metadata_prompt import build_metadata_prompt
from services.openrouter_client import generate_metadata_with_openrouter
from services.dataloader import load_csv
from services.csvw import CSVW_DATATYPES, infer_csvw_datatype, create_csvw_metadata, csvw_to_json
from services.zip import create_export_zip
from services.validate import step2_incomplete, step3_incomplete

st.set_page_config(layout="wide")
# ----------------------------
# Session State
# ----------------------------
if "step" not in st.session_state:
    st.session_state.step = 1

if "df" not in st.session_state:
    st.session_state.df = None

if "datatype_map" not in st.session_state:
    st.session_state.datatype_map = {}

if "metadata" not in st.session_state:
    st.session_state.metadata = {}

# Session-State initialisieren
if "title" not in st.session_state:
    st.session_state["title"] = ""

if "keywords" not in st.session_state:
    st.session_state["keywords"] = []

if "selected_themes" not in st.session_state:
    st.session_state["selected_themes"] = []

if "places" not in st.session_state:
    st.session_state["places"] = [None]

if "place_keys" not in st.session_state:
    st.session_state["place_keys"] = [None]

if "selected_district_key" not in st.session_state:
    st.session_state["selected_district_key"] = None

if "district_lookup" not in st.session_state:
    st.session_state["district_lookup"] = {}

#if "csvw_datatypes" not in st.session_state:
#    st.session_state["csvw_datatypes"] = {}

if "csvw_metadata" not in st.session_state:
    st.session_state["csvw_metadata"] = None

if "csvw_columns" not in st.session_state:
    st.session_state["csvw_columns"] = {}

if "time_from" not in st.session_state:
    st.session_state["time_from"] = None

if "time_till" not in st.session_state:
    st.session_state["time_till"] = None

THEME = Namespace("http://publications.europa.eu/resource/authority/data-theme/")
AVA = Namespace("https://www.dcat-ap.de/def/plannedAvailability/1_0#")

city_map = {
    "Halle (Saale)": "https://www.halle.de",
    "Magdeburg": "https://www.magdeburg.de",
    "Dessau": "https://www.dessau.de"
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
    "stabil": AVA.stable
}

llm_map = {
    "Mistral Small 3.2": "mistralai/mistral-small-3.2-24b-instruct",
    "Llama 3.1 Instruct": "meta-llama/llama-3.1-70b-instruct",
    "GPT-5": "openai/gpt-5",
    "GPT-5-mini": "openai/gpt-5-mini"
}

if "publisher" not in st.session_state:
    st.session_state["publisher"] = None

if "availability" not in st.session_state:
    st.session_state["availability"] = None

if "theme" not in st.session_state:
    st.session_state["theme"] = None

if "license" not in st.session_state:
    st.session_state["license"] = None

g = Graph()
g.parse("rdf/licenses.rdf")  # Pfad zur Datei

license_map = {}

for s in g.subjects(RDF.type, SKOS.Concept):
    label = g.value(subject=s, predicate=SKOS.prefLabel)
    if label:
        license_map[str(label)] = str(s)

if "license" not in st.session_state:
    st.session_state["license"] = list(license_map.keys())[0]

with open("system_messages/text_prompt.txt", "r", encoding="utf-8") as editor_f:
    editor_prompt = editor_f.read()

with open("system_messages/metadata_prompt.txt", "r", encoding="utf-8") as metadata_f:
    metadata_prompt = metadata_f.read()

# Den Index testen
schema_builder = SchemaBuilder()
schema_builder.add_text_field("district_name", stored=True, tokenizer_name='default')

# Integer-Felder
schema_builder.add_integer_field("district_id", stored=True, indexed=True)
schema_builder.add_integer_field("district_key", stored=True, fast=True)

# Schema finalisieren
schema = schema_builder.build()
index_path = "districts"
index = Index(schema, path=str(index_path))


def load_places_from_rdf(query: str) -> list:
    results = []
    place_lookup = {}

    searcher = index.searcher()
    q = index.parse_query(query, ["district_name"])
    hits = searcher.search(q, 10).hits
    for score, addr in hits:
        hit = searcher.doc(addr)
        place_name = hit["district_name"][0]
        place_key = hit["district_key"][0]

        results.append(place_name)
        place_lookup[place_name] = place_key

    st.session_state["district_lookup"].update(place_lookup)

    return results

# ----------------------------
# Helper
# ----------------------------
def set_step(step):
    st.session_state.step = step

def step1_complete():
    return st.session_state.df is not None

def generate_description():

    dataset = Dataset({
        "title": st.session_state["title"],
        "publisher": city_map[st.session_state["publisher"]],
    })

    for place_key in st.session_state["place_keys"]:
        if place_key is not None:
            dataset.add_place(place_key)

    st.session_state["dataset"] = dataset

    sample_data = st.session_state.df.head(10).to_markdown(index=False)

    final_prompt = build_metadata_prompt(
        editable_prompt=st.session_state["prompt_template"],
        title=st.session_state["title"],
        publisher=st.session_state["publisher"],
        sample_data=sample_data,
    )

    result = generate_metadata_with_openrouter(
        prompt=final_prompt,
        model=llm_map[st.session_state["selected_llm"]],
        api_key=st.secrets["OPENROUTER_API_KEY"],
        temperature=st.session_state["temperature"],
    )

    st.session_state["generated_description"] = result.get("description", "")
    st.session_state["generated_themes"] = result.get("themes", [])
    st.session_state["generated_keywords"] = result.get("keywords", [])
    print(st.session_state["generated_description"])
    st.session_state.step = 3

st.sidebar.button(
    "Upload & Datentypen",
    on_click=set_step,
    args=(1,),
    use_container_width=True
)

st.sidebar.button(
    "Metadaten & DCAT",
    on_click=set_step,
    args=(2,),
    disabled=not step1_complete(),
    use_container_width=True
)

st.sidebar.button(
    "Beschreibung",
    on_click=set_step,
    args=(3,),
    disabled=not step1_complete(),
    use_container_width=True
)

if st.session_state.step == 1:
    st.header("Schritt 1: Upload & Datentypen")

    up_file = st.file_uploader(" ", type=["csv"], accept_multiple_files=False)
    if st.button("↗ CSV hochladen", type="primary", use_container_width=False):
        try:
            if up_file is None:
                st.warning("Bitte zuerst eine CSV-Datei auswählen.")
            else:
                with st.spinner("Lade CSV-Datei..."):
                    df = load_csv(source_path=None, uploaded_file=up_file)
                    st.session_state.df = df
                st.success(f"{len(df)} Zeilen wurden hochgeladen.")

                st.session_state.df = df
                st.session_state["csvw_datatypes"] = {
                    col: infer_csvw_datatype(df[col])
                    for col in df.columns
                }
        except Exception as e:
            st.error(f"Fehler beim Laden: {e}")
    #print(df)
    if st.session_state.df is not None:
        st.dataframe(st.session_state.df.head())

        st.subheader("CSVW-Spaltenbeschreibung")

        for col in st.session_state.df.columns:
                if col not in st.session_state["csvw_columns"]:
                    st.session_state["csvw_columns"][col] = {
                        "datatype": "xsd:string",
                        "description": "",
                        "required": False,
                        "minimum": "",
                        "maximum": "",
                        "pattern": "",
                        "null": "",
                    }

                with st.container(border=True):
                    st.markdown(f"### {col}")

                    datatype = st.selectbox(
                        "Datentyp",
                        CSVW_DATATYPES,
                        index=CSVW_DATATYPES.index(
                            st.session_state["csvw_columns"][col]["datatype"]
                        ),
                        key=f"csvw_datatype_{col}",
                    )

                    description = st.text_area(
                        "Beschreibung",
                        value=st.session_state["csvw_columns"][col]["description"],
                        key=f"csvw_description_{col}",
                        height=80,
                    )

                    required = st.checkbox(
                        "Pflichtfeld",
                        value=st.session_state["csvw_columns"][col]["required"],
                        key=f"csvw_required_{col}",
                    )

                    with st.expander("Optionale Constraints"):
                        minimum = st.text_input(
                            "Minimum",
                            value=st.session_state["csvw_columns"][col]["minimum"],
                            key=f"csvw_minimum_{col}",
                        )

                        maximum = st.text_input(
                            "Maximum",
                            value=st.session_state["csvw_columns"][col]["maximum"],
                            key=f"csvw_maximum_{col}",
                        )

                        pattern = st.text_input(
                            "Regex Pattern",
                            value=st.session_state["csvw_columns"][col]["pattern"],
                            key=f"csvw_pattern_{col}",
                        )

                        null_values = st.text_input(
                            "Null-Werte",
                            value=st.session_state["csvw_columns"][col]["null"],
                            placeholder="z.B. '', NA, null",
                            key=f"csvw_null_{col}",
                        )

                    st.session_state["csvw_columns"][col] = {
                        "datatype": datatype,
                        "description": description,
                        "required": required,
                        "minimum": minimum,
                        "maximum": maximum,
                        "pattern": pattern,
                        "null": null_values,
        }

    st.button(
            "Weiter zu Metadaten",
            on_click=set_step,
            args=(2,),
            disabled=not step1_complete(),
            type="secondary",
    )

elif st.session_state.step == 2:
    st.header("Schritt 2: Metadaten & DCAT")
    with st.container(border=True):
        col_small, col_large = st.columns([3,1])

        with col_small:
            st.session_state["title"] = st.text_input(
                "Datensatz-Titel (dcterms:title)*",
                placeholder="z.B. Unternehmenszahlen in Halle (Saale)",
                help="Titel-Hilfe"
            )

            st.session_state["publisher"] = st.selectbox(
                "Veröffentlichende Stelle (dcterms:publisher)*",
                list(city_map.keys()),
                index=None,
                help="Publisher-Hilfe"
            )

            st.session_state["license"] = st.selectbox(
                "Lizenz",
                list(license_map.keys()),
                index=None,
                help="Lizenz-Hilfe",

            )

            st.session_state["availability"] = st.selectbox(
                "Verfügbarkeit",
                list(availability_map.keys()),
                index=None,
                help="**temporär**: Daten können jederzeit verschwinden  \n"
                     "**experimental**: Daten versuchsweise verfügbar, sind aber noch etwa ein Jahr erreichbar  \n"
                     "**verfügbar**: Daten sind für einige Jahre verfügbar, mittelfristige Planung  \n"
                     "**stabil**: Daten werden langfristig erhalten bleiben. "
            )

            with st.container(border=True):
                st.write("Zeitliche Abdeckung")
                time_from = st.date_input("Zeitraum von", value=None)
                if time_from:
                    st.session_state["time_from"] = time_from
                time_till = st.date_input("Zeitraum bis", value=None)
                if time_till:
                    st.session_state["time_till"] = time_till

            with st.container(border=True):
                st.write("Räumliche Abdeckung")
                for i in range(len(st.session_state["places"])):
                    col_place, col_remove = st.columns([5, 1])

                    with col_place:
                        selected_place = st_searchbox(
                            load_places_from_rdf,
                            placeholder="Nach Ort suchen...",
                            label=f"Gebiet {i + 1}",
                            clear_on_submit=False,
                            key=f"place_{i}",
                        )

                        st.session_state["places"][i] = selected_place

                        if selected_place:
                            st.session_state["place_keys"][i] = (
                                st.session_state["district_lookup"].get(selected_place)
                            )

                    with col_remove:
                        st.markdown(" ")
                        st.markdown(" ")

                        if len(st.session_state["places"]) > 1:
                            if st.button(
                                    "Entfernen",
                                    key=f"remove_place_{i}",
                                    use_container_width=True
                            ):
                                st.session_state["places"].pop(i)
                                st.session_state["place_keys"].pop(i)
                                st.rerun()

                if st.button("➕ Ort hinzufügen"):
                    st.session_state["places"].append(None)
                    st.session_state["place_keys"].append(None)
                    st.rerun()

        with col_large:
            with st.expander("KI-Konfiguration"):
                models = st.selectbox(
                    "KI-Modelle",
                    list(llm_map.keys()),
                    help="LLM-Hilfe",
                    key="selected_llm"
                )

                prompt_template = st.text_area(
                    "Die folgende Nachricht wird an die KI übegeben:",
                    value=metadata_prompt,
                    height=200,
                    help="Vorgaben für die Metadatengenerierung.",
                    key="prompt_template"
                )

                st.markdown("<h4>Parameter</h4>", unsafe_allow_html=True)
                temperature = st.slider(
                    "Temperature",
                    0.0, 2.0, 0.4, 0.1,
                    help="Steuert die Kreativität der KI: niedriger Wert = präzise, hoher Wert = variabler. Empfehlung: 0,2-0,6",
                    key="temperature"
                )

    step2_missing = step2_incomplete(st.session_state["title"], st.session_state["publisher"])
    if len(step2_missing) > 0:
        st.warning(
            "Folgende Pflichtfelder fehlen:\n\n- "
            + "\n- ".join(step2_missing)
        )

    st.button(
            "Weiter zur Beschreibung",
            on_click=generate_description,
            type="secondary",
            disabled=len(step2_missing) > 0
    )

    st.button("⬅ Zurück", on_click=set_step, args=(1,))

elif st.session_state.step == 3:
    st.header("Schritt 3: Beschreibungs-Erstellung")

    st.text_area(
        "Beschreibung (dct:description)",
        value=st.session_state.get("generated_description", ""),
        height=180,
        key="description"
    )

    st_tags(
        label="Keywords (dcat:keyword)",
        text="Keyword eingeben und Enter drücken",
        value=st.session_state.get("generated_keywords", []),
        key="keywords_generated"
    )

    valid_themes = [
        theme
        for theme in st.session_state.get("generated_themes", [])
        if theme in theme_map.keys()
    ]

    selected_themes = st.multiselect(
        "Themen (dcat:theme)",
        options=list(theme_map.keys()),
        default=valid_themes,
        help="Mehrere Themen möglich."
    )

    st.session_state["selected_themes"] = selected_themes

    step3_missing = step3_incomplete(st.session_state["description"])

    if len(step3_missing) > 0:
        st.warning("Folgende Pflichtfelder fehlen:\n\n- "
            + "\n- ".join(step3_missing)
        )

    if st.button("Metadaten generieren", type="secondary", disabled=len(step3_missing) > 0):

        csvw_filename = st.session_state["dataset"].dataset_id+".csv-metadata.json"
        csvw_uri = f"https://example.org/{csvw_filename}"

        st.session_state["csvw_metadata"] = create_csvw_metadata(
            df=st.session_state.df,
            csvw_columns=st.session_state["csvw_columns"],
            csv_url=st.session_state["dataset"].dataset_id + ".csv",
        )

        st.session_state["dataset"].add_description(st.session_state["description"])
        st.session_state["dataset"].add_license(license_map.get(st.session_state["license"]))
        st.session_state["dataset"].add_availability(availability_map.get(st.session_state["availability"]))

        for keyword in st.session_state["keywords_generated"]:
            st.session_state["dataset"].add_keyword(keyword)

        for theme in st.session_state["selected_themes"]:
            st.session_state["dataset"].add_theme(theme_map[theme])

        st.session_state["dataset"].add_conforms_to(csvw_uri)

        st.session_state["dataset"].add_temporal_coverage(
            start_date=st.session_state["time_from"],
            end_date=st.session_state["time_till"]
        )

        rdf_turtle = st.session_state["dataset"].serialize(format="turtle")

        st.session_state["export_zip"] = create_export_zip(
            dataset_id=st.session_state["dataset"].dataset_id,
            rdf_turtle=rdf_turtle,
            csvw_json=st.session_state["csvw_metadata"]
        )

        if st.session_state.get("export_zip"):
            st.download_button(
                label="ZIP herunterladen",
                data=st.session_state["export_zip"],
                file_name="metadata_export.zip",
                mime="application/zip",
                type="primary"
            )

    st.button("⬅ Zurück", on_click=set_step, args=(2,))
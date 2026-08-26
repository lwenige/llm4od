import streamlit as st

from config import llm_map, theme_map
from services.metadata_prompt import build_metadata_prompt
from services.openrouter_client import generate_metadata_with_openrouter
from state import set_step, sync_state_to_widget, sync_widget_to_state


DEFAULT_SYSTEM_PROMPT = """Du bist ein Experte für Open-Data-Metadaten nach DCAT-AP.de. Deine Aufgabe ist es, vorhandene Metadaten eines Datensatzes zu prüfen, sinnvoll zu ergänzen und daraus hochwertige DCAT-Metadaten zu generieren.

Erzeuge ausschließlich folgende Felder: dct:description, dcat:theme, dcat:keyword.

Berücksichtige dabei alle bereitgestellten Informationen, insbesondere vorhandene Beschreibung, Titel, Publisher, Beispieldaten und sonstige Hinweise."""


DEFAULT_DESCRIPTION_PROMPT = """- Schreibe eine prägnante, sachliche und professionelle Beschreibung auf Deutsch.
- Länge: 10–15 Sätze.
- Ergänze nur Informationen, die aus den Metadaten, Spaltennamen oder Beispieldaten plausibel ableitbar sind.
- Keine Halluzinationen, erfundenen Zwecke, Institutionen, Zeiträume oder Inhalte.
- Erwähne räumliche oder zeitliche Bezüge nur, wenn sie angegeben oder klar erkennbar sind.
- Keine Werbesprache.
- Kein Markdown."""


DEFAULT_THEME_PROMPT = """- Wähle passende Themen ausschließlich aus der bereitgestellten Themenliste.
- Mehrfachauswahl ist erlaubt.
- Typischerweise genau 1 Thema.
- Maximal 2 Themen.
- Keine eigenen Themen erfinden.
- Gib Themen exakt wie in der Themenliste vorgegeben zurück."""


DEFAULT_KEYWORD_PROMPT = """- Erzeuge 3–8 sinnvolle Keywords.
- Keywords müssen deutsch, kurz und fachlich präzise sein.
- Bevorzuge Substantive oder etablierte Fachbegriffe.
- Keine vollständigen Sätze.
- Keine Duplikate.
- Keine generischen Begriffe wie „Daten“, „CSV“, „Tabelle“, „Datensatz“."""


def initialize_prompt_state():
    """Initialisiert die editierbaren Prompt-Bestandteile."""
    defaults = {
        "system_prompt": DEFAULT_SYSTEM_PROMPT,
        "description_prompt": DEFAULT_DESCRIPTION_PROMPT,
        "theme_prompt": DEFAULT_THEME_PROMPT,
        "keyword_prompt": DEFAULT_KEYWORD_PROMPT,
    }

    for key, default_value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = default_value


def combine_prompt_parts():
    """Fügt Systemprompt und feldspezifische Vorgaben zusammen."""
    return f"""SYSTEMPROMPT:
{st.session_state["system_prompt"].strip()}

DESCRIPTION:
{st.session_state["description_prompt"].strip()}

THEME:
{st.session_state["theme_prompt"].strip()}

KEYWORD:
{st.session_state["keyword_prompt"].strip()}"""


def generate_description():
    sample_data = st.session_state.df.head(10).to_markdown(index=False)

    editable_prompt = combine_prompt_parts()

    # Kompatibilität mit dem bisherigen State-Eintrag.
    st.session_state["prompt_template"] = editable_prompt

    final_prompt = build_metadata_prompt(
        editable_prompt=editable_prompt,
        title=st.session_state["title"],
        publisher=st.session_state["publisher"],
        sample_data=sample_data,
        themes=theme_map,
    )

    with st.spinner(
            "KI generiert Metadatenfelder",
            show_time=True,
    ):
        result = generate_metadata_with_openrouter(
            prompt=final_prompt,
            model=llm_map[st.session_state["selected_llm"]],
            api_key=st.secrets["OPENROUTER_API_KEY"],
            temperature=st.session_state["temperature"],
        )

    st.session_state["description"] = result.get("description", "")
    st.session_state["generated_themes"] = result.get("themes", [])
    st.session_state["keywords"] = result.get("keywords", [])
    st.session_state["step3_completed"] = True

    set_step(4)


def render_prompt_field(
    label,
    help_text,
    widget_key,
    state_key,
    height,
):
    """Rendert ein Prompt-Feld mit separatem Label und Hilfetext."""
    sync_state_to_widget(widget_key, state_key)

    st.markdown(
        f"**{label}**",
        help=help_text,
    )

    st.text_area(
        label=label,
        label_visibility="collapsed",
        height=height,
        key=widget_key,
        on_change=sync_widget_to_state,
        args=(widget_key, state_key),
    )


def render_ai_config():
    initialize_prompt_state()

    st.header("Schritt 3: KI-Konfiguration")

    st.markdown(
        "Hier können Festlegungen für den Einsatz des KI-Modells getroffen "
        "werden. Im Hintergrund werden dann die Felder: **Datensatz-Beschreibung**, **Keywords** (Schlüsselwörter) "
        "und **Kategorien** (Themen) erzeugt. Das Modell bekommt als Input die in Schritt 1 und 2 "
        "festgelegten Metadaten sowie einen Ausschnitt der hochgeladenen CSV-Datei."
    )

    left_column, right_column = st.columns(
        [1, 1],
        gap="large",
        vertical_alignment="top",
    )

    # Linke Spalte:
    # KI-Modell, Systemprompt und Temperatur
    with left_column:
        sync_state_to_widget("_selected_llm", "selected_llm")

        st.markdown(
            "**KI-Modell**",
            unsafe_allow_html=True,
            help=(
                "Wählt das Sprachmodell aus, das die Metadaten generiert. "
                "Je nach Modell können Qualität, Geschwindigkeit und Kosten "
                "unterschiedlich ausfallen. Bei den GPT-Modellen handelt es sich "
                "um proprietäre, kommerzielle Modelle der Firma OpenAI. Bei Mistral und "
                "Llama um Open-Weight-Modelle."
            )
        )

        st.selectbox(
            label="KI-Modell",
            label_visibility="collapsed",
            options=list(llm_map.keys()),
            key="_selected_llm",
            on_change=sync_widget_to_state,
            args=("_selected_llm", "selected_llm"),
        )

        st.markdown(
            "**Temperatur**",
            unsafe_allow_html=True,
            help=(
                "Steuert die Zufälligkeit der Ausgabe im Temperaturbereich 0.0 bis 0.5. Niedrige Werte erzeugen "
                "gleichmäßigere und vorhersehbarere Ergebnisse. Höhere Werte "
                "erhöhen die sprachliche Variation, es können aber ggf. mehr Fehler auftreten."
            )
        )

        sync_state_to_widget("_temperature", "temperature")
        st.slider(
            label="Temperatur",
            label_visibility="collapsed",
            min_value=0.0,
            max_value=0.5,
            step=0.1,
            format="%.1f",
            key="_temperature",
            on_change=sync_widget_to_state,
            args=("_temperature", "temperature"),
        )

        render_prompt_field(
            label="Systemprompt",
            help_text=(
                "Definiert die grundsätzliche Rolle und Aufgabe des "
                "KI-Modells. Der Systemprompt wird vor den Vorgaben für "
                "DESCRIPTION, THEME und KEYWORD an das Modell übergeben."
            ),
            widget_key="_system_prompt",
            state_key="system_prompt",
            height=460,
        )



    # Rechte Spalte:
    # Feldspezifische Vorgaben
    with right_column:
        render_prompt_field(
            label="Datensatz-Beschreibung (Prompt)",
            help_text=(
                "Legt fest, wie die Beschreibung des Datensatzes erzeugt "
                "werden soll. Hier können Sprache, Länge, Stil und inhaltliche "
                "Einschränkungen angepasst werden."
            ),
            widget_key="_description_prompt",
            state_key="description_prompt",
            height=200,
        )

        render_prompt_field(
            label="Keywords (Prompt)",
            help_text=(
                "Legt fest, wie die Schlagwörter erzeugt werden. Hier können "
                "Anzahl, Sprache, Form und ausgeschlossene Begriffe angepasst "
                "werden."
            ),
            widget_key="_keyword_prompt",
            state_key="keyword_prompt",
            height=170,
        )

        render_prompt_field(
            label="Kategorien (Prompt)",
            help_text=(
                "Legt fest, wie passende Themen aus der bereitgestellten "
                "Themenliste ausgewählt werden. Die Themen müssen exakt aus "
                "dieser Liste übernommen werden."
            ),
            widget_key="_theme_prompt",
            state_key="theme_prompt",
            height=170,
        )

    st.divider()

    button_column, back_column, spacer = st.columns(
        [2, 1, 5],
        gap="small",
    )

    with button_column:
        st.button(
            "Beschreibung mit KI generieren",
            on_click=generate_description,
            type="primary",
            use_container_width=True,
        )

    with back_column:
        st.button(
            "⬅ Zurück",
            on_click=set_step,
            args=(2,),
            use_container_width=True,
        )
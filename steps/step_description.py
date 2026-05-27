from streamlit_tags import st_tags

from config import theme_map, availability_map
from resources import load_license_map
from services.csvw import create_csvw_metadata
from services.validate import step3_incomplete
from services.zip import create_export_zip
from state import init_state, set_step
import streamlit as st

def render_description():
    #init_state()
    license_map = load_license_map()
    st.header("Schritt 3: Beschreibungs-Erstellung")
    st.markdown(
        "Datensatz-Beschreibung "
        "<span style='color:red'>*</span>",
        unsafe_allow_html=True
    )
    st.text_area(
        "Beschreibung",
        label_visibility="collapsed",
        value=st.session_state.get("generated_description", ""),
        height=180,
        key="description"
    )

    st.markdown("Schlagwörter")
    st_tags(
        label="",
        text="Keyword eingeben und Enter drücken",
        value=st.session_state.get("generated_keywords", []),
        key="keywords_generated"
    )

    theme_uri_to_label = {
        str(uri): label
        for label, uri in theme_map.items()
    }

    generated_theme_uris = st.session_state.get("generated_themes", [])

    valid_theme_labels = [
        theme_uri_to_label[uri]
        for uri in generated_theme_uris
        if uri in theme_uri_to_label
    ]

    st.markdown("Themen")
    selected_themes = st.multiselect(
        label="Themen",
        label_visibility="collapsed",
        options=list(theme_map.keys()),
        default=valid_theme_labels,
        help="Themen aus der Liste der \"EU Vocabulary DCAT Themes\". Mehrere Themen sind möglich."
    )

    st.session_state["selected_themes"] = selected_themes

    step3_missing = step3_incomplete(st.session_state["description"])

    if len(step3_missing) > 0:
        st.warning("Folgende Pflichtfelder fehlen:\n\n- "
                   + "\n- ".join(step3_missing)
                   )

    if st.button("Metadaten generieren", type="secondary", disabled=len(step3_missing) > 0):

        csvw_filename = st.session_state["dataset"].dataset_id + ".csv-metadata.json"
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
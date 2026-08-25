from streamlit_tags import st_tags

from config import theme_map
from services.validate import step3_incomplete
from state import (
    set_step,
    step3_complete,
    sync_state_to_widget,
    sync_widget_to_state,
)

import streamlit as st


def init_description_state():
    theme_uri_to_label = {
        str(uri): label
        for label, uri in theme_map.items()
    }

    generated_theme_uris = st.session_state.get("generated_themes", [])

    generated_theme_labels = [
        theme_uri_to_label[str(uri)]
        for uri in generated_theme_uris
        if str(uri) in theme_uri_to_label
    ]
    print(generated_theme_labels)
    # st.session_state.setdefault(
    #     "description",
    #     st.session_state.get("generated_description", "")
    # )
    #st.session_state["themes"] = generated_theme_labels
    st.session_state.setdefault("themes", generated_theme_labels)
    # st.session_state.setdefault(
    #     "theme",
    #     generated_theme_labels
    # )

    # st.session_state.setdefault(
    #     "_description",
    #     st.session_state["description"]
    # )
    # st.session_state.setdefault(
    #     "_keywords_generated",
    #     st.session_state["keywords_generated"]
    # )
    # st.session_state.setdefault(
    #     "_theme",
    #     st.session_state["theme"]
    # )


def render_description():
    init_description_state()

    st.header("Schritt 4: Beschreibungs-Erstellung")

    st.markdown(
        "Datensatz-Beschreibung "
        "<span style='color:red'>*</span>",
        unsafe_allow_html=True
    )
    sync_state_to_widget("_description", "description")
    st.text_area(
        "Beschreibung",
        label_visibility="collapsed",
        height=180,
        key="_description",
        on_change=sync_widget_to_state,
        args=("_description", "description"),
    )

    st.markdown("Schlagwörter")
    sync_state_to_widget("_keywords", "keywords")
    keywords = st_tags(
        label="",
        text="Keyword eingeben und Enter drücken",
        value=st.session_state["_keywords"],
        key="_keywords",
    )

    # st_tags liefert den aktuellen Wert direkt zurück.
    st.session_state["keywords"] = keywords or []

    st.markdown("Themen")
    sync_state_to_widget("_themes", "themes")
    st.multiselect(
        label="Themen",
        label_visibility="collapsed",
        options=list(theme_map.keys()),
        key="_themes",
        on_change=sync_widget_to_state,
        args=("_themes", "themes"),
        help=(
            'Themen aus der Liste der "EU Vocabulary DCAT Themes". '
            "Mehrere Themen sind möglich."
        ),
    )

    # Beibehalten, falls der Export weiterhin diesen Namen verwendet.
    #st.session_state["selected_themes"] = st.session_state["theme"]

    step3_missing = step3_incomplete(
        st.session_state.get("description", "")
    )

    if step3_missing:
        st.warning(
            "Folgende Pflichtfelder fehlen:\n\n- "
            + "\n- ".join(step3_missing)
        )

    if st.button(
        "Metadaten prüfen",
        type="secondary",
        disabled=bool(step3_missing),
    ):
        st.session_state["step4_completed"] = True
        set_step(5)
        st.rerun()

    st.button(
        "⬅ Zurück",
        on_click=set_step,
        disabled=not step3_complete(),
        args=(3,),
    )
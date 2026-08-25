import streamlit as st
from streamlit_searchbox import st_searchbox
from config import city_map, availability_map
from services.search import create_district_index, search_places
from services.validate import step1_incomplete
from state import sync_widget_to_state, sync_state_to_widget, set_step, sync_widget_to_state_and_invalidate
if "district_index" not in st.session_state:
    st.session_state["district_index"] = create_district_index()

def load_places_from_rdf(query: str):
    results, place_lookup = search_places(st.session_state["district_index"], query)
    st.session_state["district_lookup"].update(place_lookup)
    return results

def render_metadata():

    st.header("Schritt 2: Metadaten & DCAT")
    with st.container(border=True):
        col_large, col_small = st.columns([2.5, 1.5])

        with col_large:
            st.markdown(
                "Datensatz-Titel "
                "<span style='color:red'>*</span>",
                unsafe_allow_html=True
            )
            sync_state_to_widget("_title", "title")
            st.text_input(
                label="Datensatz-Titel",
                label_visibility="collapsed",
                placeholder="z.B. Unternehmenszahlen in Halle (Saale)",
                help="Titel-Hilfe",
                on_change=sync_widget_to_state_and_invalidate,
                args=("_title", "title"),
                key="_title"
            )

            st.markdown(
                "Veröffentlichende Stelle"
                "<span style='color:red'>*</span>",
                unsafe_allow_html=True
            )
            sync_state_to_widget("_publisher", "publisher")
            st.selectbox(
                "Veröffentlichende Stelle",
                label_visibility="collapsed",
                options=list(city_map.keys()),
                index=None,
                placeholder="Bitte auswählen...",
                help="Publisher-Hilfe",
                on_change=sync_widget_to_state_and_invalidate,
                args=("_publisher", "publisher"),
                key="_publisher",
            )

            sync_state_to_widget("_availability", "availability")
            st.selectbox(
                "Verfügbarkeit",
                options=list(availability_map.keys()),
                index=None,
                placeholder="Bitte auswählen...",
                help="**temporär**: Daten können jederzeit verschwinden  \n"
                     "**experimental**: Daten versuchsweise verfügbar, sind aber noch etwa ein Jahr erreichbar  \n"
                     "**verfügbar**: Daten sind für einige Jahre verfügbar, mittelfristige Planung  \n"
                     "**stabil**: Daten werden langfristig erhalten bleiben.",
                on_change=sync_widget_to_state,
                args=("_availability", "availability"),
                key="_availability",
            )

            with st.container(border=True):
                st.write("Zeitliche Abdeckung")

                sync_state_to_widget("_time_from", "time_from")
                st.date_input(
                    "Zeitraum von",
                    value=None,
                    on_change=sync_widget_to_state,
                    args=("_time_from", "time_from"),
                    key="_time_from"
                )

                sync_state_to_widget("_time_till", "time_till")
                st.date_input(
                    "Zeitraum bis",
                    value=None,
                    on_change=sync_widget_to_state,
                    args=("_time_till", "time_till"),
                    key="_time_till"
                )

            with st.container(border=True):
                st.write("Räumliche Abdeckung")
                if "district_index" not in st.session_state:
                    st.session_state["district_index"] = create_district_index()

                for i in range(len(st.session_state["places"])):
                    col_place, col_remove = st.columns([5, 1])

                    with col_place:
                        stored_place = st.session_state["places"][i]
                        selected_place = st_searchbox(
                            load_places_from_rdf,
                            placeholder="Nach Ort suchen...",
                            label=f"Gebiet {i + 1}",
                            clear_on_submit=False,
                            default=stored_place,
                            default_searchterm=stored_place or "",
                            default_options=[stored_place] if stored_place else [],
                            edit_after_submit="option",
                            key=f"place_{i}",
                        )

                        if selected_place:
                            st.session_state["places"][i] = selected_place
                            st.session_state["place_keys"][i] = (
                                    st.session_state["district_lookup"].get(selected_place)
                                    or st.session_state["place_keys"][i]
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

                                # alle Searchbox-Widget-Keys löschen, damit Indizes sauber neu aufgebaut werden
                                for key in list(st.session_state.keys()):
                                    if key.startswith("place_"):
                                        del st.session_state[key]

                                st.rerun()

                if st.button("+ Ort hinzufügen"):
                    st.session_state["places"].append(None)
                    st.session_state["place_keys"].append(None)
                    st.rerun()

        with col_small:
            st.write("Test")
            # with st.expander("KI-Konfiguration"):
            #     sync_state_to_widget("_selected_llm", "selected_llm")
            #     st.selectbox(
            #         "KI-Modelle",
            #         options=list(llm_map.keys()),
            #         help="LLM-Hilfe",
            #         on_change=sync_widget_to_state,
            #         args=("_selected_llm", "selected_llm"),
            #         key="_selected_llm",
            #     )
            #
            #     sync_state_to_widget("_prompt_template", "prompt_template")
            #     st.text_area(
            #         "Die folgende Nachricht wird an die KI übergeben:",
            #         height=500,
            #         help="Vorgaben für die Metadatengenerierung.",
            #         on_change=sync_widget_to_state,
            #         #value=st.session_state["_prompt_template"],
            #         args=("_prompt_template", "prompt_template"),
            #         key="_prompt_template"
            #     )
            #
            #     sync_state_to_widget("_temperature", "temperature")
            #     st.slider(
            #         "Temperatur",
            #         0.0,
            #         2.0,
            #         #value=st.session_state["_temperature"],
            #         step=0.1,
            #         help="Steuert die Kreativität der KI.",
            #         on_change=sync_widget_to_state,
            #         args=("_temperature", "temperature"),
            #         key="_temperature",
            #     )

    step1_missing = step1_incomplete(
        st.session_state["title"],
        st.session_state["publisher"]
    )

    if len(step1_missing) > 0:
        st.warning(
            "Folgende Pflichtfelder fehlen:\n\n- "
            + "\n- ".join(step1_missing)
        )

    # st.button(
    #     "Weiter zur Beschreibung",
    #     on_click=generate_description,
    #     type="secondary",
    #     disabled=len(step2_missing) > 0
    # )

    st.button(
        "Weiter zur KI-Konfiguration",
        on_click=set_step,
        args=(2,),
        type="secondary",
        disabled=len(step1_missing) > 0,
    )

    st.button(
        "⬅ Zurück",
        on_click=lambda: st.session_state.update(step=1)
    )

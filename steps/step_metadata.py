import streamlit as st
from streamlit_searchbox import st_searchbox
from config import city_map, availability_map
from services.search import create_district_index, search_places
from services.validate import step1_incomplete
#from state import sync_widget_to_state, sync_state_to_widget, set_step, sync_widget_to_state_and_invalidate
from state import (
    sync_widget_to_state,
    sync_state_to_widget,
    set_step,
    sync_widget_to_state_and_invalidate,
    sync_time_widget_to_state_and_invalidate,
    sync_time_state_to_widget,
    invalidate_dependent_steps, sync_bounding_box_to_state,
)
import folium

from folium.plugins import Draw
from streamlit_folium import st_folium

if "district_index" not in st.session_state:
    st.session_state["district_index"] = create_district_index()

def load_places_from_rdf(query: str):
    results, place_lookup = search_places(st.session_state["district_index"], query)
    st.session_state["district_lookup"].update(place_lookup)
    return results

def render_metadata():

    st.header("Schritt 1: Metadaten zur DCAT-Erstellung")
    st.write("Bitte füllen Sie alle relevanten Metadenfelder aus. "
             "Pflichtfelder sind mit einem * markiert.")
    with st.container(border=True):
        col_large, col_small = st.columns([2.5, 1.5])

        with col_large:
            st.markdown(
                "**Datensatz-Titel**"
                "<span style='color:red'>*</span>",
                unsafe_allow_html=True,
                help="DCAT-Feld Datensatz-Titel (dct:title), siehe https://www.dcat-ap.de/def/dcatde/2.0/spec/#datensatz-titel"
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
                "**Veröffentlichende Stelle**"
                "<span style='color:red'>*</span>",
                unsafe_allow_html=True,
                help="DCAT-Feld Datensatz-Herausgeber (dct:publischer), siehe DCAT-AP.de https://www.dcat-ap.de/def/dcatde/2.0/spec/#datensatz-titel"
                     "\n\n"
                     "*Hinweis: Die vorliegende Liste enthält zu Demonstrationszwecken beispielhaft größere Städte"
                     "in Deutschland als Herausgeber. In einem Produktivsystem wären die für die Fachstelle relevanten"
                     "herausgebenden Körperschaften hinterlegt.*"
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

            st.markdown(
                "**Verfügbarkeit**",
                unsafe_allow_html=True,
                help="DCAT-Feld Datensatz-Verfügbarkeit (dcatap:availability), siehe DCAT-AP.de https://www.dcat-ap.de/def/dcatde/2.0/spec/#datensatz-verfugbarkeit"
                     "\n\n"
                     "DCAT-AP.de macht Vorgaben zu den möglichen Werten. Wählen Sie einen aus."
                     "\n\n"
                     "**temporär**: Daten können jederzeit verschwinden  \n"
                     "**experimental**: Daten versuchsweise verfügbar, sind aber noch etwa ein Jahr erreichbar  \n"
                     "**verfügbar**: Daten sind für einige Jahre verfügbar, mittelfristige Planung  \n"
                     "**stabil**: Daten werden langfristig erhalten bleiben."
            )

            st.selectbox(
                "**Verfügbarkeit**",
                label_visibility="collapsed",
                options=list(availability_map.keys()),
                index=None,
                placeholder="Bitte auswählen...",
                on_change=sync_widget_to_state,
                args=("_availability", "availability"),
                key="_availability",
            )

            # with st.container(border=True):
            #     st.write("Zeitliche Abdeckung")
            #
            #     sync_state_to_widget("_time_from", "time_from")
            #     st.date_input(
            #         "Zeitraum von",
            #         value=None,
            #         on_change=sync_widget_to_state,
            #         args=("_time_from", "time_from"),
            #         key="_time_from"
            #     )
            #
            #     sync_state_to_widget("_time_till", "time_till")
            #     st.date_input(
            #         "Zeitraum bis",
            #         value=None,
            #         on_change=sync_widget_to_state,
            #         args=("_time_till", "time_till"),
            #         key="_time_till"
            #     )

            with st.container(border=True):

                st.markdown(
                    "**Zeitliche Abdeckung**",
                    help="Zeitraum, den die Daten abdecken (dct:temporal), siehe DCAT-AP.de https://www.dcat-ap.de/def/dcatde/2.0/spec/#klasse-zeitraum"
                )

                for i in range(len(st.session_state["time_periods"])):
                    col_from, col_till, col_remove = st.columns([2, 2, 1])

                    from_key = f"_time_from_{i}"
                    till_key = f"_time_till_{i}"

                    # Persistenten State in Widget-State synchronisieren
                    sync_time_state_to_widget(
                        from_key,
                        i,
                        "from",
                    )

                    sync_time_state_to_widget(
                        till_key,
                        i,
                        "till",
                    )

                    with col_from:
                        st.date_input(
                            "Zeitraum von",
                            value=None,
                            key=from_key,
                            on_change=sync_time_widget_to_state_and_invalidate,
                            args=(from_key, i, "from"),
                        )

                    with col_till:
                        st.date_input(
                            "Zeitraum bis",
                            value=None,
                            key=till_key,
                            on_change=sync_time_widget_to_state_and_invalidate,
                            args=(till_key, i, "till"),
                        )

                    with col_remove:
                        st.markdown(" ")
                        st.markdown(" ")

                        if len(st.session_state["time_periods"]) > 1:
                            if st.button(
                                    "Entfernen",
                                    key=f"remove_time_period_{i}",
                                    use_container_width=True,
                            ):
                                st.session_state["time_periods"].pop(i)

                                # Alte Widget-Keys entfernen
                                for key in list(st.session_state.keys()):
                                    if (
                                            key.startswith("_time_from_")
                                            or key.startswith("_time_till_")
                                    ):
                                        del st.session_state[key]

                                invalidate_dependent_steps()
                                st.rerun()

                if st.button(
                        "+ Zeitraum hinzufügen",
                        key="add_time_period",
                ):
                    st.session_state["time_periods"].append({
                        "from": None,
                        "till": None,
                    })

                    invalidate_dependent_steps()
                    st.rerun()

            with st.container(border=True):
                st.markdown(
                    "**Räumliche Abdeckung (AGS-Landkreise und kreisfreie Städte)**",
                    help="Ein räumlicher Bereich oder ein Standort, den die Daten abdecken (dct:spatial), siehe DCAT-AP.de https://www.dcat-ap.de/def/dcatde/2.0/spec/#klasse-standort"
                         "\n\n"
                         "*Hinweis: Die vorliegende Liste enthält zu Demonstrationszwecken beispielhaft die Amtlichen Gemeindeschlüssel (AGS) der "
                         "kreisfreien Städte und Landkreise. In einem Produktivsystem könnten AGS-Schlüssel gröberer oder "
                         "feingranularer Verwaltungsebenen hinterlegt sein (siehe hier: https://www.dcat-ap.de/def/) bzw. Standort-Links (URIs) aus weiteren Ortsdatenbanken"
                         "(z.B. GeoNames)*"
                )
                st.markdown("*Tipp: Suchen Sie über das Eingabefeld*")
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
                                old_place_count = len(st.session_state["places"])

                                st.session_state["places"].pop(i)
                                st.session_state["place_keys"].pop(i)

                                # Nur die erzeugten Searchbox-Widget-Keys löschen.
                                # startswith("place_") würde auch den persistenten
                                # State "place_keys" löschen.
                                for widget_index in range(old_place_count):
                                    st.session_state.pop(
                                        f"place_{widget_index}",
                                        None,
                                    )

                                st.rerun()

                if st.button("+ Ort hinzufügen"):
                    st.session_state["places"].append(None)
                    st.session_state["place_keys"].append(None)
                    st.rerun()

        with col_small:
            st.markdown(
                "**Räumliche Abdeckung (Bounding Box)**",
                help="Ein räumlicher Bereich oder ein Standort, den die Daten abdecken (dct:spatial), siehe DCAT-AP.de https://www.dcat-ap.de/def/dcatde/2.0/spec/#klasse-standort"
                     "\n\n"
                     "*Hinweis: In der vorliegenden Karte können Sie aktuell nur einen geographischen "
                     "Bereich selber auswählen. In einem Produktivsystem sollte eine Mehrfach-Kartenauswahl"
                     "möglich sein, um dem DCAT-AP.de-Standard vollumfänglich zu entsprechen.*"
            )

            st.markdown(
                "\n\n"
                "Bitte markieren Sie bei Bedarf einen geographischen Bereich auf der Karte, auf den "
                "sich Ihre Daten beziehen. Selektieren Sie dafür das Rechteck (◼️) und zeichnen Sie den "
                "betroffenen Bereich ein.",
            )
            # -----------------------------------
            # Persistent State -> Widget State
            # -----------------------------------

            sync_state_to_widget(
                "_bounding_box",
                "bounding_box",
            )

            bbox = st.session_state["_bounding_box"]

            # -----------------------------------
            # Karte
            # -----------------------------------

            m = folium.Map(
                location=[51.34, 12.37],
                zoom_start=8,
            )

            # Bereits gespeicherte Bounding Box anzeigen
            if bbox:
                bounds = [
                    [bbox["south"], bbox["west"]],
                    [bbox["north"], bbox["east"]],
                ]

                folium.Rectangle(
                    bounds=bounds,
                    weight=2,
                    fill=True,
                    fill_opacity=0.15,
                ).add_to(m)

                m.fit_bounds(bounds)

            # Nur Rechtecke erlauben
            Draw(
                export=False,
                draw_options={
                    "polyline": False,
                    "polygon": False,
                    "circle": False,
                    "marker": False,
                    "circlemarker": False,
                    "rectangle": True,
                },
                edit_options={
                    "edit": False,
                    "remove": False,
                },
            ).add_to(m)

            # -----------------------------------
            # Streamlit-Komponente
            # -----------------------------------

            map_data = st_folium(
                m,
                width=None,
                height=450,
                key="spatial_bbox_map",
            )

            # -----------------------------------
            # Neue Bounding Box auslesen
            # -----------------------------------

            drawing = map_data.get("last_active_drawing")

            if drawing and drawing.get("geometry"):
                geometry = drawing["geometry"]

                if geometry.get("type") == "Polygon":
                    coordinates = geometry["coordinates"][0]

                    longitudes = [
                        point[0]
                        for point in coordinates
                    ]

                    latitudes = [
                        point[1]
                        for point in coordinates
                    ]

                    new_bbox = {
                        "west": min(longitudes),
                        "south": min(latitudes),
                        "east": max(longitudes),
                        "north": max(latitudes),
                    }

                    # Nur reagieren, wenn wirklich eine neue Box
                    # gezeichnet wurde.
                    if new_bbox != st.session_state["_bounding_box"]:
                        # Component/Widget State setzen
                        st.session_state["_bounding_box"] = new_bbox

                        # Widget State -> persistent State
                        sync_bounding_box_to_state()

                        st.rerun()

            # -----------------------------------
            # Aktuellen persistenten State anzeigen
            # -----------------------------------

            bbox = st.session_state["bounding_box"]

            if bbox:
                st.caption(
                    f'W: {bbox["west"]:.6f} | '
                    f'S: {bbox["south"]:.6f} | '
                    f'E: {bbox["east"]:.6f} | '
                    f'N: {bbox["north"]:.6f}'
                )

                if st.button(
                        "Bounding Box entfernen",
                        key="remove_bounding_box",
                ):
                    st.session_state["_bounding_box"] = None

                    sync_bounding_box_to_state()

                    st.rerun()
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
        "Weiter zum Datenupload",
        on_click=set_step,
        args=(2,),
        type="primary",
        disabled=len(step1_missing) > 0,
    )

    st.button(
        "⬅ Zurück",
        on_click=lambda: st.session_state.update(step=1)
    )


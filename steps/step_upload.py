import streamlit as st

import config
from models.dataset import Dataset
from services.resources import load_license_map
from services.csvw import infer_csvw_datatype, CSVW_DATATYPES
from services.dataloader import load_csv
from services.validate import step2_incomplete
from state import set_step, step1_complete, sync_state_to_widget, sync_widget_to_state, \
    sync_widget_to_state_and_invalidate


def render_upload():
    #init_state()
    # dataset = Dataset({
    #     "title": st.session_state["title"],
    #     "publisher": config.city_map[st.session_state["publisher"]],
    #     "publisher_name": st.session_state["publisher"],
    #     #"license": st.session_state["license"]
    # })
    #
    # for place_key in st.session_state["place_keys"]:
    #     if place_key is not None:
    #         dataset.add_place(place_key)
    #
    # st.session_state["dataset"] = dataset
    st.header("Schritt 1: Upload & Datentypen")

    sync_state_to_widget("_dist_title", "dist_title")
    st.text_input(
        label="Daten-Titel",
        placeholder="z.B. Unternehmenszahlen in Halle (Saale) - CSV",
        help="Titel-Hilfe",
        on_change=sync_widget_to_state,
        args=("_dist_title", "dist_title"),
        key="_dist_title"
    )

    st.markdown(
        "Lizenz"
        "<span style='color:red'>*</span>",
        unsafe_allow_html=True
    )

    sync_state_to_widget("_license", "license")
    st.selectbox(
        label="Lizenz",
        label_visibility="collapsed",
        options=list(config.license_map.keys()),
        index=None,
        placeholder="Bitte auswählen...",
        help="Lizenz-Hilfe",
        on_change=sync_widget_to_state_and_invalidate,
        args=("_license", "license"),
        key="_license",
    )

    st.write("Datenupload")
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

    step2_missing = step2_incomplete(
        st.session_state["df"],
        st.session_state["license"]
    )

    if len(step2_missing) > 0:
        st.warning(
            "Folgende Pflichtfelder fehlen:\n\n- "
            + "\n- ".join(step2_missing)
        )

    st.button(
        "Weiter zu Metadaten",
        on_click=set_step,
        #args=(2,),
        args=(3,),
        disabled=len(step2_missing) > 0,
        type="secondary",
    )

    if st.session_state.df is not None:
        st.dataframe(st.session_state.df.head())

        st.subheader("CSVW-Spaltenbeschreibung")

        for col in st.session_state.df.columns:
            if col not in st.session_state["csvw_columns"]:
                st.session_state["csvw_columns"][col] = {
                    #"datatype": "xsd:string",
                    "datatype": st.session_state["csvw_datatypes"].get(
                        col,
                        "xsd:string"
                    ),
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


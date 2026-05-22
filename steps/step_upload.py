import streamlit as st
from services.csvw import infer_csvw_datatype, CSVW_DATATYPES
from services.dataloader import load_csv
from state import init_state, set_step, step1_complete


def render_upload():
    #init_state()
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
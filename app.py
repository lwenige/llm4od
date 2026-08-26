import streamlit as st

from state import (
    init_state,
    set_step,
    step1_complete,
    step2_complete,
    step3_complete,
    step4_complete,
)

from steps.step_upload import render_upload
from steps.step_metadata import render_metadata
from steps.step_ai_config import render_ai_config
from steps.step_description import render_description
from steps.step_validation import render_validation


st.set_page_config(
    layout="wide",
    page_title="DCAT-AP.de Generator",
)

init_state()


def enforce_valid_step() -> None:
    current_step = st.session_state.get("step", 1)

    if current_step >= 2 and not step1_complete():
        st.session_state["step"] = 1
    elif current_step >= 3 and not step2_complete():
        st.session_state["step"] = 2
    elif current_step >= 4 and not step3_complete():
        st.session_state["step"] = 3
    elif current_step >= 5 and not step4_complete():
        st.session_state["step"] = 4


enforce_valid_step()

st.sidebar.title("Navigation")

st.sidebar.button(
    "1 Metadateneingabe",
    on_click=set_step,
    args=(1,),
    use_container_width=True,
)

st.sidebar.button(
    "2 Datenupload",
    on_click=set_step,
    args=(2,),
    disabled=not step1_complete(),
    use_container_width=True,
)

st.sidebar.button(
    "3 KI-Konfiguration",
    on_click=set_step,
    args=(3,),
    disabled=not step2_complete(),
    use_container_width=True,
)

st.sidebar.button(
    "4 Generierte Metadatenfelder",
    on_click=set_step,
    args=(4,),
    disabled=not step3_complete(),
    use_container_width=True,
)

st.sidebar.button(
    "5 Metadatenqualität & Publikation",
    on_click=set_step,
    args=(5,),
    disabled=not step4_complete(),
    use_container_width=True,
)

if st.session_state["step"] == 1:
    render_metadata()
elif st.session_state["step"] == 2:
    render_upload()
elif st.session_state["step"] == 3:
    render_ai_config()
elif st.session_state["step"] == 4:
    render_description()
elif st.session_state["step"] == 5:
    render_validation()
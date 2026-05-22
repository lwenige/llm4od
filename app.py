import streamlit as st

from state import init_state, set_step, step1_complete, step2_complete

from steps.step_upload import render_upload
from steps.step_metadata import render_metadata
from steps.step_description import render_description

st.set_page_config(
    layout="wide",
    page_title="DCAT-AP.de Generator"
)

init_state()

st.sidebar.title("Navigation")

st.sidebar.button(
    "1 Upload",
    on_click=set_step,
    args=(1,),
    use_container_width=True
)

st.sidebar.button(
    "2 Metadaten",
    on_click=set_step,
    args=(2,),
    disabled=not step1_complete(),
    use_container_width=True
)

st.sidebar.button(
    "3 Beschreibung",
    on_click=set_step,
    args=(3,),
    disabled=not step2_complete(),
    use_container_width=True
)


if st.session_state.step == 1:
    render_upload()

elif st.session_state.step == 2:
    render_metadata()

elif st.session_state.step == 3:
    render_description()
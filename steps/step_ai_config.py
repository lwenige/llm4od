import streamlit as st
from streamlit.runtime.state import session_state

from config import city_map, llm_map, theme_map
from models.dataset import Dataset
from services.metadata_prompt import build_metadata_prompt
from services.openrouter_client import generate_metadata_with_openrouter
from state import set_step, sync_state_to_widget, sync_widget_to_state


def generate_description():
    # dataset = Dataset({
    #     "title": st.session_state["title"],
    #     "publisher": city_map[st.session_state["publisher"]],
    #     "publisher_name": st.session_state["publisher"],
    #     "license": st.session_state["license"]
    # })
    #
    # for place_key in st.session_state["place_keys"]:
    #     if place_key is not None:
    #         dataset.add_place(place_key)
    #
    # st.session_state["dataset"] = dataset

    sample_data = st.session_state.df.head(10).to_markdown(index=False)

    final_prompt = build_metadata_prompt(
        editable_prompt=st.session_state["prompt_template"],
        title=st.session_state["title"],
        publisher=st.session_state["publisher"],
        sample_data=sample_data,
        themes=theme_map,
    )

    result = generate_metadata_with_openrouter(
        prompt=final_prompt,
        model=llm_map[st.session_state["selected_llm"]],
        api_key=st.secrets["OPENROUTER_API_KEY"],
        temperature=st.session_state["temperature"],
    )

    #st.session_state["generated_description"] = result.get("description", "")
    #st.session_state["generated_themes"] = result.get("themes", [])
    #st.session_state["generated_keywords"] = result.get("keywords", [])
    st.session_state["description"] = result.get("description", "")
    st.session_state["generated_themes"] = result.get("themes", [])
    st.session_state["keywords"] = result.get("keywords", [])
    #st.session_state["step3_completed"] = True
    st.session_state["step3_completed"] = True
    set_step(4)


def render_ai_config():
    st.header("Schritt 3: KI-Konfiguration")
    #st.session_state["step3_completed"] = False
    sync_state_to_widget("_selected_llm", "selected_llm")
    st.selectbox(
        "KI-Modell",
        options=list(llm_map.keys()),
        on_change=sync_widget_to_state,
        args=("_selected_llm", "selected_llm"),
        key="_selected_llm",
    )

    sync_state_to_widget("_prompt_template", "prompt_template")
    st.text_area(
        "Prompt",
        height=500,
        on_change=sync_widget_to_state,
        args=("_prompt_template", "prompt_template"),
        key="_prompt_template",
    )

    sync_state_to_widget("_temperature", "temperature")
    st.slider(
        "Temperatur",
        0.0,
        0.5,
        step=0.1,
        on_change=sync_widget_to_state,
        args=("_temperature", "temperature"),
        key="_temperature",
    )

    st.button("Beschreibung mit KI generieren", on_click=generate_description, type="primary")
    st.button("⬅ Zurück", on_click=set_step, args=(2,))

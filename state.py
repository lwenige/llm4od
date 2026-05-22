import streamlit as st


def set_step(step):
    st.session_state.step = step


def step1_complete():
    return st.session_state.df is not None


def step2_complete():
    return st.session_state['title'] is not None and st.session_state['publisher'] is not None


def init_state():
    defaults = {
        "step": 1,

        "df": None,

        # persistent values
        "title": "",
        "publisher": None,
        "license": None,
        "availability": None,
        "time_from": None,
        "time_till": None,

        # widget values
        "_title": "",
        "_publisher": None,
        "_license": None,
        "_availability": None,
        "_time_from": None,
        "_time_till": None,

        "places": [None],
        "place_keys": [None],

        "district_lookup": {},

        "generated_description": "",
        "generated_themes": [],
        "generated_keywords": [],

        "description": "",
        "_description": "",

        "csvw_columns": {},
        "csvw_metadata": None,

        "dataset": None,

        "temperature": 0.4,
        "selected_llm": "GPT-5-mini",

        "_temperature": 0.4,
        "_selected_llm": "GPT-5-mini",
        "_prompt_template": "",

        "prompt_template": "",

        "export_zip": None,
    }

    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def sync_widget_to_state(widget_key: str, state_key: str):
    st.session_state[state_key] = st.session_state[widget_key]


def sync_state_to_widget(widget_key: str, state_key: str):
    #if widget_key not in st.session_state:
    st.session_state[widget_key] = st.session_state[state_key]
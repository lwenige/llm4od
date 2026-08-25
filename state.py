import streamlit as st

import config
from models.dataset import Dataset
from services.csvw import create_csvw_metadata
from services.resources import load_metadata_prompt

def invalidate_dependent_steps():
    st.session_state["step3_completed"] = False
    st.session_state["step4_completed"] = False

    # Remove results generated from the previous metadata.
    st.session_state["rdf_turtle"] = None
    st.session_state["validation_report"] = None
    st.session_state["validation_error"] = None
    st.session_state["fair_score"] = None
    st.session_state["export_zip"] = None

def set_step(step):
    st.session_state.step = step

def create_dataset():
    dataset = Dataset({
        "title": st.session_state["title"],
        "publisher": config.city_map[st.session_state["publisher"]],
        "publisher_name": st.session_state["publisher"],
        # "license": st.session_state["license"]
    })

    for place_key in st.session_state["place_keys"]:
        if place_key is not None:
            dataset.add_place(place_key)

    availability = st.session_state.get("availability")

    if availability and availability in config.availability_map:
        dataset.add_availability(
            config.availability_map[availability]
        )

    time_from = st.session_state.get("time_from")
    time_till = st.session_state.get("time_till")

    if time_from or time_till:
        dataset.add_temporal_coverage(
            start_date=time_from,
            end_date=time_till,
        )

    st.session_state["dataset"] = dataset


def update_dataset():
    st.session_state["dataset"].add_distribution(
        {
            "license": st.session_state["license"]
        })


    csvw_filename = st.session_state["dataset"].dataset_id + ".csv-metadata.json"
    csvw_uri = f"https://example.org/{csvw_filename}"

    st.session_state["csvw_metadata"] = create_csvw_metadata(
        df=st.session_state.df,
        csvw_columns=st.session_state["csvw_columns"],
        csv_url=st.session_state["dataset"].dataset_id + ".csv",
    )
    st.session_state["dataset"].add_conforms_to(csvw_uri)

#def go_to_step2():
    #create_dataset()
    #set_step(2)

#def go_to_step3():
    #update_dataset()
#    set_step(3)

def step1_complete():
    #return st.session_state.df is not None
    #return st.session_state['title'] is not None and st.session_state['publisher'] is not None
    title = (st.session_state.get("title") or "").strip()
    publisher = (st.session_state.get("publisher") or "").strip()

    return bool(title) and bool(publisher)

def step2_complete():
    #return st.session_state['title'] is not None and st.session_state['publisher'] is not None
    #return st.session_state.df is not None and st.session_state['license'] is not None
    title = (st.session_state.get("title") or "").strip()
    publisher = (st.session_state.get("publisher") or "").strip()
    license = (st.session_state.get("license") or "").strip()

    return bool(license) and bool(title) and bool(publisher)

def step3_complete():
    return st.session_state.get("step3_completed", False)

def step4_complete():
    return st.session_state.get("step4_completed", False)



def init_state():
    metadata_prompt = load_metadata_prompt()
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
        "dist_title": None,

        # widget values
        "_title": "",
        "_publisher": None,
        "_license": None,
        "_availability": None,
        "_time_from": None,
        "_time_till": None,
        "_dist_title": None,

        "places": [None],
        "place_keys": [None],

        "district_lookup": {},

        #"generated_description": "",
        "generated_themes": [],
        #"generated_keywords": [],

        "description": "",
        "_description": "",

        "csvw_columns": {},
        "csvw_metadata": None,

        "dataset": None,

        "temperature": 0.0,
        "selected_llm": "GPT-5-mini",

        "_temperature": 0.0,
        "_selected_llm": "GPT-5-mini",
        "_prompt_template": metadata_prompt,

        "prompt_template": metadata_prompt,

        "description": "",
        "keywords": [],
        "themes": [],

        "export_zip": None,
        "step3_completed": False,
        "steop4_completed": False,

        "rdf_turtle": None,
        "validation_report": None,
        "validation_error": None,
        "step5_completed":  False,

        "fair_score": None
    }

    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def sync_widget_to_state(widget_key: str, state_key: str):
    st.session_state[state_key] = st.session_state[widget_key]


def sync_state_to_widget(widget_key: str, state_key: str):
    #if widget_key not in st.session_state:
    st.session_state[widget_key] = st.session_state[state_key]

def sync_widget_to_state_and_invalidate(
    widget_key: str,
    state_key: str,
) -> None:
    sync_widget_to_state(widget_key, state_key)
    invalidate_dependent_steps()
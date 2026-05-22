from tantivy import SchemaBuilder, Index
import streamlit as st

@st.cache_resource
def create_district_index(index_path="districts"):
    schema_builder = SchemaBuilder()

    schema_builder.add_text_field(
        "district_name",
        stored=True,
        tokenizer_name="default"
    )

    schema_builder.add_integer_field(
        "district_id",
        stored=True,
        indexed=True
    )

    schema_builder.add_integer_field(
        "district_key",
        stored=True,
        fast=True
    )

    schema = schema_builder.build()

    return Index(schema, path=str(index_path))


def search_places(index, query: str, limit: int = 10) -> tuple[list[str], dict]:
    results = []
    place_lookup = {}

    searcher = index.searcher()
    q = index.parse_query(query, ["district_name"])
    hits = searcher.search(q, limit).hits

    for score, addr in hits:
        hit = searcher.doc(addr)

        place_name = hit["district_name"][0]
        place_key = hit["district_key"][0]

        results.append(place_name)
        place_lookup[place_name] = place_key

    return results, place_lookup
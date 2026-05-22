from rdflib import Graph
from rdflib.namespace import RDF, SKOS


def load_license_map():
    g = Graph()
    g.parse("rdf/licenses.rdf")

    license_map = {}

    for s in g.subjects(RDF.type, SKOS.Concept):
        label = g.value(subject=s, predicate=SKOS.prefLabel)

        if label:
            license_map[str(label)] = str(s)

    return license_map


def load_editor_prompt():
    with open(
        "system_messages/text_prompt.txt",
        "r",
        encoding="utf-8"
    ) as f:
        return f.read()


def load_metadata_prompt():
    with open(
        "system_messages/metadata_prompt.txt",
        "r",
        encoding="utf-8"
    ) as f:
        return f.read()
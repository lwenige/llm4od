from pathlib import Path

from rdflib import Graph
from rdflib.namespace import RDF, SKOS

BASE_DIR = Path(__file__).resolve().parent.parent
SYSTEM_MESSAGES = BASE_DIR / "system_messages"

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
    return (SYSTEM_MESSAGES / "text_prompt.txt").read_text(encoding="utf-8")


def load_metadata_prompt():
    return (SYSTEM_MESSAGES / "metadata_prompt.txt").read_text(encoding="utf-8")


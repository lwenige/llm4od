import os
import pathlib
from tantivy import Document, Index, Query, SchemaBuilder
import rdflib
from rdflib.namespace import RDF, SKOS


schema_builder = SchemaBuilder()
schema_builder.add_text_field("district_name", stored=True, tokenizer_name='default')

# Integer-Felder
schema_builder.add_integer_field("district_id", stored=True, indexed=True)
schema_builder.add_integer_field("district_key", stored=True, fast=True)

# Schema finalisieren
schema = schema_builder.build()

# 2) Index-Verzeichnis erstellen und Writer initialisieren.
index_path = "../districts"  # Relativer Pfad für das Index-Verzeichnis
if not os.path.exists(index_path):
    os.makedirs(index_path)
    print(f"Der {index_path}-Ordner wurde angelegt.")
else:
    print(f"Ordner {index_path} existiert bereits.")

index_path = pathlib.Path(index_path)
index = Index(schema, path=str(index_path))
writer = index.writer()
g = rdflib.Graph()
g.parse("districts.rdf", format="xml")
for subj in g.subjects(RDF.type, SKOS.Concept):
    doc = Document()
    #print(subj.toPython())
    pref_labels = list(g.objects(subj, SKOS.prefLabel))
    for pref_label in pref_labels:
        key = int(pref_label.toPython())
        print(key)
        doc.add_integer("district_id", key)
        doc.add_integer("district_key", key)
    alt_labels = list(g.objects(subj, SKOS.altLabel))
    for alt_label in alt_labels:
        name = str(alt_label.toPython())
        print(name)
        doc.add_text("district_name", name)
    writer.add_document(doc)
  # Writer für Batch-Schreibvorgänge
writer.commit()             # Schreibvorgänge bestätigen
writer.wait_merging_threads()   # Hintergrund-Mergeprozesse abwarten


from datetime import date
from uuid import uuid4

from rdflib import Graph, Literal, Namespace, URIRef, XSD, BNode
from rdflib.namespace import RDF, DCTERMS


DCAT = Namespace("http://www.w3.org/ns/dcat#")
DCATAP = Namespace("http://data.europa.eu/r5r/")
EX = Namespace("https://example.org/")

DCATDE = Namespace("http://dcat-ap.de/def/dcatde/")
POLITICAL_GEOCODING = Namespace("http://dcat-ap.de/def/politicalGeocoding/")
DISTRICT_KEY = Namespace("http://dcat-ap.de/def/politicalGeocoding/districtKey/")
LANGUAGE = Namespace("http://publications.europa.eu/resource/authority/language/")

class Dataset:
    def __init__(self, meta: dict):
        self.graph = Graph()

        self.dataset_id = str(uuid4())
        self.distribution_id = str(uuid4())

        self.dataset = EX[f"dataset/{self.dataset_id}"]
        self.distribution = EX[f"distribution/{self.distribution_id}"]

        self._bind_namespaces()
        self._create_base_dataset(meta)
        self._create_distribution(meta)

    def _bind_namespaces(self):
        self.graph.bind("rdf", RDF)
        self.graph.bind("dct", DCTERMS)
        self.graph.bind("dcat", DCAT)
        self.graph.bind("dcatap", DCATAP)
        self.graph.bind("ex", EX)
        self.graph.bind("dcatde", DCATDE)
        self.graph.bind("pg", POLITICAL_GEOCODING)
        self.graph.bind("district", DISTRICT_KEY)
        self.graph.bind("lang", LANGUAGE)

    def _create_base_dataset(self, meta: dict):
        self.graph.add((self.dataset, RDF.type, DCAT.Dataset))
        self.graph.add((self.dataset, DCTERMS.identifier, Literal(self.dataset_id)))
        self.graph.add((self.dataset, DCTERMS.issued, Literal(date.today().isoformat(), datatype=XSD.date)))
        self.graph.add((self.dataset, DCTERMS.language, LANGUAGE.DEU))
        self.graph.add((self.dataset, DCTERMS.title, Literal(meta["title"])))
        self.graph.add((self.dataset, DCTERMS.publisher, URIRef(meta["publisher"])))

        place_keys = [
            place_key
            for place_key in meta.get("place_keys", [])
            if place_key
        ]

        if place_keys:

            self.graph.add((
                self.dataset,
                DCATDE.politicalGeocodingLevelURI,
                POLITICAL_GEOCODING.districtKey
            ))

            for place_key in place_keys:
                self.add_place(place_key)

    def _create_distribution(self, meta: dict):
        self.graph.add((self.dataset, DCAT.distribution, self.distribution))
        self.graph.add((self.distribution, RDF.type, DCAT.Distribution))
        self.graph.add((self.distribution, DCTERMS.identifier, Literal(self.distribution_id)))

    def add_theme(self, theme_uri):
        self.graph.add((
            self.dataset,
            DCAT.theme,
            URIRef(theme_uri)
        ))

    def add_availability(self, availability_uri):
        if availability_uri:
            self.graph.add((self.dataset, DCATAP.availabilty, URIRef(availability_uri)))

    def add_license(self, license_uri):
        if license_uri:
            self.graph.add((self.dataset, DCTERMS.license, URIRef(license_uri)))

    def add_keyword(self, keyword: str):
        self.graph.add((
            self.dataset,
            DCAT.keyword,
            Literal(keyword, lang="de")
        ))

    def add_keywords(self, keywords: list[str]):
        for keyword in keywords:
            self.add_keyword(keyword)

    def add_place(self, place_key):
        self.graph.add((
            self.dataset,
            DCTERMS.spatial,
            DISTRICT_KEY[str(place_key)]
        ))

        self.graph.add((
            self.dataset,
            DCATDE.politicalGeocodingURI,
            DISTRICT_KEY[str(place_key)]
        ))

    def add_description(self, description: str):
        self.graph.add((
                self.dataset,
                DCTERMS.description,
                Literal(description, lang="de")
        ))

    def add_conforms_to(self, uri: str):
        self.graph.add((
            self.distribution,
            DCTERMS.conformsTo,
            URIRef(uri)
        ))

    def add_temporal_coverage(self, start_date=None, end_date=None):
        if not start_date and not end_date:
            return

        temporal = BNode()

        self.graph.add((self.dataset, DCTERMS.temporal, temporal))
        self.graph.add((temporal, RDF.type, DCTERMS.PeriodOfTime))

        if start_date:
            self.graph.add((
                temporal,
                DCAT.startDate,
                Literal(str(start_date), datatype=XSD.date)
            ))

        if end_date:
            self.graph.add((
                temporal,
                DCAT.endDate,
                Literal(str(end_date), datatype=XSD.date)
            ))

    def serialize(self, format="turtle"):
        return self.graph.serialize(format=format)
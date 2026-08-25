from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

from rdflib import Graph, URIRef
from rdflib.namespace import DCTERMS, RDF, RDFS, XSD, Namespace

import config
from rdflib.namespace import DCAT

DCAT = Namespace("http://www.w3.org/ns/dcat#")
DCATAP = Namespace("http://data.europa.eu/r5r/")

@dataclass
class FairCheck:
    id: str
    category: str
    title: str
    passed: bool
    weight: float
    message: str
    recommendation: str | None = None


@dataclass
class FairScoreResult:
    total_score: float
    category_scores: dict[str, float]
    checks: list[FairCheck]

    def to_dict(self) -> dict[str, Any]:
        return {
            "total_score": self.total_score,
            "category_scores": self.category_scores,
            "checks": [asdict(check) for check in self.checks],
        }


def _has_any(graph: Graph, subject: URIRef, predicates: list[URIRef]) -> bool:
    return any(any(graph.objects(subject, predicate)) for predicate in predicates)


def _objects(graph: Graph, subject: URIRef, predicates: list[URIRef]) -> list[Any]:
    values: list[Any] = []
    for predicate in predicates:
        values.extend(list(graph.objects(subject, predicate)))
    return values


def _is_http_uri(value: Any) -> bool:
    return isinstance(value, URIRef) and str(value).startswith(("http://", "https://"))


def _dataset_subjects(graph: Graph) -> list[URIRef]:
    return [
        subject
        for subject in graph.subjects(RDF.type, DCAT.Dataset)
        if isinstance(subject, URIRef)
    ]


def _distribution_subjects(graph: Graph, dataset: URIRef) -> list[Any]:
    return list(graph.objects(dataset, DCAT.distribution))


def _add_check(
    checks: list[FairCheck],
    *,
    check_id: str,
    category: str,
    title: str,
    passed: bool,
    weight: float,
    success_message: str,
    failure_message: str,
    recommendation: str | None = None,
) -> None:
    checks.append(
        FairCheck(
            id=check_id,
            category=category,
            title=title,
            passed=passed,
            weight=weight,
            message=success_message if passed else failure_message,
            recommendation=None if passed else recommendation,
        )
    )


#def calculate_fair_score(rdf_turtle: str) -> FairScoreResult:

def calculate_fair_score(
    rdf_turtle: str,
    df=None,
    csvw_columns: dict | None = None,
) -> FairScoreResult:
    """
    Calculate a transparent, pre-publication FAIR readiness score for DCAT RDF.

    This is not an official FAIR certification. It is intended as an early,
    local quality indicator before a dataset is published.
    """
    graph = Graph()

    try:
        graph.parse(data=rdf_turtle, format="turtle")
    except Exception as exc:
        failed = FairCheck(
            id="I1-RDF",
            category="Interoperable",
            title="Gültiges RDF",
            passed=False,
            weight=10.0,
            message=f"Das Turtle-Dokument konnte nicht geparst werden: {exc}",
            recommendation="Turtle-Syntax korrigieren, bevor weitere FAIR-Prüfungen erfolgen.",
        )
        return FairScoreResult(
            total_score=0.0,
            category_scores={
                "Findable": 0.0,
                "Accessible": 0.0,
                "Interoperable": 0.0,
                "Reusable": 0.0,
            },
            checks=[failed],
        )

    datasets = _dataset_subjects(graph)
    checks: list[FairCheck] = []

    if not datasets:
        failed = FairCheck(
            id="F-DATASET",
            category="Findable",
            title="DCAT-Datensatz vorhanden",
            passed=False,
            weight=10.0,
            message="Im RDF wurde keine Ressource vom Typ dcat:Dataset gefunden.",
            recommendation="Eine Ressource mit rdf:type dcat:Dataset erzeugen.",
        )
        return FairScoreResult(
            total_score=0.0,
            category_scores={
                "Findable": 0.0,
                "Accessible": 0.0,
                "Interoperable": 0.0,
                "Reusable": 0.0,
            },
            checks=[failed],
        )

    dataset = datasets[0]
    distributions = _distribution_subjects(graph, dataset)

    # Findable
    _add_check(
        checks,
        check_id="F1",
        category="Findable",
        title="Global eindeutige Datensatz-URI",
        passed=_is_http_uri(dataset),
        weight=5.0,
        success_message="Der Datensatz besitzt eine HTTP(S)-URI.",
        failure_message="Der Datensatz besitzt keine HTTP(S)-URI.",
        recommendation="Für den Datensatz eine dauerhaft nutzbare HTTP(S)-URI vergeben.",
    )

    titles = _objects(graph, dataset, [DCTERMS.title])
    _add_check(
        checks,
        check_id="F2-title",
        category="Findable",
        title="Titel",
        passed=bool(titles),
        weight=4.0,
        success_message="Ein maschinenlesbarer Titel ist vorhanden.",
        failure_message="Es fehlt ein dct:title.",
        recommendation="Einen aussagekräftigen dct:title ergänzen.",
    )

    descriptions = _objects(graph, dataset, [DCTERMS.description])
    _add_check(
        checks,
        check_id="F2-description",
        category="Findable",
        title="Beschreibung",
        passed=bool(descriptions),
        weight=5.0,
        success_message="Eine Datensatzbeschreibung ist vorhanden.",
        failure_message="Es fehlt eine dct:description.",
        recommendation="Eine verständliche, inhaltlich konkrete Beschreibung ergänzen.",
    )

    keywords = _objects(graph, dataset, [DCAT.keyword])
    _add_check(
        checks,
        check_id="F2-keywords",
        category="Findable",
        title="Schlagwörter",
        passed=bool(keywords),
        weight=3.0,
        success_message="Mindestens ein Schlagwort ist vorhanden.",
        failure_message="Es sind keine dcat:keyword-Werte vorhanden.",
        recommendation="Mehrere präzise Suchbegriffe als dcat:keyword ergänzen.",
    )

    themes = _objects(graph, dataset, [DCAT.theme])
    _add_check(
        checks,
        check_id="F2-theme",
        category="Findable",
        title="Themenklassifikation",
        passed=bool(themes),
        weight=3.0,
        success_message="Der Datensatz ist mindestens einem Thema zugeordnet.",
        failure_message="Es fehlt eine dcat:theme-Zuordnung.",
        recommendation="Ein oder mehrere kontrollierte DCAT-Themen ergänzen.",
    )

    _add_check(
        checks,
        check_id="F3-distribution",
        category="Findable",
        title="Distribution beschrieben",
        passed=bool(distributions),
        weight=5.0,
        success_message="Mindestens eine Distribution ist beschrieben.",
        failure_message="Es ist keine dcat:distribution verknüpft.",
        recommendation="Mindestens eine Distribution mit Format und Zugriffsangabe beschreiben.",
    )

    # Accessible
    access_urls: list[Any] = []
    download_urls: list[Any] = []
    for distribution in distributions:
        access_urls.extend(_objects(graph, distribution, [DCAT.accessURL]))
        download_urls.extend(_objects(graph, distribution, [DCAT.downloadURL]))

    _add_check(
        checks,
        check_id="A1-access",
        category="Accessible",
        title="Zugriffs- oder Download-URL",
        passed=any(_is_http_uri(value) for value in access_urls + download_urls),
        weight=7.0,
        success_message="Mindestens eine HTTP(S)-Zugriffs- oder Download-URL ist vorhanden.",
        failure_message="Es fehlt eine HTTP(S)-Zugriffs- oder Download-URL.",
        recommendation=(
            "Vor Veröffentlichung eine stabile dcat:accessURL oder "
            "dcat:downloadURL für mindestens eine Distribution ergänzen."
        ),
    )

    formats: list[Any] = []
    media_types: list[Any] = []
    for distribution in distributions:
        formats.extend(_objects(graph, distribution, [DCTERMS.format]))
        #media_types.extend(_objects(graph, distribution, [DCAT.mediaType]))

    _add_check(
        checks,
        check_id="A1-format",
        category="Accessible",
        title="Dateiformat oder Medientyp",
        passed=bool(formats or media_types),
        weight=4.0,
        success_message="Das Format oder der Medientyp einer Distribution ist angegeben.",
        failure_message="Es fehlt dct:format oder dcat:mediaType.",
        recommendation="Für jede Distribution Format oder MIME-Type ergänzen.",
    )

    availability_values = _objects(
        graph,
        dataset,
        [DCATAP.availability],
    )

    has_valid_availability = any(
        availability in config.availability_map.values()
        for availability in availability_values
    )

    _add_check(
        checks,
        check_id="A1-availability",
        category="Accessible",
        title="Verfügbarkeit",
        passed=has_valid_availability,
        weight=3.0,
        success_message="Eine gültige Verfügbarkeitsangabe ist am Datensatz vorhanden.",
        failure_message=(
            "Es fehlt eine gültige Verfügbarkeitsangabe am Datensatz "
            "oder der verwendete Wert gehört nicht zum "
            "DCAT-AP.de Planned Availability Vocabulary."
        ),
        recommendation=(
            "Am Datensatz dcat:availability mit einem Wert aus dem "
            "DCAT-AP.de Planned Availability Vocabulary angeben, zum Beispiel "
            "<https://www.dcat-ap.de/def/plannedAvailability/1_0#experimental>."
        ),
    )

    # Interoperable
    # CSV konnte im vorherigen Verarbeitungsschritt
    # strukturiert eingelesen werden.
    _add_check(
        checks,
        check_id="I1-csv",
        category="Interoperable",
        title="Maschinenlesbare Tabellendaten",
        passed=df is not None,
        weight=6.0,
        success_message=(
            "Die CSV-Datei konnte strukturiert eingelesen und "
            "maschinenlesbar verarbeitet werden."
        ),
        failure_message="Die CSV-Datei konnte nicht verarbeitet werden.",
        recommendation="Eine valide und maschinenlesbare CSV-Datei bereitstellen.",
    )

    has_csvw = bool(csvw_columns)

    _add_check(
        checks,
        check_id="I3-csvw",
        category="Interoperable",
        title="Maschinenlesbare Tabellenbeschreibung",
        passed=has_csvw,
        weight=6.0,
        success_message=(
            "Die Struktur der CSV-Datei ist mit CSVW "
            "maschinenlesbar beschrieben."
        ),
        failure_message=(
            "Für die CSV-Datei liegt keine CSVW-Beschreibung vor."
        ),
        recommendation=(
            "Eine CSVW-Beschreibung mit Spalten und Datentypen ergänzen."
        ),
    )

    _add_check(
        checks,
        check_id="I1-rdf",
        category="Interoperable",
        title="Gültiges RDF",
        passed=True,
        weight=8.0,
        success_message="Das Turtle-Dokument ist syntaktisch gültiges RDF.",
        failure_message="Das RDF ist ungültig.",
    )

    controlled_theme = any(_is_http_uri(value) for value in themes)
    _add_check(
        checks,
        check_id="I2-theme-vocabulary",
        category="Interoperable",
        title="Kontrolliertes Themenvokabular",
        passed=controlled_theme,
        weight=4.0,
        success_message="Themen werden über URI-Ressourcen referenziert.",
        failure_message="Die Themen sind nicht als URI-Ressourcen angegeben.",
        recommendation="Themen als URIs aus einem kontrollierten Vokabular verwenden.",
    )

    licenses = _objects(graph, dataset, [DCTERMS.license])
    for distribution in distributions:
        licenses.extend(_objects(graph, distribution, [DCTERMS.license]))

    # controlled_license = any(_is_http_uri(value) for value in licenses)
    # _add_check(
    #     checks,
    #     check_id="I2-license-vocabulary",
    #     category="Interoperable",
    #     title="Maschinenlesbare Lizenz-URI",
    #     passed=controlled_license,
    #     weight=4.0,
    #     success_message="Die Lizenz wird über eine URI referenziert.",
    #     failure_message="Es wurde keine maschinenlesbare Lizenz-URI gefunden.",
    #     recommendation="Eine Lizenz als URI aus einem etablierten Lizenzvokabular angeben.",
    # )

    conforms_to = _objects(graph, dataset, [DCTERMS.conformsTo])
    _add_check(
        checks,
        check_id="I3-conforms-to",
        category="Interoperable",
        title="Konformitätsangabe",
        passed=bool(conforms_to),
        weight=4.0,
        success_message="Mindestens eine dct:conformsTo-Angabe ist vorhanden.",
        failure_message="Es fehlt eine dct:conformsTo-Angabe.",
        recommendation="Das verwendete Metadaten- oder Datenprofil als dct:conformsTo ergänzen.",
    )

    # Reusable
    csvw_columns = csvw_columns or {}

    all_columns_described = (
        bool(csvw_columns)
        and all(
            meta.get("description", "").strip()
            for meta in csvw_columns.values()
        )
    )

    _add_check(
        checks,
        check_id="R1-csvw-description",
        category="Reusable",
        title="Spalten beschrieben",
        passed=all_columns_described,
        weight=4.0,
        success_message=(
            "Alle Spalten der CSV-Datei sind in CSVW beschrieben."
        ),
        failure_message=(
            "Nicht alle Spalten der CSV-Datei besitzen eine Beschreibung."
        ),
        recommendation=(
            "Die Bedeutung der Spalten in der CSVW-Beschreibung ergänzen."
        ),
    )

    publishers = _objects(graph, dataset, [DCTERMS.publisher])
    _add_check(
        checks,
        check_id="R1-publisher",
        category="Reusable",
        title="Herausgebende Stelle",
        passed=bool(publishers),
        weight=5.0,
        success_message="Eine herausgebende Stelle ist angegeben.",
        failure_message="Es fehlt dct:publisher.",
        recommendation="Die verantwortliche Organisation als dct:publisher ergänzen.",
    )

    _add_check(
        checks,
        check_id="R1-license",
        category="Reusable",
        title="Nutzungslizenz",
        passed=bool(licenses),
        weight=7.0,
        success_message="Eine Nutzungslizenz ist angegeben.",
        failure_message="Es fehlt eine Nutzungslizenz.",
        recommendation="Eine klare, maschinenlesbare Lizenz ergänzen.",
    )

    issued = _objects(graph, dataset, [DCTERMS.issued])
    modified = _objects(graph, dataset, [DCTERMS.modified])
    _add_check(
        checks,
        check_id="R1-dates",
        category="Reusable",
        title="Veröffentlichungs- oder Änderungsdatum",
        passed=bool(issued or modified),
        weight=3.0,
        success_message="Ein Veröffentlichungs- oder Änderungsdatum ist vorhanden.",
        failure_message="Es fehlt dct:issued oder dct:modified.",
        recommendation="Mindestens ein Veröffentlichungs- oder Änderungsdatum ergänzen.",
    )

    temporal = _objects(graph, dataset, [DCTERMS.temporal])
    _add_check(
        checks,
        check_id="R1-temporal",
        category="Reusable",
        title="Zeitliche Abdeckung",
        passed=bool(temporal),
        weight=3.0,
        success_message="Die zeitliche Abdeckung ist beschrieben.",
        failure_message="Es fehlt eine zeitliche Abdeckung.",
        recommendation="Bei zeitbezogenen Daten dct:temporal ergänzen.",
    )

    spatial = _objects(graph, dataset, [DCTERMS.spatial])
    _add_check(
        checks,
        check_id="R1-spatial",
        category="Reusable",
        title="Räumliche Abdeckung",
        passed=bool(spatial),
        weight=3.0,
        success_message="Die räumliche Abdeckung ist beschrieben.",
        failure_message="Es fehlt eine räumliche Abdeckung.",
        recommendation="Bei raumbezogenen Daten dct:spatial ergänzen.",
    )

    contact_points = _objects(graph, dataset, [DCAT.contactPoint])
    _add_check(
        checks,
        check_id="R1-contact",
        category="Reusable",
        title="Kontaktstelle",
        passed=bool(contact_points),
        weight=3.0,
        success_message="Eine Kontaktstelle ist angegeben.",
        failure_message="Es fehlt dcat:contactPoint.",
        recommendation="Eine zuständige Kontaktstelle ergänzen.",
    )

    category_scores: dict[str, float] = {}
    categories = ("Findable", "Accessible", "Interoperable", "Reusable")

    for category in categories:
        category_checks = [check for check in checks if check.category == category]
        maximum = sum(check.weight for check in category_checks)
        achieved = sum(check.weight for check in category_checks if check.passed)
        category_scores[category] = round(
            (achieved / maximum * 100.0) if maximum else 0.0,
            1,
        )

    total_maximum = sum(check.weight for check in checks)
    total_achieved = sum(check.weight for check in checks if check.passed)

    return FairScoreResult(
        total_score=round(
            (total_achieved / total_maximum * 100.0) if total_maximum else 0.0,
            1,
        ),
        category_scores=category_scores,
        checks=checks,
    )

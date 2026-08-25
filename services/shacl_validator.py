from typing import Any

import requests


ITB_BASE_URL = "https://www.itb.ec.europa.eu/shacl"
ITB_DOMAIN = "dcat-ap.de"

REQUEST_TIMEOUT_SECONDS = 60


class ShaclValidationError(RuntimeError):
    """Fehler bei der Kommunikation mit dem SHACL-Validator."""


def get_validation_types() -> list[dict[str, str]]:
    """
    Ruft die verfügbaren Validierungsprofile des DCAT-AP.de-Validators ab.
    """

    url = f"{ITB_BASE_URL}/{ITB_DOMAIN}/api/info"

    try:
        response = requests.get(
            url,
            timeout=REQUEST_TIMEOUT_SECONDS,
        )
        response.raise_for_status()
    except requests.RequestException as exc:
        raise ShaclValidationError(
            "Die verfügbaren SHACL-Validierungsprofile konnten "
            "nicht vom ITB-Testbed geladen werden."
        ) from exc

    try:
        payload = response.json()
    except ValueError as exc:
        raise ShaclValidationError(
            "Das ITB-Testbed hat keine gültige JSON-Antwort geliefert."
        ) from exc

    validation_types = payload.get("validationTypes", [])

    if not isinstance(validation_types, list):
        return []

    return validation_types


def get_default_validation_type() -> str | None:
    """
    Ermittelt automatisch das erste verfügbare Validierungsprofil.

    Dadurch muss kein Profilname fest im Code hinterlegt werden.
    """

    validation_types = get_validation_types()

    if not validation_types:
        return None

    first_type = validation_types[0]

    if not isinstance(first_type, dict):
        return None

    return first_type.get("type")


def validate_dcat_ap_de(
    rdf_turtle: str,
    validation_type: str | None = None,
) -> dict[str, Any]:
    """
    Validiert Turtle-RDF über das ITB-Testbed für DCAT-AP.de.

    Gibt den JSON-Bericht des Validators zurück.
    """

    if not rdf_turtle or not rdf_turtle.strip():
        raise ShaclValidationError(
            "Es wurde kein DCAT-Turtle-Inhalt zur Validierung übergeben."
        )

    if validation_type is None:
        validation_type = get_default_validation_type()

    payload: dict[str, Any] = {
        "contentToValidate": rdf_turtle,
        "contentSyntax": "text/turtle",
        "embeddingMethod": "STRING",
        "reportSyntax": "application/json",
        "locale": "de",
        "addInputToReport": False,
        "addShapesToReport": False,
    }

    if validation_type:
        payload["validationType"] = validation_type

    url = f"{ITB_BASE_URL}/{ITB_DOMAIN}/api/validate"

    try:
        response = requests.post(
            url,
            json=payload,
            headers={
                "Accept": "application/json",
                "Content-Type": "application/json",
            },
            timeout=REQUEST_TIMEOUT_SECONDS,
        )
        response.raise_for_status()
    except requests.Timeout as exc:
        raise ShaclValidationError(
            "Die SHACL-Validierung hat das Zeitlimit überschritten."
        ) from exc
    except requests.RequestException as exc:
        response_text = ""

        if getattr(exc, "response", None) is not None:
            response_text = exc.response.text[:1000]

        message = (
            "Das DCAT konnte nicht durch das ITB-Testbed "
            "validiert werden."
        )

        if response_text:
            message += f"\n\nAntwort des Testbeds:\n{response_text}"

        raise ShaclValidationError(message) from exc

    try:
        return response.json()
    except ValueError as exc:
        raise ShaclValidationError(
            "Das ITB-Testbed hat keinen gültigen JSON-Bericht geliefert."
        ) from exc


def normalize_report_entries(
    validation_report: dict[str, Any],
    report_type: str,
) -> list[dict[str, str]]:
    """
    Normalisiert Fehler, Warnungen oder Hinweise aus dem GITB-Bericht.

    report_type:
        - error
        - warning
        - info
    """

    reports = validation_report.get("reports", {})

    if not isinstance(reports, dict):
        return []

    entries = reports.get(report_type, [])

    if entries is None:
        return []

    if isinstance(entries, dict):
        entries = [entries]

    if not isinstance(entries, list):
        return []

    normalized_entries: list[dict[str, str]] = []

    for entry in entries:
        if not isinstance(entry, dict):
            normalized_entries.append({
                "description": str(entry),
                "location": "",
                "test": "",
            })
            continue

        normalized_entries.append({
            "description": str(
                entry.get("description", "Keine Beschreibung vorhanden")
            ),
            "location": str(entry.get("location", "")),
            "test": str(entry.get("test", "")),
        })

    return normalized_entries
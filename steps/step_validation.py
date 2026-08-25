import streamlit as st

from config import availability_map, theme_map
from services.csvw import create_csvw_metadata
from services.fair_scoring import calculate_fair_score
from services.shacl_validator import (
    ShaclValidationError,
    normalize_report_entries,
    validate_dcat_ap_de,
)
from services.zip import create_export_zip
from state import set_step, update_dataset, create_dataset


def reset_validation_state(error_message: str | None = None) -> None:
    """Setzt die Ergebnisse der Validierung zurück."""
    st.session_state["validation_report"] = None
    st.session_state["validation_error"] = error_message
    st.session_state["fair_score"] = None
    st.session_state["step5_completed"] = False


def run_validation() -> None:
    """
    Erstellt die aktuellen Metadaten, erzeugt den Export und führt anschließend
    FAIR- sowie SHACL-Prüfung aus.

    Diese Funktion wird nicht automatisch beim Rendern von Schritt 5 ausgeführt.
    Sie muss ausdrücklich durch einen Button-Callback aufgerufen werden.
    """
    create_dataset()
    update_dataset()
    if st.session_state["dataset"] is None:
        reset_validation_state(
            "Es wurde kein aktueller Datensatz zur Validierung gefunden."
        )
        return

    st.session_state["dataset"].add_description(st.session_state["description"])

    for keyword in st.session_state["keywords"]:
        st.session_state["dataset"].add_keyword(keyword)

    print(st.session_state["themes"])
    for theme in st.session_state["themes"]:
        st.session_state["dataset"].add_theme(theme_map[theme])
    dataset = st.session_state.get("dataset")

    dataframe = st.session_state.get("df")

    if dataframe is None:
        reset_validation_state(
            "Es wurden keine Tabellendaten zur Validierung gefunden."
        )
        return

    try:

        rdf_turtle = dataset.serialize(format="turtle")

        if isinstance(rdf_turtle, bytes):
            rdf_turtle = rdf_turtle.decode("utf-8")

    except Exception as exc:
        reset_validation_state(
            "Der aktuelle Datensatz konnte nicht aktualisiert oder "
            f"serialisiert werden: {exc}"
        )
        return

    if not rdf_turtle.strip():
        reset_validation_state(
            "Der aktuelle Datensatz enthält keine DCAT-Metadaten."
        )
        return

    st.session_state["rdf_turtle"] = rdf_turtle

    try:
        st.session_state["export_zip"] = create_export_zip(
            dataset_id=dataset.dataset_id,
            rdf_turtle=rdf_turtle,
            csvw_json=st.session_state["csvw_metadata"],
        )
    except Exception as exc:
        reset_validation_state(
            f"Das ZIP-Archiv konnte nicht erstellt werden: {exc}"
        )
        return

    st.session_state["validation_report"] = None
    st.session_state["validation_error"] = None
    st.session_state["fair_score"] = None
    st.session_state["step5_completed"] = False

    try:
        # st.session_state["fair_score"] = calculate_fair_score(
        #     rdf_turtle
        # ).to_dict()
        st.session_state["fair_score"] = calculate_fair_score(
            rdf_turtle,
            df=st.session_state.get("df"),
            csvw_columns=st.session_state.get("csvw_columns"),
        ).to_dict()
    except Exception as exc:
        st.session_state["validation_error"] = (
            f"Der FAIR Readiness Score konnte nicht berechnet werden: {exc}"
        )
        return

    try:
        validation_report = validate_dcat_ap_de(rdf_turtle)

        st.session_state["validation_report"] = validation_report
        st.session_state["validation_error"] = None
        st.session_state["step5_completed"] = True

    except ShaclValidationError as exc:
        st.session_state["validation_report"] = None
        st.session_state["validation_error"] = str(exc)
        st.session_state["step5_completed"] = False


def render_report_entry(
    entry: dict[str, str],
    index: int,
    prefix: str,
) -> None:
    description = entry.get(
        "description",
        "Keine Beschreibung vorhanden",
    )
    location = entry.get("location", "")
    test = entry.get("test", "")

    with st.expander(f"{prefix} {index}: {description}"):
        st.markdown("**Beschreibung**")
        st.write(description)

        if location:
            st.markdown("**Position / betroffene Ressource**")
            st.code(location, language=None)

        if test:
            st.markdown("**SHACL-Test**")
            st.code(test, language=None)


def render_validation_result(validation_report: dict) -> None:
    result = validation_report.get("result", "UNKNOWN")
    counters = validation_report.get("counters", {})

    errors = normalize_report_entries(validation_report, "error")
    warnings = normalize_report_entries(validation_report, "warning")
    infos = normalize_report_entries(validation_report, "info")

    number_of_errors = counters.get("nrOfErrors", len(errors))
    number_of_warnings = counters.get(
        "nrOfWarnings",
        len(warnings),
    )
    number_of_assertions = counters.get(
        "nrOfAssertions",
        len(infos),
    )

    col_result, col_errors, col_warnings, col_infos = st.columns(4)

    col_result.metric("Ergebnis", result)
    col_errors.metric("Fehler", number_of_errors)
    col_warnings.metric("Warnungen", number_of_warnings)
    col_infos.metric("Hinweise", number_of_assertions)

    if result == "SUCCESS":
        st.success(
            "Die Metadaten haben die "
            "DCAT-AP.de-SHACL-Prüfung bestanden."
        )
    elif errors:
        st.error("Die Metadaten enthalten Fehler.")
    elif warnings:
        st.warning("Es wurden Warnungen gefunden.")
    else:
        st.info(
            f"Das ITB-Testbed meldet das Ergebnis „{result}“."
        )

    if errors:
        st.subheader("Fehler")

        for index, entry in enumerate(errors, start=1):
            render_report_entry(
                entry,
                index,
                "❌ Fehler",
            )

    if warnings:
        st.subheader("Warnungen")

        for index, entry in enumerate(warnings, start=1):
            render_report_entry(
                entry,
                index,
                "⚠️ Warnung",
            )

    if infos:
        st.subheader("Hinweise")

        for index, entry in enumerate(infos, start=1):
            render_report_entry(
                entry,
                index,
                "ℹ️ Hinweis",
            )

    with st.expander(
        "Technischen Validierungsbericht anzeigen"
    ):
        st.json(validation_report)


def render_fair_score(fair_score: dict) -> None:
    st.subheader("FAIR Readiness Score")

    st.caption(
        "Lokale Vorabprüfung für noch nicht veröffentlichte Datensätze. "
        "Der Wert ist keine offizielle FAIR-Zertifizierung."
    )

    total_score = float(
        fair_score.get("total_score", 0.0)
    )

    st.metric("Gesamtwert", f"{total_score:.1f} %")
    st.progress(
        min(
            max(total_score / 100.0, 0.0),
            1.0,
        )
    )

    category_scores = fair_score.get(
        "category_scores",
        {},
    )
    columns = st.columns(4)

    labels = [
        ("Findable", "Auffindbar"),
        ("Accessible", "Zugänglich"),
        ("Interoperable", "Interoperabel"),
        ("Reusable", "Nachnutzbar"),
    ]

    for column, (key, label) in zip(columns, labels):
        score = float(category_scores.get(key, 0.0))
        column.metric(label, f"{score:.1f} %")

    checks = fair_score.get("checks", [])

    failed_checks = [
        check
        for check in checks
        if not check.get("passed")
    ]

    passed_checks = [
        check
        for check in checks
        if check.get("passed")
    ]

    if failed_checks:
        st.markdown("#### Verbesserungspotenzial")

        for check in failed_checks:
            title = check.get("title", "Prüfung")
            category = check.get("category", "")
            message = check.get("message", "")
            recommendation = (
                check.get("recommendation")
                or message
            )

            with st.expander(
                f"⚠️ {category}: {title}"
            ):
                st.write(message)

                if recommendation:
                    st.markdown("**Empfehlung**")
                    st.write(recommendation)
    else:
        st.success(
            "Alle lokalen FAIR-Readiness-Prüfungen "
            "wurden erfüllt."
        )

    with st.expander(
        f"Erfüllte Prüfungen ({len(passed_checks)})"
    ):
        for check in passed_checks:
            st.markdown(
                f"- **{check.get('category', '')} – "
                f"{check.get('title', '')}:** "
                f"{check.get('message', '')}"
            )


def render_validation() -> None:
    st.header("Schritt 5: Metadatenqualität prüfen")

    st.markdown(
        "Die erzeugten DCAT-Metadaten wurden lokal auf FAIR Readiness "
        "und zusätzlich über das ITB-Testbed auf SHACL-Konformität geprüft."
    )

    # Keine automatische Validierung beim Öffnen von Schritt 5.
    # Die Prüfung wurde bereits durch den Button in Schritt 4 gestartet.
    st.divider()
    st.subheader("DCAT-AP.de SHACL-Prüfung")

    validation_error = st.session_state.get(
        "validation_error"
    )
    validation_report = st.session_state.get(
        "validation_report"
    )
    fair_score = st.session_state.get("fair_score")

    if validation_error:
        st.error(validation_error)

    if validation_report:
        render_validation_result(validation_report)
    elif not validation_error:
        st.info(
            "Es liegt noch kein Validierungsergebnis vor. "
            "Starten Sie die Prüfung über den Button "
            "„Metadaten prüfen“ in Schritt 4."
        )

    if st.button(
        "Validierung erneut ausführen",
        type="secondary",
    ):
        with st.spinner("Metadaten werden geprüft …"):
            run_validation()
        st.rerun()

    if fair_score:
        render_fair_score(fair_score)

    export_zip = st.session_state.get("export_zip")

    if export_zip:
        st.download_button(
            label="ZIP herunterladen",
            data=export_zip,
            file_name="metadata_export.zip",
            mime="application/zip",
            type="primary",
        )

    st.button(
        "⬅ Zurück",
        on_click=set_step,
        args=(4,),
    )
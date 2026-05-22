import io
import zipfile
import json

def create_export_zip(
    dataset_id: str,
    rdf_turtle: str,
    csvw_json: dict
) -> bytes:

    zip_buffer = io.BytesIO()

    with zipfile.ZipFile(
        zip_buffer,
        "w",
        zipfile.ZIP_DEFLATED
    ) as zip_file:

        zip_file.writestr(
            f"{dataset_id}.ttl",
            rdf_turtle
        )

        zip_file.writestr(
            f"{dataset_id}.csv-metadata.json",
            json.dumps(
                csvw_json,
                ensure_ascii=False,
                indent=2
            )
        )

    zip_buffer.seek(0)

    return zip_buffer.getvalue()
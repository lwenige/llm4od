import re
from typing import List

import pandas as pd


# header normalization
# - lowercase
# - spaces -> underscores
# - special chars removed
# - empty names -> col
# - duplicates -> suffix (_2, _3, ...)
def _normalize_header(header: List[str]) -> List[str]:
    out, seen = [], set()

    for h in header:
        # cleaned column name
        n = re.sub(
            r"[^0-9a-zA-Z_ ]",
            "",
            (h or "").strip()
        ).lower().replace(" ", "_") or "col"

        base, k = n, 1

        # duplicate handling
        while n in seen:
            k += 1
            n = f"{base}_{k}"

        seen.add(n)
        out.append(n)

    return out


def load_csv(source_path=None, uploaded_file=None):
    encodings = [
        "utf-8",
        "cp1252",
        "latin1",
        "iso-8859-1"
    ]

    last_error = None

    file_source = uploaded_file if uploaded_file else source_path

    for encoding in encodings:
        try:
            # important for Streamlit uploads
            if uploaded_file:
                uploaded_file.seek(0)

            df = pd.read_csv(
                file_source,
                sep=None,
                engine="python",
                encoding=encoding,
                encoding_errors="replace"
            )

            # normalize headers
            df.columns = _normalize_header(df.columns.tolist())

            print(f"CSV erfolgreich geladen mit Encoding: {encoding}")

            return df

        except Exception as e:
            last_error = e
            print(f"Encoding {encoding} fehlgeschlagen: {e}")

    raise ValueError(
        f"Datei konnte nicht gelesen werden.\n"
        f"Getestete Encodings: {encodings}\n"
        f"Letzter Fehler: {last_error}"
    )
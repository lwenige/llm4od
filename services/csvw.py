import json
import pandas as pd


CSVW_DATATYPES = [
    "xsd:string",
    "xsd:integer",
    "xsd:decimal",
    "xsd:double",
    "xsd:boolean",
    "xsd:date",
    "xsd:dateTime",
    "xsd:time",
    "xsd:anyURI",
]


def infer_csvw_datatype(series: pd.Series) -> str:
    s = series.dropna()

    if s.empty:
        return "xsd:string"

    # native pandas dtypes first
    if pd.api.types.is_bool_dtype(s):
        return "xsd:boolean"

    if pd.api.types.is_integer_dtype(s):
        return "xsd:integer"

    if pd.api.types.is_float_dtype(s):
        return "xsd:decimal"

    if pd.api.types.is_datetime64_any_dtype(s):
        return "xsd:dateTime"

    # string-based inference
    sample = s.astype(str).head(20)

    # integer
    try:
        sample.astype(int)
        return "xsd:integer"
    except:
        pass

    # decimal
    try:
        sample.astype(float)
        return "xsd:decimal"
    except:
        pass

    # boolean
    boolean_values = {
        "true", "false",
        "0", "1",
        "yes", "no",
        "ja", "nein"
    }

    if all(v.strip().lower() in boolean_values for v in sample):
        return "xsd:boolean"

    # datetime
    try:
        pd.to_datetime(sample)
        return "xsd:dateTime"
    except:
        pass

    return "xsd:string"

def create_csvw_metadata(df, csvw_columns, csv_url="data.csv"):
    columns = []

    for col in df.columns:
        meta = csvw_columns.get(col, {})

        column = {
            "name": col,
            "titles": col,
             "datatype": meta.get(
                "datatype"
            ) or infer_csvw_datatype(df[col]),
        }

        if meta.get("description"):
            column["description"] = meta["description"]

        if meta.get("required"):
            column["required"] = True

        if meta.get("minimum"):
            column["minimum"] = meta["minimum"]

        if meta.get("maximum"):
            column["maximum"] = meta["maximum"]

        if meta.get("pattern"):
            column["pattern"] = meta["pattern"]

        if meta.get("null"):
            column["null"] = [
                value.strip()
                for value in meta["null"].split(",")
                if value.strip()
            ]

        columns.append(column)

    return {
        "@context": [
            "http://www.w3.org/ns/csvw",
            {
                "xsd": "http://www.w3.org/2001/XMLSchema#"
            }
        ],
        "url": csv_url,
        "tableSchema": {
            "columns": columns
        }
    }


def csvw_to_json(csvw_metadata: dict) -> str:
    return json.dumps(csvw_metadata, ensure_ascii=False, indent=2)
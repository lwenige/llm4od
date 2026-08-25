def _check_missing_fields(required_fields: dict):
    missing = []

    for name, value in required_fields.items():
        if value is None:
            missing.append(name)
        elif isinstance(value, str) and value == "":
            missing.append(name)
        elif isinstance(value, dict) and not value:
            missing.append(name)  # {}
        elif isinstance(value, list) and not value:
            missing.append(name)  # []

    return missing


def step1_incomplete(title: str, publisher: str):
    required_fields = {
        "Titel": title,
        "Publisher": publisher,
    }

    return _check_missing_fields(required_fields)

def step2_incomplete(df: dict, license: str):
    required_fields = {
        "Daten": df,
        "Lizenz": license,
    }

    return _check_missing_fields(required_fields)

def step3_incomplete(description: str):
    required_fields = {
        "Description": description,
    }

    return _check_missing_fields(required_fields)

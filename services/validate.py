def _check_missing_fields(required_fields: dict):
    missing = [
        name
        for name, value in required_fields.items()
        if value in [None, "", []]
    ]

    return missing


def step2_incomplete(title: str, publisher: str):
    required_fields = {
        "Titel": title,
        "Publisher": publisher,
    }

    return _check_missing_fields(required_fields)

def step3_incomplete(description: str):
    required_fields = {
        "Description": description,
    }

    return _check_missing_fields(required_fields)

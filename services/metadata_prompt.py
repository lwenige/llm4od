import json


def build_metadata_prompt(
    editable_prompt: str,
    title: str,
    publisher: str,
    sample_data: str,
    themes: dict,
) -> str:

    allowed_themes = {
        str(uri): label
        for label, uri in themes.items()
    }

    return f"""
{editable_prompt}

ZULÄSSIGE THEMEN:

Es dürfen ausschließlich die folgenden Theme-URIs verwendet werden.

Gib ausschließlich die URI(s) zurück.
Keine Labels.
Keine erfundenen Werte.

{json.dumps(allowed_themes, ensure_ascii=False, indent=2)}

AUSGABEFORMAT:

Antworte ausschließlich als valides JSON.
Keine Markdown-Formatierung.
Keine Erklärung.
Keine zusätzlichen Texte.

Schema:

{{
  "description": "string",
  "themes": [
    "uri"
  ],
  "keywords": [
    "string"
  ]
}}

EINGABEDATEN:

Titel:
{title}

Publisher:
{publisher}

Tabellarische Beispieldaten:

{sample_data}
"""
import json

def build_metadata_prompt(
    editable_prompt: str,
    title: str,
    publisher: str,
    sample_data: str,
) -> str:
    return f"""
{editable_prompt}

AUSGABEFORMAT:

Antworte ausschließlich als valides JSON.
Keine Markdown-Formatierung.
Keine Erklärung.
Keine zusätzlichen Texte.

Schema:

{{
  "description": "string",
  "themes": ["string"],
  "keywords": ["string"]
}}

EINGABEDATEN:

Titel:
{title}

Publisher:
{publisher}

Tabellarische Beispieldaten:
{sample_data}
"""
import json
import requests
from langchain_core.messages import SystemMessage, HumanMessage
from langchain_openai import ChatOpenAI
from json_repair import repair_json

def parse_llm_json(text: str) -> dict:
    repaired = repair_json(text)
    return json.loads(repaired)

def generate_metadata_with_openrouter(
        prompt: str,
        model: str,
        api_key: str,
        temperature: float = 0.4,
) -> dict:
    llm = ChatOpenAI(
        model=model,  # e.g. "openai/gpt-4o-mini"
        api_key=api_key,
        base_url="https://openrouter.ai/api/v1",
        temperature=temperature,
        timeout=60,
    )
    messages = [
        SystemMessage(content="Return a single valid JSON object. No markdown, no extra text."),
        HumanMessage(content=prompt),
    ]
    response = llm.invoke(messages)
    repaired = repair_json(response.content)
    return json.loads(repaired)
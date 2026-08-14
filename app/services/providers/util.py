import json
import re
from typing import Any, cast

_FENCED_JSON = re.compile(r"```(?:json)?\s*(\{.*\})\s*```", re.DOTALL)


def extract_json_object(text: str) -> dict[str, Any]:
    """Pull a JSON object out of an LLM text response.

    Models sometimes wrap the JSON in markdown code fences or add stray
    text around it despite instructions not to - this recovers the object
    in both cases before falling back to a strict parse.
    """
    text = text.strip()
    fenced = _FENCED_JSON.search(text)
    if fenced:
        text = fenced.group(1)
    else:
        start = text.find("{")
        end = text.rfind("}")
        if start != -1 and end != -1 and end > start:
            text = text[start : end + 1]
    return cast(dict[str, Any], json.loads(text))

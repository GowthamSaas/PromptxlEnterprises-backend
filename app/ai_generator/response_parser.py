import json
from typing import Any

from .exceptions import InvalidGenerationResponseError


def parse_generation_response(raw_response: str) -> dict[str, Any]:
    if not raw_response:
        raise InvalidGenerationResponseError("Empty response from model")

    try:
        payload = json.loads(raw_response)
    except json.JSONDecodeError as exc:
        raise InvalidGenerationResponseError("Model response was not valid JSON") from exc

    if not isinstance(payload, dict):
        raise InvalidGenerationResponseError("Model response must be a JSON object")

    return payload

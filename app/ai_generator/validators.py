from typing import Any


def validate_generation_payload(payload: dict[str, Any]) -> None:
    if not payload.get("files"):
        raise ValueError("Generation response must include a files array")

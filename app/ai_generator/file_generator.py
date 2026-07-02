from typing import Any


def build_generated_files(payload: dict[str, Any]) -> list[dict[str, Any]]:
    files = payload.get("files", [])
    if not isinstance(files, list):
        return []

    generated_files = []
    for item in files:
        if isinstance(item, dict) and "path" in item and "content" in item:
            generated_files.append({
                "path": str(item["path"]),
                "content": str(item.get("content", "")),
            })
    return generated_files

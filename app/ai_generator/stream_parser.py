from typing import Any


def parse_stream_chunk(chunk: str) -> str:
    if not chunk:
        return ""
    return chunk.strip()


def merge_stream_chunks(chunks: list[str]) -> str:
    return "".join(parse_stream_chunk(chunk) for chunk in chunks if chunk)

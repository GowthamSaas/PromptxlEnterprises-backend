import json
import re
from typing import Any


class ResponseParser:
    """
    Responsible for parsing AI Modifier
    responses from different LLM providers.
    """

    def parse(
        self,
        response: Any,
    ) -> dict:

        if response is None:
            return {
                "message": "",
                "files": [],
            }

        # ----------------------------------
        # Extract Text
        # ----------------------------------

        if isinstance(response, dict):

            text = (
                response.get("text")
                or response.get("content")
                or response.get("message")
                or ""
            )

        elif isinstance(response, str):

            text = response

        else:

            text = str(response)

        # ----------------------------------
        # Remove Thinking Block
        # ----------------------------------

        text = re.sub(
            r"<think>.*?</think>",
            "",
            text,
            flags=re.DOTALL | re.IGNORECASE,
        ).strip()

        # ----------------------------------
        # Remove Markdown
        # ----------------------------------

        text = re.sub(
            r"^```json\s*|\s*```$",
            "",
            text,
            flags=re.MULTILINE,
        ).strip()

        # ----------------------------------
        # Parse JSON
        # ----------------------------------

        try:

            data = json.loads(text)

            return {
                "message": data.get(
                    "message",
                    "",
                ),
                "files": data.get(
                    "files",
                    [],
                ),
            }

        except Exception:

            return {
                "message": text,
                "files": [],
            }


response_parser = ResponseParser()
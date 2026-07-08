import json
import re
from typing import Any


class ResponseParser:
    """
    Responsible for parsing
    AI Chat responses from
    different LLM providers.
    """

    def parse(
        self,
        response: Any,
    ) -> str:

        if response is None:
            return ""

        # -----------------------------
        # Extract text
        # -----------------------------

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

        # -----------------------------
        # Remove thinking block
        # -----------------------------

        text = re.sub(
            r"<think>.*?</think>",
            "",
            text,
            flags=re.DOTALL | re.IGNORECASE,
        )

        text = text.strip()

        # -----------------------------
        # Remove Markdown JSON
        # -----------------------------

        text = re.sub(
            r"^```json\s*|\s*```$",
            "",
            text,
            flags=re.MULTILINE,
        ).strip()

        # -----------------------------
        # Parse JSON Response
        # -----------------------------

        try:

            data = json.loads(text)

            if isinstance(data, dict):

                return (
                    data.get("response")
                    or data.get("message")
                    or text
                )

        except json.JSONDecodeError:
            pass

        return text


response_parser = ResponseParser()
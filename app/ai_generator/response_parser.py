# from typing import Any


# class ResponseParser:
#     """
#     Responsible for parsing and normalizing
#     responses from different LLM providers.
#     """

#     def parse(self, response: Any) -> str:
#         """
#         Normalize the response into plain text.
#         """

#         if response is None:
#             return ""

#         # Dictionary response
#         if isinstance(response, dict):
#             return (
#                 response.get("text")
#                 or response.get("content")
#                 or response.get("message")
#                 or ""
#             )

#         # String response
#         if isinstance(response, str):
#             return response

#         # Fallback
#         return str(response)



import json
import re
from typing import Any


class ResponseParser:
    """
    Responsible for parsing and normalizing
    responses from different LLM providers.
    """

    def parse(self, response: Any) -> dict:
        """
        Normalize the response into a Python dictionary.
        """

        if response is None:
            return {}

        # Extract text
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

        # Remove reasoning block
        text = re.sub(
            r"<think>.*?</think>",
            "",
            text,
            flags=re.DOTALL | re.IGNORECASE,
        )

        text = text.strip()

        # Remove markdown json block
        text = re.sub(
            r"^```json\s*|\s*```$",
            "",
            text,
            flags=re.MULTILINE,
        )

        try:
            return json.loads(text)

        except json.JSONDecodeError:
            return {
                "project_name": "Generated Project",
                "description": "",
                "framework": "",
                "files": [],
                "raw_response": text,
            }
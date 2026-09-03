import json
import re
from typing import Any


class AIResponseParser:
    """
    Parses and normalizes AI Agent responses.

    The parser only converts the provider response into
    the standard AI Agent response structure.

    It does NOT:
        - decide user intent
        - create projects
        - create files
        - modify projects
        - generate application source code
    """

    # =========================================================
    # DEFAULT RESPONSE
    # =========================================================

    DEFAULT_RESPONSE = {
        "type": "text",
        "message": "",
        "data": None,
        "components": [],
    }

    # =========================================================
    # PUBLIC
    # =========================================================

    def parse(
        self,
        response: Any,
    ) -> dict:
        """
        Convert an LLM/provider response into a predictable
        dictionary.

        JSON response:
            Parse and normalize it.

        Plain text response:
            Return it as a normal text response.

        This is important because simple prompts such as
        "hi" may naturally return plain text from the LLM.
        """

        if response is None:
            raise ValueError(
                "AI returned an empty response."
            )

        # -----------------------------------------------------
        # Extract text
        # -----------------------------------------------------

        text = self._extract_text(
            response
        )

        if not text:
            raise ValueError(
                "AI returned an empty response."
            )

        # -----------------------------------------------------
        # Clean response
        # -----------------------------------------------------

        text = self._clean_text(
            text
        )

        if not text:
            raise ValueError(
                "AI returned an empty response."
            )

        # -----------------------------------------------------
        # Parse JSON
        # -----------------------------------------------------

        parsed = self._parse_json(
            text
        )

        # =====================================================
        # IMPORTANT
        # =====================================================
        #
        # If the LLM returns plain text instead of JSON,
        # do NOT throw an error.
        #
        # Example:
        #
        # "Hi! How can I help you today?"
        #
        # becomes:
        #
        # {
        #     "type": "text",
        #     "message": "Hi! How can I help you today?",
        #     "data": null,
        #     "components": []
        # }
        #
        # =====================================================

        if parsed is None:

            return {
                "type": "text",
                "message": text,
                "data": None,
                "components": [],
            }

        # -----------------------------------------------------
        # Normalize JSON response
        # -----------------------------------------------------

        return self._normalize(
            parsed
        )

    # =========================================================
    # EXTRACT TEXT
    # =========================================================

    def _extract_text(
        self,
        response: Any,
    ) -> str:
        """
        Extract text from different LLM provider response
        formats.
        """

        # -----------------------------------------------------
        # String response
        # -----------------------------------------------------

        if isinstance(
            response,
            str,
        ):
            return response

        # -----------------------------------------------------
        # Dictionary response
        # -----------------------------------------------------

        if isinstance(
            response,
            dict,
        ):

            value = (
                response.get("text")
                or response.get("content")
                or response.get("message")
            )

            # Example:
            #
            # {
            #     "text": "{...}"
            # }

            if isinstance(
                value,
                str,
            ):
                return value

            # -------------------------------------------------
            # Nested message
            # -------------------------------------------------

            if isinstance(
                value,
                dict,
            ):

                nested = (
                    value.get("content")
                    or value.get("text")
                    or value.get("message")
                )

                if isinstance(
                    nested,
                    str,
                ):
                    return nested

            return ""

        # -----------------------------------------------------
        # Unexpected provider object
        # -----------------------------------------------------

        return str(response)

    # =========================================================
    # CLEAN TEXT
    # =========================================================

    def _clean_text(
        self,
        text: str,
    ) -> str:
        """
        Remove common LLM formatting artifacts.
        """

        text = text.strip()

        # -----------------------------------------------------
        # Remove thinking blocks
        # -----------------------------------------------------

        text = re.sub(
            r"<think>.*?</think>",
            "",
            text,
            flags=re.DOTALL | re.IGNORECASE,
        )

        text = text.strip()

        # -----------------------------------------------------
        # Remove ```json
        # -----------------------------------------------------

        text = re.sub(
            r"^```json\s*",
            "",
            text,
            flags=re.IGNORECASE,
        )

        # -----------------------------------------------------
        # Remove generic ```
        # -----------------------------------------------------

        text = re.sub(
            r"^```\s*",
            "",
            text,
        )

        text = re.sub(
            r"\s*```$",
            "",
            text,
        )

        return text.strip()

    # =========================================================
    # JSON PARSER
    # =========================================================

    def _parse_json(
        self,
        text: str,
    ) -> dict | None:
        """
        Parse JSON safely.

        First attempts to parse the complete response.

        If the model accidentally adds text before/after
        the JSON object, attempts to extract the JSON object.

        If no valid JSON exists, returns None.

        The caller will treat the response as plain text.
        """

        # -----------------------------------------------------
        # Direct JSON parsing
        # -----------------------------------------------------

        try:

            data = json.loads(
                text
            )

            if isinstance(
                data,
                dict,
            ):
                return data

        except json.JSONDecodeError:
            pass

        # -----------------------------------------------------
        # Extract JSON object
        # -----------------------------------------------------

        start = text.find(
            "{"
        )

        end = text.rfind(
            "}"
        )

        if (
            start != -1
            and end != -1
            and end > start
        ):

            json_text = text[
                start : end + 1
            ]

            try:

                data = json.loads(
                    json_text
                )

                if isinstance(
                    data,
                    dict,
                ):
                    return data

            except json.JSONDecodeError:
                pass

        return None

    # =========================================================
    # NORMALIZE
    # =========================================================

    def _normalize(
        self,
        data: dict,
    ) -> dict:
        """
        Normalize the parsed AI response.

        Expected structure:

        {
            "type": "...",
            "message": "...",
            "data": ...,
            "components": [...]
        }
        """

        # -----------------------------------------------------
        # Response type
        # -----------------------------------------------------

        response_type = (
            data.get("type")
            or "text"
        )

        # -----------------------------------------------------
        # Message
        # -----------------------------------------------------

        message = data.get(
            "message",
            "",
        )

        # -----------------------------------------------------
        # Data
        # -----------------------------------------------------

        response_data = data.get(
            "data",
            None,
        )

        # -----------------------------------------------------
        # Components
        # -----------------------------------------------------

        components = data.get(
            "components",
            [],
        )

        # =====================================================
        # Normalize message
        # =====================================================

        if message is None:
            message = ""

        if not isinstance(
            message,
            str,
        ):
            message = str(
                message
            )

        # =====================================================
        # Normalize components
        # =====================================================

        if components is None:
            components = []

        if not isinstance(
            components,
            list,
        ):
            components = []

        # =====================================================
        # Normalize response type
        # =====================================================

        if not isinstance(
            response_type,
            str,
        ):
            response_type = "text"

        response_type = (
            response_type
            .strip()
            .lower()
        )

        # =====================================================
        # Return normalized response
        # =====================================================

        return {
            "type": response_type,
            "message": message.strip(),
            "data": response_data,
            "components": components,
        }


# ============================================================
# SINGLETON
# ============================================================

response_parser = AIResponseParser()

# Optional alias if your service imports this name
ai_agent_response_parser = response_parser
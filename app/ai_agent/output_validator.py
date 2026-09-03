from typing import Any


class AIOutputValidator:
    """
    Validates normalized AI Agent output.

    This validator is NOT UI-specific.

    It validates:
        - response type
        - message
        - data
        - components
        - component types
        - type-specific requirements

    It does NOT:
        - create applications
        - create projects
        - modify files
        - decide user intent
        - call external APIs
        - call the LLM
    """

    # =========================================================
    # ALLOWED RESPONSE TYPES
    # =========================================================

    ALLOWED_TYPES = {
        "text",
        "data",
        "table",
        "chart",
        "dashboard",
        "card",
        "list",
    }

    # =========================================================
    # ALLOWED COMPONENT TYPES
    # =========================================================

    ALLOWED_COMPONENT_TYPES = {
        "text",
        "stat",
        "card",
        "table",
        "chart",
        "list",
    }

    # =========================================================
    # LIMITS
    # =========================================================

    MAX_COMPONENTS = 50

    # =========================================================
    # PUBLIC VALIDATION
    # =========================================================

    def validate(
        self,
        output: Any,
    ) -> dict:
        """
        Validate and return normalized AI output.

        Raises:
            ValueError:
                If the AI output is invalid.
        """

        # -----------------------------------------------------
        # Output must be a dictionary
        # -----------------------------------------------------

        if not isinstance(
            output,
            dict,
        ):
            raise ValueError(
                "AI output must be a JSON object."
            )

        # =====================================================
        # RESPONSE TYPE
        # =====================================================

        response_type = output.get(
            "type"
        )

        if not response_type:

            raise ValueError(
                "AI output type is required."
            )

        if not isinstance(
            response_type,
            str,
        ):

            raise ValueError(
                "AI output type must be a string."
            )

        response_type = (
            response_type
            .strip()
            .lower()
        )

        if (
            response_type
            not in self.ALLOWED_TYPES
        ):

            raise ValueError(
                f"Unsupported AI output type: "
                f"{response_type}"
            )

        # =====================================================
        # MESSAGE
        # =====================================================

        message = output.get(
            "message",
            "",
        )

        if message is None:

            message = ""

        if not isinstance(
            message,
            str,
        ):

            raise ValueError(
                "AI output message must be a string."
            )

        # =====================================================
        # DATA
        # =====================================================

        data = output.get(
            "data",
            None,
        )

        self._validate_data(
            data
        )

        # =====================================================
        # COMPONENTS
        # =====================================================

        components = output.get(
            "components",
            [],
        )

        if components is None:

            components = []

        if not isinstance(
            components,
            list,
        ):

            raise ValueError(
                "AI output components must be a list."
            )

        if len(components) > self.MAX_COMPONENTS:

            raise ValueError(
                "AI output contains too many "
                f"components. Maximum allowed: "
                f"{self.MAX_COMPONENTS}."
            )

        # -----------------------------------------------------
        # Validate every component
        # -----------------------------------------------------

        for component in components:

            self._validate_component(
                component
            )

        # =====================================================
        # TYPE-SPECIFIC VALIDATION
        # =====================================================

        self._validate_response_type(
            response_type=response_type,
            data=data,
            components=components,
        )

        # =====================================================
        # RETURN NORMALIZED OUTPUT
        # =====================================================

        return {
            "type": response_type,
            "message": message.strip(),
            "data": data,
            "components": components,
        }

    # =========================================================
    # DATA VALIDATION
    # =========================================================

    def _validate_data(
        self,
        data: Any,
    ) -> None:
        """
        Validate JSON-compatible data.

        Allowed:

            None
            dict
            list
            string
            integer
            float
            boolean
        """

        if data is None:

            return

        if isinstance(
            data,
            (
                dict,
                list,
                str,
                int,
                float,
                bool,
            ),
        ):

            return

        raise ValueError(
            "AI output data contains an unsupported value."
        )

    # =========================================================
    # COMPONENT VALIDATION
    # =========================================================

    def _validate_component(
        self,
        component: Any,
    ) -> None:
        """
        Validate a single dynamic UI/data component.
        """

        # -----------------------------------------------------
        # Component must be object
        # -----------------------------------------------------

        if not isinstance(
            component,
            dict,
        ):

            raise ValueError(
                "Each AI component must be a JSON object."
            )

        # -----------------------------------------------------
        # Component type
        # -----------------------------------------------------

        component_type = component.get(
            "type"
        )

        if not component_type:

            raise ValueError(
                "AI component type is required."
            )

        if not isinstance(
            component_type,
            str,
        ):

            raise ValueError(
                "AI component type must be a string."
            )

        component_type = (
            component_type
            .strip()
            .lower()
        )

        if (
            component_type
            not in self.ALLOWED_COMPONENT_TYPES
        ):

            raise ValueError(
                f"Unsupported component type: "
                f"{component_type}"
            )

        # -----------------------------------------------------
        # Component title
        # -----------------------------------------------------

        title = component.get(
            "title"
        )

        if (
            title is not None
            and not isinstance(
                title,
                str,
            )
        ):

            raise ValueError(
                "Component title must be a string."
            )

        # -----------------------------------------------------
        # Component data
        # -----------------------------------------------------

        component_data = component.get(
            "data",
            None,
        )

        self._validate_data(
            component_data
        )

    # =========================================================
    # RESPONSE TYPE VALIDATION
    # =========================================================

    def _validate_response_type(
        self,
        response_type: str,
        data: Any,
        components: list,
    ) -> None:

        # =====================================================
        # TEXT
        # =====================================================

        if response_type == "text":

            return

        # =====================================================
        # DATA
        # =====================================================

        if response_type == "data":

            if data is None:

                raise ValueError(
                    "Data response must contain data."
                )

            return

        # =====================================================
        # TABLE
        # =====================================================

        if response_type == "table":

            if (
                not components
                and data is None
            ):

                raise ValueError(
                    "Table response must contain "
                    "data or components."
                )

            return

        # =====================================================
        # CHART
        # =====================================================

        if response_type == "chart":

            if (
                not components
                and data is None
            ):

                raise ValueError(
                    "Chart response must contain "
                    "data or components."
                )

            return

        # =====================================================
        # DASHBOARD
        # =====================================================

        if response_type == "dashboard":

            if not components:

                raise ValueError(
                    "Dashboard response must contain "
                    "at least one component."
                )

            return

        # =====================================================
        # CARD
        # =====================================================

        if response_type == "card":

            if (
                not components
                and data is None
            ):

                raise ValueError(
                    "Card response must contain "
                    "data or components."
                )

            return

        # =====================================================
        # LIST
        # =====================================================

        if response_type == "list":

            if (
                data is None
                and not components
            ):

                raise ValueError(
                    "List response must contain "
                    "data or components."
                )

            return


# ============================================================
# SINGLETON
# ============================================================

output_validator = AIOutputValidator()
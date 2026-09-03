"""
Intent Service for AI Agent

Handles intent detection, follow-up detection, and action planning.
This service ensures the LLM understands user intent and produces
structured, validated intent objects.

Architecture:
    User Prompt → Intent Detection → Structured Intent → Endpoint Selection → Execution
"""

import json
import re
from typing import Any

from app.ai_agent.schemas import AIAgentPromptResponse


# ============================================================
# HTTP METHOD NORMALIZATION
# ============================================================


def normalize_http_method(method: str | None) -> str:
    """
    Safely normalize an HTTP method string.
    
    Args:
        method: HTTP method string or None
        
    Returns:
        Normalized uppercase HTTP method
        
    Raises:
        ValueError: If method is None, empty, or not a supported HTTP method
        
    Rules:
        - None → ValueError (validation error, not silent default)
        - Empty string → ValueError
        - Strip whitespace and convert to uppercase
        - Validate against supported methods
        - Unknown methods → ValueError
    """
    if not method:
        raise ValueError("HTTP method is required but was None or empty")
    
    normalized = str(method).strip().upper()
    
    SUPPORTED_METHODS = {"GET", "POST", "PUT", "PATCH", "DELETE"}
    
    if normalized in SUPPORTED_METHODS:
        return normalized
    
    # Unknown methods raise error per architecture requirements
    raise ValueError(f"Unsupported HTTP method: {method}")


# ============================================================
# INTENT MODEL
# ============================================================


class Intent:
    """
    Structured intent object representing the user's desired action.
    
    This replaces raw prompt parsing with a clean, validated model.
    """
    
    def __init__(
        self,
        action: str,  # list, get, create, update, delete
        resource: str | None = None,
        operation: str | None = None,  # read, create, update, delete
        method: str = "GET",
        target: str | None = None,
        request_body: dict | None = None,
        path_parameters: dict | None = None,
        query_parameters: dict | None = None,
        missing_fields: list[str] | None = None,
        selected_endpoint_id: int | None = None,
        can_execute: bool = False,
        message: str | None = None,
    ):
        self.action = action
        self.resource = resource
        self.operation = operation or self._action_to_operation(action)
        self.method = normalize_http_method(method)
        self.target = target
        self.request_body = request_body or {}
        self.path_parameters = path_parameters or {}
        self.query_parameters = query_parameters or {}
        self.missing_fields = missing_fields or []
        self.selected_endpoint_id = selected_endpoint_id
        self.can_execute = can_execute
        self.message = message
    
    @staticmethod
    def _action_to_operation(action: str) -> str:
        """Map action to operation"""
        mapping = {
            "list": "read",
            "get": "read",
            "create": "create",
            "update": "update",
            "delete": "delete",
        }
        return mapping.get(action.lower(), "read")
    
    def to_dict(self) -> dict:
        return {
            "action": self.action,
            "resource": self.resource,
            "operation": self.operation,
            "method": self.method,
            "target": self.target,
            "request_body": self.request_body,
            "path_parameters": self.path_parameters,
            "query_parameters": self.query_parameters,
            "missing_fields": self.missing_fields,
            "selected_endpoint_id": self.selected_endpoint_id,
            "can_execute": self.can_execute,
            "message": self.message,
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "Intent":
        return cls(
            action=data.get("action", "list"),
            resource=data.get("resource"),
            operation=data.get("operation"),
            method=data.get("method") or "GET",
            target=data.get("target"),
            request_body=data.get("request_body"),
            path_parameters=data.get("path_parameters"),
            query_parameters=data.get("query_parameters"),
            missing_fields=data.get("missing_fields"),
            selected_endpoint_id=data.get("selected_endpoint_id"),
            can_execute=data.get("can_execute", False),
            message=data.get("message"),
        )
    
    @classmethod
    def from_previous_output(cls, previous_output: dict) -> "Intent | None":
        """
        Create an Intent from a previous AIAgentPromptResponse.
        
        This allows us to recover the pending operation from a previous
        response that indicated missing_fields.
        
        Args:
            previous_output: Previous AI response dict
            
        Returns:
            Intent object or None if not recoverable
        """
        if not previous_output:
            return None
        
        # Extract relevant fields from the previous response
        # Use "or GET" to handle None values (when key exists but is null)
        method = previous_output.get("method") or "GET"
        request_body = previous_output.get("request_body") or {}
        missing_fields = previous_output.get("missing_fields") or []
        can_execute = previous_output.get("can_execute", True)
        message = previous_output.get("message")
        
        # Infer action from method
        action_map = {
            "GET": "get",
            "POST": "create",
            "PUT": "update",
            "PATCH": "update",
            "DELETE": "delete",
        }
        action = action_map.get(method.upper(), "list")
        
        return cls(
            action=action,
            method=method,
            request_body=request_body,
            missing_fields=missing_fields if not can_execute else [],
            can_execute=can_execute,
            message=message,
        )
    
    def is_follow_up(self) -> bool:
        """Check if this intent indicates missing information"""
        return not self.can_execute and bool(self.missing_fields)


# ============================================================
# FOLLOW-UP DETECTION
# ============================================================


def is_follow_up_request(
    prompt: str,
    previous_output: dict | None,
) -> bool:
    """
    Determine if the current prompt is a follow-up to a previous request.
    
    Rules:
    1. If previous_output.pending is True, this is a follow-up
    2. If previous_output has missing_fields and can_execute is False, this is a follow-up
    3. ONLY use word count as a hint, not as the primary determinant
    4. A short prompt followed by pending state = follow-up
    5. A short prompt without any pending state = new request
    
    Args:
        prompt: Current user prompt
        previous_output: Previous AI response
        
    Returns:
        True if this is a follow-up request
    """
    if not previous_output:
        return False
    
    # Check explicit pending flag
    if previous_output.get("pending") is True:
        return True
    
    # Check if previous output indicated missing information
    can_execute = previous_output.get("can_execute")
    missing_fields = previous_output.get("missing_fields", [])
    message = previous_output.get("message", "")
    
    # If previous couldn't execute due to missing fields, current short answer is likely a follow-up
    if can_execute is False and missing_fields:
        return True
    
    # Parse missing fields from message if not in missing_fields
    if can_execute is False and not missing_fields and ":" in message:
        # Try to extract field names from message like "Please provide: list_name"
        match = re.search(r'provide:\s*([^.]+)', message, re.IGNORECASE)
        if match:
            return True
    
    return False


def resolve_follow_up(
    prompt: str,
    previous_intent: Intent,
    previous_output: dict | None,
) -> Intent:
    """
    Resolve a follow-up answer by merging the user's answer into the pending request.
    
    Args:
        prompt: Current user prompt (the answer)
        previous_intent: The intent from the previous turn
        previous_output: The previous AI response
        
    Returns:
        New Intent with the answer merged into request_body
    """
    if not previous_output or not previous_intent.missing_fields:
        # Not actually a follow-up, return as-is
        return previous_intent
    
    # Build updated request body by merging the answer
    updated_request_body = dict(previous_intent.request_body or {})
    
    # Get the field that was being asked for
    missing_fields = previous_intent.missing_fields
    first_missing = missing_fields[0] if missing_fields else None
    
    if first_missing:
        # The current prompt is the answer to the first missing field
        value = _normalize_answer_value(prompt, first_missing)
        updated_request_body[first_missing] = value
    
    # Create new intent with merged answer
    new_intent = Intent.from_dict(previous_intent.to_dict())
    new_intent.request_body = updated_request_body
    new_intent.missing_fields = missing_fields[1:]  # Remove resolved field
    
    # If all fields are now provided, mark as executable
    if not new_intent.missing_fields:
        new_intent.can_execute = True
        new_intent.message = None
    
    return new_intent


def _normalize_answer_value(value: Any, field_name: str) -> Any:
    """
    Normalize the user's answer based on the field type expected.
    
    Args:
        value: The value provided by the user
        field_name: The name of the field being answered
        
    Returns:
        Normalized value
    """
    # Handle boolean fields
    if field_name.lower() in ("standardlist", "standard_list", "isactive", "is_active"):
        if isinstance(value, bool):
            return value
        value_str = str(value).lower().strip()
        return value_str in ("true", "yes", "1", "standard", "active")
    
    # Handle numeric fields
    if field_name.lower() in ("id", "count", "quantity", "limit", "page"):
        try:
            return int(value)
        except (ValueError, TypeError):
            pass
    
    # Default: return as string
    return str(value)


# ============================================================
# METHOD DETECTION FROM INTENT
# ============================================================


def get_method_from_intent(intent: Intent | dict) -> str:
    """
    Get the authoritative HTTP method from intent.
    
    The method must be deterministic based on the action, not random LLM output.
    
    Args:
        intent: Intent object or dict
        
    Returns:
        HTTP method (GET, POST, PUT, PATCH, DELETE)
    """
    if isinstance(intent, dict):
        action = intent.get("action", "list")
        method = intent.get("method")
    else:
        action = intent.action
        method = intent.method
    
    # If method is explicitly specified, validate it
    if method:
        method = method.upper()
        if method in {"GET", "POST", "PUT", "PATCH", "DELETE"}:
            return method
    
    # Derive method from action
    action_lower = action.lower()
    
    if action_lower in ("list", "get"):
        return "GET"
    elif action_lower == "create":
        return "POST"
    elif action_lower == "update":
        return "PATCH"  # Could be PUT, but PATCH is more common for partial updates
    elif action_lower == "delete":
        return "DELETE"
    
    # Default
    return "GET"


# ============================================================
# INTENT PLANNING PROMPT
# ============================================================


def build_intent_planning_prompt(
    prompt: str,
    intent: Intent | None,
    previous_output: dict | None,
    conversation_history: list[dict] | None,
    candidate_endpoints: list[dict] | None,
) -> str:
    """
    Build a prompt for the LLM to plan the user's intent.
    
    The LLM should return a structured JSON intent object.
    
    Args:
        prompt: Current user prompt
        intent: Previous intent (for context)
        previous_output: Previous AI response (for follow-up handling)
        conversation_history: Full conversation history
        candidate_endpoints: List of authorized endpoints
        
    Returns:
        Prompt string for LLM
    """
    # Build conversation history text
    history_text = _build_conversation_text(conversation_history)
    
    # Build pending state text
    pending_text = ""
    if previous_output:
        prev_method = previous_output.get("method", "")
        prev_missing = previous_output.get("missing_fields", [])
        prev_request_body = previous_output.get("request_body") or {}
        prev_message = previous_output.get("message", "")
        
        if prev_missing or previous_output.get("can_execute") is False:
            pending_text = f"""
============================================================
PENDING REQUEST (AWAITING INFORMATION)
============================================================

Method: {prev_method}
Missing fields: {prev_missing}
Current request body: {json.dumps(prev_request_body) if prev_request_body else "empty"}
Previous message: "{prev_message}"

The user's next message should be treated as an answer to the missing field(s).
"""
    
    # Build endpoints text
    endpoints_text = ""
    if candidate_endpoints:
        endpoints_text = """
============================================================
AUTHORIZED ENDPOINTS
============================================================

Select the best endpoint based on user intent.
Return ONLY the endpoint ID (number), not the full URL.

"""
        for ep in candidate_endpoints:
            ep_id = ep.get("id", "unknown")
            ep_resource = ep.get("resource_name", "")
            ep_method = ep.get("method", "GET")
            ep_desc = ep.get("description", "") or ""
            ep_endpoint = ep.get("endpoint", "")
            endpoints_text += f"- ID: {ep_id} | Resource: {ep_resource} | Method: {ep_method} | URL: {ep_endpoint}\n"
            if ep_desc:
                endpoints_text += f"  Description: {ep_desc}\n"
    
    return f"""
You are the Intent Planner for PromptXL AI Agent.

Your job is to understand the user's request and produce a structured intent.

============================================================
CRITICAL: RESOURCE EXTRACTION RULE (MOST IMPORTANT)
============================================================

The 'resource' field is MANDATORY and must ALWAYS be extracted from the user's prompt.

STEPS to extract resource:
1. Look at the ENDPOINT LIST below - each endpoint has a 'Resource' field
2. Find words in the user's prompt that match endpoint Resource names
3. If "models" is in prompt and endpoint has Resource="models", extract "models"

EXAMPLES of correct extraction:
- "get me the models" -> resource="models" (because an endpoint has Resource: models)
- "show dimensions" -> resource="dimensions" (because an endpoint has Resource: dimensions)
- "get users" -> resource="users" (because an endpoint has Resource: users)
- "list all projects" -> resource="projects" (because an endpoint has Resource: projects)
- "delete the Sales list" -> resource="lists", target="Sales"

CRITICAL RULES:
- resource MUST NOT be null/empty - if you cannot find a matching resource, set can_execute=false
- NEVER return can_execute=true if resource is null or doesn't match an endpoint's Resource
- If no word in the prompt matches any endpoint's Resource, set can_execute=false
- Do NOT guess a resource name that isn't in the endpoint list

============================================================
CONVERSATION HISTORY
============================================================

{history_text}

{pending_text}
============================================================
CURRENT USER REQUEST
============================================================

{prompt}

{endpoints_text}
============================================================
OUTPUT FORMAT
============================================================

Return ONLY valid JSON with this structure:

{{
    "action": "list|get|create|update|delete",
    "resource": "MUST match a Resource from the endpoint list above - NEVER null/empty",
    "operation": "read|create|update|delete",
    "method": "GET|POST|PUT|PATCH|DELETE",
    "selected_endpoint_id": null or integer endpoint ID from the authorized endpoints list,
    "target": "optional target identifier (e.g., 'Sales' for 'delete Sales list')",
    "request_body": {{}},
    "path_parameters": {{}},
    "query_parameters": {{}},
    "missing_fields": [],
    "can_execute": true|false,
    "message": ""
}}

Rules:
1. RESOURCE IS MANDATORY - never return null/empty for resource
2. If resource cannot be determined, set can_execute=false and message="Could not identify resource. Please specify which resource you want."
3. The resource MUST match an endpoint's Resource from the list above
3. action + operation must be consistent with method
4. selected_endpoint_id must be from the authorized endpoints list above
5. For GET requests, request_body should be empty or null
6. For POST/PUT/PATCH, include required fields in request_body
7. If required fields are missing, set can_execute=false and list fields in missing_fields
8. NEVER invent endpoint IDs - use null if no endpoint matches
9. NEVER invent field values - ask for missing required values
10. If the user asks for a follow-up (answer to missing info), preserve the pending state
11. Use the conversation history to understand context

Do not return markdown. Return only valid JSON.
""".strip()


# ============================================================
# PARSE LLM INTENT RESPONSE
# ============================================================


def parse_intent_response(raw_response: Any) -> Intent:
    """
    Parse LLM intent response safely.

    Handles:
    - dict responses
    - plain JSON strings
    - <think>...</think> + JSON responses
    - markdown ```json blocks
    """

    if raw_response is None:
        raise ValueError("Intent response is empty.")

    # ---------------------------------------------------------
    # 1. Extract raw text
    # ---------------------------------------------------------
    if isinstance(raw_response, dict):
        # LLM provider may return:
        # {"text": "..."}
        # or already parsed intent dict
        if "text" in raw_response:
            text = str(raw_response["text"])
        elif "content" in raw_response:
            text = str(raw_response["content"])
        else:
            data = raw_response
            return Intent.from_dict(data)
    else:
        text = str(raw_response)

    text = text.strip()

    # ---------------------------------------------------------
    # 2. Remove <think>...</think>
    # ---------------------------------------------------------
    text = re.sub(
        r"<think>.*?</think>",
        "",
        text,
        flags=re.DOTALL | re.IGNORECASE,
    ).strip()

    # ---------------------------------------------------------
    # 3. Remove markdown code fences
    # ---------------------------------------------------------
    text = re.sub(
        r"^```(?:json)?\s*",
        "",
        text,
        flags=re.IGNORECASE,
    )

    text = re.sub(
        r"\s*```$",
        "",
        text,
    ).strip()

    # ---------------------------------------------------------
    # 4. Parse JSON directly
    # ---------------------------------------------------------
    try:
        data = json.loads(text)

    except json.JSONDecodeError:

        # -----------------------------------------------------
        # 5. Extract JSON object from surrounding text
        # -----------------------------------------------------
        start = text.find("{")
        end = text.rfind("}")

        if start == -1 or end <= start:
            raise ValueError(
                f"Could not parse intent response. Raw response: {text}"
            )

        json_text = text[start:end + 1]

        try:
            data = json.loads(json_text)

        except json.JSONDecodeError as exc:
            raise ValueError(
                f"Invalid intent JSON: {exc}. Raw response: {text}"
            ) from exc

    # ---------------------------------------------------------
    # 6. Validate parsed object
    # ---------------------------------------------------------
    if not isinstance(data, dict):
        raise ValueError("Intent response must be a JSON object.")

    # ---------------------------------------------------------
    # 7. Normalize important fields
    # ---------------------------------------------------------
    if data.get("request_body") is None:
        data["request_body"] = {}

    if data.get("path_parameters") is None:
        data["path_parameters"] = {}

    if data.get("query_parameters") is None:
        data["query_parameters"] = {}

    if data.get("missing_fields") is None:
        data["missing_fields"] = []

    # ---------------------------------------------------------
    # 8. Create Intent
    # ---------------------------------------------------------
    return Intent.from_dict(data)

# ============================================================
# HELPER FUNCTIONS
# ============================================================


def _build_conversation_text(
    conversation_history: list[dict] | None,
) -> str:
    """
    Build conversation text from history.
    
    Handles both dict items and Pydantic model items safely.
    """
    if not conversation_history:
        return "No previous conversation."
    
    messages = []
    for item in conversation_history:
        # Handle both dict and Pydantic/object items
        if isinstance(item, dict):
            role = item.get("role", "user")
            content = item.get("content") or item.get("message", "")
        else:
            role = getattr(item, "role", "user")
            content = getattr(item, "content", None) or getattr(item, "message", "")
        
        if not isinstance(content, str):
            content = str(content)
        
        content = content.strip()
        if content:
            messages.append(f"{role}: {content}")
    
    if not messages:
        return "No previous conversation."
    
    return "\n".join(messages)


def _extract_resource_from_path(endpoint_path: str) -> str:
    """Extract resource name from endpoint path"""
    if not endpoint_path:
        return ""
    
    # Remove leading/trailing slashes
    path = endpoint_path.strip("/")
    
    # Split by slashes and get the last meaningful segment
    parts = path.split("/")
    
    # Skip common prefixes like 'api', 'v1', 'v2'
    skip_prefixes = {"api", "v1", "v2", "v3", "rest"}
    segments = [p for p in parts if p.lower() not in skip_prefixes]
    
    if segments:
        # Get the last segment and remove {param} suffixes
        resource = segments[-1]
        resource = re.sub(r'\{[^}]+\}', '', resource)
        return resource.strip().lower()
    
    return path.lower()


# ============================================================
# VALIDATE INTENT
# ============================================================


def validate_intent(
    intent: Intent,
    authorized_endpoints: list[dict],
) -> tuple[bool, str | None]:
    """
    Validate that the intent can be executed with authorized endpoints.
    
    Args:
        intent: The planned intent
        authorized_endpoints: List of authorized endpoint dicts
        
    Returns:
        (is_valid, error_message)
    """
    # Check if endpoint_id is in authorized endpoints
    if intent.selected_endpoint_id is not None:
        endpoint_ids = {ep.get("id") for ep in authorized_endpoints}
        if intent.selected_endpoint_id not in endpoint_ids:
            return False, f"Endpoint ID {intent.selected_endpoint_id} is not authorized."
    
    # Check method compatibility
    if intent.selected_endpoint_id is not None:
        for ep in authorized_endpoints:
            if ep.get("id") == intent.selected_endpoint_id:
                ep_method = (ep.get("method") or "GET").upper()
                if ep_method != intent.method.upper():
                    return False, f"Method {intent.method} is not supported by endpoint. Expected {ep_method}."
                break
    
    return True, None

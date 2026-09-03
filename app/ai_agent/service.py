import json
import re
from typing import Any

from sqlalchemy.orm import Session

from app.ai_agent import crud
from app.ai_agent.encryption import decrypt_api_token

from app.ai_agent.endpoint_service import (
    call_endpoint,
    call_direct_endpoint,
)

from app.ai_agent.prompt_builder import (
    ai_agent_prompt_builder,
)

from app.ai_agent.response_parser import (
    response_parser,
)

from app.ai_agent.output_validator import (
    output_validator,
)

from app.ai_generator.provider_selector import (
    ProviderSelector,
)

from app.ai_generator.services.generation_service import (
    GenerationService,
)

# New Intent-based services
from app.ai_agent.intent_service import (
    Intent,
    is_follow_up_request,
    resolve_follow_up,
    build_intent_planning_prompt,
    parse_intent_response,
    get_method_from_intent,
)

from app.ai_agent.endpoint_selector import (
    EndpointSelector,
    get_endpoint_request_schema,
    validate_request_body_against_schema,
    transform_request_body_for_endpoint,
    log_endpoint_selection,
)

from app.ai_agent.schemas import AIAgentPromptResponse


# ============================================================
# HELPER FUNCTIONS
# ============================================================


def _resolve_resource_from_prompt(
    prompt: str,
    endpoints: list[dict] | None,
) -> str | None:
    """
    Fallback resource resolution: match prompt words against registered endpoint metadata.

    This function is called when the LLM fails to extract the resource from the prompt.
    It normalizes the prompt and compares against endpoint metadata to find a match.

    Args:
        prompt: The user's natural language prompt
        endpoints: List of endpoint dicts with resource_name, endpoint, description

    Returns:
        Resolved resource name or None if no match found
    """
    if not prompt or not endpoints:
        return None

    # Normalize the prompt
    prompt_lower = prompt.lower().strip()

    # Common variations of "get/list/show" to normalize
    action_normalizations = {
        "get me the": "",
        "get the": "",
        "show me the": "",
        "show all": "",
        "show": "",
        "get all": "",
        "get": "",
        "list all": "",
        "list": "",
        "fetch": "",
        "retrieve": "",
        "display": "",
    }

    normalized_prompt = prompt_lower
    for phrase, replacement in action_normalizations.items():
        normalized_prompt = normalized_prompt.replace(phrase, replacement)

    # Clean up extra spaces and punctuation
    normalized_prompt = re.sub(r'\s+', ' ', normalized_prompt).strip()
    normalized_prompt = normalized_prompt.strip('.,!?;:\'"')

    print(f"\n========== RESOURCE RESOLUTION DEBUG ==========")
    print(f"ORIGINAL PROMPT: {prompt}")
    print(f"NORMALIZED PROMPT: {normalized_prompt}")
    print(f"CHECKING AGAINST ENDPOINTS:")
    print("============================================\n")

    # Check each endpoint for matches
    for ep in endpoints:
        resource_name = (ep.get("resource_name") or "").lower().strip()
        endpoint_url = (ep.get("endpoint") or "").lower()
        description = (ep.get("description") or "").lower()

        if not resource_name:
            continue

        print(f"  Checking resource: '{resource_name}'")

        # Exact match in normalized prompt
        if normalized_prompt == resource_name:
            print(f"    ✓ EXACT MATCH on normalized prompt")
            return resource_name

        # Resource name as standalone word in prompt
        prompt_words = normalized_prompt.split()
        if resource_name in prompt_words:
            print(f"    ✓ WORD MATCH in prompt words")
            return resource_name

        # Resource plural/singular variations
        singular = resource_name.rstrip('s')
        plural = resource_name + 's'
        if singular in normalized_prompt or plural in normalized_prompt:
            print(f"    ✓ PLURAL/SINGULAR MATCH")
            return resource_name

        # Check if resource is mentioned anywhere in prompt
        if resource_name in prompt_lower:
            print(f"    ✓ CONTAINED IN PROMPT")
            return resource_name

        # Check URL path for resource
        url_path = endpoint_url.split('?')[0]  # Remove query params
        if f"/{resource_name}" in url_path or f"/{plural}" in url_path:
            print(f"    ✓ MATCH IN URL PATH")
            return resource_name

        # Check description for resource mentions
        if resource_name in description or singular in description or plural in description:
            print(f"    ✓ MATCH IN DESCRIPTION")
            return resource_name

    print(f"  No match found for any endpoint resource")
    return None


# ============================================================
# API CONNECTION
# ============================================================


def connect_api(
    db: Session,
    user_id: int,
    tenant_id: int,
    api_token: str,
    external_tenant: str | None,
):
    existing = crud.get_connection(
        db,
        tenant_id,
        user_id,
    )

    if existing:
        return crud.update_connection(
            db,
            existing,
            api_token=api_token,
            external_tenant=external_tenant,
        )

    return crud.create_connection(
        db,
        tenant_id=tenant_id,
        user_id=user_id,
        api_token=api_token,
        external_tenant=external_tenant,
    )


def get_api_connection(
    db: Session,
    user_id: int,
    tenant_id: int,
):
    return crud.get_connection(
        db,
        tenant_id,
        user_id,
    )


def update_api_connection(
    db: Session,
    user_id: int,
    tenant_id: int,
    api_token: str | None = None,
    external_tenant: str | None = None,
):
    connection = crud.get_connection(
        db,
        tenant_id,
        user_id,
    )

    if not connection:
        raise ValueError(
            "API connection not found."
        )

    return crud.update_connection(
        db,
        connection,
        api_token=api_token,
        external_tenant=external_tenant,
    )


# ============================================================
# ENDPOINT CONNECTION
# ============================================================


def get_user_connection(
    db: Session,
    user_id: int,
    external_tenant: str,
):
    connection = crud.get_connection_by_external_tenant(
        db,
        user_id,
        external_tenant,
    )

    if not connection:
        raise ValueError(
            "Please connect an API before connecting an endpoint."
        )

    return connection


def connect_endpoint(
    db: Session,
    user_id: int,
    external_tenant: str,
    endpoint: str,
    method: str | None = None,
    description: str | None = None,
    resource_name: str | None = None,
    request_schema: dict | None = None,
    response_schema: dict | None = None,
):
    connection = get_user_connection(
        db,
        user_id,
        external_tenant,
    )

    existing = crud.get_endpoint_by_url(
        db,
        connection.id,
        endpoint,
    )

    if existing:
        # Update description and other fields if new values provided
        updated = crud.update_endpoint(
            db,
            existing,
            endpoint=endpoint,
            method=method,
            description=description,
            resource_name=resource_name,
            request_schema=request_schema,
            response_schema=response_schema,
        )
        print(f"\n{'='*60}")
        print(f"ENDPOINT ALREADY EXISTS - UPDATED:")
        print(f"  Endpoint ID: {updated.id}")
        print(f"  Endpoint: {updated.endpoint}")
        print(f"  Method: {updated.method}")
        print(f"  Description: {updated.description}")
        print(f"  Resource Name: {updated.resource_name}")
        print(f"{'='*60}\n")
        return updated

    created = crud.create_endpoint(
        db,
        connection.id,
        endpoint,
        method=method,
        description=description,
        resource_name=resource_name,
        request_schema=request_schema,
        response_schema=response_schema,
    )

    # ENDPOINT CONNECT DEBUG
    print(f"\n{'='*60}")
    print(f"ENDPOINT CONNECT DEBUG:")
    print(f"  Endpoint: {endpoint}")
    print(f"  Method: {method}")
    print(f"  Description: {description}")
    print(f"  Resource: {resource_name}")
    print(f"  Request Schema: {request_schema}")
    print(f"  Request Schema Type: {type(request_schema)}")
    print(f"  Connection ID: {connection.id}")
    print(f"{'='*60}\n")

    # ENDPOINT SAVED
    print(f"\n{'='*60}")
    print(f"ENDPOINT SAVED:")
    print(f"  Endpoint ID: {created.id}")
    print(f"  Connection ID: {created.connection_id}")
    print(f"  Endpoint: {created.endpoint}")
    print(f"  Method: {created.method}")
    print(f"  Description: {created.description}")
    print(f"  Resource Name: {created.resource_name}")
    print(f"{'='*60}\n")

    return created


def get_connected_endpoints(
    db: Session,
    user_id: int,
    external_tenant: str,
):
    connection = get_user_connection(
        db,
        user_id,
        external_tenant,
    )

    return crud.get_endpoints(
        db,
        connection.id,
    )


def update_connected_endpoint(
    db: Session,
    user_id: int,
    external_tenant: str,
    endpoint_id: int,
    endpoint: str | None = None,
    method: str | None = None,
    description: str | None = None,
    resource_name: str | None = None,
    request_schema: dict | None = None,
    response_schema: dict | None = None,
):
    connection = get_user_connection(
        db,
        user_id,
        external_tenant,
    )

    endpoint_obj = crud.get_endpoint(
        db,
        connection.id,
        endpoint_id,
    )

    if not endpoint_obj:
        raise ValueError(
            "Endpoint not found."
        )

    # ENDPOINT UPDATE DEBUG
    print(f"\n{'='*60}")
    print(f"ENDPOINT UPDATE DEBUG:")
    print(f"  Endpoint ID: {endpoint_id}")
    print(f"  Endpoint: {endpoint}")
    print(f"  Method: {method}")
    print(f"  Description: {description}")
    print(f"  Resource: {resource_name}")
    print(f"  Connection ID: {connection.id}")
    print(f"{'='*60}\n")

    updated = crud.update_endpoint(
        db,
        endpoint_obj,
        endpoint=endpoint,
        method=method,
        description=description,
        resource_name=resource_name,
        request_schema=request_schema,
        response_schema=response_schema,
    )

    # ENDPOINT UPDATED
    print(f"\n{'='*60}")
    print(f"ENDPOINT UPDATED:")
    print(f"  Endpoint ID: {updated.id}")
    print(f"  Endpoint: {updated.endpoint}")
    print(f"  Method: {updated.method}")
    print(f"  Description: {updated.description}")
    print(f"  Resource Name: {updated.resource_name}")
    print(f"{'='*60}\n")

    return updated


def delete_connected_endpoint(
    db: Session,
    user_id: int,
    external_tenant: str,
    endpoint_id: int,
):
    connection = get_user_connection(
        db,
        user_id,
        external_tenant,
    )

    endpoint_obj = crud.get_endpoint(
        db,
        connection.id,
        endpoint_id,
    )

    if not endpoint_obj:
        raise ValueError(
            "Endpoint not found."
        )

    crud.delete_endpoint(
        db,
        endpoint_obj,
    )

    return {
        "id": endpoint_id,
        "deleted": True,
    }


# ============================================================
# DIRECT URL EXTRACTION
# ============================================================


def extract_endpoint_from_prompt(
    prompt: str,
) -> tuple[str | None, str]:
    """
    Extract explicit endpoint URL or path from the user's prompt.
    
    This does NOT do resource keyword matching - that is handled
    by the Intent Planner LLM which has access to authorized endpoints.
    
    Args:
        prompt: User's prompt
        
    Returns:
        Tuple of (extracted_endpoint_or_path, cleaned_prompt)
    """
    if not prompt:
        return None, prompt

    # Pattern 1: Full URL with http/https
    pattern = r"https?://[^\s]+"

    match = re.search(
        pattern,
        prompt,
        re.IGNORECASE,
    )

    if match:
        endpoint = match.group(0).strip()
        cleaned_prompt = (
            prompt[:match.start()]
            + prompt[match.end():]
        ).strip()
        return endpoint, cleaned_prompt

    # Pattern 2: API path like /api/models, /models
    api_pattern = r'(?:^|\s)(/(?:api|v\d+)?/[^\s]+)(?:\s|$)'

    match = re.search(
        api_pattern,
        prompt,
        re.IGNORECASE,
    )

    if match:
        endpoint = match.group(1).strip()
        cleaned_prompt = re.sub(
            api_pattern,
            ' ',
            prompt,
            flags=re.IGNORECASE,
        ).strip()
        return endpoint, cleaned_prompt

    # No explicit endpoint found - let the Intent Planner decide
    return None, prompt.strip()


# ============================================================
# EXPLICIT METHOD DETECTION
# ============================================================


def detect_explicit_http_method(
    prompt: str,
) -> str | None:

    if not prompt:
        return None

    text = prompt.lower().strip()

    # DELETE
    if any(
        word in text
        for word in [
            "delete",
            "remove",
            "destroy",
            "erase",
        ]
    ):
        return "DELETE"

    # UPDATE
    if any(
        word in text
        for word in [
            "update",
            "edit",
            "modify",
            "change",
            "rename",
        ]
    ):
        return "PATCH"

    # CREATE
    if any(
        word in text
        for word in [
            "create",
            "add",
            "insert",
            "register",
            "make",
        ]
    ):
        return "POST"

    # GET
    if any(
        word in text
        for word in [
            "get",
            "fetch",
            "show",
            "list",
            "retrieve",
            "view",
        ]
    ):
        return "GET"

    return None


# ============================================================
# FOLLOW-UP DETECTION
# ============================================================


def is_short_follow_up(
    prompt: str,
) -> bool:

    if not prompt:
        return False

    text = prompt.strip()

    words = text.split()

    if len(words) <= 5:
        return True

    return False


# ============================================================
# RECOVER METHOD FROM CONVERSATION
# ============================================================

def recover_method_from_history(
    conversation_history: list[Any] | None,
) -> str | None:

    if not conversation_history:
        return None

    # Read newest messages first
    for item in reversed(
        conversation_history
    ):

        role = get_history_value(
            item,
            "role",
            "",
        )

        content = get_history_value(
            item,
            "content",
            "",
        )

        if not content:
            content = get_history_value(
                item,
                "message",
                "",
            )

        if not isinstance(
            content,
            str,
        ):
            content = str(content)

        content = content.strip()

        if not content:
            continue

        if role != "user":
            continue

        text = content.lower()

        # ====================================================
        # CREATE
        # ====================================================

        if any(
            word in text
            for word in [
                "create",
                "add",
                "insert",
                "register",
                "make",
                "new",
            ]
        ):
            return "POST"

        # ====================================================
        # UPDATE
        # ====================================================

        if any(
            word in text
            for word in [
                "update",
                "edit",
                "modify",
                "change",
                "rename",
            ]
        ):
            return "PATCH"

        # ====================================================
        # DELETE
        # ====================================================

        if any(
            word in text
            for word in [
                "delete",
                "remove",
                "destroy",
                "erase",
            ]
        ):
            return "DELETE"

        # ====================================================
        # GET
        # ====================================================

        if any(
            word in text
            for word in [
                "get",
                "fetch",
                "show",
                "list",
                "retrieve",
                "view",
            ]
        ):
            return "GET"

    return None
# ============================================================
# METHOD DETECTION
# ============================================================


def detect_http_method(
    prompt: str,
    conversation_history: list[dict] | None = None,
) -> str:

    # 1. Check current message
    explicit_method = detect_explicit_http_method(
        prompt
    )

    if explicit_method:
        return explicit_method

    # 2. Follow-up answer → recover original operation
    if is_short_follow_up(prompt):

        history_method = recover_method_from_history(
            conversation_history
        )

        if history_method:
            return history_method

    # 3. Default read operation
    return "GET"


# ============================================================
# SCHEMA LOOKUP (DEPRECATED - Use endpoint_selector instead)
# ============================================================


def get_request_schema(
    endpoint_id: int | None,
    method: str,
    db: Session | None = None,
    connection = None,
) -> dict | None:
    """
    Get request schema from the endpoint's stored metadata.
    
    This replaces the old KNOWN_API_SCHEMAS lookup with the actual
    schema stored in the database for the connected endpoint.
    
    Args:
        endpoint_id: The connected endpoint ID
        method: HTTP method
        db: Database session
        connection: AIAgentConnection object
        
    Returns:
        Request schema dict or None
    """
    if endpoint_id is None or db is None or connection is None:
        return None

    from app.ai_agent.crud import get_endpoint
    
    endpoint_obj = get_endpoint(
        db=db,
        connection_id=connection.id,
        endpoint_id=endpoint_id,
    )
    
    if not endpoint_obj:
        return None
    
    # Parse request_schema if it's a JSON string
    schema = endpoint_obj.request_schema
    if isinstance(schema, str):
        try:
            schema = json.loads(schema)
        except json.JSONDecodeError:
            return None
    
    return schema


# ============================================================
# ACTION JSON PARSER
# ============================================================


def parse_action_response(
    raw_response: Any,
) -> dict:

    if raw_response is None:

        raise ValueError(
            "AI action response is empty."
        )

    if isinstance(
        raw_response,
        dict,
    ):

        data = raw_response

    else:

        text = str(
            raw_response
        ).strip()

        text = re.sub(
            r"^```json\s*",
            "",
            text,
            flags=re.IGNORECASE,
        )

        text = re.sub(
            r"\s*```$",
            "",
            text,
        )

        try:

            data = json.loads(
                text
            )

        except json.JSONDecodeError:

            start = text.find("{")
            end = text.rfind("}")

            if (
                start == -1
                or end == -1
                or end <= start
            ):

                raise ValueError(
                    "AI returned an invalid action response."
                )

            try:

                data = json.loads(
                    text[
                        start:end + 1
                    ]
                )

            except json.JSONDecodeError:

                raise ValueError(
                    "AI returned an invalid action response."
                )

    if not isinstance(
        data,
        dict,
    ):

        raise ValueError(
            "AI action response must be an object."
        )

    return data


# ============================================================
# BOOLEAN NORMALIZATION
# ============================================================


def normalize_boolean(
    value: Any,
) -> Any:

    if isinstance(
        value,
        bool,
    ):
        return value

    if isinstance(
        value,
        str,
    ):

        value_lower = (
            value
            .strip()
            .lower()
        )

        if value_lower in {
            "true",
            "yes",
            "1",
            "standard",
        }:
            return True

        if value_lower in {
            "false",
            "no",
            "0",
            "non-standard",
            "nonstandard",
        }:
            return False

    return value


# ============================================================
# REQUEST BODY NORMALIZATION
# ============================================================


def normalize_request_body(
    request_body: dict | None,
) -> dict:

    if not request_body:
        return {}

    result = {}

    for key, value in request_body.items():

        result[key] = normalize_boolean(
            value
        )

    return result


# ============================================================
# EXTERNAL API REQUEST BODY TRANSFORMATION
# ============================================================


def transform_request_body_for_external_api(
    method: str,
    endpoint: str | None,
    request_body: dict | None,
    endpoint_id: int | None = None,
    db: Session | None = None,
    connection = None,
) -> dict:
    """
    Transform request body for the target endpoint.
    
    This uses the endpoint's actual schema to derive field names,
    replacing the old hardcoded snake_case -> camelCase mapping.
    
    Args:
        method: HTTP method
        endpoint: Endpoint URL (for direct endpoints)
        request_body: The request body to transform
        endpoint_id: Connected endpoint ID
        db: Database session
        connection: AIAgentConnection object
        
    Returns:
        Transformed request body
    """
    if not request_body:
        return {}
    
    # Safely normalize method before using
    safe_method = method.upper().strip() if method else "GET"
    
    # For GET/DELETE, no body needed
    if safe_method in ("GET", "DELETE"):
        return {}
    
    # Get endpoint definition for schema lookup
    endpoint_def = None
    if endpoint_id is not None and db is not None and connection is not None:
        from app.ai_agent.crud import get_endpoint
        endpoint_obj = get_endpoint(
            db=db,
            connection_id=connection.id,
            endpoint_id=endpoint_id,
        )
        if endpoint_obj:
            # Build endpoint dict for the selector
            endpoint_def = {
                "id": endpoint_obj.id,
                "endpoint": endpoint_obj.endpoint,
                "method": endpoint_obj.method,
                "resource_name": endpoint_obj.resource_name,
                "request_schema": endpoint_obj.request_schema,
            }
    
    # Use the new transformation function
    return transform_request_body_for_endpoint(
        request_body=request_body,
        endpoint=endpoint_def,
        method=method,
    )


# ============================================================
# REQUEST BODY VALIDATION
# ============================================================


def validate_request_body(
    request_body: dict | None,
    schema: dict | None,
) -> list[str]:

    if not schema:
        return []

    request_body = (
        request_body
        or {}
    )

    missing = []

    required_fields = schema.get(
        "required",
        [],
    )

    for field in required_fields:

        if (
            field not in request_body
            or request_body[field] is None
            or (
                isinstance(
                    request_body[field],
                    str,
                )
                and not request_body[field].strip()
            )
        ):

            missing.append(
                field
            )

    return missing

def get_history_value(
    item: Any,
    key: str,
    default=None,
):
    """
    Supports both:
    - dict
    - Pydantic / object based conversation messages
    """

    if isinstance(item, dict):
        return item.get(
            key,
            default,
        )

    return getattr(
        item,
        key,
        default,
    )

# ============================================================
# CONVERSATION TEXT
# ============================================================

def build_conversation_text(
    conversation_history: list[Any] | None,
) -> str:

    if not conversation_history:
        return "No previous conversation."

    messages = []

    for item in conversation_history:

        role = get_history_value(
            item,
            "role",
            "user",
        )

        message = get_history_value(
            item,
            "content",
            "",
        )

        if not message:
            message = get_history_value(
                item,
                "message",
                "",
            )

        if not isinstance(
            message,
            str,
        ):
            message = str(message)

        message = message.strip()

        if not message:
            continue

        messages.append(
            f"{role}: {message}"
        )

    if not messages:
        return "No previous conversation."

    return "\n".join(
        messages
    )

# ============================================================
# ACTION PROMPT
# ============================================================


def build_action_prompt(
    prompt: str,
    endpoint: str | None,
    method: str,
    schema: dict | None,
    conversation_history: list[dict] | None = None,
    previous_output: dict | None = None,
    all_endpoints: list[dict] | None = None,
) -> str:

    schema_text = (
        json.dumps(
            schema,
            indent=2,
            ensure_ascii=False,
        )
        if schema
        else "No request schema supplied."
    )

    history_text = (
        build_conversation_text(
            conversation_history
        )
    )

    # Build previous output info for follow-up handling
    previous_output_text = ""
    if previous_output:
        prev_method = previous_output.get("method", "")
        prev_missing = previous_output.get("missing_fields", [])
        prev_request_body = previous_output.get("request_body") or {}
        prev_message = previous_output.get("message", "")
        
        if prev_missing:
            previous_output_text = f"""

============================================================
PREVIOUS AI OUTPUT (PENDING REQUEST)
============================================================

Method: {prev_method}
Missing fields: {prev_missing}
Current request body: {json.dumps(prev_request_body) if prev_request_body else "empty"}
Previous message: "{prev_message}"

"""
            # If current message is short, it might be an answer to a missing field
            if len(prompt.split()) <= 3 and prev_missing:
                previous_output_text += f"""

IMPORTANT - FOLLOW-UP ANSWER:
The user's message "{prompt}" appears to be a short answer.
The previous AI asked for: {prev_missing[0]}

Treat the current message as the value for {prev_missing[0]}.
Merge it with the existing request body.
"""

    # Build all connected endpoints info for generic selection
    all_endpoints_text = ""
    if all_endpoints and len(all_endpoints) > 0:
        endpoints_list = []
        for ep in all_endpoints:
            ep_info = {
                "id": ep.get("id"),
                "endpoint": ep.get("endpoint"),  # Full URL like https://api.dev.unasoft.app/api/models
                "method": ep.get("method"),
                "description": ep.get("description") or "",
                "resource_name": ep.get("resource_name") or "",
                "request_schema": ep.get("request_schema"),
            }
            endpoints_list.append(ep_info)
        
        all_endpoints_text = f"""

============================================================
ALL CONNECTED ENDPOINTS
============================================================

The user has access to these API endpoints. You MUST
select the most appropriate endpoint based on the user's intent.

{json.dumps(endpoints_list, indent=2)}

============================================================
ENDPOINT SELECTION RULES
============================================================

1. Match the user's intent to the endpoint description or resource_name
2. If user asks for "models" and an endpoint has resource_name="models", use it
3. ALWAYS return the FULL URL from the endpoint field (e.g., "https://api.dev.unasoft.app/api/models")
4. Do NOT shorten or modify the URL - use it exactly as shown in the endpoint field

Example:
- User: "get me all models" 
- Endpoint with resource_name="models" has endpoint="https://api.dev.unasoft.app/api/models"
- Return: {{"endpoint": "https://api.dev.unasoft.app/api/models", "method": "GET", "can_execute": true, ...}}

"""

    # Load endpoint-specific instructions
    endpoint_instruction = ""
    try:
        from app.ai_agent.instructions import get_instruction_for_endpoint
        instruction = get_instruction_for_endpoint(endpoint)
        if instruction and instruction.get("instruction_text"):
            endpoint_instruction = f"""

============================================================
ENDPOINT-SPECIFIC INSTRUCTIONS: {instruction['name']}
============================================================

{instruction['instruction_text']}
"""
    except ImportError:
        pass

    return f"""
You are the API action planner inside PromptXL.

Your ONLY job is to understand the user's request
and prepare an API action.

Do NOT call the API.

Do NOT claim that the API operation was completed.

The backend will execute the API call after your response.

============================================================
CONVERSATION HISTORY
============================================================

{history_text}
{previous_output_text}

============================================================
CURRENT USER REQUEST
============================================================

{prompt}

============================================================
ENDPOINT
============================================================

{endpoint or "Not provided"}

{all_endpoints_text}
============================================================
IMPORTANT - ENDPOINT SELECTION
============================================================

If the user mentions a specific endpoint in their request,
use THAT endpoint instead of the default endpoint above.

For example:
- User: "get me all models" → use /api/models or /models
- User: "show dimensions" → use /api/dimensions or /dimensions
- User: "fetch items from /api/items" → use /api/items

Do NOT always use the default endpoint. Use the endpoint
that matches what the user is asking for.

============================================================
DETECTED HTTP METHOD
============================================================

{method}

============================================================
API REQUEST SCHEMA
============================================================

{schema_text}

============================================================
IMPORTANT RULES
============================================================

1. The detected HTTP method is authoritative.

2. NEVER change POST to GET for a create/add operation.

3. NEVER change GET to POST for a read/list operation.

4. If the original conversation started with:
   create
   add
   insert
   register
   make

   preserve POST even when the current message is only
   a follow-up answer.

5. If the original conversation started with:
   update
   edit
   modify
   change
   rename

   preserve PATCH or PUT.

6. If the original conversation started with:
   delete
   remove
   destroy
   erase

   preserve DELETE.

7. The latest user message can be only an answer
   to the previous assistant question.

8. IMPORTANT - CHECK CONVERSATION HISTORY:
    Before asking for missing information, CHECK if the user
    already provided this information in the conversation history.
    If yes, use that value instead of asking again.

9. IMPORTANT - REMEMBER ANSWERS:
    If the user answered a question,
    REMEMBER that answer and include it in your request_body.
    Do NOT ask for the same information again.

10. Never invent field values.

11. Never use placeholder values.

12. Use ONLY fields defined by the API schema.

{endpoint_instruction}
============================================================
OUTPUT FORMAT
============================================================

Return ONLY valid JSON.

Example for GET or complete POST:

{{
    "can_execute": true,
    "method": "{method}",
    "request_body": null,
    "missing_fields": [],
    "message": ""
}}

Example for incomplete POST:

{{
    "can_execute": false,
    "method": "POST",
    "request_body": null,
    "missing_fields": ["list_name"],
    "message": "What should the list name be?"
}}

============================================================
ENDPOINT OVERRIDE (REQUIRED)
============================================================

You MUST return the "endpoint" field in your response to specify
which API endpoint to use.

For example, if the user asks for "models" and the endpoint is "/api/models":

{{
    "endpoint": "/api/models",
    "can_execute": true,
    "method": "GET",
    "request_body": null,
    "missing_fields": [],
    "message": ""
}}

Do not return markdown.
Do not return explanations outside JSON.
""".strip()


# ============================================================
# PROVIDER RESPONSE HELPERS
# ============================================================


def get_provider_name(
    provider_context,
    fallback=None,
):
    if isinstance(
        provider_context,
        dict,
    ):
        return provider_context.get(
            "provider"
        )

    return getattr(
        provider_context,
        "provider",
        fallback,
    )


def get_model_name(
    provider_context,
    fallback=None,
):
    if isinstance(
        provider_context,
        dict,
    ):
        return provider_context.get(
            "model"
        )

    return getattr(
        provider_context,
        "model",
        fallback,
    )


# ============================================================
# MAIN AI AGENT
# ============================================================


async def process_prompt(
    db: Session,
    user,
    prompt: str,
    endpoint_id: int | None = None,
    endpoint: str | None = None,
    external_tenant: str | None = None,
    provider: str | None = None,
    model: str | None = None,
    previous_output: dict | None = None,
    method: str | None = None,
    request_body: dict | None = None,
    conversation_history: list[dict] | None = None,
):

    # ========================================================
    # 0. CLEAN TRANSACTION STATE
    # ========================================================
    
    # Rollback any pending transaction to start fresh
    # This handles cases where a prior failed operation left the session in an aborted state
    try:
        db.rollback()
    except Exception:
        pass

    # ========================================================
    # 1. VALIDATE PROMPT
    # ========================================================

    if not prompt or not prompt.strip():

        raise ValueError(
            "Prompt is required."
        )

    original_prompt = prompt.strip()

    # ========================================================
    # 2. GET CONNECTION
    # ========================================================

    connection = crud.get_connection(
        db=db,
        tenant_id=user.tenant_id,
        user_id=user.id,
    )

    if not connection:

        raise ValueError(
            "Please connect the external API first."
        )

    # ========================================================
    # 3. DIRECT ENDPOINT FROM PROMPT
    # ========================================================

    # Always try to extract endpoint from prompt first
    # This allows "create a list" to override the UI's selected endpoint
    
    (
        detected_endpoint,
        cleaned_prompt,
    ) = extract_endpoint_from_prompt(
        original_prompt
    )

    if detected_endpoint:
        # If prompt mentions a specific endpoint, use it
        # This overrides whatever endpoint was passed in
        endpoint = detected_endpoint
        prompt = cleaned_prompt
    elif endpoint:
        # No endpoint in prompt, use the passed-in endpoint
        prompt = original_prompt
    else:
        # No endpoint at all
        prompt = original_prompt

    # ========================================================
    # 3.5. SIMPLE CHAT - NO ENDPOINT
    # ========================================================
    
    # Check if this is a simple conversational message
    # (not endpoint-related)
    
    is_simple_chat = False
    
    if not endpoint and endpoint_id is None:
        # No endpoint info provided - treat as simple chat
        is_simple_chat = True
    elif endpoint_id is not None and not endpoint:
        # endpoint_id provided but no URL in prompt
        # Check if prompt looks like casual conversation
        casual_patterns = [
            r'^(hi|hello|hey|yo|sup|howdy|greetings)',  # greetings
            r'^(thanks|thank you|thx|ty)',  # thanks
            r'^(bye|goodbye|see ya|take care)',  # farewells
            r'^(how are you|how do you do|what\'s up|wassup)',  # how are you
            r'^(nice|cool|awesome|great|good)',  # positive reactions
            r'^(sorry|apologies|my bad)',  # apologies
            r'^(what can you do|help me|help)',  # help requests
            r'^(who are you|what are you|tell me about yourself)',  # identity
            r'^[^a-zA-Z]*$',  # just symbols/numbers
        ]
        
        prompt_lower = prompt.lower().strip()
        for pattern in casual_patterns:
            if re.match(pattern, prompt_lower):
                is_simple_chat = True
                break
    
    if is_simple_chat:

        # Set up provider for simple chat
        provider_selector = ProviderSelector()
        provider_context = (
            await provider_selector.get_provider(
                user=user,
                provider=provider,
                model=model,
            )
        )
        
        generation_service = GenerationService()
        
        # Simple conversational prompt
        chat_prompt = (
            f"User: {prompt}\n"
            f"AI:"
        )
        
        response = await generation_service.generate(
            provider=provider_context,
            prompt=chat_prompt,
        )
        
        # Extract text from response dict
        message_text = response.get("text", str(response))
        
        # Clean up any think/reasoning tags from AI response
        message_text = re.sub(
            r'<think>.*?</think>',
            '',
            message_text,
            flags=re.DOTALL | re.IGNORECASE
        ).strip()
        
        # If the response is a JSON string, extract just the message value
        if message_text.startswith("{") and message_text.endswith("}"):
            try:
                parsed = json.loads(message_text)
                # Look for common message fields
                if "message" in parsed:
                    message_text = parsed["message"]
                elif "text" in parsed:
                    message_text = parsed["text"]
                elif "content" in parsed:
                    message_text = parsed["content"]
                elif "response" in parsed:
                    message_text = parsed["response"]
            except json.JSONDecodeError:
                pass  # Not valid JSON, keep as is
        
        message_text = message_text.strip()
        
        return {
            "success": True,
            "type": "text",
            "message": message_text,
            "data": None,
            "components": [],
            "endpoint_id": None,
            "status_code": None,
            "provider": get_provider_name(
                provider_context,
                provider,
            ),
            "model": get_model_name(
                provider_context,
                model,
            ),
            "method": None,
            "endpoint": None,
        }

    # ========================================================
    # 4. TENANT
    # ========================================================

    api_tenant = (
        external_tenant
        or connection.external_tenant
    )

    if not api_tenant:

        raise ValueError(
            "External tenant is required."
        )

    # ========================================================
    # 5. FIND ENDPOINT
    # ========================================================

    endpoint_url = endpoint

    if (
        endpoint_id is not None
        and not endpoint_url
    ):

        endpoint_obj = crud.get_endpoint(
            db,
            connection.id,
            endpoint_id,
        )

        if not endpoint_obj:

            raise ValueError(
                "Connected endpoint not found."
            )

        endpoint_url = endpoint_obj.endpoint

    # ========================================================
    # 6. HTTP METHOD
    # ========================================================

    if method:

        http_method = (
            method
            .upper()
            .strip()
        )

    else:

        http_method = detect_http_method(
            prompt,
            conversation_history,
        )

    if http_method not in {
        "GET",
        "POST",
        "PUT",
        "PATCH",
        "DELETE",
    }:

        raise ValueError(
            f"Unsupported HTTP method: {http_method}"
        )

    # ========================================================
    # 7. PROVIDER
    # ========================================================

    provider_selector = ProviderSelector()

    provider_context = (
        await provider_selector.get_provider(
            user=user,
            provider=provider,
            model=model,
        )
    )

    generation_service = GenerationService()

    # ========================================================
    # 8. REQUEST SCHEMA
    # ========================================================

    request_schema = get_request_schema(
        endpoint_url,
        http_method,
    )

    # ========================================================
    # 8.5 GET ALL ENDPOINTS FOR GENERIC SELECTION
    # ========================================================

    all_endpoints_data = []
    if connection:
        try:
            from app.ai_agent import crud as endpoint_crud
            endpoints_from_db = endpoint_crud.get_endpoints(db, connection.id)
            for ep in endpoints_from_db:
                all_endpoints_data.append({
                    "id": ep.id,
                    "endpoint": ep.endpoint,
                    "method": ep.method,
                    "description": ep.description,
                    "resource_name": ep.resource_name,
                    "request_schema": ep.request_schema,
                    "response_schema": ep.response_schema,
                })
        except Exception as e:
            print(f"Could not fetch all endpoints: {e}")
            # Rollback the transaction to clear the aborted state
            db.rollback()
            all_endpoints_data = []

    # ========================================================
    # 9. INTENT PLANNING
    # ========================================================
    # The new Intent-based flow:
    # 1. Build intent planning prompt (replaces build_action_prompt)
    # 2. Generate intent from LLM (replaces parse_action_response)
    # 3. Handle follow-ups using is_follow_up_request + resolve_follow_up
    # 4. Select best endpoint using EndpointSelector
    # 5. Validate request body against schema
    # 6. Execute via MCP
    # ========================================================

    # Step 1: Check if this is a follow-up request
    pending_intent = None
    if previous_output:
        pending_intent = Intent.from_previous_output(previous_output)

    if pending_intent and is_follow_up_request(prompt, previous_output):
        print(f"\n========== FOLLOW-UP DETECTED ==========")
        print(f"PENDING INTENT: action={pending_intent.action}, resource={pending_intent.resource}")
        print(f"PENDING MISSING FIELDS: {pending_intent.missing_fields}")
        print(f"CURRENT PROMPT: '{prompt}'")
        print("==========================================\n")

        # Resolve the follow-up using the new function
        resolved_intent = resolve_follow_up(prompt, pending_intent, previous_output)

        # If resolved, use the resolved intent for execution
        if resolved_intent.can_execute:
            intent = resolved_intent
            print(f"\n========== FOLLOW-UP RESOLVED ==========")
            print(f"RESOLVED INTENT: {intent.action} on {intent.resource}")
            print(f"REQUEST BODY: {json.dumps(intent.request_body, indent=2)}")
            print("==========================================\n")
    else:
        # Step 2: Build intent planning prompt
        # Note: HTTP method comes from DB endpoint, NOT from intent planning
        intent_planning_prompt = build_intent_planning_prompt(
            prompt=prompt,
            intent=None,  # No previous intent context for new requests
            conversation_history=conversation_history,
            candidate_endpoints=all_endpoints_data,
            previous_output=previous_output,
        )

        # Step 3: Generate intent from LLM
        raw_intent = (
            await generation_service.generate(
                provider=provider_context,
                prompt=intent_planning_prompt,
            )
        )

        print("\n========== RAW INTENT RESPONSE ==========")
        print(raw_intent)
        print("=========================================")

        # Step 4: Parse intent response
        intent = parse_intent_response(raw_intent)

        print("\n========== PARSED INTENT ==========")
        print("action:", intent.action)
        print("resource:", intent.resource)
        print("operation:", intent.operation)
        print("can_execute:", intent.can_execute)
        print("missing_fields:", intent.missing_fields)
        print("message:", intent.message)
        print("selected_endpoint_id:", intent.selected_endpoint_id)
        print("request_body:", intent.request_body)
        print("===================================\n")

        # Debug logging
        print("\n========== INTENT PLANNING DEBUG ==========")
        print(f"CURRENT PROMPT: {prompt}")
        print(f"CONVERSATION HISTORY COUNT: {len(conversation_history) if conversation_history else 0}")
        print(f"DETECTED METHOD: {http_method}")
        print(f"SELECTED ENDPOINT: {endpoint_url}")
        print(f"ALL ENDPOINTS DATA COUNT: {len(all_endpoints_data) if all_endpoints_data else 0}")
        print(f"LLM INTENT: action={intent.action}, resource={intent.resource}, operation={intent.operation}")
        print(f"LLM METHOD: {intent.method}")
        print(f"LLM REQUEST BODY: {intent.request_body}")
        print(f"LLM MISSING FIELDS: {intent.missing_fields}")
        print(f"LLM SELECTED ENDPOINT ID: {intent.selected_endpoint_id}")
        print("============================================\n")

    # ========================================================
    # 4.5. VALIDATE RESOURCE EXTRACTION
    # ========================================================
    # If LLM failed to extract resource, we CANNOT proceed with endpoint selection.
    # This is a CRITICAL safeguard - never select arbitrary endpoints based on
    # generic action/method when the user clearly mentioned a specific resource.
    #
    # NOTE: We check resource validity REGARDLESS of can_execute flag.
    # Even if can_execute=False (due to missing fields), we need a valid resource
    # to know which endpoint to ask the user to complete.

    _intent_resource = getattr(intent, 'resource', None) or None

    # ========================================================
    # FALLBACK: Try to resolve resource from prompt if LLM failed
    # ========================================================
    # If LLM returned None/empty resource, try to match the prompt against
    # registered endpoint metadata (resource_name, path, description)
    if _intent_resource is None or (isinstance(_intent_resource, str) and not _intent_resource.strip()):
        print(f"\n========== LLM RESOURCE EXTRACTION FAILED ==========")
        print(f"LLM RETURNED RESOURCE: {_intent_resource}")
        print(f"ATTEMPTING FALLBACK RESOURCE MATCHING...")
        print("====================================================\n")

        resolved_resource = _resolve_resource_from_prompt(prompt, all_endpoints_data)

        if resolved_resource:
            print(f"\n========== FALLBACK RESOLUTION SUCCESS ==========")
            print(f"PROMPT: {prompt}")
            print(f"RESOLVED RESOURCE: {resolved_resource}")
            print("================================================\n")

            # Update the intent with the resolved resource
            intent.resource = resolved_resource
            _intent_resource = resolved_resource
        else:
            # Resource cannot be resolved - return clarification
            available_resources = []
            if all_endpoints_data:
                for ep in all_endpoints_data:
                    rn = ep.get("resource_name")
                    if rn and rn not in available_resources:
                        available_resources.append(rn)

            resources_list = ", ".join(available_resources) if available_resources else "unknown"

            print(f"\n========== RESOURCE EXTRACTION FAILED ==========")
            print(f"PROMPT: {prompt}")
            print(f"LLM RETURNED ACTION: {getattr(intent, 'action', 'unknown')}")
            print(f"LLM RETURNED RESOURCE: {_intent_resource}")
            print(f"LLM RETURNED CAN_EXECUTE: {getattr(intent, 'can_execute', 'unknown')}")
            print(f"AVAILABLE RESOURCES: {resources_list}")
            print("================================================")
            print("PREVENTING: Arbitrary endpoint selection due to missing resource")
            print("================================================\n")

            # Return schema-compatible clarification response
            return AIAgentPromptResponse(
                success=True,
                type="text",
                message=f"I couldn't identify which resource you want to access. "
                        f"Your request mentioned a resource but I couldn't match it. "
                        f"Available resources: {resources_list}. Which would you like to access?",
                data=None,
                components=[],
                endpoint_id=None,
                status_code=None,
                provider=getattr(provider_context, 'provider_name', None) if provider_context else None,
                model=getattr(provider_context, 'model', None) if provider_context else None,
                method=None,
                endpoint=None,
            )

    # Step 5: Use Intent's method if available, otherwise use backend-detected method
    # IMPORTANT: Backend detected method is authoritative - prevents AI from returning
    # incorrect method (e.g., GET when user started a create operation)
    action_method = get_method_from_intent(intent) or http_method

    # Step 6: Validate the method
    if action_method not in {"GET", "POST", "PUT", "PATCH", "DELETE"}:
        raise ValueError(f"Unsupported HTTP method: {action_method}")

    # ========================================================
    # 10. REQUEST BODY - Use Intent's request_body
    # ========================================================

    # Start with Intent's request_body
    ai_request_body = intent.request_body

    if ai_request_body is not None:

        if not isinstance(
            ai_request_body,
            dict,
        ):

            raise ValueError(
                "AI request body must be a JSON object."
            )

        ai_request_body = (
            normalize_request_body(
                ai_request_body
            )
        )

    # ========================================================
    # 11. FRONTEND REQUEST BODY OVERRIDE
    # ========================================================

    if request_body is not None:

        if not isinstance(
            request_body,
            dict,
        ):

            raise ValueError(
                "Request body must be a JSON object."
            )

        ai_request_body = (
            normalize_request_body(
                request_body
            )
        )

    # ========================================================
    # 12. ENDPOINT SELECTION - Use EndpointSelector
    # ========================================================
    # If Intent has a selected_endpoint_id, validate it exists and is authorized
    # If not, use EndpointSelector to find the best match

    target_endpoint = None
    target_endpoint_id = None

    if intent.selected_endpoint_id is not None and connection:
        # Validate the LLM-selected endpoint
        from app.ai_agent import crud as endpoint_crud
        endpoint_obj = endpoint_crud.get_endpoint(
            db,
            connection.id,
            intent.selected_endpoint_id,
        )
        if endpoint_obj:
            target_endpoint = {
                "id": endpoint_obj.id,
                "endpoint": endpoint_obj.endpoint,
                "method": endpoint_obj.method,
                "resource_name": endpoint_obj.resource_name,
                "request_schema": endpoint_obj.request_schema,
            }
            target_endpoint_id = endpoint_obj.id
            print(f"\n========== ENDPOINT VALIDATED (from LLM selection) ==========")
            print(f"ENDPOINT ID: {target_endpoint_id}")
            print(f"ENDPOINT URL: {endpoint_obj.endpoint}")
            print(f"METHOD: {endpoint_obj.method}")
            print("=============================================================\n")

    if target_endpoint is None and all_endpoints_data:
        # Use EndpointSelector to find best endpoint
        selector = EndpointSelector(
            endpoints=all_endpoints_data,
            intent=intent,
            method=action_method,
        )
        target_endpoint = selector.select_endpoint()
        if target_endpoint:
            target_endpoint_id = target_endpoint.get("id")

    if target_endpoint is None:
        raise ValueError(
            f"Could not find suitable endpoint for intent: "
            f"{intent.action} on {intent.resource}"
        )

    # ========================================================
    # 13. VALIDATE REQUIRED FIELDS against selected endpoint's schema
    # ========================================================

    endpoint_request_schema = target_endpoint.get("request_schema")
    missing_fields = []

    if endpoint_request_schema:
        missing_fields = validate_request_body_against_schema(
            request_body=ai_request_body or {},
            schema=endpoint_request_schema,
            # path_parameters=path_parameters,
        )

    # Also check Intent's reported missing fields
    if intent.missing_fields:
        for field in intent.missing_fields:
            if field not in missing_fields:
                missing_fields.append(field)

    # ========================================================
    # 14. MISSING INFORMATION - Return with Intent details
    # ========================================================

    if missing_fields:

        message = intent.message

        if not message:
            readable_fields = ", ".join(missing_fields)
            message = f"Please provide: {readable_fields}."

        return {
            "success": True,
            "type": "text",
            "message": message,
            "data": None,
            "components": [],
            "endpoint_id": target_endpoint_id,
            "status_code": None,
            "provider": get_provider_name(
                provider_context,
                provider,
            ),
            "model": get_model_name(
                provider_context,
                model,
            ),
            "method": action_method,
            "endpoint": target_endpoint.get("endpoint"),
            # Include intent data so frontend can pass it back for follow-ups
            "can_execute": False,
            "missing_fields": missing_fields,
            "request_body": ai_request_body,
        }

    # ========================================================
    # 15. CHECK CAN EXECUTE
    # ========================================================

    if not intent.can_execute:

        message = intent.message or "More information is required."

        return {
            "success": True,
            "type": "text",
            "message": message,
            "data": None,
            "components": [],
            "endpoint_id": target_endpoint_id,
            "status_code": None,
            "provider": get_provider_name(
                provider_context,
                provider,
            ),
            "model": get_model_name(
                provider_context,
                model,
            ),
            "method": action_method,
            "endpoint": target_endpoint.get("endpoint"),
            # Include intent data so frontend can pass it back for follow-ups
            "can_execute": False,
            "missing_fields": intent.missing_fields or [],
            "request_body": intent.request_body,
        }

    # ========================================================
    # 16. FINAL SAFETY VALIDATION
    # ========================================================

    # Transform request body for the external API using endpoint schema
    transformed_request_body = transform_request_body_for_endpoint(
        request_body=ai_request_body or {},
        endpoint=target_endpoint,
        method=action_method,
    )

    # ========================================================
    # 17. MCP EXECUTION
    # ========================================================

    # Use the already-selected target_endpoint
    effective_endpoint_url = target_endpoint.get("endpoint")

    print(f"\n{'='*60}")
    print(f"INTENT-BASED MCP EXECUTION:")
    print(f"  PROMPT: {original_prompt}")
    print(f"  METHOD: {action_method}")
    print(f"  ENDPOINT: {effective_endpoint_url}")
    print(f"  ENDPOINT ID: {target_endpoint_id}")
    print(f"  REQUEST BODY: {json.dumps(transformed_request_body, indent=2)}")
    print(f"  INTENT: action={intent.action}, resource={intent.resource}")
    print(f"{'='*60}\n")

    # MCP EXECUTION
    mcp_result = await execute_mcp_tool_from_agent(
        db=db,
        user=user,
        tool_name="generic_execute",
        arguments={
            "endpoint_id": target_endpoint_id,
            "method": action_method,
            "path_parameters": intent.path_parameters or {},
            "query_parameters": intent.query_parameters or {},
            "request_body": transformed_request_body,
        },
        endpoint_id=target_endpoint_id,
    )

    # Determine response type based on operation
    if action_method == "GET":
        response_type = "data"
        response_message = "Here are the results."
    elif action_method == "POST":
        response_type = "text"
        response_message = "Resource created successfully."
    elif action_method in ("PUT", "PATCH"):
        response_type = "text"
        response_message = "Resource updated successfully."
    else:  # DELETE
        response_type = "text"
        response_message = "Resource deleted successfully."

    # Get the actual status code and data from MCP result
    mcp_status = mcp_result.get("status_code", 200)
    mcp_data = mcp_result.get("data")
    mcp_success = mcp_result.get("success", False)

    # If MCP reports failure, return error response
    if not mcp_success:
        return {
            "success": False,
            "type": "error",
            "message": mcp_result.get("error") or mcp_result.get("message") or "Operation failed.",
            "data": mcp_data,
            "components": [],
            "endpoint_id": target_endpoint_id,
            "status_code": mcp_status,
            "provider": get_provider_name(
                provider_context,
                provider,
            ),
            "model": get_model_name(
                provider_context,
                model,
            ),
            "method": action_method,
            "endpoint": effective_endpoint_url,
        }

    # Return MCP result with proper AIAgentPromptResponse structure
    final_response = {
        "success": True,
        "type": response_type,
        "message": response_message,
        "data": mcp_data,
        "components": [],
        "endpoint_id": target_endpoint_id,
        "status_code": mcp_status,
        "provider": get_provider_name(
            provider_context,
            provider,
        ),
        "model": get_model_name(
            provider_context,
            model,
        ),
        "method": action_method,
        "endpoint": effective_endpoint_url or endpoint,
    }

    print(f"\n[AI AGENT FINAL RESPONSE]")
    print(json.dumps(final_response, indent=2))
    print(f"{'='*60}\n")

    return final_response


# ============================================================
# MCP INTEGRATION
# ============================================================
# 
# This section provides integration between the existing AI Agent
# and the MCP (Model Context Protocol) tools.
#
# The MCP tools provide structured List CRUD operations that:
# 1. Use existing AIAgentConnection infrastructure
# 2. Handle authorization (user + tenant verification)
# 3. Transform snake_case to camelCase for external API
# 4. Handle HTTP 2xx as success, 4xx/5xx as failure
#
# Usage:
#   result = await execute_mcp_tool_from_agent(
#       db=db,
#       user=current_user,
#       tool_name="create_list",
#       arguments={"list_name": "Sales", "standard_list": False},
#       endpoint_id=9,
#   )
#
# ============================================================


async def execute_mcp_tool_from_agent(
    db: Session,
    user,
    tool_name: str,
    arguments: dict,
    endpoint_id: int | None = None,
) -> dict:
    """
    Execute an MCP tool from within the AI Agent flow.
    
    This function bridges the existing AI Agent service with MCP tools,
    reusing the existing:
    - User authentication (user.id, user.tenant_id)
    - Connection authorization
    - Endpoint validation
    - Encryption/token handling
    
    Args:
        db: Database session
        user: Current authenticated user object (must have .id and .tenant_id)
        tool_name: Name of the MCP tool to execute
        arguments: Tool-specific arguments (e.g., {"list_name": "Sales"})
        endpoint_id: Optional specific endpoint ID to use
        
    Returns:
        dict with keys:
        - success: bool
        - operation: str
        - status_code: int
        - message: str
        - data: any (for GET) or None
        - error: any (if success=False)
    """
    from app.ai_agent.mcp.tools import execute_mcp_tool
    
    print(f"\n{'='*60}")
    print(f"MCP TOOL EXECUTION FROM AI AGENT:")
    print(f"  TOOL: {tool_name}")
    print(f"  USER ID: {user.id}")
    print(f"  TENANT ID: {user.tenant_id}")
    print(f"  ENDPOINT ID: {endpoint_id}")
    print(f"  ARGUMENTS: {arguments}")
    print(f"{'='*60}\n")
    
    try:
        # Execute MCP tool
        # Include endpoint_id in arguments if provided
        tool_arguments = dict(arguments)
        if endpoint_id is not None:
            tool_arguments["endpoint_id"] = endpoint_id

        result = await execute_mcp_tool(
            tool_name=tool_name,
            db=db,
            user_id=user.id,
            tenant_id=user.tenant_id,
            arguments=tool_arguments,
        )
        
        print(f"\n{'='*60}")
        print(f"MCP TOOL RESULT:")
        print(f"  SUCCESS: {result.get('success')}")
        print(f"  STATUS CODE: {result.get('status_code')}")
        print(f"  MESSAGE: {result.get('message')}")
        print(f"{'='*60}\n")
        
        return result
        
    except Exception as e:
        print(f"\n{'='*60}")
        print(f"MCP TOOL ERROR:")
        print(f"  EXCEPTION: {str(e)}")
        print(f"{'='*60}\n")
        
        return {
            "success": False,
            "operation": tool_name,
            "status_code": 500,
            "error": str(e),
            "message": "Internal error during MCP tool execution.",
            "data": None,
        }


# ============================================================
# MCP TOOL SELECTION HELPERS
# ============================================================


def detect_mcp_tool_from_prompt(prompt: str) -> tuple[str | None, dict | None]:
    """
    Detect if a prompt should trigger an MCP tool call.
    
    This is a simple keyword-based detector. In production,
    this would be handled by the LLM.
    
    Args:
        prompt: User's prompt text
        
    Returns:
        Tuple of (tool_name, arguments) if detected, else (None, None)
    """
    prompt_lower = prompt.lower().strip()
    
    # get_lists patterns
    get_lists_patterns = [
        "get me the lists",
        "show all lists",
        "get all lists",
        "show the lists",
        "list all lists",
        "what lists exist",
        "get lists",
    ]
    
    for pattern in get_lists_patterns:
        if pattern in prompt_lower:
            return ("get_lists", {})
    
    # create_list patterns
    create_list_patterns = [
        "create a list called ",
        "create a new list called ",
        "create a standard list called ",
    ]
    
    for pattern in create_list_patterns:
        if pattern in prompt_lower:
            # Extract list name
            list_name = prompt_lower.split(pattern)[-1].strip()
            standard = "standard list" in prompt_lower
            return ("create_list", {"list_name": list_name, "standard_list": standard})
    
    # Simple "create a list" without name
    if "create a list" in prompt_lower or "create a new list" in prompt_lower:
        # Missing list_name - return None to trigger clarification
        return (None, None)
    
    # delete_list patterns
    delete_patterns = [
        "delete the ",
        "delete list ",
    ]
    
    for pattern in delete_patterns:
        if pattern in prompt_lower and "list" in prompt_lower:
            # Extract list name
            parts = prompt_lower.split(pattern)
            if len(parts) > 1:
                list_name = parts[-1].strip().rstrip(" list").strip()
                if list_name:
                    return ("delete_list", {"name": list_name})
    
    # update_list - not yet implemented
    if "update " in prompt_lower and "list" in prompt_lower:
        return ("update_list", {"name": ""})  # Will return not implemented
    
    return (None, None)


# ============================================================
# MCP-ENHANCED PROCESSING
# ============================================================


async def process_prompt_with_mcp(
    db: Session,
    user,
    prompt: str,
    endpoint_id: int | None = None,
    endpoint: str | None = None,
    external_tenant: str | None = None,
    provider: str | None = None,
    model: str | None = None,
    previous_output: dict | None = None,
    method: str | None = None,
    request_body: dict | None = None,
    conversation_history: list[dict] | None = None,
    use_mcp: bool = True,
) -> dict:
    """
    Process a prompt with optional MCP tool support.
    
    This function first checks if the prompt matches an MCP tool pattern.
    If so, it executes the MCP tool directly instead of going through
    the full LLM-based AI Agent flow.
    
    Args:
        Same as process_prompt() plus:
        use_mcp: Whether to attempt MCP tool detection (default True)
        
    Returns:
        Same structure as process_prompt()
    """
    if not use_mcp:
        # Fall back to regular processing
        return await process_prompt(
            db=db,
            user=user,
            prompt=prompt,
            endpoint_id=endpoint_id,
            endpoint=endpoint,
            external_tenant=external_tenant,
            provider=provider,
            model=model,
            previous_output=previous_output,
            method=method,
            request_body=request_body,
            conversation_history=conversation_history,
        )
    
    # Try to detect MCP tool
    tool_name, arguments = detect_mcp_tool_from_prompt(prompt)
    
    if tool_name and arguments is not None:
        # Execute MCP tool
        return await execute_mcp_tool_from_agent(
            db=db,
            user=user,
            tool_name=tool_name,
            arguments=arguments,
            endpoint_id=endpoint_id,
        )
    
    # No MCP tool detected - fall back to regular processing
    return await process_prompt(
        db=db,
        user=user,
        prompt=prompt,
        endpoint_id=endpoint_id,
        endpoint=endpoint,
        external_tenant=external_tenant,
        provider=provider,
        model=model,
        previous_output=previous_output,
        method=method,
        request_body=request_body,
        conversation_history=conversation_history,
    )
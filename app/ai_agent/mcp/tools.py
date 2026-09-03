"""
MCP Tools - List CRUD operations.

This module defines MCP tools for List management:
- get_lists: Retrieve all lists
- create_list: Create a new list
- update_list: Update an existing list (TODO: schema not fully defined)
- delete_list: Delete a list

All tools:
1. Are authorized via MCPContext
2. Use existing endpoint execution services
3. Transform internal snake_case to external camelCase
4. Handle HTTP 2xx as success, 4xx/5xx as failure
"""

import json
from typing import Any, Optional

from sqlalchemy.orm import Session

from app.ai_agent.mcp.context import (
    MCPContext,
    get_mcp_context,
    authorize_endpoint,
    build_mcp_result,
)


# ============================================================
# TOOL SCHEMAS
# ============================================================


# Schema for get_lists tool
GET_LISTS_SCHEMA = {
    "name": "get_lists",
    "description": "Retrieve all lists from the connected external API. Use this when the user wants to see, view, or get all available lists.",
}

# Schema for create_list tool
CREATE_LIST_SCHEMA = {
    "name": "create_list",
    "description": "Create a new list in the external API. Required: list_name. Optional: standard_list (defaults to false).",
    "parameters": {
        "type": "object",
        "properties": {
            "list_name": {
                "type": "string",
                "description": "The name of the list to create. Required.",
            },
            "standard_list": {
                "type": "boolean",
                "description": "Whether this is a standard list. Defaults to false.",
                "default": False,
            },
        },
        "required": ["list_name"],
    },
}

# Schema for update_list tool - NOTE: PUT body schema not fully defined
UPDATE_LIST_SCHEMA = {
    "name": "update_list",
    "description": "Update an existing list in the external API. The path parameter 'name' is required. NOTE: The PUT request body schema is not fully defined - do not use until API schema is confirmed.",
    "parameters": {
        "type": "object",
        "properties": {
            "name": {
                "type": "string",
                "description": "The current name of the list to update (path parameter).",
            },
            # TODO: Add request body fields once PUT schema is confirmed
            # This is intentionally left incomplete per requirements
        },
        "required": ["name"],
    },
}

# Schema for delete_list tool
DELETE_LIST_SCHEMA = {
    "name": "delete_list",
    "description": "Delete a list from the external API. The list name is required.",
    "parameters": {
        "type": "object",
        "properties": {
            "name": {
                "type": "string",
                "description": "The name of the list to delete.",
            },
        },
        "required": ["name"],
    },
}


# ============================================================
# REQUEST BODY TRANSFORMATION
# ============================================================


def to_camel_case(snake_str: str) -> str:
    """
    Convert snake_case to camelCase.
    
    Examples:
        list_name -> listName
        standard_list -> standardList
        order_id -> orderId
        customer_name -> customerName
    """
    components = snake_str.split('_')
    return components[0] + ''.join(x.title() for x in components[1:])


def transform_request_body(request_body: dict) -> dict:
    """
    Transform internal snake_case request body to external API camelCase.
    
    Generic transformation that handles any snake_case key.
    
    Args:
        request_body: Internal request body with snake_case keys
        
    Returns:
        External API request body with camelCase keys
    """
    if not request_body:
        return {}
    
    result = {}
    for key, value in request_body.items():
        # Convert snake_case to camelCase
        camel_key = to_camel_case(key)
        result[camel_key] = value
    
    return result


def transform_list_request_body(request_body: dict) -> dict:
    """
    Transform internal snake_case request body to external API camelCase.
    
    Internal schema:
        list_name -> listName
        standard_list -> standardList
        
    Args:
        request_body: Internal request body with snake_case keys
        
    Returns:
        External API request body with camelCase keys
    """
    if not request_body:
        return {}
    
    transformation_map = {
        "list_name": "listName",
        "standard_list": "standardList",
    }
    
    result = {}
    for key, value in request_body.items():
        if key in transformation_map:
            result[transformation_map[key]] = value
        else:
            result[key] = value
    
    return result


# ============================================================
# HTTP EXECUTION HELPERS
# ============================================================


def execute_external_request(
    context: MCPContext,
    method: str,
    path_or_url: str,
    request_body: Optional[dict] = None,
) -> dict:
    """
    Execute an HTTP request against the external API.

    This function reuses the existing endpoint execution infrastructure:
    - Uses call_direct_endpoint from endpoint_service
    - Builds proper headers with x-api-token and Tenant
    - Transforms request body to camelCase

    Args:
        context: MCP context with authorized connection
        method: HTTP method (GET, POST, PUT, DELETE)
        path_or_url: API path (e.g., "/api/lists") OR full URL
        request_body: Optional request body (will be transformed to camelCase)

    Returns:
        dict with keys: success, status_code, data, error
    """
    # Import here to avoid circular imports
    from app.ai_agent.endpoint_service import call_direct_endpoint
    from urllib.parse import urlparse

    # Check if path_or_url is already a full URL
    parsed = urlparse(path_or_url)

    if parsed.scheme and parsed.netloc:
        # It's already a full URL, use it directly
        full_url = path_or_url
    else:
        # It's a path, get base URL from connection's endpoints
        endpoints = context.connection.endpoints if context.connection else []
        if not endpoints:
            return {
                "success": False,
                "status_code": None,
                "error": "No endpoints configured for this connection.",
            }

        # Get base URL from first endpoint
        first_endpoint = endpoints[0].endpoint
        parsed = urlparse(first_endpoint)
        base_url = f"{parsed.scheme}://{parsed.netloc}"

        # Build full URL
        full_url = base_url + path_or_url if path_or_url.startswith("/") else base_url + "/" + path_or_url
    
    # Transform request body if present
    external_body = None
    if request_body:
        external_body = transform_request_body(request_body)
    
    print(f"\n{'='*60}")
    print(f"EXTERNAL API REQUEST:")
    print(f"  URL: {full_url}")
    print(f"  METHOD: {method}")
    print(f"  INTERNAL REQUEST BODY: {json.dumps(request_body) if request_body else 'none'}")
    print(f"  EXTERNAL REQUEST BODY: {json.dumps(external_body) if external_body else 'none'}")
    print(f"{'='*60}\n")
    
    try:
        # Execute the request
        result = call_direct_endpoint(
            api_token=context.api_token,
            endpoint=full_url,
            tenant=context.external_tenant,
            method=method,
            payload=external_body,
        )
        
        status_code = result.get("status_code")
        data = result.get("data")
        
        # Determine success based on status code
        is_success = status_code is not None and 200 <= status_code < 300
        
        print(f"\n{'='*60}")
        print(f"EXTERNAL API RESPONSE:")
        print(f"  STATUS CODE: {status_code}")
        print(f"  SUCCESS: {is_success}")
        print(f"  DATA: {json.dumps(data) if data else 'empty'}")
        print(f"{'='*60}\n")
        
        return {
            "success": is_success,
            "status_code": status_code,
            "data": data,
            "error": None if is_success else f"HTTP {status_code}",
        }
        
    except Exception as e:
        print(f"\n{'='*60}")
        print(f"EXTERNAL API ERROR:")
        print(f"  EXCEPTION: {str(e)}")
        print(f"{'='*60}\n")
        
        return {
            "success": False,
            "status_code": None,
            "data": None,
            "error": str(e),
        }


# ============================================================
# MCP TOOL DEFINITIONS
# ============================================================


async def get_lists_tool(
    db: Session,
    user_id: int,
    tenant_id: int,
    endpoint_id: Optional[int] = None,
) -> dict:
    """
    MCP tool: Get all lists.
    
    Executes: GET /api/lists
    
    Returns:
        MCP result with success status, operation name, status code, and data
    """
    print(f"\n{'='*60}")
    print(f"MCP TOOL CALL: get_lists")
    print(f"  USER ID: {user_id}")
    print(f"  TENANT ID: {tenant_id}")
    print(f"  ENDPOINT ID: {endpoint_id}")
    print(f"{'='*60}\n")
    
    try:
        # Get MCP context
        context = get_mcp_context(
            db=db,
            user_id=user_id,
            tenant_id=tenant_id,
            endpoint_id=endpoint_id,
        )
        
        # Execute GET /api/lists
        result = execute_external_request(
            context=context,
            method="GET",
            path="/api/lists",
        )
        
        if result["success"]:
            return build_mcp_result(
                success=True,
                operation="get_lists",
                status_code=result["status_code"],
                data=result["data"],
                message="Lists retrieved successfully.",
            )
        else:
            return build_mcp_result(
                success=False,
                operation="get_lists",
                status_code=result["status_code"],
                error=result["error"],
                message="Failed to retrieve lists.",
            )
            
    except ValueError as e:
        return build_mcp_result(
            success=False,
            operation="get_lists",
            status_code=401,
            error=str(e),
            message="Authorization failed.",
        )
    except Exception as e:
        return build_mcp_result(
            success=False,
            operation="get_lists",
            status_code=500,
            error=str(e),
            message="Internal error while retrieving lists.",
        )


async def create_list_tool(
    db: Session,
    user_id: int,
    tenant_id: int,
    list_name: str,
    standard_list: bool = False,
    endpoint_id: Optional[int] = None,
) -> dict:
    """
    MCP tool: Create a new list.
    
    Executes: POST /api/lists
    Request body: { listName: string, standardList: boolean }
    
    Args:
        db: Database session
        user_id: Current user ID
        tenant_id: Current tenant ID
        list_name: Name of the list to create (required)
        standard_list: Whether this is a standard list (optional, default False)
        endpoint_id: Optional specific endpoint to use
        
    Returns:
        MCP result with success status
    """
    print(f"\n{'='*60}")
    print(f"MCP TOOL CALL: create_list")
    print(f"  USER ID: {user_id}")
    print(f"  TENANT ID: {tenant_id}")
    print(f"  LIST NAME: {list_name}")
    print(f"  STANDARD LIST: {standard_list}")
    print(f"  ENDPOINT ID: {endpoint_id}")
    print(f"{'='*60}\n")
    
    try:
        # Get MCP context
        context = get_mcp_context(
            db=db,
            user_id=user_id,
            tenant_id=tenant_id,
            endpoint_id=endpoint_id,
        )
        
        # Build internal request body
        request_body = {
            "list_name": list_name,
            "standard_list": standard_list,
        }
        
        # Execute POST /api/lists
        result = execute_external_request(
            context=context,
            method="POST",
            path="/api/lists",
            request_body=request_body,
        )
        
        if result["success"]:
            # HTTP 204 No Content is success
            return build_mcp_result(
                success=True,
                operation="create_list",
                status_code=result["status_code"],
                data=None,
                message=f"List '{list_name}' was created successfully.",
            )
        else:
            return build_mcp_result(
                success=False,
                operation="create_list",
                status_code=result["status_code"],
                error=result["error"],
                message="Failed to create list.",
            )
            
    except ValueError as e:
        return build_mcp_result(
            success=False,
            operation="create_list",
            status_code=401,
            error=str(e),
            message="Authorization failed.",
        )
    except Exception as e:
        return build_mcp_result(
            success=False,
            operation="create_list",
            status_code=500,
            error=str(e),
            message="Internal error while creating list.",
        )


async def update_list_tool(
    db: Session,
    user_id: int,
    tenant_id: int,
    name: str,
    # TODO: Add request body fields once PUT schema is confirmed
    # This is intentionally left incomplete per requirements
    endpoint_id: Optional[int] = None,
) -> dict:
    """
    MCP tool: Update an existing list.
    
    Executes: PUT /api/lists/{name}
    
    NOTE: The PUT request body schema is not fully defined in the external API.
    This tool is provided as a stub - do not use until the schema is confirmed.
    
    Args:
        db: Database session
        user_id: Current user ID
        tenant_id: Current tenant ID
        name: Current name of the list (path parameter)
        endpoint_id: Optional specific endpoint to use
        
    Returns:
        MCP result with TODO message
    """
    print(f"\n{'='*60}")
    print(f"MCP TOOL CALL: update_list (NOT YET IMPLEMENTED)")
    print(f"  USER ID: {user_id}")
    print(f"  TENANT ID: {tenant_id}")
    print(f"  LIST NAME: {name}")
    print(f"  ENDPOINT ID: {endpoint_id}")
    print(f"  WARNING: PUT request body schema not defined")
    print(f"{'='*60}\n")
    
    return build_mcp_result(
        success=False,
        operation="update_list",
        status_code=501,
        error="PUT request body schema not defined",
        message=(
            "The update_list tool is not yet implemented because the "
            "PUT /api/lists/{name} request body schema is not defined. "
            "Please confirm the external API schema before implementing."
        ),
    )


async def delete_list_tool(
    db: Session,
    user_id: int,
    tenant_id: int,
    name: str,
    endpoint_id: Optional[int] = None,
) -> dict:
    """
    MCP tool: Delete a list.
    
    Executes: DELETE /api/lists/{name}
    
    Args:
        db: Database session
        user_id: Current user ID
        tenant_id: Current tenant ID
        name: Name of the list to delete
        endpoint_id: Optional specific endpoint to use
        
    Returns:
        MCP result with success status
    """
    print(f"\n{'='*60}")
    print(f"MCP TOOL CALL: delete_list")
    print(f"  USER ID: {user_id}")
    print(f"  TENANT ID: {tenant_id}")
    print(f"  LIST NAME: {name}")
    print(f"  ENDPOINT ID: {endpoint_id}")
    print(f"{'='*60}\n")
    
    try:
        # Get MCP context
        context = get_mcp_context(
            db=db,
            user_id=user_id,
            tenant_id=tenant_id,
            endpoint_id=endpoint_id,
        )
        
        # Execute DELETE /api/lists/{name}
        result = execute_external_request(
            context=context,
            method="DELETE",
            path=f"/api/lists/{name}",
        )
        
        if result["success"]:
            # HTTP 204 No Content is success
            return build_mcp_result(
                success=True,
                operation="delete_list",
                status_code=result["status_code"],
                data=None,
                message=f"List '{name}' was deleted successfully.",
            )
        else:
            return build_mcp_result(
                success=False,
                operation="delete_list",
                status_code=result["status_code"],
                error=result["error"],
                message="Failed to delete list.",
            )
            
    except ValueError as e:
        return build_mcp_result(
            success=False,
            operation="delete_list",
            status_code=401,
            error=str(e),
            message="Authorization failed.",
        )
    except Exception as e:
        return build_mcp_result(
            success=False,
            operation="delete_list",
            status_code=500,
            error=str(e),
            message="Internal error while deleting list.",
        )


# ============================================================
# TOOL REGISTRY
# ============================================================


# Map of tool name to tool function
MCP_TOOLS = {
    "get_lists": get_lists_tool,
    "create_list": create_list_tool,
    "update_list": update_list_tool,
    "delete_list": delete_list_tool,
}


# ============================================================
# GENERIC MCP TOOL - Generic API execution
# ============================================================


async def generic_execute_tool(
    db: Session,
    user_id: int,
    tenant_id: int,
    endpoint_id: int,
    method: str,
    path_parameters: Optional[dict] = None,
    query_parameters: Optional[dict] = None,
    request_body: Optional[dict] = None,
) -> dict:
    """
    Generic MCP tool: Execute any connected API endpoint.

    This tool can dynamically execute any endpoint that the user has connected,
    based on the endpoint_id and method provided.

    Args:
        db: Database session
        user_id: Current user ID
        tenant_id: Current tenant ID
        endpoint_id: The specific endpoint ID to execute (required)
        method: HTTP method (GET, POST, PUT, PATCH, DELETE)
        path_parameters: Dict of path parameters to substitute in URL (e.g., {"id": "123"})
        query_parameters: Dict of query parameters to add to URL
        request_body: Dict for POST/PUT/PATCH request body

    Returns:
        MCP result with success status, status code, and data
    """
    print(f"\n{'='*60}")
    print(f"MCP TOOL CALL: generic_execute")
    print(f"  USER ID: {user_id}")
    print(f"  TENANT ID: {tenant_id}")
    print(f"  ENDPOINT ID: {endpoint_id}")
    print(f"  METHOD: {method}")
    print(f"  PATH PARAMETERS: {path_parameters}")
    print(f"  QUERY PARAMETERS: {query_parameters}")
    print(f"  REQUEST BODY: {request_body}")
    print(f"{'='*60}\n")

    try:
        # Get MCP context with authorization
        context = get_mcp_context(
            db=db,
            user_id=user_id,
            tenant_id=tenant_id,
            endpoint_id=endpoint_id,
        )

        # Get the specific endpoint
        from app.ai_agent.crud import get_endpoint
        endpoint_obj = context.get_authorized_endpoint(endpoint_id)

        if not endpoint_obj:
            return build_mcp_result(
                success=False,
                operation="generic_execute",
                status_code=404,
                error="Endpoint not found or not authorized.",
                message="The specified endpoint does not exist or you don't have access to it.",
            )

        # Get base URL from the endpoint
        from urllib.parse import urlparse, urlunparse, quote

        base_endpoint = endpoint_obj.endpoint
        parsed = urlparse(base_endpoint)

        # Start with the base path
        path_template = parsed.path

        # Substitute path parameters if provided
        if path_parameters:
            for key, value in path_parameters.items():
                # Replace {key} or :key with the actual value
                path_template = path_template.replace(f"{{{key}}}", str(value))
                path_template = path_template.replace(f":{key}", str(value))

        # Build query string if provided
        query_string = ""
        if query_parameters:
            query_parts = []
            for key, value in query_parameters.items():
                if value is not None:
                    query_parts.append(f"{quote(str(key))}={quote(str(value))}")
            query_string = "&".join(query_parts)

        # Reconstruct the full URL
        new_parsed = parsed._replace(
            path=path_template,
            query=query_string
        )
        full_url = urlunparse(new_parsed)

        print(f"\n{'='*60}")
        print(f"GENERIC EXECUTE - REQUEST DETAILS:")
        print(f"  BASE ENDPOINT: {base_endpoint}")
        print(f"  FULL URL: {full_url}")
        print(f"  METHOD: {method}")
        print(f"{'='*60}\n")

        # Transform request body keys to camelCase
        external_body = None
        if request_body:
            external_body = transform_list_request_body(request_body)

        # Execute the request
        result = execute_external_request(
            context=context,
            method=method.upper(),
            path_or_url=full_url,  # Already contains full URL
            request_body=external_body,
        )

        # Determine success based on status code
        is_success = result.get("success", False)
        status_code = result.get("status_code")
        data = result.get("data")
        error = result.get("error")

        if is_success:
            return build_mcp_result(
                success=True,
                operation=f"generic_execute_{method.lower()}",
                status_code=status_code,
                data=data,
                message=f"{method} request completed successfully.",
            )
        else:
            return build_mcp_result(
                success=False,
                operation=f"generic_execute_{method.lower()}",
                status_code=status_code or 500,
                error=error,
                message=f"Failed to execute {method} request.",
            )

    except ValueError as e:
        error_msg = str(e)
        print(f"\n{'='*60}")
        print(f"GENERIC EXECUTE - VALUE ERROR: {error_msg}")
        print(f"{'='*60}\n")

        # Check if it's an authorization error
        if "connect" in error_msg.lower() or "API token" in error_msg:
            return build_mcp_result(
                success=False,
                operation="generic_execute",
                status_code=401,
                error=error_msg,
                message="API connection not configured. Please connect an API first.",
            )
        elif "not found" in error_msg.lower() or "not exist" in error_msg.lower():
            return build_mcp_result(
                success=False,
                operation="generic_execute",
                status_code=404,
                error=error_msg,
                message="Endpoint not found.",
            )
        else:
            return build_mcp_result(
                success=False,
                operation="generic_execute",
                status_code=400,
                error=error_msg,
                message=error_msg,
            )

    except Exception as e:
        error_msg = str(e)
        print(f"\n{'='*60}")
        print(f"GENERIC EXECUTE - EXCEPTION: {error_msg}")
        print(f"{'='*60}\n")

        return build_mcp_result(
            success=False,
            operation="generic_execute",
            status_code=500,
            error=error_msg,
            message="Internal error during API execution.",
        )


# Add generic_execute to MCP_TOOLS registry
MCP_TOOLS["generic_execute"] = generic_execute_tool


# ============================================================
# TOOL EXECUTION DISPATCHER
# ============================================================


async def execute_mcp_tool(
    tool_name: str,
    db: Session,
    user_id: int,
    tenant_id: int,
    arguments: dict,
) -> dict:
    """
    Execute an MCP tool by name with the given arguments.

    Args:
        tool_name: Name of the tool to execute
        db: Database session
        user_id: Current user ID
        tenant_id: Current tenant ID
        arguments: Tool-specific arguments

    Returns:
        MCP result from the tool execution

    Raises:
        ValueError: If tool_name is not found
    """
    if tool_name not in MCP_TOOLS:
        return build_mcp_result(
            success=False,
            operation=tool_name,
            status_code=400,
            error=f"Unknown tool: {tool_name}",
            message=f"Tool '{tool_name}' is not defined.",
        )

    tool_func = MCP_TOOLS[tool_name]

    # Call the tool with unpacked arguments
    return await tool_func(
        db=db,
        user_id=user_id,
        tenant_id=tenant_id,
        **arguments,
    )

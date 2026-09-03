"""
MCP Server - FastMCP server for PromptXL AI Agent.

This module provides an MCP server that exposes the List CRUD tools
through the Model Context Protocol.

Transport: Streamable HTTP (preferred for FastAPI integration)
"""

from typing import Optional
import json

from fastmcp import FastMCP

from app.ai_agent.mcp.tools import (
    get_lists_tool,
    create_list_tool,
    update_list_tool,
    delete_list_tool,
    generic_execute_tool,
)
from app.ai_agent.mcp.context import build_mcp_result


# ============================================================
# MCP SERVER INSTANCE
# ============================================================


# Create FastMCP server instance
mcp_server = FastMCP(
    name="PromptXL AI Agent",
    instructions=(
        "PromptXL AI Agent MCP Server. "
        "Provides tools for managing Lists via the external API. "
        "Use get_lists to retrieve lists, create_list to create new lists, "
        "update_list to update lists (not yet implemented), "
        "and delete_list to delete lists."
    ),
)


# ============================================================
# MCP TOOL DEFINITIONS
# ============================================================


@mcp_server.tool()
async def get_lists(
    db,  # Will be injected by the integration layer
    user_id: int,
    tenant_id: int,
    endpoint_id: Optional[int] = None,
) -> str:
    """
    Retrieve all lists from the connected external API.
    
    Args:
        user_id: Current authenticated user's ID
        tenant_id: Current tenant's ID
        endpoint_id: Optional specific endpoint to use
        
    Returns:
        JSON string with MCP result
    """
    result = await get_lists_tool(
        db=db,
        user_id=user_id,
        tenant_id=tenant_id,
        endpoint_id=endpoint_id,
    )
    return json.dumps(result)


@mcp_server.tool()
async def create_list(
    db,  # Will be injected by the integration layer
    user_id: int,
    tenant_id: int,
    list_name: str,
    standard_list: bool = False,
    endpoint_id: Optional[int] = None,
) -> str:
    """
    Create a new list in the external API.
    
    Args:
        user_id: Current authenticated user's ID
        tenant_id: Current tenant's ID
        list_name: Name of the list to create (required)
        standard_list: Whether this is a standard list (optional, default False)
        endpoint_id: Optional specific endpoint to use
        
    Returns:
        JSON string with MCP result
    """
    result = await create_list_tool(
        db=db,
        user_id=user_id,
        tenant_id=tenant_id,
        list_name=list_name,
        standard_list=standard_list,
        endpoint_id=endpoint_id,
    )
    return json.dumps(result)


@mcp_server.tool()
async def update_list(
    db,  # Will be injected by the integration layer
    user_id: int,
    tenant_id: int,
    name: str,
    endpoint_id: Optional[int] = None,
) -> str:
    """
    Update an existing list. 
    
    NOTE: This tool is not yet implemented because the PUT request body
    schema is not defined in the external API.
    
    Args:
        user_id: Current authenticated user's ID
        tenant_id: Current tenant's ID
        name: Current name of the list to update
        endpoint_id: Optional specific endpoint to use
        
    Returns:
        JSON string with MCP result (will indicate not implemented)
    """
    result = await update_list_tool(
        db=db,
        user_id=user_id,
        tenant_id=tenant_id,
        name=name,
        endpoint_id=endpoint_id,
    )
    return json.dumps(result)


@mcp_server.tool()
async def delete_list(
    db,  # Will be injected by the integration layer
    user_id: int,
    tenant_id: int,
    name: str,
    endpoint_id: Optional[int] = None,
) -> str:
    """
    Delete a list from the external API.
    
    Args:
        user_id: Current authenticated user's ID
        tenant_id: Current tenant's ID
        name: Name of the list to delete
        endpoint_id: Optional specific endpoint to use
        
    Returns:
        JSON string with MCP result
    """
    result = await delete_list_tool(
        db=db,
        user_id=user_id,
        tenant_id=tenant_id,
        name=name,
        endpoint_id=endpoint_id,
    )
    return json.dumps(result)


@mcp_server.tool()
async def generic_execute(
    db,  # Will be injected by the integration layer
    user_id: int,
    tenant_id: int,
    endpoint_id: int,
    method: str,
    path_parameters: Optional[dict] = None,
    query_parameters: Optional[dict] = None,
    request_body: Optional[dict] = None,
) -> str:
    """
    Generic API endpoint executor.

    This tool can execute any connected API endpoint dynamically.
    Use this for resources that don't have specific tools.

    Args:
        user_id: Current authenticated user's ID
        tenant_id: Current tenant's ID
        endpoint_id: The specific endpoint ID to execute (required)
        method: HTTP method (GET, POST, PUT, PATCH, DELETE)
        path_parameters: Dict of path parameters to substitute in URL (e.g., {"id": "123"})
        query_parameters: Dict of query parameters
        request_body: Dict for POST/PUT/PATCH request body

    Returns:
        JSON string with MCP result
    """
    result = await generic_execute_tool(
        db=db,
        user_id=user_id,
        tenant_id=tenant_id,
        endpoint_id=endpoint_id,
        method=method,
        path_parameters=path_parameters or {},
        query_parameters=query_parameters or {},
        request_body=request_body,
    )
    return json.dumps(result)


# ============================================================
# SERVER ACCESSOR
# ============================================================


def get_server() -> FastMCP:
    """
    Get the MCP server instance.
    
    Returns:
        The FastMCP server instance
    """
    return mcp_server


# ============================================================
# HTTP TRANSPORT CONFIGURATION
# ============================================================


def get_http_handlers():
    """
    Get HTTP handlers for the MCP server.
    
    This returns the ASGI application for Streamable HTTP transport.
    
    Usage:
        from fastmcp.server.streamable import streamable_http_handler
        
        app.add_route(
            "/mcp",
            streamable_http_handler(mcp_server),
            methods=["POST", "GET"],
        )
    """
    from fastmcp.server.streamable import streamable_http_handler
    
    return streamable_http_handler(mcp_server)


def get_sse_handlers():
    """
    Get SSE (Server-Sent Events) handlers for the MCP server.
    
    This returns the ASGI application for SSE transport.
    
    Usage:
        from fastmcp.server.sse import sse_handler
        
        app.add_route(
            "/mcp/sse",
            sse_handler(mcp_server),
            methods=["GET"],
        )
    """
    from fastmcp.server.sse import sse_handler
    
    return sse_handler(mcp_server)

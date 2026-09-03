"""
MCP (Model Context Protocol) module for PromptXL AI Agent.

This module provides MCP tools for executing external API operations
through the existing AIAgentConnection infrastructure.

Architecture:
    AI Agent -> MCP Client -> MCP Server -> MCP Tools -> Existing API Execution Service
"""

from app.ai_agent.mcp.context import (
    MCPContext,
    get_mcp_context,
)

from app.ai_agent.mcp.server import (
    mcp_server,
    get_server,
)

from app.ai_agent.mcp.tools import (
    # Tool definitions
    get_lists_tool,
    create_list_tool,
    update_list_tool,
    delete_list_tool,
    # Tool execution
    execute_mcp_tool,
)

__all__ = [
    "MCPContext",
    "get_mcp_context",
    "mcp_server",
    "get_server",
    "get_lists_tool",
    "create_list_tool",
    "update_list_tool",
    "delete_list_tool",
    "execute_mcp_tool",
]

"""
MCP Context - User/Tenant handling and authorization.

This module provides context for MCP tool execution, including:
- Current user identification
- Tenant validation
- Connection and endpoint authorization
- Secure token handling
"""

from dataclasses import dataclass
from typing import Optional
import json

from sqlalchemy.orm import Session

from app.ai_agent import crud
from app.ai_agent.encryption import decrypt_api_token
from app.ai_agent.models import AIAgentConnection, AIAgentEndpoint


# ============================================================
# MCP CONTEXT
# ============================================================


@dataclass
class MCPContext:
    """
    Context for MCP tool execution.
    
    Contains all necessary information for:
    - User authentication
    - Tenant validation  
    - Connection authorization
    - Secure token access
    """
    
    # Database session
    db: Session
    
    # Current authenticated user
    user_id: int
    tenant_id: int
    
    # Authorized connection (if exists)
    connection: Optional[AIAgentConnection] = None
    
    # Authorized endpoint (if specified)
    endpoint: Optional[AIAgentEndpoint] = None
    
    @property
    def api_token(self) -> Optional[str]:
        """Decrypt and return the API token."""
        if self.connection and self.connection.encrypted_api_token:
            return decrypt_api_token(self.connection.encrypted_api_token)
        return None
    
    @property
    def external_tenant(self) -> Optional[str]:
        """Get the external tenant identifier."""
        if self.connection:
            return self.connection.external_tenant
        return None
    
    def is_endpoint_authorized(self, endpoint_id: int) -> bool:
        """
        Verify that the endpoint belongs to the current user and tenant.
        
        Args:
            endpoint_id: The endpoint ID to verify.
            
        Returns:
            True if authorized, False otherwise.
        """
        if not self.connection:
            return False
        
        # Find the endpoint
        endpoint = crud.get_endpoint(
            db=self.db,
            connection_id=self.connection.id,
            endpoint_id=endpoint_id,
        )
        
        if not endpoint:
            return False
        
        # Verify ownership:
        # 1. endpoint.connection.connected_by == user_id
        # 2. endpoint.connection.tenant_id == tenant_id
        return (
            endpoint.connection.connected_by == self.user_id
            and endpoint.connection.tenant_id == self.tenant_id
        )
    
    def get_authorized_endpoint(self, endpoint_id: int) -> Optional[AIAgentEndpoint]:
        """
        Get an endpoint if it is authorized for this user/tenant.
        
        Args:
            endpoint_id: The endpoint ID to retrieve.
            
        Returns:
            The endpoint if authorized, None otherwise.
        """
        if not self.is_endpoint_authorized(endpoint_id):
            return None
        
        return crud.get_endpoint(
            db=self.db,
            connection_id=self.connection.id,
            endpoint_id=endpoint_id,
        )


# ============================================================
# CONTEXT FACTORY
# ============================================================


def get_mcp_context(
    db: Session,
    user_id: int,
    tenant_id: int,
    endpoint_id: Optional[int] = None,
) -> MCPContext:
    """
    Create an MCP context for the given user/tenant.
    
    This function:
    1. Gets the user's AIAgentConnection
    2. Optionally validates the specified endpoint
    3. Returns a context with authorized access
    
    Args:
        db: Database session
        user_id: Current user's ID
        tenant_id: Current tenant's ID
        endpoint_id: Optional endpoint ID to validate
        
    Returns:
        MCPContext with authorized connection and endpoint
        
    Raises:
        ValueError: If connection is not found or endpoint is not authorized
    """
    print(f"\n{'='*60}")
    print(f"Getting MCP context for user_id={user_id}, tenant_id={tenant_id}")
    print(f"{'='*60}\n")
    
    # Get the connection for this user/tenant
    connection = crud.get_connection(
        db=db,
        tenant_id=tenant_id,
        user_id=user_id,
    )
    
    if not connection:
        raise ValueError("Please connect the external API first.")
    
    # Verify connection ownership
    if connection.connected_by != user_id:
        raise ValueError("API connection does not belong to this user.")
    
    if connection.tenant_id != tenant_id:
        raise ValueError("API connection does not belong to this tenant.")
    
    # Create base context
    context = MCPContext(
        db=db,
        user_id=user_id,
        tenant_id=tenant_id,
        connection=connection,
    )
    
    # If endpoint_id specified, validate and store it
    if endpoint_id is not None:
        authorized_endpoint = context.get_authorized_endpoint(endpoint_id)
        if not authorized_endpoint:
            raise ValueError(
                f"Endpoint {endpoint_id} is not authorized. "
                "The endpoint must belong to your connection."
            )
        context.endpoint = authorized_endpoint
    
    print(f"\n{'='*60}")
    print(f"MCP CONTEXT CREATED:")
    print(f"  USER ID: {context.user_id}")
    print(f"  TENANT ID: {context.tenant_id}")
    print(f"  CONNECTION ID: {context.connection.id if context.connection else None}")
    print(f"  ENDPOINT: {context.endpoint.endpoint if context.endpoint else None}")
    print(f"  EXTERNAL TENANT: {context.external_tenant}")
    print(f"{'='*60}\n")
    
    return context


# ============================================================
# AUTHORIZATION HELPERS
# ============================================================


def authorize_endpoint(
    context: MCPContext,
    endpoint_id: int,
) -> AIAgentEndpoint:
    """
    Authorize and return an endpoint for the given context.
    
    Args:
        context: MCP context with user/tenant info
        endpoint_id: Endpoint ID to authorize
        
    Returns:
        Authorized endpoint
        
    Raises:
        ValueError: If endpoint is not found or not authorized
    """
    endpoint = context.get_authorized_endpoint(endpoint_id)
    
    if not endpoint:
        raise ValueError(
            f"Endpoint {endpoint_id} is not authorized. "
            "Verify that the endpoint belongs to your connection."
        )
    
    return endpoint


def build_mcp_result(
    success: bool,
    operation: str,
    status_code: int,
    data: any = None,
    message: str = None,
    error: any = None,
) -> dict:
    """
    Build a standardized MCP tool result.
    
    Args:
        success: Whether the operation succeeded
        operation: Name of the operation (e.g., "get_lists")
        status_code: HTTP status code
        data: Response data (for GET) or None (for POST/PUT/DELETE)
        message: Human-readable message
        error: Error details (if success=False)
        
    Returns:
        Standardized MCP result dictionary
    """
    result = {
        "success": success,
        "operation": operation,
        "status_code": status_code,
    }
    
    if data is not None:
        result["data"] = data
    
    if message:
        result["message"] = message
    
    if error:
        result["error"] = error
    
    return result

"""
AI Agent Instructions
=====================

This package contains endpoint-specific instruction files
that define behavior for different API endpoints.

Each instruction file contains:
- Endpoint path patterns
- HTTP method detection
- Request schema
- Natural language extraction patterns
- Boolean normalization rules
- Validation rules
- Response handling

Usage:
    from app.ai_agent.instructions import get_instruction_for_endpoint
    
    instruction = get_instruction_for_endpoint("/api/lists")
    if instruction:
        # Use instruction data
"""

from .list_api import (
    LIST_API_PATHS,
    INSTRUCTION_NAME,
    INSTRUCTION_VERSION,
    LIST_API_SCHEMA,
    LIST_API_INSTRUCTION_TEXT,
    GET_KEYWORDS,
    POST_KEYWORDS,
    LIST_NAME_PATTERNS,
    STANDARD_TRUE_PATTERNS,
    STANDARD_FALSE_PATTERNS,
    get_instruction_for_endpoint,
)

__all__ = [
    "LIST_API_PATHS",
    "INSTRUCTION_NAME",
    "INSTRUCTION_VERSION",
    "LIST_API_SCHEMA",
    "LIST_API_INSTRUCTION_TEXT",
    "GET_KEYWORDS",
    "POST_KEYWORDS",
    "LIST_NAME_PATTERNS",
    "STANDARD_TRUE_PATTERNS",
    "STANDARD_FALSE_PATTERNS",
    "get_instruction_for_endpoint",
]

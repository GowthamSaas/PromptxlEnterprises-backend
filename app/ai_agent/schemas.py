from datetime import datetime
import json
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator


# ============================================================
# API CONNECTION
# ============================================================

class AIAgentConnectRequest(BaseModel):

    api_token: str = Field(
        ...,
        min_length=1,
    )

    external_tenant: str = Field(
        ...,
        min_length=1,
        max_length=255,
    )


class AIAgentUpdateRequest(BaseModel):

    api_token: str | None = Field(
        default=None,
        min_length=1,
    )

    external_tenant: str | None = Field(
        default=None,
        min_length=1,
        max_length=255,
    )


class AIAgentConnectionResponse(BaseModel):

    id: int

    connected: bool

    external_tenant: str

    api_token: str | None = None

    created_at: datetime

    updated_at: datetime

    model_config = ConfigDict(
        from_attributes=True
    )


# ============================================================
# EXTERNAL ENDPOINT
# ============================================================

class AIAgentEndpointCreate(BaseModel):

    endpoint: str = Field(
        ...,
        min_length=1,
        max_length=2048,
    )

    method: str | None = Field(
        default="GET",
        max_length=10,
    )

    description: str | None = Field(
        default=None,
        max_length=1024,
    )

    resource_name: str | None = Field(
        default=None,
        max_length=255,
    )

    request_schema: dict | None = Field(
        default=None,
    )

    response_schema: dict | None = Field(
        default=None,
    )


class AIAgentEndpointUpdate(BaseModel):

    endpoint: str | None = Field(
        default=None,
        min_length=1,
        max_length=2048,
    )

    method: str | None = Field(
        default=None,
        max_length=10,
    )

    description: str | None = Field(
        default=None,
        max_length=1024,
    )

    resource_name: str | None = Field(
        default=None,
        max_length=255,
    )

    request_schema: dict | None = Field(
        default=None,
    )

    response_schema: dict | None = Field(
        default=None,
    )


class AIAgentEndpointResponse(BaseModel):

    id: int

    endpoint: str

    method: str | None = None

    description: str | None = None

    resource_name: str | None = None

    request_schema: dict | str | None = None

    response_schema: dict | str | None = None

    created_at: datetime

    updated_at: datetime

    model_config = ConfigDict(
        from_attributes=True
    )

    @field_validator("request_schema", "response_schema", mode="before")
    @classmethod
    def parse_schema_json(cls, v):
        if v is None:
            return None
        if isinstance(v, dict):
            return v
        if isinstance(v, str):
            try:
                return json.loads(v)
            except json.JSONDecodeError:
                return v
        return v


class AIAgentEndpointDeleteResponse(BaseModel):

    id: int

    deleted: bool


# ============================================================
# CONVERSATION HISTORY
# ============================================================

class AIAgentConversationMessage(BaseModel):

    role: str = Field(
        ...,
        min_length=1,
    )

    content: str = Field(
        default="",
    )


# ============================================================
# AI AGENT EXECUTION
# ============================================================

class AIAgentPromptRequest(BaseModel):

    prompt: str = Field(
        ...,
        min_length=1,
    )

    # Connected endpoint
    endpoint_id: int | None = None

    # Direct endpoint
    endpoint: str | None = Field(
        default=None,
        max_length=2048,
    )

    external_tenant: str | None = Field(
        default=None,
        min_length=1,
        max_length=255,
    )

    provider: str | None = None

    model: str | None = None

    # Previous structured output
    previous_output: dict | None = None

    # Full previous conversation
    conversation_history: list[
        AIAgentConversationMessage
    ] | None = None

    # Optional HTTP method
    method: str | None = Field(
        default=None,
        max_length=10,
    )

    # Optional request body
    request_body: dict[str, Any] | None = None


# ============================================================
# AI AGENT RESPONSE
# ============================================================

class AIAgentPromptResponse(BaseModel):

    success: bool

    type: str

    message: str

    data: Any = None

    components: list[dict[str, Any]] = Field(
        default_factory=list
    )

    endpoint_id: int | None = None

    status_code: int | None = None

    provider: str | None = None

    model: str | None = None

    method: str | None = None

    endpoint: str | None = None
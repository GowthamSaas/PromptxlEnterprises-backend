from datetime import datetime
from typing import Optional, Dict, Any

from pydantic import BaseModel, Field


# =====================================================
# Deploy Request
# =====================================================

class DeploymentRequest(BaseModel):

    project_id: int

    provider: str = Field(
        ...,
        examples=["vercel"]
    )

    deployment_method: str = Field(
        ...,
        examples=["github", "direct"]
    )

    use_github: bool = False

    use_supabase: bool = False

    class Config:
        from_attributes = True


# =====================================================
# Deployment Response
# =====================================================

class DeploymentResponse(BaseModel):

    success: bool

    deployment_id: int

    project_id: int

    provider: str

    deployment_method: str

    status: str

    deployment_url: Optional[str] = None

    repository_name: Optional[str] = None

    repository_url: Optional[str] = None

    message: str

    # New fields for project type detection
    application_type: Optional[str] = None  # "frontend_only" or "full_stack"

    # Safe Supabase info (no secrets)
    supabase_project: Optional[Dict[str, Any]] = None

    class Config:
        from_attributes = True


# =====================================================
# Deployment Status
# =====================================================

class DeploymentStatusResponse(BaseModel):

    deployment_id: int

    status: str

    deployment_url: Optional[str] = None

    created_at: Optional[datetime] = None

    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# =====================================================
# Deployment Logs
# =====================================================

class DeploymentLogResponse(BaseModel):

    deployment_id: int

    logs: Optional[str] = None

    class Config:
        from_attributes = True


# =====================================================
# Deployment Details
# =====================================================

class DeploymentDetailsResponse(BaseModel):

    id: int

    project_id: int

    provider: str

    deployment_method: str

    repository_name: Optional[str]

    repository_url: Optional[str]

    deployment_url: Optional[str]

    status: str

    deployment_metadata: Optional[Dict[str, Any]]

    created_at: datetime

    updated_at: Optional[datetime]

    class Config:
        from_attributes = True


# =====================================================
# Deployment List
# =====================================================

class DeploymentListResponse(BaseModel):

    deployments: list[DeploymentDetailsResponse]

    class Config:
        from_attributes = True
from typing import Optional

from sqlalchemy.orm import Session

from app.deployment.models import Deployment


# =====================================================
# Create Deployment
# =====================================================

def create_deployment(
    db: Session,
    *,
    tenant_id: int,
    project_id: int,
    created_by: int,
    provider: str,
    deployment_method: str,
    repository_name: str | None = None,
    repository_url: str | None = None,
    deployment_id: str | None = None,
    deployment_url: str | None = None,
    deployment_metadata: dict | None = None,
    status: str = "queued",
) -> Deployment:

    deployment_record = crud.create_deployment(
        db=db,
        tenant_id=user.tenant_id,
        project_id=project.id,
        created_by=user.id,
        provider=request.provider,
        deployment_method=request.deployment_method,
        repository_name=github_result["repository_name"],
        repository_url=github_result["repository_url"],
        deployment_url=deployment_url,
        status="success",
    )

    db.add(deployment)
    db.commit()
    db.refresh(deployment)

    return deployment


# =====================================================
# Get Deployment
# =====================================================

def get_deployment(
    db: Session,
    *,
    deployment_id: int,
) -> Optional[Deployment]:

    return (
        db.query(Deployment)
        .filter(
            Deployment.id == deployment_id
        )
        .first()
    )


# =====================================================
# Get Project Deployments
# =====================================================

def get_project_deployments(
    db: Session,
    *,
    project_id: int,
):

    return (
        db.query(Deployment)
        .filter(
            Deployment.project_id == project_id
        )
        .order_by(
            Deployment.created_at.desc()
        )
        .all()
    )


# =====================================================
# Get Tenant Deployments
# =====================================================

def get_tenant_deployments(
    db: Session,
    *,
    tenant_id: int,
):

    return (
        db.query(Deployment)
        .filter(
            Deployment.tenant_id == tenant_id
        )
        .order_by(
            Deployment.created_at.desc()
        )
        .all()
    )


# =====================================================
# Update Status
# =====================================================

def update_status(
    db: Session,
    *,
    deployment: Deployment,
    status: str,
) -> Deployment:

    deployment.status = status

    db.commit()
    db.refresh(deployment)

    return deployment


# =====================================================
# Update Deployment URL
# =====================================================

def update_deployment_url(
    db: Session,
    *,
    deployment: Deployment,
    deployment_url: str,
) -> Deployment:

    deployment.deployment_url = deployment_url

    db.commit()
    db.refresh(deployment)

    return deployment


# =====================================================
# Update Repository
# =====================================================

def update_repository(
    db: Session,
    *,
    deployment: Deployment,
    repository_name: str,
    repository_url: str,
) -> Deployment:

    deployment.repository_name = repository_name
    deployment.repository_url = repository_url

    db.commit()
    db.refresh(deployment)

    return deployment


# =====================================================
# Update Deployment ID
# =====================================================

def update_provider_deployment_id(
    db: Session,
    *,
    deployment: Deployment,
    provider_deployment_id: str,
) -> Deployment:

    deployment.deployment_id = provider_deployment_id

    db.commit()
    db.refresh(deployment)

    return deployment


# =====================================================
# Update Metadata
# =====================================================

def update_metadata(
    db: Session,
    *,
    deployment: Deployment,
    metadata: dict,
) -> Deployment:

    deployment.deployment_metadata = metadata

    db.commit()
    db.refresh(deployment)

    return deployment


# =====================================================
# Update Logs
# =====================================================

def update_logs(
    db: Session,
    *,
    deployment: Deployment,
    logs: str,
) -> Deployment:

    deployment.logs = logs

    db.commit()
    db.refresh(deployment)

    return deployment


# =====================================================
# Delete Deployment
# =====================================================

def delete_deployment(
    db: Session,
    *,
    deployment: Deployment,
):

    db.delete(deployment)
    db.commit()
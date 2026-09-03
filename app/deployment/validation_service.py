from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.user import User, UserRole

from app.projects import crud as project_crud

from app.connectors import crud as connector_crud
from app.connectors.models import ConnectorProvider


class DeploymentValidationService:

    # --------------------------------------------------
    # Role Validation
    # --------------------------------------------------

    def validate_permission(
        self,
        current_user: User,
    ):

        if current_user.role not in [
            UserRole.OWNER,
            UserRole.ADMIN,
        ]:

            raise HTTPException(
                status_code=403,
                detail="Only Owner and Admin can deploy projects.",
            )

        if current_user.tenant_id is None:

            raise HTTPException(
                status_code=400,
                detail="User is not assigned to any tenant.",
            )

    # --------------------------------------------------
    # Project Validation
    # --------------------------------------------------

    def validate_project(
        self,
        db: Session,
        *,
        project_id: int,
        tenant_id: int,
    ):

        project = project_crud.get_project(
            db=db,
            project_id=project_id,
        )

        if not project:

            raise HTTPException(
                status_code=404,
                detail="Project not found.",
            )

        # Get project owner and validate tenant through user relationship
        project_user = (
            db.query(User)
            .filter(User.id == project.user_id)
            .first()
        )

        if not project_user:

            raise HTTPException(
                status_code=404,
                detail="Project owner not found.",
            )

        if project_user.tenant_id != tenant_id:

            raise HTTPException(
                status_code=403,
                detail="Project does not belong to your tenant.",
            )

        return project

    # --------------------------------------------------
    # Connector Validation
    # --------------------------------------------------

    def validate_connector(
        self,
        db: Session,
        *,
        tenant_id: int,
        provider: ConnectorProvider,
    ):

        connected = connector_crud.is_connected(
            db=db,
            tenant_id=tenant_id,
            provider=provider,
        )

        if not connected:

            raise HTTPException(
                status_code=400,
                detail=f"{provider.value} connector is not connected.",
            )

    # --------------------------------------------------
    # Deployment Method
    # --------------------------------------------------

    def validate_method(
        self,
        method: str,
    ):

        methods = [
            "github",
            "direct",
        ]

        if method not in methods:

            raise HTTPException(
                status_code=400,
                detail="Invalid deployment method.",
            )

    # --------------------------------------------------
    # Validate Full-Stack Requirements
    # --------------------------------------------------

    def validate_full_stack_deployment(
        self,
        db: Session,
        *,
        tenant_id: int,
        requires_supabase: bool,
    ):
        """
        Validate that Supabase is properly configured for full-stack deployments.
        """
        if requires_supabase:
            connected = connector_crud.is_connected(
                db=db,
                tenant_id=tenant_id,
                provider=ConnectorProvider.SUPABASE,
            )

            if not connected:
                raise HTTPException(
                    status_code=400,
                    detail=(
                        "This project requires Supabase for deployment, "
                        "but no Supabase connector is configured."
                    ),
                )

deployment_validation_service = DeploymentValidationService()
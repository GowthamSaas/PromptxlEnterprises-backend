from sqlalchemy.orm import Session
from fastapi import HTTPException

from app.models.user import User

from app.projects import crud as project_crud
from app.project_files import crud as project_file_crud

from app.connectors import crud as connector_crud
from app.connectors.models import ConnectorProvider

from app.connectors.services.encryption_service import (
    encryption_service,
)

from app.deployment.services.github_deployment_service import (
    github_deployment_service,
)

from app.deployment.services.vercel_cli_service import (
    vercel_cli_service,
)

from app.deployment.services.vercel_python_service import (
    vercel_python_service,
)

from app.deployment.services.supabase_deployment_service import (
    supabase_deployment_service,
)

from app.deployment.services.project_type_detection_service import (
    project_type_detection_service,
)

from app.deployment import crud
from app.projects.service import project_service


class DeploymentService:

    async def deploy(
        self,
        db: Session,
        user,
        request,
    ):

        # ----------------------------------------
        # Step 1: Validate Project Ownership
        # ----------------------------------------

        project = project_crud.get_project(
            db=db,
            project_id=request.project_id,
        )

        if not project:
            raise HTTPException(
                status_code=404,
                detail="Project not found.",
            )

        # Validate tenant ownership through project user relationship
        project_user = db.query(User).filter(User.id == project.user_id).first()
        if not project_user or project_user.tenant_id != user.tenant_id:
            raise HTTPException(
                status_code=403,
                detail="Project does not belong to your tenant.",
            )

        # ----------------------------------------
        # Step 2: Load Project Files
        # ----------------------------------------

        project_files = (
            project_file_crud.get_project_files(
                db=db,
                project_id=project.id,
            )
        )

        if not project_files:
            raise HTTPException(
                status_code=400,
                detail="Project files are empty.",
            )

        # ----------------------------------------
        # Step 3: Detect Application Type
        # ----------------------------------------

        project_type = project_type_detection_service.detect_project_type(
            project_files=project_files,
        )

        # Backend detection is authoritative; use_supabase from request
        # is only a hint. If backend is detected, Supabase is required.
        requires_supabase = (
            project_type.requires_supabase
        )

        # ----------------------------------------
        # Step 4: Validate Connectors
        # ----------------------------------------

        # Vercel connector is ALWAYS required
        vercel_connector = (
            connector_crud.get_connector_by_provider(
                db=db,
                tenant_id=user.tenant_id,
                provider=ConnectorProvider.VERCEL,
            )
        )

        if not vercel_connector:
            raise HTTPException(
                status_code=400,
                detail="Vercel connector not found. Please connect Vercel first.",
            )

        vercel_token = encryption_service.decrypt_token(
            vercel_connector.encrypted_token
        )

        # GitHub connector is required if deployment_method is "github"
        github_token = None
        github_connector = None

        if request.deployment_method == "github":
            github_connector = (
                connector_crud.get_connector_by_provider(
                    db=db,
                    tenant_id=user.tenant_id,
                    provider=ConnectorProvider.GITHUB,
                )
            )

            if not github_connector:
                raise HTTPException(
                    status_code=400,
                    detail="GitHub connector not found. Please connect GitHub first.",
                )

            github_token = encryption_service.decrypt_token(
                github_connector.encrypted_token
            )

        # Supabase connector is required ONLY for full-stack deployments
        supabase_token = None
        supabase_connector = None
        supabase_config = None

        if requires_supabase:
            supabase_connector = (
                connector_crud.get_connector_by_provider(
                    db=db,
                    tenant_id=user.tenant_id,
                    provider=ConnectorProvider.SUPABASE,
                )
            )

            if not supabase_connector:
                raise HTTPException(
                    status_code=400,
                    detail=(
                        "This project requires Supabase for deployment, "
                        "but no Supabase connector is configured."
                    ),
                )

            # Check if connector is connected before trying to use it
            if not supabase_connector.connected:
                raise HTTPException(
                    status_code=400,
                    detail=(
                        "Supabase connector is disconnected. "
                        "Please reconnect your Supabase connector."
                    ),
                )

            supabase_token = encryption_service.decrypt_token(
                supabase_connector.encrypted_token
            )

            # Get existing project_ref from connector metadata if available
            existing_project_ref = None
            if supabase_connector.provider_metadata:
                existing_project_ref = supabase_connector.provider_metadata.get(
                    "project_ref"
                )

            # Select Supabase project (validates token)
            supabase_project = await supabase_deployment_service.select_project(
                token=supabase_token,
                existing_project_ref=existing_project_ref,
            )

            # Get safe configuration
            supabase_config = await supabase_deployment_service.get_project_config(
                token=supabase_token,
                project_ref=supabase_project.id,
            )

        # ----------------------------------------
        # Step 5: GitHub Repository (if method is github)
        # ----------------------------------------

        github_result = {
            "repository_url": None,
            "repository_name": None,
        }

        if request.deployment_method == "github":
            github_user = await github_deployment_service.get_user(
                github_token,
            )

            owner = github_user["login"]

            repository = await github_deployment_service.create_repository(
                token=github_token,
                name=project.name,
            )

            repository_name = repository["name"]

            files = [
                {"path": file.file_path, "content": file.content}
                for file in project_files
            ]

            github_result = await github_deployment_service.push_project(
                token=github_token,
                owner=owner,
                repository=repository_name,
                files=files,
            )

        # ----------------------------------------
        # Step 6: Export Project
        # ----------------------------------------

        project_path = project_service.export_project_directory(
            db=db,
            project_id=project.id,
        )

        print("Exported Path:", project_path)

        # ----------------------------------------
        # Step 7: Prepare Python Backend (FastAPI/Django)
        # ----------------------------------------

        python_deployment_config = None
        if project_type.backend_framework in ("fastapi", "django"):
            python_deployment_config = await vercel_python_service.prepare_python_deployment(
                project_path=str(project_path),
                backend_framework=project_type.backend_framework,
                backend_root=project_type.backend_root,
                project_type=project_type,
            )

        # ----------------------------------------
        # Step 8: Deploy to Vercel
        # ----------------------------------------

        deployment = await vercel_cli_service.deploy(
            project_path=str(project_path),
            token=vercel_token,
            frontend_root=project_type.frontend_root,
            backend_root=project_type.backend_root,
            framework=project_type.frontend_framework,
            is_full_stack=requires_supabase,
            is_backend_vercel_compatible=project_type.vercel_python_runtime,
            python_deployment_config=python_deployment_config,
            api_health_endpoint=project_type.api_health_endpoint,
        )

        deployment_url = deployment["deployment_url"]

        # ----------------------------------------
        # Step 9: Verify Deployment Health
        # ----------------------------------------

        if not deployment.get("health_check_passed"):
            # Deployment was created but URL returns error
            error_msg = (
                f"Vercel deployment created (ID: {deployment.get('deployment_id')}), "
                f"but the application is not accessible at {deployment_url}. "
                f"Health check returned HTTP {deployment.get('health_check_status')}. "
                f"Deployment state: {deployment.get('deployment_state')}. "
                f"Diagnostics: frontend_root={deployment.get('diagnostics', {}).get('frontend_root')}, "
                f"framework={deployment.get('diagnostics', {}).get('framework')}, "
                f"has_vercel_json={deployment.get('diagnostics', {}).get('has_vercel_json')}"
            )
            raise HTTPException(status_code=400, detail=error_msg)

        # Check backend health for full-stack deployments
        if python_deployment_config and not deployment.get("backend_health_check_passed"):
            raise HTTPException(
                status_code=400,
                detail=(
                    f"Vercel deployment created (ID: {deployment.get('deployment_id')}), "
                    f"but the backend API is not accessible at {deployment_url}{project_type.api_health_endpoint}. "
                    f"Backend health check returned HTTP {deployment.get('backend_health_check_status')}. "
                    f"Deployment state: {deployment.get('deployment_state')}"
                ),
            )

        if deployment.get("deployment_state") != "READY":
            # Use the actual polling error if available
            polling_error = deployment.get("polling_error", "Unknown error")
            raise HTTPException(
                status_code=400,
                detail=(
                    f"Vercel deployment failed or timed out. "
                    f"Deployment ID: {deployment.get('deployment_id')}. "
                    f"State: {deployment.get('deployment_state')}. "
                    f"Error: {polling_error}"
                ),
            )

        # ----------------------------------------
        # Step 10: Configure Supabase (for full-stack)
        # ----------------------------------------

        if requires_supabase and supabase_token:
            await supabase_deployment_service.configure_project(
                token=supabase_token,
                project_ref=supabase_config.project_ref,
                deployment_url=deployment_url,
            )

        # ----------------------------------------
        # Step 11: Save Deployment Record
        # ----------------------------------------

        # Validate tenant assignment
        if user.tenant_id is None:
            raise HTTPException(
                status_code=400,
                detail="User is not assigned to a tenant.",
            )

        metadata = {
            "frontend_framework": project_type.frontend_framework,
            "backend_framework": project_type.backend_framework,
            "application_type": project_type.application_type,
        }

        if python_deployment_config:
            metadata["python_entrypoint"] = python_deployment_config.get("entrypoint")

        deployment_record = crud.create_deployment(
            db=db,
            tenant_id=user.tenant_id,
            project_id=project.id,
            created_by=user.id,
            provider=request.provider,
            deployment_method=request.deployment_method,
            repository_name=github_result["repository_name"],
            repository_url=github_result["repository_url"],
            deployment_id=deployment.get("deployment_id"),
            deployment_url=deployment_url,
            status="success",
            deployment_metadata=metadata,
        )

        # ----------------------------------------
        # Build Response
        # ----------------------------------------

        response = {
            "success": True,
            "deployment_id": deployment_record.id,
            "project_id": project.id,
            "provider": request.provider,
            "deployment_method": request.deployment_method,
            "status": "success",
            "deployment_url": deployment_url,
            "repository_name": github_result["repository_name"],
            "repository_url": github_result["repository_url"],
            "message": "Project deployed successfully.",
            "application_type": project_type.application_type,
            "frontend_framework": project_type.frontend_framework,
        }

        # Include backend framework for full-stack deployments
        if project_type.backend_framework:
            response["backend_framework"] = project_type.backend_framework

        # Include safe Supabase info for full-stack deployments
        if requires_supabase and supabase_config:
            response["supabase_project"] = {
                "id": supabase_config.project_ref,
                "name": supabase_config.project_name,
            }

        return response

    # ----------------------------------------
    # Get Deployment
    # ----------------------------------------

    def get_deployment(
        self,
        db: Session,
        deployment_id: int,
    ):

        deployment = crud.get_deployment(
            db=db,
            deployment_id=deployment_id,
        )

        if not deployment:

            raise HTTPException(
                status_code=404,
                detail="Deployment not found.",
            )

        return deployment

    # ----------------------------------------
    # Deployment History
    # ----------------------------------------

    def get_project_deployments(
        self,
        db: Session,
        project_id: int,
    ):

        return {
            "deployments": crud.get_project_deployments(
                db=db,
                project_id=project_id,
            )
        }

    # ----------------------------------------
    # Deployment Logs
    # ----------------------------------------

    def get_logs(
        self,
        db: Session,
        deployment_id: int,
    ):

        deployment = crud.get_deployment(
            db=db,
            deployment_id=deployment_id,
        )

        if not deployment:

            raise HTTPException(
                status_code=404,
                detail="Deployment not found.",
            )

        return {
            "deployment_id": deployment.id,
            "logs": deployment.logs,
        }


deployment_service = DeploymentService()
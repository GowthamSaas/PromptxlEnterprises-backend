from sqlalchemy.orm import Session
from fastapi import HTTPException

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

from app.deployment.services.supabase_deployment_service import (
    supabase_deployment_service,
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
        # Get Project
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

        # ----------------------------------------
        # Project Files
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
        # GitHub Connector (Optional)
        # ----------------------------------------

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
                    detail="GitHub connector not found.",
                )

            github_token = encryption_service.decrypt_token(
               github_connector.encrypted_token
            ) 

        # ----------------------------------------
        # Vercel Connector
        # ----------------------------------------

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
                detail="Vercel connector not found.",
            )

        vercel_token = (
            encryption_service.decrypt_token(
                vercel_connector.encrypted_token
            )
        )

        # ----------------------------------------
        # Supabase Connector (Optional)
        # ----------------------------------------

        supabase_connector = (
            connector_crud.get_connector_by_provider(
                db=db,
                tenant_id=user.tenant_id,
                provider=ConnectorProvider.SUPABASE,
            )
        )

        supabase_token = None

        if supabase_connector:

            supabase_token = (
                encryption_service.decrypt_token(
                    supabase_connector.encrypted_token
                )
            )

        # ----------------------------------------
        # Create GitHub Repository
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

            files = []

            for file in project_files:

                files.append({
                    "path": file.path,
                    "content": file.content,
                })

            github_result = await github_deployment_service.push_project(
                token=github_token,
                owner=owner,
                repository=repository_name,
                files=files,
            )

        # ----------------------------------------
        # Export Project
        # ----------------------------------------

        project_path = project_service.export_project_directory(
           db=db,
           project_id=project.id,
        )

        print("Exported Path:", project_path)

        # ----------------------------------------
        # Deploy to Vercel
        # ----------------------------------------

        deployment = await vercel_cli_service.deploy(
           project_path=str(project_path),
           token=vercel_token,
        )

        deployment_url = deployment["deployment_url"]

        # ----------------------------------------
        # Configure Supabase
        # ----------------------------------------

        # if supabase_connector:

        #     await supabase_deployment_service.configure_project(
        #         token=supabase_token,
        #         project_ref=supabase_connector.provider_metadata[
        #             "project_ref"
        #         ],
        #         deployment_url=deployment_url,
        #     )

        # ----------------------------------------
        # Save Deployment
        # ----------------------------------------

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

        return {
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
        }

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
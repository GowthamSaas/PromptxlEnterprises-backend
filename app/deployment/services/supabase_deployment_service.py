from typing import Any

import httpx
from fastapi import HTTPException


class SupabaseDeploymentService:

    BASE_URL = "https://api.supabase.com/v1"

    # --------------------------------------------------
    # Headers
    # --------------------------------------------------

    def _headers(
        self,
        token: str,
    ):

        return {

            "Authorization": f"Bearer {token}",

            "Content-Type": "application/json",

        }

    # --------------------------------------------------
    # Get Projects
    # --------------------------------------------------

    async def get_projects(
        self,
        token: str,
    ):

        async with httpx.AsyncClient(timeout=30) as client:

            response = await client.get(
                f"{self.BASE_URL}/projects",
                headers=self._headers(token),
            )

        if response.status_code != 200:

            raise HTTPException(
                status_code=400,
                detail="Unable to fetch Supabase projects.",
            )

        return response.json()

    # --------------------------------------------------
    # Get Project
    # --------------------------------------------------

    async def get_project(
        self,
        token: str,
        project_ref: str,
    ):

        projects = await self.get_projects(
            token
        )

        for project in projects:

            if project["id"] == project_ref:

                return project

        raise HTTPException(
            status_code=404,
            detail="Supabase project not found.",
        )

    # --------------------------------------------------
    # Configure Project
    # --------------------------------------------------

    async def configure_project(
        self,
        token: str,
        project_ref: str,
        deployment_url: str,
    ):

        project = await self.get_project(
            token,
            project_ref,
        )

        return {

            "success": True,

            "project": project["name"],

            "deployment_url": deployment_url,

        }


supabase_deployment_service = (
    SupabaseDeploymentService()
)
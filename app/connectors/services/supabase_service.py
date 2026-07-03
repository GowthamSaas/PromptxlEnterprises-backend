from typing import Dict, Any

import httpx
from fastapi import HTTPException


class SupabaseService:

    BASE_URL = "https://api.supabase.com"

    # ------------------------------------
    # Headers
    # ------------------------------------

    def _headers(self, token: str):

        return {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }

    # ------------------------------------
    # Validate Token
    # ------------------------------------

    async def validate_token(
        self,
        token: str
    ) -> bool:

        async with httpx.AsyncClient(timeout=20) as client:

            response = await client.get(
                f"{self.BASE_URL}/v1/projects",
                headers=self._headers(token)
            )

        return response.status_code == 200

    # ------------------------------------
    # Get Projects
    # ------------------------------------

    async def get_projects(
        self,
        token: str
    ):

        async with httpx.AsyncClient(timeout=20) as client:

            response = await client.get(
                f"{self.BASE_URL}/v1/projects",
                headers=self._headers(token)
            )

        if response.status_code != 200:
            raise HTTPException(
                status_code=400,
                detail="Invalid Supabase Personal Access Token."
            )

        return response.json()

    # ------------------------------------
    # Validate + Fetch Details
    # ------------------------------------

    async def connect(
        self,
        token: str
    ):

        projects = await self.get_projects(token)

        project_count = len(projects)

        first_project = (
            projects[0]
            if project_count > 0
            else {}
        )

        project_name = first_project.get(
            "name",
            "No Project"
        )

        project_ref = first_project.get(
            "id",
            ""
        )

        organization = ""

        organization_data = first_project.get(
            "organization",
            {}
        )

        if isinstance(organization_data, dict):
            organization = organization_data.get(
                "name",
                ""
            )

        return {

            "account_name": project_name,

            "metadata": {

                "projects": project_count,

                "project_name": project_name,

                "project_ref": project_ref,

                "organization": organization

            }

        }


supabase_service = SupabaseService()
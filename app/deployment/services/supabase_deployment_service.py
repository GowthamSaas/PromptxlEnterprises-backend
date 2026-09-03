"""
Supabase Deployment Service

Provides reusable methods for:
- Validating Supabase access
- Getting available Supabase projects
- Selecting the correct project for deployment
- Retrieving safe project information
- Preparing Supabase configuration

Tokens are always decrypted using encryption_service.decrypt_token().
Never exposes or returns Supabase tokens.
"""

from typing import Optional, List, Dict, Any
from dataclasses import dataclass

import httpx
from fastapi import HTTPException


@dataclass
class SupabaseProjectInfo:
    """Safe project information (no secrets)"""
    id: str  # project_ref
    name: str
    region: Optional[str] = None
    created_at: Optional[str] = None


@dataclass
class SupabaseConfigResult:
    """Safe configuration for generated applications (no secrets)"""
    project_ref: str
    project_name: str
    project_url: str
    api_url: str
    is_using_local_dev_url: bool = False


class SupabaseDeploymentService:

    BASE_URL = "https://api.supabase.com/v1"

    # --------------------------------------------------
    # Headers
    # --------------------------------------------------

    def _headers(
        self,
        token: str,
    ) -> Dict[str, str]:
        return {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        }

    # --------------------------------------------------
    # Validate Supabase Access
    # --------------------------------------------------

    async def validate_access(
        self,
        token: str,
    ) -> bool:
        """
        Verify that the Supabase token is valid and has API access.
        Returns True if access is valid.
        Raises HTTPException if token is invalid.
        """
        try:
            async with httpx.AsyncClient(timeout=30) as client:
                response = await client.get(
                    f"{self.BASE_URL}/projects",
                    headers=self._headers(token),
                )

            if response.status_code == 401:
                raise HTTPException(
                    status_code=401,
                    detail=(
                        "Supabase token is invalid or expired. "
                        "Please reconnect your Supabase connector."
                    ),
                )

            if response.status_code == 403:
                raise HTTPException(
                    status_code=403,
                    detail="Access denied. Insufficient permissions for Supabase.",
                )

            if response.status_code != 200:
                raise HTTPException(
                    status_code=400,
                    detail="Unable to validate Supabase access.",
                )

            return True

        except httpx.RequestError:
            raise HTTPException(
                status_code=503,
                detail="Unable to reach Supabase API. Please try again later.",
            )

    # --------------------------------------------------
    # Get All Projects
    # --------------------------------------------------

    async def get_projects(
        self,
        token: str,
    ) -> List[Dict[str, Any]]:
        """
        Fetch all Supabase projects for the authenticated user.
        Returns list of raw project objects from Supabase API.
        """
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
    # Get Safe Project List
    # --------------------------------------------------

    async def get_safe_projects(
        self,
        token: str,
    ) -> List[SupabaseProjectInfo]:
        """
        Fetch projects and return only safe information (no secrets).
        """
        projects = await self.get_projects(token)

        return [
            SupabaseProjectInfo(
                id=p.get("id", ""),
                name=p.get("name", "Unknown"),
                region=p.get("region"),
                created_at=p.get("created_at"),
            )
            for p in projects
        ]

    # --------------------------------------------------
    # Get Single Project
    # --------------------------------------------------

    async def get_project(
        self,
        token: str,
        project_ref: str,
    ) -> Dict[str, Any]:
        """
        Fetch a specific Supabase project by reference (ID).
        Returns raw project object.
        """
        projects = await self.get_projects(token)

        for project in projects:
            if project.get("id") == project_ref:
                return project

        raise HTTPException(
            status_code=404,
            detail=f"Supabase project '{project_ref}' not found.",
        )

    # --------------------------------------------------
    # Get Safe Project Info
    # --------------------------------------------------

    async def get_safe_project_info(
        self,
        token: str,
        project_ref: str,
    ) -> SupabaseProjectInfo:
        """
        Get safe project information for a specific project.
        """
        project = await self.get_project(token, project_ref)

        return SupabaseProjectInfo(
            id=project.get("id", ""),
            name=project.get("name", "Unknown"),
            region=project.get("region"),
            created_at=project.get("created_at"),
        )

    # --------------------------------------------------
    # Select Project for Deployment
    # --------------------------------------------------

    async def select_project(
        self,
        token: str,
        existing_project_ref: Optional[str] = None,
    ) -> SupabaseProjectInfo:
        """
        Determine which Supabase project to use for deployment.

        Priority:
        1. If existing_project_ref is provided and valid, use it
        2. Otherwise, use the first available project (if only one exists)
        3. If multiple projects exist and no selection, raise error

        Returns safe project info. Never exposes tokens.
        """
        # Validate token first
        await self.validate_access(token)

        # Get all projects
        projects = await self.get_safe_projects(token)

        if not projects:
            raise HTTPException(
                status_code=400,
                detail=(
                    "No Supabase projects found. "
                    "Please create a Supabase project first at supabase.com."
                ),
            )

        # If we have an existing project reference, verify it exists
        if existing_project_ref:
            for project in projects:
                if project.id == existing_project_ref:
                    return project

            raise HTTPException(
                status_code=400,
                detail=(
                    f"Configured Supabase project '{existing_project_ref}' not found. "
                    "Please update your Supabase configuration."
                ),
            )

        # If only one project, use it automatically
        if len(projects) == 1:
            return projects[0]

        # Multiple projects and no selection - need explicit choice
        project_names = [p.name for p in projects]
        raise HTTPException(
            status_code=400,
            detail=(
                f"Multiple Supabase projects found: {', '.join(project_names)}. "
                "Please configure which project to use for deployment."
            ),
        )

    # --------------------------------------------------
    # Get Project Configuration
    # --------------------------------------------------

    async def get_project_config(
        self,
        token: str,
        project_ref: str,
    ) -> SupabaseConfigResult:
        """
        Get safe configuration for a Supabase project.
        Returns only public-safe information needed for app configuration.
        Never returns tokens or secret keys.
        """
        project = await self.get_project(token, project_ref)

        # Extract safe configuration
        return SupabaseConfigResult(
            project_ref=project.get("id", ""),
            project_name=project.get("name", "Unknown"),
            project_url=f"https://{project.get('id', '')}.supabase.co",
            api_url=f"https://{project.get('id', '')}.supabase.co",
            is_using_local_dev_url=False,
        )

    # --------------------------------------------------
    # Configure Project for Deployment
    # --------------------------------------------------

    async def configure_project(
        self,
        token: str,
        project_ref: str,
        deployment_url: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Prepare a Supabase project for deployment.
        Returns safe project information and configuration.
        """
        # Validate access first
        await self.validate_access(token)

        # Get project configuration
        config = await self.get_project_config(token, project_ref)

        # Return safe configuration for the generated app
        return {
            "success": True,
            "project_ref": config.project_ref,
            "project_name": config.project_name,
            "api_url": config.api_url,
            "configured_at": "now",
        }


supabase_deployment_service = SupabaseDeploymentService()
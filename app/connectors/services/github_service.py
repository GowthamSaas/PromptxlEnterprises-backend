from typing import Dict, Any

import httpx
from fastapi import HTTPException


class GithubService:

    BASE_URL = "https://api.github.com"

    # ------------------------------------
    # Headers
    # ------------------------------------

    def _headers(self, token: str):

        return {
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28"
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
                f"{self.BASE_URL}/user",
                headers=self._headers(token)
            )

        return response.status_code == 200

    # ------------------------------------
    # Get User
    # ------------------------------------

    async def get_user(
        self,
        token: str
    ) -> Dict[str, Any]:

        async with httpx.AsyncClient(timeout=20) as client:

            response = await client.get(
                f"{self.BASE_URL}/user",
                headers=self._headers(token)
            )

        if response.status_code != 200:

            raise HTTPException(
                status_code=400,
                detail="Invalid GitHub Personal Access Token."
            )

        return response.json()

    # ------------------------------------
    # Get Repositories
    # ------------------------------------

    async def get_repositories(
        self,
        token: str
    ):

        async with httpx.AsyncClient(timeout=20) as client:

            response = await client.get(
                f"{self.BASE_URL}/user/repos",
                headers=self._headers(token),
                params={
                    "per_page": 100
                }
            )

        if response.status_code != 200:
            return []

        return response.json()

    # ------------------------------------
    # Validate + Fetch Details
    # ------------------------------------

    async def connect(
        self,
        token: str
    ):

        user = await self.get_user(token)

        repositories = await self.get_repositories(token)

        account = (
            user.get("login")
            or user.get("name")
            or "GitHub User"
        )

        return {

            "account_name": account,

            "metadata": {

                "repositories": len(repositories)

            }

        }


github_service = GithubService()
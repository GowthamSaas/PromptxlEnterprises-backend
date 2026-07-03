from typing import Dict, Any

import httpx
from fastapi import HTTPException


class VercelService:

    BASE_URL = "https://api.vercel.com"

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

    async def validate_token(self, token: str) -> bool:

        async with httpx.AsyncClient(timeout=20) as client:

            response = await client.get(
                f"{self.BASE_URL}/v2/user",
                headers=self._headers(token)
            )

            return response.status_code == 200

    # ------------------------------------
    # Get User
    # ------------------------------------

    async def get_user(self, token: str) -> Dict[str, Any]:

        async with httpx.AsyncClient(timeout=20) as client:

            response = await client.get(
                f"{self.BASE_URL}/v2/user",
                headers=self._headers(token)
            )

        if response.status_code != 200:
            raise HTTPException(
                status_code=400,
                detail="Invalid Vercel Access Token."
            )

        return response.json()

    # ------------------------------------
    # Get Teams
    # ------------------------------------

    async def get_teams(self, token: str):

        async with httpx.AsyncClient(timeout=20) as client:

            response = await client.get(
                f"{self.BASE_URL}/v2/teams",
                headers=self._headers(token)
            )

        if response.status_code != 200:
            return []

        data = response.json()

        return data.get("teams", [])

    # ------------------------------------
    # Validate + Fetch Details
    # ------------------------------------

    async def connect(self, token: str):

        user = await self.get_user(token)

        teams = await self.get_teams(token)

        account = (
            user.get("username")
            or user.get("name")
            or "Connected Account"
        )

        return {

            "account_name": account,

            "metadata": {

                "teams": len(teams)

            }

        }


vercel_service = VercelService()
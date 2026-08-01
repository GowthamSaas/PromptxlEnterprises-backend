from pathlib import Path
from typing import Any
import json

import httpx

from fastapi import HTTPException


class VercelCLIService:

    BASE_URL = "https://api.vercel.com"

    def _project_settings(self, root: Path) -> dict[str, Any]:
        package_file = root / "package.json"
        package: dict[str, Any] = {}

        if package_file.is_file():
            try:
                package = json.loads(package_file.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                package = {}

        dependencies = {
            **package.get("dependencies", {}),
            **package.get("devDependencies", {}),
        }

        if "next" in dependencies:
            return {"framework": "nextjs"}
        if "nuxt" in dependencies:
            return {"framework": "nuxtjs"}
        if "vue" in dependencies or "vite" in dependencies:
            return {
                "framework": "vite",
                "buildCommand": "npm run build",
                "outputDirectory": "dist",
            }
        if "react" in dependencies:
            return {
                "framework": "create-react-app",
                "buildCommand": "npm run build",
                "outputDirectory": "build",
            }

        return {"framework": None}

    # --------------------------------------------------
    # Deploy Project
    # --------------------------------------------------

    async def deploy(
        self,
        project_path: str,
        token: str,
        production: bool = True,
    ):

        root = Path(project_path)
        if not root.is_dir():
            raise HTTPException(status_code=400, detail="Exported project directory not found.")

        files: list[dict[str, str]] = []
        for file_path in root.rglob("*"):
            if file_path.is_file():
                files.append({
                    "file": file_path.relative_to(root).as_posix(),
                    "data": file_path.read_text(encoding="utf-8"),
                })

        if not files:
            raise HTTPException(status_code=400, detail="Exported project has no files.")

        payload: dict[str, Any] = {
            "name": root.name,
            "files": files,
            "projectSettings": self._project_settings(root),
        }
        if production:
            payload["target"] = "production"

        async with httpx.AsyncClient(timeout=120) as client:
            response = await client.post(
                f"{self.BASE_URL}/v13/deployments",
                headers={"Authorization": f"Bearer {token}"},
                json=payload,
            )

        if response.status_code not in (200, 201):
            detail = response.json().get("error", {}).get("message", response.text)
            raise HTTPException(status_code=400, detail=f"Vercel deployment failed: {detail}")

        result = response.json()
        deployment_url = result.get("url")
        return {
            "success": True,
            "deployment_id": result.get("id"),
            "deployment_url": f"https://{deployment_url}" if deployment_url and not deployment_url.startswith("http") else deployment_url,
            "logs": None,
        }

    # --------------------------------------------------
    # Extract Deployment URL
    # --------------------------------------------------

    def extract_url(
        self,
        output: str,
    ):

        for line in output.splitlines():

            line = line.strip()

            if line.startswith("https://"):

                return line

        return None

    # --------------------------------------------------
    # Get Deployment Logs
    # --------------------------------------------------

    async def get_logs(
        self,
        deployment_id: str,
        token: str,
    ):
        async with httpx.AsyncClient(timeout=60) as client:
            response = await client.get(
                f"{self.BASE_URL}/v2/deployments/{deployment_id}/events",
                headers={"Authorization": f"Bearer {token}"},
            )
        if response.status_code != 200:
            raise HTTPException(status_code=400, detail="Unable to fetch Vercel deployment logs.")
        return response.json()

    # --------------------------------------------------
    # Inspect Deployment
    # --------------------------------------------------

    async def inspect(
        self,
        deployment_id: str,
        token: str,
    ):
        async with httpx.AsyncClient(timeout=60) as client:
            response = await client.get(
                f"{self.BASE_URL}/v13/deployments/{deployment_id}",
                headers={"Authorization": f"Bearer {token}"},
            )
        if response.status_code != 200:
            raise HTTPException(status_code=400, detail="Unable to inspect Vercel deployment.")
        return response.json()


vercel_cli_service = VercelCLIService()
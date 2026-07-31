import json
import subprocess
import os
import shutil

from fastapi import HTTPException


class VercelCLIService:

    # --------------------------------------------------
    # Deploy Project
    # --------------------------------------------------

    async def deploy(
        self,
        project_path: str,
        token: str,
        production: bool = True,
    ):

        command = [
            "vercel",
            "--token",
            token,
            "--yes",
        ]

        if production:

            command.append("--prod")

        try:

            print("=" * 80)
            print("Project Path :", project_path)
            print("Exists       :", os.path.exists(project_path))
            print("Is Dir       :", os.path.isdir(project_path))
            print("Vercel Path  :", shutil.which("vercel"))
            print("Command      :", command)
            print("=" * 80)

            result = subprocess.run(
                command,
                cwd=project_path,
                capture_output=True,
                text=True,
                shell=True,
                check=True,
            )

            deployment_url = self.extract_url(
                result.stdout
            )

            return {

                "success": True,

                "deployment_url": deployment_url,

                "logs": result.stdout,

            }

        except subprocess.CalledProcessError as exc:

            raise HTTPException(
                status_code=400,
                detail={
                   "stdout": exc.stdout,
                    "stderr": exc.stderr,
                },
            )

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
        project_path: str,
        token: str,
    ):

        command = [

            "vercel",

            "logs",

            "--token",

            token,

        ]

        

        result = subprocess.run(
            command,
            cwd=project_path,
            capture_output=True,
            text=True,
        )

        return result.stdout

    # --------------------------------------------------
    # Inspect Deployment
    # --------------------------------------------------

    async def inspect(
        self,
        deployment_url: str,
        token: str,
    ):

        command = [

            "vercel",

            "inspect",

            deployment_url,

            "--token",

            token,

        ]

        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
        )

        return result.stdout


vercel_cli_service = VercelCLIService()
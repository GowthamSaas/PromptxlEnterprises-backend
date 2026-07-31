from typing import Any

import httpx
from fastapi import HTTPException


class GithubDeploymentService:

    BASE_URL = "https://api.github.com"

    # --------------------------------------------------
    # Headers
    # --------------------------------------------------

    def _headers(self, token: str):

        return {

            "Authorization": f"Bearer {token}",

            "Accept": "application/vnd.github+json",

            "X-GitHub-Api-Version": "2022-11-28",

        }

    # --------------------------------------------------
    # Get Current User
    # --------------------------------------------------

    async def get_user(
        self,
        token: str,
    ) -> dict[str, Any]:

        async with httpx.AsyncClient(timeout=30) as client:

            response = await client.get(
                f"{self.BASE_URL}/user",
                headers=self._headers(token),
            )

        if response.status_code != 200:

            raise HTTPException(
                status_code=400,
                detail="Unable to fetch GitHub user.",
            )

        return response.json()

    # --------------------------------------------------
    # Create Repository
    # --------------------------------------------------

    async def create_repository(
        self,
        token: str,
        name: str,
        private: bool = False,
    ) -> dict[str, Any]:

        async with httpx.AsyncClient(timeout=60) as client:

            response = await client.post(
                f"{self.BASE_URL}/user/repos",
                headers=self._headers(token),
                json={
                    "name": name,
                    "private": private,
                    "auto_init": True,
                },
            )

        if response.status_code not in [200, 201]:

            raise HTTPException(
                status_code=400,
                detail=response.json().get(
                    "message",
                    "Repository creation failed.",
                ),
            )

        return response.json()

    # --------------------------------------------------
    # Get Repository
    # --------------------------------------------------

    async def get_repository(
        self,
        token: str,
        owner: str,
        repository: str,
    ) -> dict[str, Any]:

        async with httpx.AsyncClient(timeout=30) as client:

            response = await client.get(
                f"{self.BASE_URL}/repos/{owner}/{repository}",
                headers=self._headers(token),
            )

        if response.status_code != 200:

            raise HTTPException(
                status_code=404,
                detail="Repository not found.",
            )

        return response.json()

    # --------------------------------------------------
    # Get Latest Commit SHA
    # --------------------------------------------------

    async def get_latest_commit(
        self,
        token: str,
        owner: str,
        repository: str,
        branch: str = "main",
    ) -> dict[str, Any]:

        async with httpx.AsyncClient(timeout=30) as client:

            response = await client.get(
                f"{self.BASE_URL}/repos/{owner}/{repository}/git/ref/heads/{branch}",
                headers=self._headers(token),
            )

        if response.status_code != 200:

            raise HTTPException(
                status_code=400,
                detail="Unable to fetch latest commit.",
            )

        return response.json()




        # --------------------------------------------------
    # Create Blob
    # --------------------------------------------------

    async def create_blob(
        self,
        token: str,
        owner: str,
        repository: str,
        content: str,
    ):

        async with httpx.AsyncClient(timeout=60) as client:

            response = await client.post(
                f"{self.BASE_URL}/repos/{owner}/{repository}/git/blobs",
                headers=self._headers(token),
                json={
                    "content": content,
                    "encoding": "utf-8",
                },
            )

        if response.status_code not in [200, 201]:

            raise HTTPException(
                status_code=400,
                detail="Unable to create blob.",
            )

        return response.json()

    # --------------------------------------------------
    # Get Tree
    # --------------------------------------------------

    async def get_tree(
        self,
        token: str,
        owner: str,
        repository: str,
        tree_sha: str,
    ):

        async with httpx.AsyncClient(timeout=60) as client:

            response = await client.get(
                f"{self.BASE_URL}/repos/{owner}/{repository}/git/trees/{tree_sha}",
                headers=self._headers(token),
            )

        if response.status_code != 200:

            raise HTTPException(
                status_code=400,
                detail="Unable to fetch tree.",
            )

        return response.json()

    # --------------------------------------------------
    # Create Tree
    # --------------------------------------------------

    async def create_tree(
        self,
        token: str,
        owner: str,
        repository: str,
        base_tree: str,
        tree: list,
    ):

        async with httpx.AsyncClient(timeout=60) as client:

            response = await client.post(
                f"{self.BASE_URL}/repos/{owner}/{repository}/git/trees",
                headers=self._headers(token),
                json={
                    "base_tree": base_tree,
                    "tree": tree,
                },
            )

        if response.status_code not in [200, 201]:

            raise HTTPException(
                status_code=400,
                detail="Unable to create tree.",
            )

        return response.json()

    # --------------------------------------------------
    # Create Commit
    # --------------------------------------------------

    async def create_commit(
        self,
        token: str,
        owner: str,
        repository: str,
        message: str,
        tree_sha: str,
        parent_commit: str,
    ):

        async with httpx.AsyncClient(timeout=60) as client:

            response = await client.post(
                f"{self.BASE_URL}/repos/{owner}/{repository}/git/commits",
                headers=self._headers(token),
                json={
                    "message": message,
                    "tree": tree_sha,
                    "parents": [
                        parent_commit
                    ],
                },
            )

        if response.status_code not in [200, 201]:

            raise HTTPException(
                status_code=400,
                detail="Unable to create commit.",
            )

        return response.json()

    # --------------------------------------------------
    # Update Branch Reference
    # --------------------------------------------------

    async def update_reference(
        self,
        token: str,
        owner: str,
        repository: str,
        branch: str,
        commit_sha: str,
    ):

        async with httpx.AsyncClient(timeout=60) as client:

            response = await client.patch(
                f"{self.BASE_URL}/repos/{owner}/{repository}/git/refs/heads/{branch}",
                headers=self._headers(token),
                json={
                    "sha": commit_sha,
                    "force": True,
                },
            )

        if response.status_code not in [200, 201]:

            raise HTTPException(
                status_code=400,
                detail="Unable to update branch.",
            )

        return response.json()

        # --------------------------------------------------
    # Push Project
    # --------------------------------------------------

    async def push_project(
        self,
        token: str,
        owner: str,
        repository: str,
        files: list,
        branch: str = "main",
    ):

        # ----------------------------------------
        # Latest Reference
        # ----------------------------------------

        latest_ref = await self.get_latest_commit(
            token=token,
            owner=owner,
            repository=repository,
            branch=branch,
        )

        commit_sha = latest_ref["object"]["sha"]

        # ----------------------------------------
        # Commit Details
        # ----------------------------------------

        async with httpx.AsyncClient(timeout=60) as client:

            commit_response = await client.get(
                f"{self.BASE_URL}/repos/{owner}/{repository}/git/commits/{commit_sha}",
                headers=self._headers(token),
            )

        if commit_response.status_code != 200:

            raise HTTPException(
                status_code=400,
                detail="Unable to fetch commit.",
            )

        commit = commit_response.json()

        base_tree = commit["tree"]["sha"]

        # ----------------------------------------
        # Create Blobs
        # ----------------------------------------

        tree = []

        for file in files:

            blob = await self.create_blob(
                token=token,
                owner=owner,
                repository=repository,
                content=file["content"],
            )

            tree.append(
                {
                    "path": file["path"],
                    "mode": "100644",
                    "type": "blob",
                    "sha": blob["sha"],
                }
            )

        # ----------------------------------------
        # Create Tree
        # ----------------------------------------

        tree_response = await self.create_tree(
            token=token,
            owner=owner,
            repository=repository,
            base_tree=base_tree,
            tree=tree,
        )

        tree_sha = tree_response["sha"]

        # ----------------------------------------
        # Create Commit
        # ----------------------------------------

        commit_response = await self.create_commit(
            token=token,
            owner=owner,
            repository=repository,
            message="Initial AI Generated Project",
            tree_sha=tree_sha,
            parent_commit=commit_sha,
        )

        new_commit = commit_response["sha"]

        # ----------------------------------------
        # Update Branch
        # ----------------------------------------

        await self.update_reference(
            token=token,
            owner=owner,
            repository=repository,
            branch=branch,
            commit_sha=new_commit,
        )

        return {

            "success": True,

            "repository_name": repository,

            "repository_url": f"https://github.com/{owner}/{repository}",

            "branch": branch,

            "commit_sha": new_commit,

        }


github_deployment_service = GithubDeploymentService()
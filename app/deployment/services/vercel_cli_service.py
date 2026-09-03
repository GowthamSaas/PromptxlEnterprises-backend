from pathlib import Path
from typing import Any, Optional
import json
import time

import httpx

from fastapi import HTTPException


class VercelCLIService:

    BASE_URL = "https://api.vercel.com"
    DEPLOYMENT_POLL_INTERVAL = 5  # seconds
    DEPLOYMENT_MAX_WAIT = 300  # 5 minutes max wait

    def _find_package_json(self, root: Path) -> tuple[Optional[Path], Optional[dict]]:
        """Find package.json in project, possibly nested in subdirectory."""
        # Check for package.json at root
        root_package = root / "package.json"
        if root_package.is_file():
            try:
                return root_package, json.loads(root_package.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                pass

        # Search for package.json in immediate subdirectories
        for subdir in root.iterdir():
            if subdir.is_dir() and subdir.name not in (".git", "node_modules", "__pycache__"):
                pkg = subdir / "package.json"
                if pkg.is_file():
                    try:
                        return pkg, json.loads(pkg.read_text(encoding="utf-8"))
                    except (OSError, json.JSONDecodeError):
                        pass

        return None, None

    def _detect_frontend_root(self, root: Path) -> tuple[Optional[str], Optional[dict]]:
        """Detect where the frontend root is (None for root, or subdirectory name)."""
        pkg_path, pkg_data = self._find_package_json(root)
        if pkg_path:
            rel_path = pkg_path.relative_to(root).as_posix()
            if rel_path == "package.json":
                return None, pkg_data  # Frontend at root
            else:
                # Frontend in subdirectory (e.g., "frontend")
                return str(Path(rel_path).parent), pkg_data
        return None, None

    def _project_settings(
        self,
        root: Path,
        frontend_root: Optional[str] = None,
        framework: Optional[str] = None,
    ) -> dict[str, Any]:
        """Determine project settings based on package.json and framework."""

        # If frontend_root specified, look there; otherwise detect
        if frontend_root:
            check_dir = root / frontend_root
        else:
            check_dir = root

        package_file = check_dir / "package.json"
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

        # If framework was explicitly passed, use it
        if framework == "next":
            return {"framework": "nextjs"}
        if framework == "nuxt":
            return {"framework": "nuxtjs"}
        if framework in ("vue", "react"):
            # For Vue/React with Vite
            if "vite" in dependencies:
                return {
                    "framework": "vite",
                    "buildCommand": "npm run build",
                    "outputDirectory": "dist",
                }
            # React without Vite (create-react-app)
            return {
                "framework": "create-react-app",
                "buildCommand": "npm run build",
                "outputDirectory": "build",
            }

        # Auto-detect framework from dependencies
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
            if "vite" in dependencies:
                return {
                    "framework": "vite",
                    "buildCommand": "npm run build",
                    "outputDirectory": "dist",
                }
            return {
                "framework": "create-react-app",
                "buildCommand": "npm run build",
                "outputDirectory": "build",
            }

        return {"framework": None}

    def _should_add_spa_routing(self, root: Path, frontend_root: Optional[str]) -> bool:
        """Check if we need SPA routing config (React Router, Vue Router, etc.)."""
        check_dir = root / (frontend_root or "")

        # Check for SPA router indicators
        router_indicators = [
            "react-router",
            "react-router-dom",
            "vue-router",
            "wouter",
            "@remix-run/react",
        ]

        for file_path in check_dir.rglob("*"):
            if file_path.suffix in (".js", ".ts", ".jsx", ".tsx", ".vue"):
                try:
                    content = file_path.read_text(encoding="utf-8").lower()
                    for indicator in router_indicators:
                        if indicator in content:
                            return True
                except (OSError, UnicodeDecodeError):
                    continue

        return False

    def _generate_vercel_json(
        self,
        root: Path,
        frontend_root: Optional[str],
        framework: Optional[str],
    ) -> Optional[dict[str, Any]]:
        """Generate vercel.json for SPA routing if needed."""
        if not self._should_add_spa_routing(root, frontend_root):
            return None

        config: dict[str, Any] = {
            "rewrites": [
                {"source": "/(.*)", "destination": "/index.html"},
            ],
        }

        return config

    async def _wait_for_deployment_ready(
        self,
        deployment_id: str,
        token: str,
    ) -> dict[str, Any]:
        """
        Poll deployment status until READY or ERROR/FAILED.
        
        Returns dict with deployment data on success.
        Raises HTTPException with detailed error on failure.
        """
        import asyncio

        async with httpx.AsyncClient(timeout=60) as client:
            elapsed = 0
            attempt = 0
            while elapsed < self.DEPLOYMENT_MAX_WAIT:
                attempt += 1
                
                response = await client.get(
                    f"{self.BASE_URL}/v13/deployments/{deployment_id}",
                    headers={"Authorization": f"Bearer {token}"},
                )

                # Handle rate limiting with backoff
                if response.status_code == 429:
                    retry_after = int(response.headers.get("retry-after", 10))
                    print(f"[Vercel Polling] Rate limited. Waiting {retry_after}s before retry...")
                    await asyncio.sleep(retry_after)
                    elapsed += retry_after
                    continue

                if response.status_code != 200:
                    # Log the actual error response for debugging
                    error_detail = "Unable to check Vercel deployment status."
                    try:
                        error_data = response.json()
                        error_message = error_data.get("error", {}).get("message", error_data.get("message", response.text))
                        error_detail = f"Vercel API error. HTTP {response.status_code}: {error_message}"
                    except Exception:
                        error_detail = f"Vercel API error. HTTP {response.status_code}: {response.text[:200]}"
                    
                    print(f"[Vercel Polling] Error on attempt {attempt}: {error_detail}")
                    raise HTTPException(
                        status_code=400,
                        detail=error_detail,
                    )

                data = response.json()
                state = data.get("readyState", "")
                
                print(f"[Vercel Polling] Attempt {attempt}: state={state}, elapsed={elapsed}s")

                if state == "READY":
                    print(f"[Vercel Polling] Deployment {deployment_id} is READY")
                    return data
                    
                if state in ("ERROR", "CANCELED", "FAILED"):
                    # Try to get more error info from the response
                    error_message = data.get("error_message") or data.get("readyState")
                    print(f"[Vercel Polling] Deployment {deployment_id} failed with state: {state}, error: {error_message}")
                    raise HTTPException(
                        status_code=400,
                        detail=f"Vercel deployment {state}. Error: {error_message}",
                    )

                # Wait before next poll
                await asyncio.sleep(self.DEPLOYMENT_POLL_INTERVAL)
                elapsed += self.DEPLOYMENT_POLL_INTERVAL

            # Timeout
            print(f"[Vercel Polling] Timeout after {elapsed}s ({attempt} attempts)")
            raise HTTPException(
                status_code=400,
                detail=f"Vercel deployment timed out after {elapsed}s. Last state: {data.get('readyState', 'UNKNOWN')}",
            )

    async def _health_check(
        self,
        deployment_url: str,
        path: str = "",
    ) -> tuple[bool, int]:
        """Verify deployment URL is accessible at a specific path."""
        url = deployment_url.rstrip("/")
        if path:
            url = f"{url}{path}"

        async with httpx.AsyncClient(timeout=30, follow_redirects=True) as client:
            try:
                response = await client.get(url)
                # 2xx, 3xx are acceptable; 4xx/5xx means problem
                if response.status_code < 400:
                    return True, response.status_code
                return False, response.status_code
            except httpx.RequestError:
                return False, 0

    # --------------------------------------------------
    # Deploy Project
    # --------------------------------------------------

    async def deploy(
        self,
        project_path: str,
        token: str,
        production: bool = True,
        frontend_root: Optional[str] = None,
        backend_root: Optional[str] = None,
        framework: Optional[str] = None,
        is_full_stack: bool = False,
        is_backend_vercel_compatible: bool = False,
        python_deployment_config: Optional[dict] = None,
        api_health_endpoint: Optional[str] = None,
    ) -> dict[str, Any]:
        """
        Deploy project to Vercel.

        Returns dict with:
        - success: bool
        - deployment_id: str
        - deployment_url: str
        - deployment_state: str (READY, ERROR, etc.)
        - health_check_passed: bool
        - health_check_status: int (HTTP status code)
        - backend_health_check_passed: bool
        - backend_health_check_status: int
        - logs: dict or None
        - diagnostics: dict (non-sensitive info)
        """

        root = Path(project_path)
        if not root.is_dir():
            raise HTTPException(
                status_code=400,
                detail="Exported project directory not found.",
            )

        # Detect frontend root if not provided
        if frontend_root is None:
            detected_root, _ = self._detect_frontend_root(root)
            frontend_root = detected_root

        # Generate vercel.json for SPA routing if needed (only for frontend-only)
        vercel_json = None
        if not python_deployment_config:
            vercel_json = self._generate_vercel_json(root, frontend_root, framework)

        # Build file list
        # For frontend-only with nested structure, strip the frontend_root prefix
        # so files are at the root of the Vercel deployment
        files: list[dict[str, str]] = []
        for file_path in root.rglob("*"):
            if file_path.is_file():
                rel_path = file_path.relative_to(root).as_posix()
                
                # For frontend-only deployments with nested structure,
                # strip the frontend_root prefix so files deploy at root
                if frontend_root and not python_deployment_config and rel_path.startswith(frontend_root + "/"):
                    rel_path = rel_path[len(frontend_root) + 1:]
                
                files.append({
                    "file": rel_path,
                    "data": file_path.read_text(encoding="utf-8"),
                })

        # Add vercel.json if needed (frontend-only case)
        if vercel_json:
            files.append({
                "file": "vercel.json",
                "data": json.dumps(vercel_json, indent=2),
            })

        # Add Python backend files if this is a Python deployment
        if python_deployment_config:
            # Add the vercel.json from Python config
            if python_deployment_config.get("vercel_json"):
                files.append({
                    "file": "vercel.json",
                    "data": json.dumps(python_deployment_config["vercel_json"], indent=2),
                })

            # Add the api/index.py entrypoint
            if python_deployment_config.get("entrypoint_content"):
                entrypoint_filename = python_deployment_config.get("entrypoint_filename", "index.py")
                files.append({
                    "file": f"api/{entrypoint_filename}",
                    "data": python_deployment_config["entrypoint_content"],
                })

        if not files:
            raise HTTPException(
                status_code=400,
                detail="Exported project has no files.",
            )

        # Build project settings
        project_settings = self._project_settings(
            root=root,
            frontend_root=frontend_root,
            framework=framework,
        )

        # Build payload - NOTE: rootDirectory is NOT supported by Vercel deployment API
        payload: dict[str, Any] = {
            "name": root.name,
            "files": files,
            "projectSettings": project_settings,
        }

        if production:
            payload["target"] = "production"

        # Diagnostics (non-sensitive)
        diagnostics = {
            "frontend_root": frontend_root,
            "backend_root": backend_root,
            "framework": framework,
            "is_full_stack": is_full_stack,
            "is_backend_vercel_compatible": is_backend_vercel_compatible,
            "has_vercel_json": vercel_json is not None or python_deployment_config is not None,
            "has_python_backend": python_deployment_config is not None,
            "api_prefix": python_deployment_config.get("api_prefix") if python_deployment_config else None,
            "project_settings": project_settings,
            "file_count": len(files),
        }

        async with httpx.AsyncClient(timeout=120) as client:
            response = await client.post(
                f"{self.BASE_URL}/v13/deployments",
                headers={"Authorization": f"Bearer {token}"},
                json=payload,
            )

        if response.status_code not in (200, 201):
            detail = response.json().get("error", {}).get("message", response.text)
            raise HTTPException(
                status_code=400,
                detail=f"Vercel deployment creation failed: {detail}",
            )

        result = response.json()
        deployment_id = result.get("id")
        deployment_url = result.get("url")

        if not deployment_url:
            raise HTTPException(
                status_code=400,
                detail="Vercel deployment created but no URL returned.",
            )

        full_url = (
            f"https://{deployment_url}"
            if not deployment_url.startswith("http")
            else deployment_url
        )

        print(f"[Vercel Deployment] Created deployment {deployment_id}, URL: {full_url}")

        # Wait for deployment to be READY
        polling_error = None
        try:
            ready_data = await self._wait_for_deployment_ready(deployment_id, token)
            deployment_state = ready_data.get("readyState", "UNKNOWN")
        except HTTPException as exc:
            # Capture the polling error detail
            deployment_state = "POLLING_FAILED"
            polling_error = str(exc.detail)
            print(f"[Vercel Deployment] Polling failed: {polling_error}")

        # Health check the frontend (for all deployments)
        health_passed, health_status = await self._health_check(full_url)

        # Health check the backend API if this is a full-stack deployment
        backend_health_passed = True
        backend_health_status = 0
        if python_deployment_config and api_health_endpoint:
            backend_health_passed, backend_health_status = await self._health_check(
                full_url, api_health_endpoint
            )

        # Overall success requires:
        # 1. Deployment is READY
        # 2. Frontend health check passes
        # 3. Backend health check passes (for full-stack)
        success = (
            deployment_state == "READY"
            and health_passed
            and (backend_health_passed or not python_deployment_config)
        )

        return {
            "success": success,
            "deployment_id": deployment_id,
            "deployment_url": full_url,
            "deployment_state": deployment_state,
            "polling_error": polling_error,
            "health_check_passed": health_passed,
            "health_check_status": health_status,
            "backend_health_check_passed": backend_health_passed,
            "backend_health_check_status": backend_health_status,
            "logs": None,
            "diagnostics": diagnostics,
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
            raise HTTPException(
                status_code=400,
                detail="Unable to fetch Vercel deployment logs.",
            )
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
            raise HTTPException(
                status_code=400,
                detail="Unable to inspect Vercel deployment.",
            )
        return response.json()


vercel_cli_service = VercelCLIService()
"""
Vercel Python Runtime Service

Handles preparation of Python backends (FastAPI, Django) for Vercel's
Python serverless runtime.

Generates:
- vercel.json: Routing configuration for frontend/backend split
- api/index.py: Python entrypoint for Vercel Functions
"""

import json
import re
from pathlib import Path
from typing import Optional

from fastapi import HTTPException


class VercelPythonService:

    def __init__(self):
        pass

    def _find_fastapi_app(self, project_path: str, backend_root: Optional[str]) -> tuple[Optional[str], Optional[str]]:
        """
        Find the FastAPI app in the project.
        
        Returns: (app_import_path, app_attribute_name)
        e.g., ("backend.main", "app")
        """
        base = Path(project_path)
        backend_dir = base / backend_root if backend_root else base

        # Common FastAPI entry patterns
        patterns = [
            # (file_path_pattern, import_path, attribute_name)
            ("**/main.py", "main", "app"),
            ("**/app.py", "app", "app"),
            ("**/api.py", "api", "app"),
            ("**/server.py", "server", "app"),
        ]

        for glob_pattern, module_name, attr_name in patterns:
            for file_path in backend_dir.glob(glob_pattern):
                try:
                    content = file_path.read_text(encoding="utf-8")
                    # Check if this file contains FastAPI
                    if "fastapi" in content.lower():
                        # Determine the import path
                        rel_path = file_path.relative_to(base)
                        parts = list(rel_path.parts)
                        # Remove filename, add module name
                        if len(parts) > 1:
                            module_path = ".".join(parts[:-1] + [module_name])
                        else:
                            module_path = module_name

                        return module_path, attr_name
                except (OSError, UnicodeDecodeError):
                    continue

        return None, None

    def _find_django_wsgi(self, project_path: str, backend_root: Optional[str]) -> tuple[Optional[str], Optional[str]]:
        """
        Find the Django WSGI/ASGI application.
        
        Returns: (module_path, attribute_name)
        e.g., ("backend.config.wsgi", "application")
        """
        base = Path(project_path)
        backend_dir = base / backend_root if backend_root else base

        # Look for wsgi.py or asgi.py
        for wsgi_file in backend_dir.glob("**/wsgi.py"):
            try:
                content = wsgi_file.read_text(encoding="utf-8")
                if "wsgi" in content.lower() or "application" in content:
                    rel_path = wsgi_file.relative_to(base)
                    parts = list(rel_path.parts)
                    # Remove wsgi.py, construct module path
                    if len(parts) > 1:
                        module_path = ".".join(parts[:-1])
                        return module_path, "application"
            except (OSError, UnicodeDecodeError):
                continue

        # Also check asgi.py
        for asgi_file in backend_dir.glob("**/asgi.py"):
            try:
                content = asgi_file.read_text(encoding="utf-8")
                if "asgi" in content.lower() or "application" in content:
                    rel_path = asgi_file.relative_to(base)
                    parts = list(rel_path.parts)
                    if len(parts) > 1:
                        module_path = ".".join(parts[:-1])
                        return module_path, "application"
            except (OSError, UnicodeDecodeError):
                continue

        return None, None

    def _find_api_routes(self, project_path: str, backend_root: Optional[str]) -> list[str]:
        """
        Attempt to find API route prefixes from the backend code.
        Returns list of detected API prefixes like ['/api', '/api/todos']
        """
        routes = []
        base = Path(project_path)
        backend_dir = base / backend_root if backend_root else base

        # Look for FastAPI router definitions
        for py_file in backend_dir.glob("**/*.py"):
            try:
                content = py_file.read_text(encoding="utf-8")
                # Find router prefixes: @router.get("/api/...") or app.include_router(..., prefix="/api")
                router_prefixes = re.findall(r'prefix\s*=\s*["\']([^"\']+)["\']', content)
                routes.extend(router_prefixes)

                # Find direct route decorators: @app.get("/api/...") etc.
                direct_routes = re.findall(r'@(?:app|router)\.(?:get|post|put|delete|patch)\(["\']([^"\']+)["\']', content)
                for route in direct_routes:
                    # Extract prefix from route (e.g., "/api/todos" -> "/api")
                    if route.startswith("/"):
                        parts = route.split("/")
                        if len(parts) > 2:
                            prefix = "/" + "/".join(parts[:3])
                            if prefix not in routes:
                                routes.append(prefix)
            except (OSError, UnicodeDecodeError):
                continue

        return list(set(routes))[:5]  # Dedupe and limit

    def _generate_fastapi_entrypoint(
        self,
        app_import_path: str,
        app_attribute: str,
    ) -> str:
        """
        Generate the Vercel Python Function entrypoint for FastAPI.
        """
        return f'''"""
Vercel Python Function entrypoint for FastAPI backend.
DO NOT EDIT - Auto-generated by PromptXL deployment.
"""

from {app_import_path} import {app_attribute}
from fastapi.middleware.cors import CORSMiddleware

# Configure CORS for production
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Vercel serverless handler
handler = {app_attribute}
'''

    def _generate_django_entrypoint(
        self,
        django_module: str,
        use_asgi: bool = False,
    ) -> str:
        """
        Generate the Vercel Python Function entrypoint for Django.
        """
        application_var = "application" if not use_asgi else "application"
        
        return f'''"""
Vercel Python Function entrypoint for Django backend.
DO NOT EDIT - Auto-generated by PromptXL deployment.
"""

import os
import sys

# Add the backend to the path
backend_path = os.environ.get("VERCEL_DEPLOYMENT_BACKEND_PATH", "")
if backend_path and backend_path not in sys.path:
    sys.path.insert(0, backend_path)

# Configure Django settings
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "{django_module}.settings")

# Import and return the WSGI application
from {django_module}.wsgi import {application_var}
application = {application_var}
'''

    def generate_vercel_json(
        self,
        frontend_root: Optional[str],
        has_python_backend: bool,
        backend_framework: Optional[str],
        api_prefix: Optional[str] = None,
    ) -> dict:
        """
        Generate vercel.json for routing configuration.
        
        Routes:
        - /api/* -> Python backend (Vercel Functions)
        - /* -> Frontend (Static files)
        """
        rewrites = []
        
        if has_python_backend:
            # Route /api/* to the Python backend
            # The api/index.py handles the routing
            api_destination = "/api/index" if api_prefix in (None, "/api") else f"/api/index{api_prefix}"
            rewrites.append({
                "source": f"{api_prefix if api_prefix else '/api'}/(.*)",
                "destination": "/api/index"
            })
        else:
            # SPA fallback for frontend-only
            rewrites.append({
                "source": "/(.*)",
                "destination": "/index.html"
            })

        config = {
            "rewrites": rewrites,
            "headers": [
                {
                    "source": "/api/(.*)",
                    "headers": [
                        {"key": "Access-Control-Allow-Origin", "value": "*"},
                        {"key": "Access-Control-Allow-Methods", "value": "GET, POST, PUT, DELETE, PATCH, OPTIONS"},
                        {"key": "Access-Control-Allow-Headers", "value": "Content-Type, Authorization"},
                    ]
                }
            ]
        }

        # Add trailing slash handling for SPA routes
        if not has_python_backend:
            config["routes"] = [
                {"src": "/(.*)", "dest": "/$1", "headers": {"x-vercel-roaming": "legacy"}}
            ]

        return config

    async def prepare_python_deployment(
        self,
        project_path: str,
        backend_framework: str,
        backend_root: Optional[str],
        project_type,
    ) -> dict:
        """
        Prepare the Python backend for Vercel deployment.
        
        Returns dict with:
        - vercel_json: dict for vercel.json content
        - entrypoint_content: str for api/index.py
        - entrypoint_filename: str (e.g., "index.py")
        - api_prefix: str (e.g., "/api")
        """
        if backend_framework == "fastapi":
            app_import, app_attr = self._find_fastapi_app(project_path, backend_root)
            if not app_import:
                raise HTTPException(
                    status_code=400,
                    detail=(
                        "Could not find FastAPI application in the generated backend. "
                        "Please ensure your backend has a main.py or app.py with a FastAPI instance."
                    ),
                )

            # Find API routes
            api_routes = self._find_api_routes(project_path, backend_root)
            api_prefix = api_routes[0] if api_routes else "/api"

            vercel_json = self.generate_vercel_json(
                frontend_root=project_type.frontend_root,
                has_python_backend=True,
                backend_framework="fastapi",
                api_prefix=api_prefix,
            )

            entrypoint = self._generate_fastapi_entrypoint(app_import, app_attr)

            return {
                "vercel_json": vercel_json,
                "entrypoint_content": entrypoint,
                "entrypoint_filename": "index.py",
                "api_prefix": api_prefix,
            }

        elif backend_framework == "django":
            wsgi_module, _ = self._find_django_wsgi(project_path, backend_root)
            if not wsgi_module:
                raise HTTPException(
                    status_code=400,
                    detail=(
                        "Could not find Django WSGI configuration. "
                        "Please ensure your Django project has a wsgi.py file."
                    ),
                )

            # Find API routes
            api_routes = self._find_api_routes(project_path, backend_root)
            api_prefix = api_routes[0] if api_routes else "/api"

            vercel_json = self.generate_vercel_json(
                frontend_root=project_type.frontend_root,
                has_python_backend=True,
                backend_framework="django",
                api_prefix=api_prefix,
            )

            entrypoint = self._generate_django_entrypoint(wsgi_module)

            return {
                "vercel_json": vercel_json,
                "entrypoint_content": entrypoint,
                "entrypoint_filename": "index.py",
                "api_prefix": api_prefix,
            }

        else:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported backend framework: {backend_framework}",
            )


vercel_python_service = VercelPythonService()

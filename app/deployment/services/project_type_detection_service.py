"""
Project Type Detection Service

Determines whether a generated project is:
- frontend_only: No backend/database requirements
- full_stack: Requires Supabase database

Detection is conservative - a project is considered full_stack only if
there are clear indicators of backend/API/database requirements.
"""

import json
import re
from typing import List, Optional
from dataclasses import dataclass

from app.projects.models import ProjectFile


@dataclass
class ProjectTypeResult:
    application_type: str  # "frontend_only" or "full_stack"
    requires_supabase: bool
    detection_reasons: List[str]
    frontend_root: Optional[str] = None  # e.g., "frontend" or None (root)
    backend_root: Optional[str] = None   # e.g., "backend" or None
    frontend_framework: Optional[str] = None  # "react", "vue", "next", "nuxt"
    backend_framework: Optional[str] = None  # "fastapi", "django"
    vercel_python_runtime: bool = False  # True if Python backend needs Vercel Python runtime
    requirements_path: Optional[str] = None  # Path to requirements.txt
    api_health_endpoint: Optional[str] = None  # Detected health check endpoint


class ProjectTypeDetectionService:

    # Files/directories that strongly indicate a backend/API exists
    BACKEND_INDICATORS = [
        # Backend framework indicators
        "backend/",
        "backend.py",
        "server.py",
        "api.py",
        "app.py",
        # FastAPI specific
        "fastapi",
        "main.py",  # if it contains FastAPI/app imports
        # Django specific
        "manage.py",
        "settings.py",
        # Flask specific
        "flask",
        "app.route",
        # Express/Node specific
        "server.js",
        "server.ts",
        "express",
        # Database indicators
        "database",
        "db.py",
        "models.py",  # SQLAlchemy/Peewee models
        "schemas.py",  # Pydantic schemas often indicate API
        # Config files that suggest full-stack
        "requirements.txt",
        "package.json",
        "pyproject.toml",
        # Supabase indicators
        ".env",
        ".env.local",
        "supabase",
        # Docker
        "docker-compose",
        "Dockerfile",
    ]

    # Files that are purely frontend and don't indicate backend
    FRONTEND_ONLY_INDICATORS = [
        "index.html",
        "vite.config.js",
        "vite.config.ts",
        "webpack.config",
        "next.config.js",
        "nuxt.config.js",
        "svelte.config.js",
        "tailwind.config",
        "postcss.config",
    ]

    # Keywords in file content that indicate backend/API
    BACKEND_CONTENT_PATTERNS = [
        "from fastapi import",
        "from flask import",
        "from django",
        "import express",
        "from sqlalchemy",
        "from pydantic",
        "supabase.create_client",
        "async def api",
        "app.get(",
        "app.post(",
        "router = APIRouter",
        "@app.route",
        "def create_app",
    ]

    def detect_project_type(
        self,
        project_files: List[ProjectFile],
    ) -> ProjectTypeResult:
        """
        Analyze project files to determine if this is a frontend-only
        or full-stack application.

        Detection is conservative - requires strong evidence for full_stack.
        """

        detection_reasons = []
        backend_score = 0
        frontend_score = 0

        file_paths = []
        file_contents = []
        file_data = []  # Keep original paths for package.json detection

        for pf in project_files:
            path = pf.file_path if pf.file_path else ""
            content = pf.content if pf.content else ""
            file_paths.append(path.lower())
            file_contents.append(content.lower())
            file_data.append((path, content))

        # Find frontend root (where package.json is located)
        frontend_root = None
        package_json_path = None
        package_json_content = None

        for path, content in file_data:
            if path.endswith("package.json") and "node_modules" not in path:
                # Determine frontend root based on package.json location
                parts = path.split("/")
                if len(parts) > 1:
                    # package.json is in a subdirectory (e.g., frontend/package.json)
                    frontend_root = parts[0]
                else:
                    # package.json is at root
                    frontend_root = None
                package_json_path = path
                # Parse package.json for framework detection
                try:
                    package_json_content = json.loads(content) if content else {}
                except json.JSONDecodeError:
                    package_json_content = {}
                break

        # Detect frontend framework from package.json
        framework = None
        if package_json_content:
            deps = {
                **package_json_content.get("dependencies", {}),
                **package_json_content.get("devDependencies", {}),
            }
            if "next" in deps:
                framework = "next"
            elif "nuxt" in deps:
                framework = "nuxt"
            elif "vue" in deps and "vite" in deps:
                framework = "vue"
            elif "react" in deps:
                framework = "react"

        # Find backend root and framework
        backend_root = None
        backend_framework = None
        vercel_python_runtime = False
        requirements_path = None
        api_health_endpoint = None

        # First, find requirements.txt to determine backend location
        for path in file_paths:
            if "requirements.txt" in path and "node_modules" not in path:
                requirements_path = path
                # Determine backend root from requirements.txt location
                parts = path.split("/")
                if len(parts) > 1:
                    backend_root = parts[0]
                break

        # Detect Django (has manage.py, settings.py, etc.)
        django_indicators = ["manage.py", "settings.py", "wsgi.py", "asgi.py"]
        has_django = False
        for path in file_paths:
            if any(indicator in path for indicator in django_indicators):
                has_django = True
                break

        if has_django:
            backend_framework = "django"
            vercel_python_runtime = True
            detection_reasons.append("Django backend detected")
            # Find backend root for Django
            for path in file_paths:
                if "manage.py" in path:
                    parts = path.split("/")
                    if len(parts) > 1:
                        backend_root = parts[0]
                    break
            api_health_endpoint = "/api/health/"  # Django common health endpoint

        # Detect FastAPI (has fastapi imports or main.py with FastAPI)
        if not backend_framework:
            for path, content in zip(file_paths, file_contents):
                if "fastapi" in content or "from fastapi import" in content:
                    backend_framework = "fastapi"
                    vercel_python_runtime = True
                    detection_reasons.append("FastAPI backend detected")
                    # Find backend root from the file path
                    parts = path.split("/")
                    if len(parts) > 1 and parts[0] not in (frontend_root,):
                        backend_root = parts[0]
                    elif backend_root is None:
                        backend_root = None  # At root level
                    api_health_endpoint = "/api/health"
                    break

        # Detect Express/Node.js backend (alternative)
        if not backend_framework:
            for path in file_paths:
                if any(x in path for x in ["backend/server.js", "backend/server.ts", "api/index.js", "api/server.js"]):
                    backend_framework = "express"
                    backend_root = "backend" if "backend" in path else "api"
                    vercel_python_runtime = False
                    api_health_endpoint = "/api/health"
                    detection_reasons.append("Express/Node.js backend detected")
                    break

        # Check file paths for backend indicators
        for indicator in self.BACKEND_INDICATORS:
            indicator_lower = indicator.lower()
            for file_path in file_paths:
                if indicator_lower in file_path:
                    backend_score += 2
                    if indicator not in detection_reasons:
                        detection_reasons.append(f"Found backend indicator: {indicator}")
                    break

        # Check for explicit frontend indicators (reduces confidence in full_stack)
        for indicator in self.FRONTEND_ONLY_INDICATORS:
            indicator_lower = indicator.lower()
            for file_path in file_paths:
                if indicator_lower in file_path:
                    frontend_score += 1
                    break

        # Check file contents for backend patterns
        for pattern in self.BACKEND_CONTENT_PATTERNS:
            pattern_lower = pattern.lower()
            for content in file_contents:
                if pattern_lower in content:
                    backend_score += 3
                    if pattern not in detection_reasons:
                        detection_reasons.append(f"Found backend pattern: {pattern}")
                    break

        # Check for project metadata indicating full-stack
        # (e.g., generated project with explicit backend flag)
        for pf in project_files:
            if pf.file_path and "project.json" in pf.file_path.lower():
                if pf.content:
                    content_lower = pf.content.lower()
                    if '"is_full_stack": true' in content_lower or '"full_stack": true' in content_lower:
                        backend_score += 5
                        detection_reasons.append("Project metadata indicates full-stack")
                    elif '"frontend_only": true' in content_lower:
                        frontend_score += 3
                        detection_reasons.append("Project metadata indicates frontend-only")

        # Determine project type based on scores
        # Need backend_score > frontend_score + 2 to be considered full_stack
        if backend_score > frontend_score + 2 or backend_framework:
            return ProjectTypeResult(
                application_type="full_stack",
                requires_supabase=True,
                detection_reasons=detection_reasons,
                frontend_root=frontend_root,
                backend_root=backend_root,
                frontend_framework=framework,
                backend_framework=backend_framework,
                vercel_python_runtime=vercel_python_runtime,
                requirements_path=requirements_path,
                api_health_endpoint=api_health_endpoint,
            )
        else:
            return ProjectTypeResult(
                application_type="frontend_only",
                requires_supabase=False,
                detection_reasons=detection_reasons if detection_reasons else ["No backend indicators found"],
                frontend_root=frontend_root,
                backend_root=backend_root,
                frontend_framework=framework,
                backend_framework=None,
                vercel_python_runtime=False,
                requirements_path=requirements_path,
                api_health_endpoint=None,
            )


project_type_detection_service = ProjectTypeDetectionService()

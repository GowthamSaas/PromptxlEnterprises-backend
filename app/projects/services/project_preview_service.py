from pathlib import Path

from app.projects.models import Project


class ProjectPreviewService:

    BASE_DIRECTORY = Path("generated_projects")

    def get_project_preview(
        self,
        project: Project,
    ) -> dict:

        project_path = (
            self.BASE_DIRECTORY
            / f"project_{project.id}_{project.name.replace(' ', '_')}"
        )

        if not project_path.exists():
            return {
                "project_name": project.name,
                "tree": [],
            }

        tree = []

        for path in sorted(project_path.rglob("*")):
            tree.append(
                str(path.relative_to(project_path))
            )

        return {
            "project_name": project.name,
            "tree": tree,
        }


project_preview_service = ProjectPreviewService()
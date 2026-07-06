from app.projects.models import Project
from app.project_files import crud as project_file_crud


class ProjectPreviewService:

    def get_project_preview(
        self,
        db,
        project: Project,
    ) -> dict:
        """
        Build project preview from database.
        """

        project_files = project_file_crud.get_project_files(
            db=db,
            project_id=project.id,
        )

        tree = [
            file.file_path
            for file in project_files
        ]

        return {
            "project_name": project.name,
            "tree": tree,
        }


project_preview_service = ProjectPreviewService()
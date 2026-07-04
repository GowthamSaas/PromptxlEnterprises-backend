from pathlib import Path

from sqlalchemy.orm import Session

from app.projects import crud
from app.projects.models import Project


class ProjectFileService:

    BASE_DIRECTORY = Path("generated_projects")

    def create_project_folder(
        self,
        project: Project,
    ) -> Path:
        """
        Create project root folder.
        """

        project_path = (
            self.BASE_DIRECTORY
            / f"project_{project.id}_{project.name.replace(' ', '_')}"
        )

        project_path.mkdir(
            parents=True,
            exist_ok=True,
        )

        return project_path

    def save_project_files(
        self,
        db: Session,
        project: Project,
        files: list[dict],
    ) -> None:
        """
        Save all generated files.
        """

        project_root = self.create_project_folder(project)

        for file in files:

            self.write_file(
                project_root=project_root,
                file=file,
            )

            crud.create_project_file(
                db=db,
                project_id=project.id,
                file_name=Path(file["path"]).name,
                file_path=file["path"],
                language=file.get("language"),
                content=file["content"],
            )

    def write_file(
        self,
        project_root: Path,
        file: dict,
    ) -> None:
        """
        Write generated file.
        """

        file_path = project_root / file["path"]

        file_path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        file_path.write_text(
            file["content"],
            encoding="utf-8",
        )

    def delete_project_folder(
        self,
        project: Project,
    ) -> None:
        """
        Delete project folder.
        """

        import shutil

        project_path = (
            self.BASE_DIRECTORY
            / f"project_{project.id}_{project.name.replace(' ', '_')}"
        )

        if project_path.exists():
            shutil.rmtree(project_path)


project_file_service = ProjectFileService()
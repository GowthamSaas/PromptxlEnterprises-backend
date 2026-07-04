from pathlib import Path
import zipfile

from app.projects.models import Project


class ExportService:

    BASE_DIRECTORY = Path("generated_projects")

    EXPORT_DIRECTORY = Path("exports")

    def export_project(
        self,
        project: Project,
    ) -> Path:
        """
        Export project as ZIP file.
        """

        project_path = (
            self.BASE_DIRECTORY
            / f"project_{project.id}_{project.name.replace(' ', '_')}"
        )

        if not project_path.exists():
            raise FileNotFoundError(
                "Project folder not found."
            )

        self.EXPORT_DIRECTORY.mkdir(
            parents=True,
            exist_ok=True,
        )

        zip_path = (
            self.EXPORT_DIRECTORY
            / f"{project.name.replace(' ', '_')}.zip"
        )

        with zipfile.ZipFile(
            zip_path,
            "w",
            zipfile.ZIP_DEFLATED,
        ) as zipf:

            for file in project_path.rglob("*"):

                if file.is_file():

                    zipf.write(
                        file,
                        file.relative_to(project_path),
                    )

        return zip_path


export_service = ExportService()
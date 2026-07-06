from pathlib import Path
import shutil
import tempfile
import zipfile

from sqlalchemy.orm import Session

from app.projects.models import Project
from app.project_files import crud as project_file_crud


class ExportService:
    """
    Export project from database as temporary ZIP.
    """

    def export_project(
        self,
        db: Session,
        project: Project,
    ) -> Path:

        project_files = project_file_crud.get_project_files(
            db=db,
            project_id=project.id,
        )

        if not project_files:
            raise FileNotFoundError(
                "Project files not found."
            )

        base_temp = Path(
            tempfile.mkdtemp()
        )

        temp_dir = base_temp / project.name.replace(" ", "_")

        temp_dir.mkdir(
           parents=True,
           exist_ok=True,
       )

        try:

            for file in project_files:

                file_path = temp_dir / file.file_path

                file_path.parent.mkdir(
                    parents=True,
                    exist_ok=True,
                )

                file_path.write_text(
                    file.content,
                    encoding="utf-8",
                )

            zip_path = (
               base_temp.parent
               / f"{project.name.replace(' ', '_')}.zip"
            )

            with zipfile.ZipFile(
                zip_path,
                "w",
                zipfile.ZIP_DEFLATED,
            ) as zipf:
                for file in temp_dir.rglob("*"):

                    if file.is_file():

                        zipf.write(
                            file,
                            file.relative_to(base_temp),
                        )

            return zip_path

        finally:

            shutil.rmtree(
                base_temp,
                ignore_errors=True,
            )


export_service = ExportService()
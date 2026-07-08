from sqlalchemy.orm import Session

from app.projects.models import ProjectFile


class FileUpdateService:
    """
    Responsible for applying
    AI generated file changes.
    """

    def apply_changes(
        self,
        db: Session,
        project_id: int,
        modified_files: list,
    ) -> list:

        updated_files = []

        for modified_file in modified_files:

            path = modified_file["path"]
            content = modified_file.get("content", "")
            language = modified_file.get("language", "")
            action = modified_file.get(
                "action",
                "update",
            )

            file = (
                db.query(ProjectFile)
                .filter(
                    ProjectFile.project_id == project_id,
                    ProjectFile.file_path == path,
                )
                .first()
            )

            # -------------------------
            # UPDATE
            # -------------------------

            if action == "update":

                if not file:
                    continue

                file.content = content

                db.add(file)

                updated_files.append(file)

            # -------------------------
            # CREATE
            # -------------------------

            elif action == "create":

                if file:
                    continue

                new_file = ProjectFile(
                    project_id=project_id,
                    file_name=path.split("/")[-1],
                    file_path=path,
                    language=language,
                    content=content,
                )

                db.add(new_file)

                updated_files.append(new_file)

            # -------------------------
            # DELETE
            # -------------------------

            elif action == "delete":

                if file:

                    db.delete(file)

        db.commit()

        for file in updated_files:

            db.refresh(file)

        return updated_files


file_update_service = FileUpdateService()
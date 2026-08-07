from pathlib import PurePosixPath

from sqlalchemy.orm import Session

from app.project_folders.models import ProjectFolder
from app.projects.models import ProjectFile


def _normalize_path(path: str) -> str:
    normalized = str(PurePosixPath(path.strip().strip("/")))
    if normalized in {"", "."} or ".." in PurePosixPath(normalized).parts:
        raise ValueError("A valid project-relative path is required.")
    return normalized


def _build_tree(folders: list[ProjectFolder]) -> list[dict]:
    root: list[dict] = []

    for folder in sorted(folders, key=lambda item: item.folder_path):
        current = root
        parts = folder.folder_path.split("/")
        for index, part in enumerate(parts):
            path = "/".join(parts[: index + 1])
            node = next((item for item in current if item["path"] == path), None)
            if node is None:
                node = {
                    "id": folder.id if index == len(parts) - 1 else None,
                    "name": part,
                    "path": path,
                    "type": "folder",
                    "children": [],
                }
                current.append(node)
            elif index == len(parts) - 1:
                node["id"] = folder.id
            current = node["children"]

    return root


class ProjectFolderService:
    @staticmethod
    def get_folders(db: Session, project_id: int) -> list[ProjectFolder]:
        return (
            db.query(ProjectFolder)
            .filter(ProjectFolder.project_id == project_id)
            .order_by(ProjectFolder.folder_path.asc())
            .all()
        )

    def get_tree(self, db: Session, project_id: int) -> list[dict]:
        return _build_tree(self.get_folders(db, project_id))

    @staticmethod
    def create_folder(
        db: Session,
        project_id: int,
        folder_name: str,
        folder_path: str,
    ) -> ProjectFolder:
        normalized_path = _normalize_path(folder_path)
        existing = (
            db.query(ProjectFolder)
            .filter(
                ProjectFolder.project_id == project_id,
                ProjectFolder.folder_path == normalized_path,
            )
            .first()
        )
        if existing:
            raise ValueError("A folder with this path already exists.")

        folder = ProjectFolder(
            project_id=project_id,
            folder_name=folder_name.strip(),
            folder_path=normalized_path,
        )
        db.add(folder)
        db.commit()
        db.refresh(folder)
        return folder

    def rename_folder(
        self,
        db: Session,
        folder_id: int,
        folder_name: str,
    ) -> ProjectFolder:
        folder = db.query(ProjectFolder).filter(ProjectFolder.id == folder_id).first()
        if not folder:
            raise ValueError("Project folder not found.")

        parent = str(PurePosixPath(folder.folder_path).parent)
        destination = folder_name.strip() if parent == "." else f"{parent}/{folder_name.strip()}"
        self.move_folder(db, folder.project_id, folder.folder_path, destination.rsplit("/", 1)[0] if "/" in destination else "")
        return db.query(ProjectFolder).filter(ProjectFolder.id == folder_id).first()

    @staticmethod
    def delete_folder(db: Session, folder_id: int) -> None:
        folder = db.query(ProjectFolder).filter(ProjectFolder.id == folder_id).first()
        if not folder:
            raise ValueError("Project folder not found.")

        prefix = f"{folder.folder_path}/"
        db.query(ProjectFile).filter(
            ProjectFile.project_id == folder.project_id,
            (ProjectFile.file_path == folder.folder_path)
            | ProjectFile.file_path.startswith(prefix),
        ).delete(synchronize_session=False)
        db.query(ProjectFolder).filter(
            ProjectFolder.project_id == folder.project_id,
            (ProjectFolder.folder_path == folder.folder_path)
            | ProjectFolder.folder_path.startswith(prefix),
        ).delete(synchronize_session=False)
        db.commit()

    def move_folder(
        self,
        db: Session,
        project_id: int,
        source_path: str,
        destination_path: str,
    ) -> str:
        source = _normalize_path(source_path)
        destination_parent = destination_path.strip().strip("/")
        if destination_parent:
            destination_parent = _normalize_path(destination_parent)
        folder_name = PurePosixPath(source).name
        target = f"{destination_parent}/{folder_name}" if destination_parent else folder_name

        if target == source:
            return source
        if destination_parent == source or destination_parent.startswith(f"{source}/"):
            raise ValueError("A folder cannot be moved into itself or one of its descendants.")

        source_prefix = f"{source}/"
        files = (
            db.query(ProjectFile)
            .filter(
                ProjectFile.project_id == project_id,
                ProjectFile.file_path.startswith(source_prefix),
            )
            .all()
        )
        folders = (
            db.query(ProjectFolder)
            .filter(
                ProjectFolder.project_id == project_id,
                (ProjectFolder.folder_path == source)
                | ProjectFolder.folder_path.startswith(source_prefix),
            )
            .all()
        )
        if not files and not folders:
            raise ValueError("Source folder does not exist.")

        all_files = (
            db.query(ProjectFile)
            .filter(ProjectFile.project_id == project_id)
            .all()
        )
        moved_file_ids = {file.id for file in files}
        target_paths = {
            file.id: f"{target}/{file.file_path[len(source_prefix):]}"
            for file in files
        }
        if any(
            file.id not in moved_file_ids and file.file_path in target_paths.values()
            for file in all_files
        ):
            raise ValueError("A file with the same name already exists in the destination folder.")

        all_folders = self.get_folders(db, project_id)
        moved_folder_ids = {folder.id for folder in folders}
        target_folder_paths = {
            folder.id: target + folder.folder_path[len(source):]
            for folder in folders
        }
        if any(
            folder.id not in moved_folder_ids and folder.folder_path in target_folder_paths.values()
            for folder in all_folders
        ):
            raise ValueError("A folder with the same name already exists in the destination folder.")

        for file in files:
            file.file_path = target_paths[file.id]
        for folder in folders:
            folder.folder_path = target_folder_paths[folder.id]
            folder.folder_name = PurePosixPath(folder.folder_path).name

        db.commit()
        return target


project_folder_service = ProjectFolderService()
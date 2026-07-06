from app.project_files import crud


class ExplorerService:
    """
    Build VS Code style explorer tree.
    """

    @staticmethod
    def build_tree(
        db,
        project_id: int,
    ):

        files = crud.get_project_files(
            db=db,
            project_id=project_id,
        )

        tree = []

        for file in files:

            parts = file.file_path.split("/")

            current = tree

            for index, part in enumerate(parts):

                is_file = index == len(parts) - 1

                existing = next(
                    (
                        item
                        for item in current
                        if item["name"] == part
                    ),
                    None,
                )

                if existing is None:

                    existing = {
                        "name": part,
                        "type": "file" if is_file else "folder",
                        "children": [] if not is_file else None,
                    }

                    if is_file:
                        existing["id"] = file.id
                        existing["path"] = file.file_path
                        existing["language"] = file.language

                    current.append(existing)

                if not is_file:
                    current = existing["children"]

        return tree


explorer_service = ExplorerService()
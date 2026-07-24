from app.project_folders import crud


class FolderExplorerService:
    """
    Build folder tree.
    """

    @staticmethod
    def build_tree(
        db,
        project_id: int,
    ):

        folders = crud.get_project_folders(
            db=db,
            project_id=project_id,
        )

        tree = []

        for folder in folders:

            parts = folder.folder_path.split("/")

            current = tree

            for index, part in enumerate(parts):

                existing = next(
                    (
                        item
                        for item in current
                        if item["name"] == part
                    ),
                    None,
                )

                if existing is None:

                    current_path = "/".join(parts[: index + 1])

                    existing = {
                        "id": None,
                        "name": part,
                        "type": "folder",
                        "children": [],
                        "path": current_path,
                    }

                    current.append(existing)

                # IMPORTANT FIX
                if index == len(parts) - 1:
                    existing["id"] = folder.id

                current = existing["children"]

        return tree


folder_explorer_service = FolderExplorerService()
class ProjectService:
    def __init__(self) -> None:
        pass

    def scaffold_project(self, app_name: str, files: list[dict[str, str]]) -> dict[str, object]:
        return {"app_name": app_name, "files": files, "status": "ready"}

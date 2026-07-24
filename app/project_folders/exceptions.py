class ProjectFolderException(Exception):
    """Base Project Folder Exception."""


class ProjectFolderNotFoundException(
    ProjectFolderException
):
    """Folder not found."""


class ProjectFolderAlreadyExistsException(
    ProjectFolderException
):
    """Folder already exists."""


class InvalidProjectFolderException(
    ProjectFolderException
):
    """Invalid folder."""
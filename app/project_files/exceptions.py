class ProjectFileException(Exception):
    """Base Project File Exception."""


class ProjectFileNotFoundException(ProjectFileException):
    """Raised when project file is not found."""


class ProjectFileValidationException(ProjectFileException):
    """Raised when validation fails."""


class ProjectFileAlreadyExistsException(ProjectFileException):
    """Raised when file already exists."""
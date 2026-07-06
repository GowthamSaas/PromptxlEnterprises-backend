class ProjectException(Exception):
    """Base Project Exception."""


class ProjectNotFoundException(ProjectException):
    """Raised when project is not found."""


class ProjectValidationException(ProjectException):
    """Raised when validation fails."""


class ProjectExportException(ProjectException):
    """Raised when export fails."""



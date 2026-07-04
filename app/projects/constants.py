from enum import Enum


class ProjectStatus(str, Enum):
    GENERATED = "generated"
    PROCESSING = "processing"
    FAILED = "failed"
    EXPORTED = "exported"
    DELETED = "deleted"


DEFAULT_PROJECT_STATUS = ProjectStatus.GENERATED

PROJECT_FOLDER_NAME = "generated_projects"

EXPORT_FOLDER_NAME = "exports"

MAX_PROJECT_NAME_LENGTH = 255

SUPPORTED_LANGUAGES = [
    "python",
    "javascript",
    "typescript",
    "vue",
    "react",
    "html",
    "css",
    "scss",
    "json",
    "yaml",
    "markdown",
]
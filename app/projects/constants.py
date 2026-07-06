from enum import Enum


class ProjectStatus(str, Enum):
    GENERATED = "generated"
    PROCESSING = "processing"
    FAILED = "failed"
    EXPORTED = "exported"
    DELETED = "deleted"


DEFAULT_PROJECT_STATUS = ProjectStatus.GENERATED

MAX_PROJECT_NAME_LENGTH = 255
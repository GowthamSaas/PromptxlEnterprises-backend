    class AIGeneratorException(Exception):
    """Base AI Generator Exception"""
    pass


class ProviderNotFoundException(AIGeneratorException):
    """Provider not connected"""
    pass


class GenerationFailedException(AIGeneratorException):
    """Generation failed"""
    pass
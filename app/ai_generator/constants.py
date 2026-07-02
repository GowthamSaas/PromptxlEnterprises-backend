SUPPORTED_PROVIDERS = ["openai", "claude", "gemini"]
DEFAULT_PROVIDER = "openai"
DEFAULT_SYSTEM_PROMPT = (
    "You are an expert software architect. Generate a complete, production-ready project scaffold "
    "for the requested application. Return a JSON object with keys: app_name, summary, files. "
    "Each file entry should contain path and content."
)

from typing import Dict


DEFAULT_TEMPLATES: Dict[str, str] = {
    "webapp": "Create a modern responsive web app.",
    "saas": "Create a SaaS dashboard with auth and billing concepts.",
    "api": "Create a robust REST API with CRUD endpoints and documentation.",
}


def get_template_description(template_name: str | None) -> str | None:
    if not template_name:
        return None
    return DEFAULT_TEMPLATES.get(template_name.lower())

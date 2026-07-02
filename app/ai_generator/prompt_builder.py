from .constants import DEFAULT_SYSTEM_PROMPT


def build_prompt(user_prompt: str, app_name: str | None = None, template: str | None = None) -> str:
    parts = [DEFAULT_SYSTEM_PROMPT, f"User request: {user_prompt}"]
    if app_name:
        parts.append(f"Preferred app name: {app_name}")
    if template:
        parts.append(f"Use template/style: {template}")
    return "\n\n".join(parts)

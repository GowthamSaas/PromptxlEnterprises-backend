from typing import Any

from .exceptions import ProviderUnavailableError, InvalidGenerationResponseError
from .file_generator import build_generated_files
from .prompt_builder import build_prompt
from .provider_selector import select_provider
from .response_parser import parse_generation_response
from .stream_parser import merge_stream_chunks
from .template_manager import get_template_description
from .validators import validate_generation_payload


class AIGenerationService:
    def __init__(self) -> None:
        self.provider = None

    def generate_app(self, prompt: str, app_name: str | None = None, template: str | None = None, provider: str | None = None, stream: bool = False) -> dict[str, Any]:
        selected_provider = select_provider(provider)
        self.provider = selected_provider

        system_prompt = build_prompt(prompt, app_name=app_name, template=template)
        template_hint = get_template_description(template)
        if template_hint:
            system_prompt = f"{system_prompt}\n\nTemplate guidance: {template_hint}"

        if stream:
            return {
                "success": True,
                "provider": selected_provider,
                "message": "Streaming generation is enabled.",
                "metadata": {"stream": True, "prompt_preview": system_prompt[:160]},
            }

        mocked_payload = {
            "app_name": app_name or "GeneratedApp",
            "summary": "Mock AI generation completed successfully.",
            "files": [
                {
                    "path": "README.md",
                    "content": f"# {app_name or 'GeneratedApp'}\n\nGenerated from prompt: {prompt}",
                }
            ],
        }

        parsed = parse_generation_response(__import__("json").dumps(mocked_payload))
        validate_generation_payload(parsed)
        generated_files = build_generated_files(parsed)

        return {
            "success": True,
            "app_name": parsed.get("app_name"),
            "provider": selected_provider,
            "files": generated_files,
            "summary": parsed.get("summary"),
            "message": "AI generation completed successfully.",
            "metadata": {"prompt": system_prompt, "stream": False},
        }

    def generate_stream(self, prompt: str, app_name: str | None = None, template: str | None = None, provider: str | None = None) -> list[str]:
        selected_provider = select_provider(provider)
        self.provider = selected_provider

        system_prompt = build_prompt(prompt, app_name=app_name, template=template)
        return [f"provider={selected_provider}", f"prompt={system_prompt[:120]}"]

    def build_stream_response(self, chunks: list[str]) -> str:
        return merge_stream_chunks(chunks)

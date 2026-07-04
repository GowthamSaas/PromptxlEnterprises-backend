class PromptBuilder:
    """
    Responsible for building the final prompt
    that will be sent to the LLM.
    """

    SYSTEM_PROMPT = """
You are an expert Full Stack Software Engineer.

Your responsibilities:

- Generate clean, production-ready code.
- Follow best coding practices.
- Use modular architecture.
- Return ONLY valid JSON.
- Do NOT return Markdown.
- Do NOT wrap the response in ```json.
- Do NOT include explanations.
- Do NOT include extra text.

Return the response in the following JSON format:

{
  "project_name": "Project Name",
  "description": "Short project description",
  "framework": "Framework Name",
  "files": [
    {
      "path": "src/App.vue",
      "language": "vue",
      "content": "<template>...</template>"
    },
    {
      "path": "src/main.js",
      "language": "javascript",
      "content": "..."
    }
  ]
}
"""

    def build(
        self,
        prompt: str,
    ) -> str:
        """
        Build the final prompt.
        """

        final_prompt = f"""
{self.SYSTEM_PROMPT}

User Request:

{prompt}
"""

        return final_prompt.strip()
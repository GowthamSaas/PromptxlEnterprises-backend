class PromptValidator:

    @staticmethod
    def validate(prompt: str):

        if not prompt:
            raise ValueError("Prompt is required.")

        if len(prompt.strip()) < 5:
            raise ValueError("Prompt is too short.")

        return True
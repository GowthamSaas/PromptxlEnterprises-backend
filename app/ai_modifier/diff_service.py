from difflib import unified_diff


class DiffService:
    """
    Responsible for generating
    differences between old and
    modified file content.
    """

    def generate_diff(
        self,
        old_content: str,
        new_content: str,
    ) -> str:

        old_lines = old_content.splitlines()

        new_lines = new_content.splitlines()

        diff = unified_diff(
            old_lines,
            new_lines,
            fromfile="old",
            tofile="new",
            lineterm="",
        )

        return "\n".join(diff)

    def has_changes(
        self,
        old_content: str,
        new_content: str,
    ) -> bool:

        return old_content != new_content


diff_service = DiffService()
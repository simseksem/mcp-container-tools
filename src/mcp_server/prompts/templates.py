"""Prompt templates for common use cases."""

from mcp.server import Server
from mcp.types import Prompt, PromptArgument, PromptMessage, TextContent


def register_prompt_templates(server: Server) -> None:
    """Register prompt templates with the server."""

    @server.list_prompts()
    async def list_prompts() -> list[Prompt]:
        return [
            Prompt(
                name="code_review",
                description="Generate a code review for the given code",
                arguments=[
                    PromptArgument(
                        name="code",
                        description="The code to review",
                        required=True,
                    ),
                    PromptArgument(
                        name="language",
                        description="Programming language of the code",
                        required=False,
                    ),
                ],
            ),
            Prompt(
                name="explain_error",
                description="Explain an error message and suggest fixes",
                arguments=[
                    PromptArgument(
                        name="error",
                        description="The error message to explain",
                        required=True,
                    ),
                    PromptArgument(
                        name="context",
                        description="Additional context about the error",
                        required=False,
                    ),
                ],
            ),
        ]

    @server.get_prompt()
    async def get_prompt(name: str, arguments: dict | None) -> list[PromptMessage]:
        args = arguments or {}

        match name:
            case "code_review":
                return _create_code_review_prompt(args)
            case "explain_error":
                return _create_explain_error_prompt(args)
            case _:
                raise ValueError(f"Unknown prompt: {name}")


def _create_code_review_prompt(args: dict) -> list[PromptMessage]:
    """Create a code review prompt."""
    code = args.get("code", "")
    language = args.get("language", "unknown")

    content = f"""Please review the following {language} code and provide feedback on:
1. Code quality and readability
2. Potential bugs or issues
3. Performance considerations
4. Best practices and improvements

Code to review:
```{language}
{code}
```"""

    return [
        PromptMessage(
            role="user",
            content=TextContent(type="text", text=content),
        )
    ]


def _create_explain_error_prompt(args: dict) -> list[PromptMessage]:
    """Create an error explanation prompt."""
    error = args.get("error", "")
    context = args.get("context", "No additional context provided.")

    content = f"""Please explain the following error and suggest how to fix it:

Error message:
{error}

Context:
{context}

Please provide:
1. What this error means
2. Common causes
3. How to fix it
4. How to prevent it in the future"""

    return [
        PromptMessage(
            role="user",
            content=TextContent(type="text", text=content),
        )
    ]
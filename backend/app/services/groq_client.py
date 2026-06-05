import asyncio
import json
import logging
from collections.abc import AsyncGenerator
from groq import AsyncGroq
from app.core.config import get_settings


logger = logging.getLogger(__name__)


class GroqClient:
    def __init__(self) -> None:
        self.settings = get_settings()
        self.client = AsyncGroq(api_key=self.settings.groq_api_key or "missing")

    async def chat(
        self,
        messages: list[dict[str, str]],
        temperature: float = 0.2,
        response_format: dict | None = None,
        max_tokens: int = 4096,
    ) -> str:
        if not self.settings.groq_api_key:
            return self._offline_response(messages)

        last_error: Exception | None = None
        for attempt in range(self.settings.groq_max_retries):
            try:
                response = await asyncio.wait_for(
                    self.client.chat.completions.create(
                        model=self.settings.groq_model,
                        messages=messages,
                        temperature=temperature,
                        max_tokens=max_tokens,
                        response_format=response_format,
                    ),
                    timeout=self.settings.groq_timeout_seconds,
                )
                return response.choices[0].message.content or ""
            except Exception as exc:
                last_error = exc
                logger.warning("groq_retry", extra={"attempt": attempt + 1, "error": str(exc)})
                await asyncio.sleep(2**attempt)
        raise RuntimeError(f"Groq request failed: {last_error}") from last_error

    async def stream_chat(
        self,
        messages: list[dict[str, str]],
        temperature: float = 0.2,
        max_tokens: int = 4096,
    ) -> AsyncGenerator[str, None]:
        if not self.settings.groq_api_key:
            yield self._offline_response(messages)
            return

        stream = await self.client.chat.completions.create(
            model=self.settings.groq_model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            stream=True,
        )
        async for chunk in stream:
            token = chunk.choices[0].delta.content
            if token:
                yield token

    def _offline_response(self, messages: list[dict[str, str]]) -> str:
        prompt = messages[-1]["content"] if messages else ""
        if "JSON" in prompt or "json" in prompt:
            return json.dumps(
                {
                    "objective": "Create a grounded research answer from the user question and available evidence.",
                    "subtopics": ["Problem framing", "Evidence review", "Comparative analysis", "Risks and limitations"],
                    "tasks": [
                        {
                            "title": "Map the question",
                            "objective": "Identify the research scope and success criteria.",
                            "search_queries": ["research question background", "recent evidence review"],
                        }
                    ],
                }
            )
        return (
            "# Research Report\n\n"
            "## Executive Summary\n\n"
            "GROQ_API_KEY is not configured, so ResearchMind generated this local fallback report. "
            "Configure Groq to enable full agentic synthesis.\n\n"
            "## Background\n\nThe system is otherwise wired for planning, search, retrieval, citations, and export.\n\n"
            "## Literature Review\n\nUpload PDFs or run web search to populate evidence.\n\n"
            "## Key Findings\n\n- Local services are operational.\n- External inference requires a Groq key.\n\n"
            "## Comparative Analysis\n\nThe application separates planner, search, document intelligence, retrieval, writing, and citation responsibilities.\n\n"
            "## Challenges\n\nInference quality depends on source quality and model availability.\n\n"
            "## Future Scope\n\nAdd authenticated multi-user workspaces and scheduled literature monitoring.\n\n"
            "## References\n\nNo verified external references were available in fallback mode.\n"
        )

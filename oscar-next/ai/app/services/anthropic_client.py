"""
Anthropic Claude client — async, de-identified tasks only.

IMPORTANT: PHI must be stripped by deidentify() before any call here.
This client must never receive patient names, HCN, dates of birth, or
any other PIPEDA/HIPAA identifier.
"""
import httpx
from anthropic import AsyncAnthropic

from app.config import get_settings


def _client() -> AsyncAnthropic:
    settings = get_settings()
    return AsyncAnthropic(
        api_key=settings.anthropic_api_key,
        http_client=httpx.AsyncClient(timeout=60.0),
    )


async def complete(
    system: str,
    prompt: str,
    max_tokens: int | None = None,
) -> str:
    """
    Single-turn completion. Text-only, de-identified.
    Raises RuntimeError if ANTHROPIC_API_KEY not configured.
    """
    settings = get_settings()
    if not settings.anthropic_available:
        raise RuntimeError("ANTHROPIC_API_KEY not configured")

    limit = min(max_tokens or settings.max_tokens_per_request, settings.max_tokens_per_request)

    client = _client()
    message = await client.messages.create(
        model=settings.anthropic_model,
        max_tokens=limit,
        system=system,
        messages=[{"role": "user", "content": prompt}],
    )
    return message.content[0].text


async def stream(
    system: str,
    prompt: str,
    max_tokens: int | None = None,
):
    """
    Streaming completion. Yields text chunks as they arrive.
    Used for real-time encounter assist over SSE.
    """
    settings = get_settings()
    if not settings.anthropic_available:
        raise RuntimeError("ANTHROPIC_API_KEY not configured")

    limit = min(max_tokens or settings.max_tokens_per_request, settings.max_tokens_per_request)

    client = _client()
    async with client.messages.stream(
        model=settings.anthropic_model,
        max_tokens=limit,
        system=system,
        messages=[{"role": "user", "content": prompt}],
    ) as s:
        async for chunk in s.text_stream:
            yield chunk

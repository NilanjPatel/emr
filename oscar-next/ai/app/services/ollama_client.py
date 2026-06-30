"""
Ollama client — on-premise, real-time PHI-safe tasks.

PHI does NOT need to be stripped before calls here because the model
runs locally on the clinic host. Data never leaves the network.
"""
import httpx

from app.config import get_settings


async def complete(
    prompt: str,
    system: str = "",
    max_tokens: int | None = None,
) -> str:
    """
    Single-turn completion against local Ollama.
    Raises RuntimeError if Ollama is unreachable.
    """
    settings = get_settings()
    url = f"{settings.ollama_host}/api/generate"
    payload: dict = {
        "model": settings.ollama_model,
        "prompt": prompt,
        "stream": False,
    }
    if system:
        payload["system"] = system
    if max_tokens:
        payload["options"] = {"num_predict": max_tokens}

    async with httpx.AsyncClient(timeout=120.0) as client:
        response = await client.post(url, json=payload)
        response.raise_for_status()
        return response.json()["response"]


async def stream(
    prompt: str,
    system: str = "",
):
    """
    Streaming completion. Yields text chunks as they arrive.
    Used for real-time encounter assist (PHI-safe, on-premise).
    """
    settings = get_settings()
    url = f"{settings.ollama_host}/api/generate"
    payload: dict = {
        "model": settings.ollama_model,
        "prompt": prompt,
        "stream": True,
    }
    if system:
        payload["system"] = system

    async with httpx.AsyncClient(timeout=120.0) as client:
        async with client.stream("POST", url, json=payload) as response:
            response.raise_for_status()
            async for line in response.aiter_lines():
                if line:
                    import json
                    chunk = json.loads(line)
                    if text := chunk.get("response"):
                        yield text
                    if chunk.get("done"):
                        break


async def is_available() -> bool:
    """Check if Ollama is running and the configured model is loaded."""
    settings = get_settings()
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            r = await client.get(f"{settings.ollama_host}/api/tags")
            models = [m["name"] for m in r.json().get("models", [])]
            return any(settings.ollama_model in m for m in models)
    except Exception:
        return False

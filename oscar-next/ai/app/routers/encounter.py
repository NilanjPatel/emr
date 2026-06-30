"""
Encounter assist — real-time SOAP note suggestions via Ollama (PHI-safe, on-premise).
Activates in Phase 3.
"""
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from app.services import ollama_client

router = APIRouter(prefix="/ai", tags=["encounter"])

_SYSTEM = (
    "You are a clinical documentation assistant for a Canadian primary care physician. "
    "Suggest additions to SOAP notes based on the conversation context provided. "
    "Be concise. Use standard medical terminology. "
    "Always frame output as a suggestion — the physician decides what to save."
)


class EncounterAssistRequest(BaseModel):
    transcript: str          # real-time dictation or notes so far
    context: str = ""        # patient context already in note (PHI: stays on-premise)
    section: str = "SOAP"    # SOAP | S | O | A | P


class EncounterAssistResponse(BaseModel):
    suggestion: str
    section: str
    model: str


@router.post("/encounter-assist", response_model=EncounterAssistResponse)
async def encounter_assist(req: EncounterAssistRequest) -> EncounterAssistResponse:
    """
    Non-streaming encounter assist. Returns a single suggestion.
    Runs via Ollama — PHI never leaves clinic network.
    """
    available = await ollama_client.is_available()
    if not available:
        raise HTTPException(
            status_code=503,
            detail="Ollama not available — ensure the ollama container is running and the model is loaded",
        )

    prompt = f"Context so far:\n{req.context}\n\nNew dictation:\n{req.transcript}\n\nSection: {req.section}"
    suggestion = await ollama_client.complete(prompt=prompt, system=_SYSTEM)

    return EncounterAssistResponse(
        suggestion=suggestion,
        section=req.section,
        model="ollama",
    )


@router.post("/encounter-assist/stream")
async def encounter_assist_stream(req: EncounterAssistRequest) -> StreamingResponse:
    """
    Server-sent events streaming version. Frontend subscribes with EventSource.
    """
    available = await ollama_client.is_available()
    if not available:
        raise HTTPException(status_code=503, detail="Ollama not available")

    prompt = f"Context so far:\n{req.context}\n\nNew dictation:\n{req.transcript}\n\nSection: {req.section}"

    async def event_stream():
        async for chunk in ollama_client.stream(prompt=prompt, system=_SYSTEM):
            yield f"data: {chunk}\n\n"
        yield "data: [DONE]\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")

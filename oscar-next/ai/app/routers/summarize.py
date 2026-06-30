"""
Patient summarization — async, de-identified, via Anthropic Claude.
Activates in Phase 3.
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.services import anthropic_client
from app.services.deidentify import deidentify

router = APIRouter(prefix="/ai", tags=["summarize"])

_SYSTEM = (
    "You are a clinical documentation assistant. "
    "Summarize the provided patient history into a concise referral letter summary. "
    "Organize by: active problems, current medications, relevant history, and reason for referral. "
    "Use standard Canadian medical terminology. "
    "Do not invent clinical details not present in the input."
)


class SummarizeRequest(BaseModel):
    patient_history: str       # clinical text — will be de-identified before sending
    reason_for_referral: str = ""


class SummarizeResponse(BaseModel):
    summary: str
    phi_replacements: int      # how many PHI tokens were removed
    model: str


@router.post("/summarize-patient", response_model=SummarizeResponse)
async def summarize_patient(req: SummarizeRequest) -> SummarizeResponse:
    """
    Generate a patient summary for referral letters.
    De-identifies all text before sending to Anthropic.
    """
    combined = f"{req.patient_history}\n\nReason for referral: {req.reason_for_referral}"
    deidentified = deidentify(combined)

    prompt = f"Patient history (de-identified):\n\n{deidentified.text}"

    try:
        summary = await anthropic_client.complete(system=_SYSTEM, prompt=prompt)
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e))

    return SummarizeResponse(
        summary=summary,
        phi_replacements=deidentified.replacements,
        model="anthropic",
    )

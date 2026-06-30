"""
Billing code suggestions — de-identified via Anthropic Claude.
Activates in Phase 6.
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.services import anthropic_client
from app.services.deidentify import deidentify

router = APIRouter(prefix="/ai", tags=["billing"])

_SYSTEM = (
    "You are a Canadian medical billing assistant specializing in OHIP (Ontario). "
    "Given a clinical encounter note, suggest the most appropriate OHIP billing codes. "
    "For each code: provide the code number, description, and a brief rationale. "
    "List codes in order of likelihood. "
    "Always note if a complex or premium code may apply."
)


class BillingCodeRequest(BaseModel):
    encounter_note: str        # SOAP note text — will be de-identified
    province: str = "ON"       # ON | BC | AB — affects code set


class BillingCodeResponse(BaseModel):
    suggestions: str
    phi_replacements: int
    province: str
    model: str


@router.post("/suggest-codes", response_model=BillingCodeResponse)
async def suggest_codes(req: BillingCodeRequest) -> BillingCodeResponse:
    """
    Suggest OHIP/provincial billing codes from an encounter note.
    De-identifies before sending to Anthropic.
    """
    deidentified = deidentify(req.encounter_note)

    system = _SYSTEM
    if req.province != "ON":
        system = system.replace("OHIP (Ontario)", f"{req.province} billing")

    prompt = f"Encounter note:\n\n{deidentified.text}"

    try:
        suggestions = await anthropic_client.complete(system=system, prompt=prompt)
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e))

    return BillingCodeResponse(
        suggestions=suggestions,
        phi_replacements=deidentified.replacements,
        province=req.province,
        model="anthropic",
    )

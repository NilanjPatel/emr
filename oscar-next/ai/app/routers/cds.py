"""
Clinical Decision Support — care gaps, overdue preventions, drug interactions.
Activates in Phase 3 (care gaps) and Phase 4 (drug interactions).
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.services import ollama_client

router = APIRouter(prefix="/ai", tags=["cds"])

_DRUG_SYSTEM = (
    "You are a clinical pharmacology assistant for a Canadian physician. "
    "Given a list of medications, identify clinically significant drug-drug interactions. "
    "For each interaction: name the drugs, severity (major/moderate/minor), mechanism, and management. "
    "If no significant interactions exist, say so clearly."
)

_CDS_SYSTEM = (
    "You are a primary care clinical decision support assistant. "
    "Identify care gaps and overdue preventive care items based on the patient's age, sex, "
    "and conditions. Reference Canadian clinical guidelines (CTFPHC, SOGC, CDA). "
    "Format as a short bulleted list."
)


class DrugInteractionRequest(BaseModel):
    medications: list[str]      # drug names only, no PHI — safe to pass to Ollama


class DrugInteractionResponse(BaseModel):
    interactions: str
    model: str


class CdsAlertsRequest(BaseModel):
    age: int
    sex: str                    # M | F | other
    conditions: list[str]       # ICD-10 codes or plain text diagnoses
    preventions: list[str]      # already completed preventions


class CdsAlertsResponse(BaseModel):
    alerts: str
    model: str


@router.post("/drug-interaction", response_model=DrugInteractionResponse)
async def drug_interaction(req: DrugInteractionRequest) -> DrugInteractionResponse:
    """
    Narrative drug interaction check augmenting DrugRef2 data.
    Input is medication names only — no PHI — safe for on-premise Ollama.
    """
    if not req.medications:
        raise HTTPException(status_code=422, detail="medications list cannot be empty")

    available = await ollama_client.is_available()
    if not available:
        raise HTTPException(status_code=503, detail="Ollama not available")

    prompt = "Medications:\n" + "\n".join(f"- {m}" for m in req.medications)
    result = await ollama_client.complete(prompt=prompt, system=_DRUG_SYSTEM)

    return DrugInteractionResponse(interactions=result, model="ollama")


@router.post("/cds-alerts", response_model=CdsAlertsResponse)
async def cds_alerts(req: CdsAlertsRequest) -> CdsAlertsResponse:
    """
    Care gap and preventive care alerts.
    Age/sex/conditions — no PHI identifiers — safe for on-premise Ollama.
    """
    available = await ollama_client.is_available()
    if not available:
        raise HTTPException(status_code=503, detail="Ollama not available")

    prompt = (
        f"Patient: {req.age}-year-old {req.sex}\n"
        f"Conditions: {', '.join(req.conditions) or 'none'}\n"
        f"Completed preventions: {', '.join(req.preventions) or 'none'}"
    )
    result = await ollama_client.complete(prompt=prompt, system=_CDS_SYSTEM)

    return CdsAlertsResponse(alerts=result, model="ollama")

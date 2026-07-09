"""Structured-output schemas + the guardrail wrapper every agent calls
through. Mirrors report S9: schema validation, retry-once-with-repair,
then hard fail -> caller treats that as an escalation signal.
"""
import json
import re
from typing import Optional, Type, TypeVar

from langchain_ollama import ChatOllama
from pydantic import BaseModel, Field, ValidationError

MODEL_NAME = "llama3.2:3b"

T = TypeVar("T", bound=BaseModel)


# ---------------------------------------------------------------- schemas --

class DocVerificationOutput(BaseModel):
    full_name: str
    employer_name: str
    stated_monthly_income: float
    anomalies: list[str] = Field(default_factory=list)
    model_confidence: float = Field(ge=0, le=1)


class CreditOutput(BaseModel):
    score_band: str
    rationale: str
    model_confidence: float = Field(ge=0, le=1)


class RiskOutput(BaseModel):
    risk_score: float = Field(ge=0, le=1)
    flags: list[str] = Field(default_factory=list)
    rationale: str
    model_confidence: float = Field(ge=0, le=1)


class DecisionOutput(BaseModel):
    outcome: str  # "approve" | "reject" | "refer"
    rationale: str
    model_confidence: float = Field(ge=0, le=1)


# ------------------------------------------------------------ PII redact --

_PII_PATTERNS = [
    re.compile(r"\b\d{4}[- ]?\d{4}[- ]?\d{4}\b"),          # card/aadhaar-shaped
    re.compile(r"\b[A-Z]{5}\d{4}[A-Z]\b"),                  # PAN-shaped
]


def redact_pii(text: str) -> str:
    """Input guardrail: strip anything that looks like a raw identifier
    before it ever reaches a prompt (report S9.1)."""
    out = text
    for pattern in _PII_PATTERNS:
        out = pattern.sub("[REDACTED]", out)
    return out


# --------------------------------------------------------- guarded call --

def call_llm_json(prompt: str, schema: Type[T], model_name: str = MODEL_NAME) -> tuple[Optional[T], str]:
    """Call Ollama in JSON mode, validate against `schema`.
    Retries once with a repair prompt on validation failure.
    Returns (parsed_or_None, status) where status is ok | retried | failed.
    """
    llm = ChatOllama(model=model_name, format="json", temperature=0.1)

    def _attempt(p: str):
        resp = llm.invoke(p)
        raw = resp.content
        data = json.loads(raw)
        return schema.model_validate(data)

    try:
        return _attempt(prompt), "ok"
    except (ValidationError, json.JSONDecodeError, Exception) as err:  # noqa: BLE001 - demo-grade
        repair_prompt = (
            f"{prompt}\n\nYour previous response was invalid: {err}\n"
            f"Return ONLY valid JSON matching the required schema, nothing else."
        )
        try:
            return _attempt(repair_prompt), "retried"
        except Exception:  # noqa: BLE001 - second failure is a hard fail, caller escalates
            return None, "failed"


# ------------------------------------------------------- policy engine --

def policy_check(dti: float, credit_score: int, requested_amount: float) -> list[str]:
    """Deterministic rules -- stands in for OPA (report S9.3). Can only
    add hard-stop flags; never overrides a model's confidence upward."""
    flags: list[str] = []
    if dti > 0.5:
        flags.append("dti_exceeds_policy_cap")
    if credit_score < 650:
        flags.append("below_min_credit_score")
    if requested_amount > 1_000_000:
        flags.append("amount_above_auto_approve_ceiling")
    return flags

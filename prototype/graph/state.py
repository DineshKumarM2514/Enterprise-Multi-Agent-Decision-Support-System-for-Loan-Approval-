"""Shared state passed between every node in the LangGraph pipeline.

Mirrors LoanState from the design report (S8.1), trimmed to what the
prototype actually needs. Every agent reads a slice of this and returns
a partial update -- no agent writes free text into a field another
agent owns.
"""
from typing import TypedDict, Optional, List, Dict, Any


class TraceEntry(TypedDict):
    agent: str
    output: Dict[str, Any]
    confidence: Optional[float]
    status: str  # ok | retried | failed
    model_name: str


class LoanState(TypedDict, total=False):
    application_id: str
    applicant: Dict[str, Any]          # raw intake fields (name, requested_amount, product_type, ...)
    documents: Dict[str, str]          # doc_type -> raw "OCR'd" text

    verified_fields: Optional[Dict[str, Any]]
    doc_confidence: Optional[float]

    credit_profile: Optional[Dict[str, Any]]
    credit_confidence: Optional[float]

    risk_profile: Optional[Dict[str, Any]]
    risk_confidence: Optional[float]

    decision: Optional[Dict[str, Any]]
    decision_confidence: Optional[float]

    hard_stop_flags: List[str]
    escalated: bool

    trace: List[TraceEntry]

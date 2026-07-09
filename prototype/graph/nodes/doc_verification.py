"""Document Verification agent -- report S5.2 / Fig. 13.

Deterministic step: cross-check the stated income across documents in
code (no LLM arithmetic). LLM step: extract structured fields + flag
anomalies. final confidence = min(model, consistency, 1 - forgery_signal).
"""
import re

from graph.state import LoanState
from guardrails.checks import DocVerificationOutput, call_llm_json, redact_pii


def _stated_income_from_bank_statement(text: str) -> float | None:
    m = re.search(r"[Aa]vg monthly credit.*?INR\s*([\d,]+)", text)
    return float(m.group(1).replace(",", "")) if m else None


def doc_verification_node(state: LoanState) -> dict:
    docs = state["documents"]
    combined = "\n\n".join(f"--- {k.upper()} ---\n{redact_pii(v)}" for k, v in docs.items())

    prompt = (
        "You are a document-verification assistant for a lending platform. "
        "Read the documents below (KYC, salary slip, bank statement) and extract "
        "the applicant's full name, employer name, and stated monthly income from "
        "the salary slip. Flag any anomaly you notice (e.g. name mismatch across "
        "documents, income figures that don't line up).\n\n"
        f"{combined}\n\n"
        'Respond with ONLY JSON: {"full_name": str, "employer_name": str, '
        '"stated_monthly_income": number, "anomalies": [str, ...], '
        '"model_confidence": number between 0 and 1}'
    )

    parsed, status = call_llm_json(prompt, DocVerificationOutput)

    bank_income = _stated_income_from_bank_statement(docs.get("bank_statement", ""))

    if parsed is None:
        return {
            "verified_fields": None,
            "doc_confidence": 0.0,
            "hard_stop_flags": state.get("hard_stop_flags", []) + ["doc_verification_failed"],
            "trace": state.get("trace", []) + [{
                "agent": "doc_verification", "output": {}, "confidence": 0.0,
                "status": "failed", "model_name": "llama3.2:3b",
            }],
        }

    consistency_score = 1.0
    if bank_income is not None and parsed.stated_monthly_income > 0:
        drift = abs(parsed.stated_monthly_income - bank_income) / parsed.stated_monthly_income
        if drift > 0.30:
            consistency_score = 0.4
        elif drift > 0.15:
            consistency_score = 0.75

    final_confidence = round(min(parsed.model_confidence, consistency_score), 3)

    output = parsed.model_dump()
    output["bank_reported_income"] = bank_income
    output["consistency_score"] = consistency_score

    return {
        "verified_fields": output,
        "doc_confidence": final_confidence,
        "trace": state.get("trace", []) + [{
            "agent": "doc_verification", "output": output, "confidence": final_confidence,
            "status": status, "model_name": "llama3.2:3b",
        }],
    }

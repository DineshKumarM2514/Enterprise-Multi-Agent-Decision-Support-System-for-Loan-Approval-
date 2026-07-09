"""Risk Assessment agent -- report S5.4 / Fig. 15.

Runs after Document Verification and Credit Assessment, not in isolation.
Deterministic step: loan-to-income ratio + employer lookup, in code.
LLM step: risk narrative + flags.
"""
from graph.state import LoanState
from guardrails.checks import RiskOutput, call_llm_json
from mock_data.employer_registry import lookup_employer


def risk_assessment_node(state: LoanState) -> dict:
    applicant = state["applicant"]
    verified = state.get("verified_fields") or {}
    monthly_income = verified.get("stated_monthly_income") or 1
    annual_income = monthly_income * 12
    requested_amount = applicant["requested_amount"]

    lti = round(requested_amount / annual_income, 3) if annual_income else 99
    # Prefer the known-exact intake value; the LLM's re-extraction from
    # OCR'd text is only a fallback if intake didn't have it.
    employer = lookup_employer(applicant.get("employer_name") or verified.get("employer_name"))

    prompt = (
        "You are a risk-assessment assistant for a lending platform. Given the "
        "loan-to-income ratio and employer reliability below, produce a risk score "
        "between 0 (very safe) and 1 (very risky), list any risk flags, and write "
        "a one-sentence rationale.\n\n"
        f"Requested amount: {requested_amount}\n"
        f"Applicant annual income (from verified docs): {annual_income}\n"
        f"Loan-to-income ratio: {lti}\n"
        f"Employer verified: {employer['verified']}\n"
        f"Employer reliability score (0-1): {employer['reliability']}\n\n"
        'Respond with ONLY JSON: {"risk_score": number 0-1, "flags": [str, ...], '
        '"rationale": str, "model_confidence": number between 0 and 1}'
    )

    parsed, status = call_llm_json(prompt, RiskOutput)

    if parsed is None:
        return {
            "risk_profile": None,
            "risk_confidence": 0.0,
            "hard_stop_flags": state.get("hard_stop_flags", []) + ["risk_assessment_failed"],
            "trace": state.get("trace", []) + [{
                "agent": "risk_assessment", "output": {}, "confidence": 0.0,
                "status": "failed", "model_name": "llama3.2:3b",
            }],
        }

    rule_penalty = 1.0
    if not employer["verified"]:
        rule_penalty = 0.6
    if lti > 5:
        rule_penalty = min(rule_penalty, 0.5)
    final_confidence = round(min(parsed.model_confidence, rule_penalty), 3)

    output = parsed.model_dump()
    output.update({"lti": lti, "employer_verified": employer["verified"],
                    "employer_reliability": employer["reliability"]})

    return {
        "risk_profile": output,
        "risk_confidence": final_confidence,
        "trace": state.get("trace", []) + [{
            "agent": "risk_assessment", "output": output, "confidence": final_confidence,
            "status": status, "model_name": "llama3.2:3b",
        }],
    }

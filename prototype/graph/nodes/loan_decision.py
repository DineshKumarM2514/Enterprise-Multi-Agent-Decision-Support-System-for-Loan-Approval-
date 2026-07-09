"""Loan Decision agent -- report S5.5 / Fig. 16.

LLM drafts a rationale + recommended outcome. The deterministic policy
check then runs independently and can only veto/downgrade -- never
upgrade -- the LLM's recommendation (report's deliberately asymmetric
check).
"""
from graph.state import LoanState
from guardrails.checks import DecisionOutput, call_llm_json, policy_check

ESCALATION_THRESHOLD = 0.75


def loan_decision_node(state: LoanState) -> dict:
    applicant = state["applicant"]
    doc_conf = state.get("doc_confidence") or 0.0
    credit = state.get("credit_profile") or {}
    risk = state.get("risk_profile") or {}
    credit_conf = state.get("credit_confidence") or 0.0
    risk_conf = state.get("risk_confidence") or 0.0

    prompt = (
        "You are the loan-decision assistant for a lending platform. Given the "
        "summaries below from Document Verification, Credit Assessment, and Risk "
        "Assessment, recommend an outcome: \"approve\", \"reject\", or \"refer\" "
        "(refer = needs a human underwriter). Write a one-sentence rationale.\n\n"
        f"Requested amount: {applicant['requested_amount']}\n"
        f"Credit score band: {credit.get('score_band')} (bureau score {credit.get('bureau_score')}, "
        f"DTI {credit.get('dti')})\n"
        f"Risk score: {risk.get('risk_score')} (flags: {risk.get('flags')})\n"
        f"Document anomalies: {(state.get('verified_fields') or {}).get('anomalies')}\n\n"
        'Respond with ONLY JSON: {"outcome": "approve"|"reject"|"refer", "rationale": str, '
        '"model_confidence": number between 0 and 1}'
    )

    parsed, status = call_llm_json(prompt, DecisionOutput)

    existing_hard_stops = list(state.get("hard_stop_flags", []))

    if parsed is None:
        hard_stops = existing_hard_stops + ["loan_decision_failed"]
        return {
            "decision": None,
            "decision_confidence": 0.0,
            "hard_stop_flags": hard_stops,
            "escalated": True,
            "trace": state.get("trace", []) + [{
                "agent": "loan_decision", "output": {}, "confidence": 0.0,
                "status": "failed", "model_name": "llama3.2:3b",
            }],
        }

    policy_flags = policy_check(
        dti=credit.get("dti", 1.0),
        credit_score=credit.get("bureau_score", 0),
        requested_amount=applicant["requested_amount"],
    )
    policy_certainty = 0.5 if policy_flags else 1.0

    final_confidence = round(min(parsed.model_confidence, doc_conf, credit_conf, risk_conf, policy_certainty), 3)

    hard_stops = existing_hard_stops + policy_flags

    # Policy can only downgrade, never upgrade, an approve recommendation.
    outcome = parsed.outcome.strip().lower()
    if outcome not in ("approve", "reject", "refer"):
        outcome = "refer"  # model drifted from the schema's allowed values -- fail safe to human
    if policy_flags and outcome == "approve":
        outcome = "refer"

    # A "refer" recommendation IS the agent asking for a human, independent
    # of the numeric confidence -- both signals must be able to trigger
    # escalation, not just the threshold.
    escalated = final_confidence < ESCALATION_THRESHOLD or bool(hard_stops) or outcome == "refer"

    output = parsed.model_dump()
    output["outcome"] = outcome
    output["policy_flags"] = policy_flags

    return {
        "decision": output,
        "decision_confidence": final_confidence,
        "hard_stop_flags": hard_stops,
        "escalated": escalated,
        "trace": state.get("trace", []) + [{
            "agent": "loan_decision", "output": output, "confidence": final_confidence,
            "status": status, "model_name": "llama3.2:3b",
        }],
    }

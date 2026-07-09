"""Credit Assessment agent -- report S5.3 / Fig. 14.

Deterministic step: pull the (mock) bureau report, compute DTI in code.
LLM step: classify into a policy score band and write the rationale --
it never computes the ratio itself.
"""
from graph.state import LoanState
from guardrails.checks import CreditOutput, call_llm_json
from mock_data.bureau import get_bureau_report


def credit_assessment_node(state: LoanState) -> dict:
    app_id = state["application_id"]
    verified = state.get("verified_fields") or {}
    monthly_income = verified.get("stated_monthly_income") or 1

    bureau = get_bureau_report(app_id)
    dti = round(bureau["monthly_emi"] / monthly_income, 3) if monthly_income else 1.0

    prompt = (
        "You are a credit-assessment assistant for a lending platform. Given this "
        "bureau profile and debt-to-income ratio, classify the applicant into a "
        "policy score band (A = excellent, B = good, C = borderline, D = weak) and "
        "write a one-sentence rationale.\n\n"
        f"Bureau score: {bureau['score']}\n"
        f"Credit history length: {bureau['history_months']} months\n"
        f"Outstanding loans: {bureau['outstanding_loans']}\n"
        f"Repayment behaviour: {bureau['repayment_behaviour']}\n"
        f"Computed debt-to-income ratio: {dti}\n\n"
        'Respond with ONLY JSON: {"score_band": str, "rationale": str, '
        '"model_confidence": number between 0 and 1}'
    )

    parsed, status = call_llm_json(prompt, CreditOutput)

    if parsed is None:
        return {
            "credit_profile": None,
            "credit_confidence": 0.0,
            "hard_stop_flags": state.get("hard_stop_flags", []) + ["credit_assessment_failed"],
            "trace": state.get("trace", []) + [{
                "agent": "credit_assessment", "output": {}, "confidence": 0.0,
                "status": "failed", "model_name": "llama3.2:3b",
            }],
        }

    rule_penalty = 1.0
    if bureau["history_months"] < 6:
        rule_penalty = 0.5   # thin file
    final_confidence = round(min(parsed.model_confidence, rule_penalty), 3)

    output = parsed.model_dump()
    output.update({"bureau_score": bureau["score"], "dti": dti,
                    "history_months": bureau["history_months"]})

    return {
        "credit_profile": output,
        "credit_confidence": final_confidence,
        "trace": state.get("trace", []) + [{
            "agent": "credit_assessment", "output": output, "confidence": final_confidence,
            "status": status, "model_name": "llama3.2:3b",
        }],
    }

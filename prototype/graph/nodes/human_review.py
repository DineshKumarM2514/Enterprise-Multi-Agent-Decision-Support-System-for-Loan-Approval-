"""Human Review agent -- report S5.6 / Fig. 17.

Not autonomous: it never decides. It assembles the case file the graph
already built (every upstream output is already in `trace`) and stops.
The actual verdict is captured afterwards through the Streamlit UI,
outside the graph, then logged with the same schema as the other
agents -- so it becomes ground truth for the eval set (report S11.4).
"""
from graph.state import LoanState


def human_review_node(state: LoanState) -> dict:
    case_bundle = {
        "verified_fields": state.get("verified_fields"),
        "credit_profile": state.get("credit_profile"),
        "risk_profile": state.get("risk_profile"),
        "decision": state.get("decision"),
        "hard_stop_flags": state.get("hard_stop_flags", []),
        "reason": "confidence below 0.75 or a hard-stop flag was raised",
    }
    return {
        "trace": state.get("trace", []) + [{
            "agent": "human_review", "output": case_bundle, "confidence": None,
            "status": "pending", "model_name": "n/a",
        }],
    }

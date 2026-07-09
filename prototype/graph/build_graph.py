"""Wires the LangGraph StateGraph -- report S4.2 / Fig. 3 and S8.1.

LangGraph itself is the orchestrator: a linear chain with one
conditional edge after the decision node. No separate "orchestrator
node" is needed -- the graph's own routing *is* that agent.
"""
from langgraph.graph import StateGraph, END

from graph.state import LoanState
from graph.nodes.doc_verification import doc_verification_node
from graph.nodes.credit_assessment import credit_assessment_node
from graph.nodes.risk_assessment import risk_assessment_node
from graph.nodes.loan_decision import loan_decision_node
from graph.nodes.human_review import human_review_node


def _needs_escalation(state: LoanState) -> str:
    if state.get("escalated"):
        return "human_review"
    return END


def build_graph():
    graph = StateGraph(LoanState)

    graph.add_node("doc_verification", doc_verification_node)
    graph.add_node("credit_assessment", credit_assessment_node)
    graph.add_node("risk_assessment", risk_assessment_node)
    graph.add_node("loan_decision", loan_decision_node)
    graph.add_node("human_review", human_review_node)

    graph.set_entry_point("doc_verification")
    graph.add_edge("doc_verification", "credit_assessment")
    graph.add_edge("credit_assessment", "risk_assessment")
    graph.add_edge("risk_assessment", "loan_decision")
    graph.add_conditional_edges("loan_decision", _needs_escalation, {
        "human_review": "human_review",
        END: END,
    })
    graph.add_edge("human_review", END)

    return graph.compile()

"""Fake credit bureau. Stands in for the external Bureau API in the design
report (S5.3 / Fig. 14). Deterministic per applicant_id so demo runs are
repeatable.
"""
from typing import Dict, Any

_BUREAU_RECORDS: Dict[str, Dict[str, Any]] = {
    "APP-1001": {
        "score": 742,
        "history_months": 48,
        "outstanding_loans": 1,
        "monthly_emi": 8500,
        "repayment_behaviour": "on_time, no missed payments in 24mo",
    },
    "APP-1002": {
        "score": 615,
        "history_months": 4,          # thin file on purpose
        "outstanding_loans": 2,
        "monthly_emi": 21000,
        "repayment_behaviour": "1 missed payment in the last 12mo",
    },
    "APP-1003": {
        "score": 801,
        "history_months": 96,
        "outstanding_loans": 0,
        "monthly_emi": 0,
        "repayment_behaviour": "no active loans, excellent history",
    },
}

_DEFAULT = {
    "score": 690,
    "history_months": 30,
    "outstanding_loans": 1,
    "monthly_emi": 12000,
    "repayment_behaviour": "on_time, occasional late fee",
}


def get_bureau_report(application_id: str) -> Dict[str, Any]:
    return dict(_BUREAU_RECORDS.get(application_id, _DEFAULT))

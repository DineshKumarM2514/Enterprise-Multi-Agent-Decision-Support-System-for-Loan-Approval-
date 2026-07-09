"""Fake employer reliability registry. Stands in for the external
employer-verification API in the design report (S5.4 / Fig. 15).
"""
from typing import Dict, Any

_EMPLOYERS: Dict[str, Dict[str, Any]] = {
    "Nimbus Cloud Systems": {"verified": True, "industry": "Technology", "reliability": 0.92},
    "Two Rivers Textiles":  {"verified": True, "industry": "Manufacturing", "reliability": 0.74},
    "Self-Employed":        {"verified": False, "industry": "N/A", "reliability": 0.40},
}

_DEFAULT = {"verified": False, "industry": "Unknown", "reliability": 0.5}


def lookup_employer(employer_name: str) -> Dict[str, Any]:
    """Case/whitespace-tolerant lookup -- an LLM re-extracting the employer
    name from OCR'd text won't always reproduce the registry's exact
    casing, and a real registry lookup would be fuzzy too."""
    needle = (employer_name or "").strip().lower()
    for name, record in _EMPLOYERS.items():
        if needle == name.lower() or needle in name.lower() or name.lower() in needle:
            return dict(record)
    return dict(_DEFAULT)

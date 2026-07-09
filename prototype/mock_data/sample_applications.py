"""Three sample applications used to drive the demo. Documents are plain
text standing in for OCR output (report S6.5: agents never touch raw
files, only normalized text/fields -- OCR itself is out of scope for the
prototype, swap in pytesseract later without touching any agent).

- APP-1001: clean file, should sail through to auto-approve.
- APP-1002: thin bureau file + unverified employer + a stated-vs-actual
  income mismatch between the salary slip and the bank statement --
  built to trip confidence below threshold and escalate to Human Review.
- APP-1003: excellent file, small ticket size, should auto-approve.
"""
from typing import Dict, Any

SAMPLE_APPLICATIONS: Dict[str, Dict[str, Any]] = {
    "APP-1001": {
        "applicant": {
            "application_id": "APP-1001",
            "full_name": "Priya Raghavan",
            "employer_name": "Nimbus Cloud Systems",
            "product_type": "personal_loan",
            "requested_amount": 500000,
            "tenure_months": 48,
        },
        "documents": {
            "kyc": "NATIONAL ID CARD\nName: Priya Raghavan\nDOB: 1990-04-12\nAddress: 14 MG Road, Bengaluru",
            "salary_slip": "SALARY SLIP - Nimbus Cloud Systems\nEmployee: Priya Raghavan\nMonth: June\nGross Monthly Salary: INR 95,000\nNet Pay: INR 82,000",
            "bank_statement": "BANK STATEMENT SUMMARY\nAccount Holder: Priya Raghavan\nAvg monthly credit (last 6mo): INR 83,500\nRecurring credit from: NIMBUS CLOUD SYSTEMS PVT LTD",
        },
    },
    "APP-1002": {
        "applicant": {
            "application_id": "APP-1002",
            "full_name": "Arjun Mehta",
            "employer_name": "Self-Employed",
            "product_type": "personal_loan",
            "requested_amount": 800000,
            "tenure_months": 36,
        },
        "documents": {
            "kyc": "NATIONAL ID CARD\nName: Arjun Mehta\nDOB: 1988-11-02\nAddress: 22 Lake View, Pune",
            "salary_slip": "SELF-DECLARED INCOME STATEMENT\nName: Arjun Mehta\nDeclared Monthly Income: INR 60,000\nSource: Freelance consulting",
            "bank_statement": "BANK STATEMENT SUMMARY\nAccount Holder: Arjun Mehta\nAvg monthly credit (last 6mo): INR 42,000\nCredits are irregular, 3 months below INR 30,000",
        },
    },
    "APP-1003": {
        "applicant": {
            "application_id": "APP-1003",
            "full_name": "Lakshmi Iyer",
            "employer_name": "Two Rivers Textiles",
            "product_type": "personal_loan",
            "requested_amount": 150000,
            "tenure_months": 24,
        },
        "documents": {
            "kyc": "NATIONAL ID CARD\nName: Lakshmi Iyer\nDOB: 1995-02-19\nAddress: 7 Harbour St, Chennai",
            "salary_slip": "SALARY SLIP - Two Rivers Textiles\nEmployee: Lakshmi Iyer\nMonth: June\nGross Monthly Salary: INR 68,000\nNet Pay: INR 60,000",
            "bank_statement": "BANK STATEMENT SUMMARY\nAccount Holder: Lakshmi Iyer\nAvg monthly credit (last 6mo): INR 59,500\nRecurring credit from: TWO RIVERS TEXTILES LTD",
        },
    },
}

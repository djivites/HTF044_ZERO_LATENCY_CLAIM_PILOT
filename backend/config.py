DOC_RELIABILITY = {
    "inspection_report": 1.0,
    "warranty_terms": 0.95,
    "contract": 0.95,
    "invoice": 0.9,
    "receipt": 0.9,
    "company_response": 0.7,
    "photo": 0.6,
    "email_thread": 0.6,
    "other": 0.4,
}
DEFAULT_RELIABILITY = 0.4
SEVERITY_WEIGHT = {"high": 1.0, "medium": 0.6, "low": 0.3}
SEVERITY_RANK = {"high": 0, "medium": 1, "low": 2}
SCORE_WEIGHTS = {"support": 0.35, "contradiction": 0.30, "completeness": 0.20, "timeline": 0.15}
CONTRADICTION_SATURATION = 3.0
SCORE_BANDS = [(80, "Strong"), (60, "Moderate"), (40, "Mixed"), (0, "Weak")]
MAX_FINDINGS_IN_LETTER = 5
MAX_LETTER_RETRIES = 2

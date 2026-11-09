"""
Document Classification Service.
Classifies documents into predefined types using keyword/layout scoring.
"""
import os
import re
from typing import Dict, Tuple

DOC_TYPES = [
    "Identity Proof",
    "Bank Statement",
    "Salary Slip",
    "Application Form",
    "Transaction Receipt",
    "Invoice",
    "Declaration",
    "Supporting Document",
    "Other",
]

# Keyword weights for each document type
KEYWORD_PROFILES: Dict[str, Dict[str, float]] = {
    "Identity Proof": {
        "aadhaar": 3.0, "aadhar": 3.0, "pan card": 3.0, "passport": 3.0, "voter": 2.5,
        "driving licence": 2.5, "driving license": 2.5, "identity": 2.0, "proof of identity": 3.0,
        "date of birth": 2.0, "nationality": 2.0, "dob": 2.0, "gender": 1.5, "photo id": 2.5,
        "unique identification": 2.0, "government of india": 2.0,
    },
    "Bank Statement": {
        "bank statement": 4.0, "account statement": 4.0, "transaction history": 3.0,
        "opening balance": 3.0, "closing balance": 3.0, "credit": 1.5, "debit": 1.5,
        "ifsc": 2.0, "account number": 2.0, "cheque": 1.5, "neft": 2.0, "rtgs": 2.0,
        "imps": 2.0, "balance": 1.0, "statement period": 3.0,
    },
    "Salary Slip": {
        "salary slip": 4.0, "pay slip": 4.0, "payslip": 4.0, "pay stub": 3.0,
        "basic salary": 3.0, "basic pay": 3.0, "gross salary": 3.0, "net salary": 3.0,
        "net pay": 3.0, "deduction": 2.0, "pf": 2.0, "provident fund": 2.0,
        "esi": 2.0, "tds": 2.0, "allowance": 2.0, "hra": 2.0, "da": 1.5,
        "employee id": 2.0, "designation": 1.5, "department": 1.5,
    },
    "Application Form": {
        "application form": 4.0, "application for": 3.0, "please fill": 2.0,
        "applicant name": 3.0, "applicant details": 2.5, "declaration": 1.5,
        "i hereby": 2.0, "undersigned": 2.0, "signature": 1.5, "date of application": 2.5,
        "loan application": 3.0, "form no": 2.0, "reference number": 1.5,
    },
    "Transaction Receipt": {
        "receipt": 3.0, "transaction id": 3.0, "transaction number": 3.0,
        "payment receipt": 4.0, "amount paid": 3.0, "paid to": 2.5, "received from": 2.5,
        "ref no": 2.0, "utr": 2.5, "acknowledgement": 2.0,
    },
    "Invoice": {
        "invoice": 4.0, "invoice no": 3.0, "bill to": 3.0, "ship to": 2.5,
        "gst": 2.5, "gstin": 3.0, "tax invoice": 4.0, "total amount": 2.0,
        "unit price": 2.0, "quantity": 1.5, "item description": 2.0, "due date": 1.5,
    },
    "Declaration": {
        "declaration": 3.0, "i hereby declare": 4.0, "solemn declaration": 3.5,
        "declared": 2.0, "sworn": 2.0, "affirm": 2.0, "certify": 2.0,
        "witness": 2.0, "notary": 2.5, "oath": 2.5,
    },
    "Supporting Document": {
        "supporting document": 3.0, "enclosure": 2.5, "attachment": 2.0,
        "certificate": 2.0, "annexure": 2.5, "appendix": 2.0,
    },
}

STRUCTURE_KEYWORDS = {
    "table": ["no.", "sr.", "date", "description", "amount", "particulars"],
    "form": ["name:", "address:", "date:", "signature:", "designation:"],
    "statement": ["balance", "credit", "debit", "date", "particulars"],
}


def score_document(text: str) -> Dict[str, float]:
    """Score each document type based on keyword presence."""
    text_lower = text.lower()
    scores = {dt: 0.0 for dt in DOC_TYPES}

    for doc_type, keywords in KEYWORD_PROFILES.items():
        for keyword, weight in keywords.items():
            if keyword in text_lower:
                # Boost score for multiple occurrences
                count = text_lower.count(keyword)
                scores[doc_type] += weight * min(count, 3)

    return scores


def classify(text: str, file_path: str = "") -> Dict:
    """Classify a document. Returns doc_type and confidence."""
    if not text or not text.strip():
        return {"doc_type": "Other", "confidence": 0.1, "scores": {}}

    scores = score_document(text)
    total = sum(scores.values())

    if total == 0:
        return {"doc_type": "Other", "confidence": 0.2, "scores": scores}

    # Get best match
    best_type = max(scores, key=scores.get)
    best_score = scores[best_type]

    if best_score == 0:
        return {"doc_type": "Other", "confidence": 0.2, "scores": scores}

    # Compute confidence as ratio of best score to total
    confidence = min(best_score / (total + 1e-9) * 3, 0.98)
    confidence = max(confidence, 0.3)

    # Normalize scores for display
    normalized = {k: round(v / (total + 1e-9), 3) for k, v in scores.items()}

    return {
        "doc_type": best_type,
        "confidence": round(confidence, 3),
        "scores": normalized
    }


def analyze_structure(text: str) -> Dict:
    """Identify document structure elements."""
    lines = text.split('\n')
    structure = {
        "has_tables": False,
        "has_forms": False,
        "has_signature_region": False,
        "line_count": len(lines),
        "sections": [],
        "missing_fields": [],
    }

    # Detect tables (lines with multiple columns of numeric/tabular data)
    table_lines = sum(1 for l in lines if len(re.findall(r'\d+[\.,]\d+|\d{4,}', l)) > 2)
    structure["has_tables"] = table_lines > 3

    # Detect form-like structure
    colon_lines = sum(1 for l in lines if ':' in l and len(l) < 80)
    structure["has_forms"] = colon_lines > 4

    # Detect signature region
    sig_patterns = r'(?i)(?:signature|sign\s*here|authorized\s*signatory|thumb\s*impression)'
    structure["has_signature_region"] = bool(re.search(sig_patterns, text))

    # Detect sections (lines that are short, all-caps or title-case headings)
    for line in lines[:50]:  # Check first 50 lines
        stripped = line.strip()
        if stripped and len(stripped) > 4 and len(stripped) < 50:
            if stripped.isupper() or (stripped.istitle() and not any(c.isdigit() for c in stripped)):
                structure["sections"].append(stripped)

    return structure

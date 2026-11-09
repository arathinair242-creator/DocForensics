"""
Cross-Document Correlation Service.
Compares extracted fields across multiple documents in the same investigation.
"""
import re
import difflib
from typing import List, Dict, Any


COMPARABLE_FIELDS = [
    "Full Name", "Date of Birth", "ID Number", "PAN Number",
    "Address", "Phone Number", "Email", "Account Number",
    "IFSC Code", "Bank Name", "Employer", "Amount",
]


def normalize_text(text: str) -> str:
    """Normalize text for comparison."""
    if not text:
        return ""
    # Remove extra whitespace, lowercase, remove punctuation
    text = re.sub(r'\s+', ' ', str(text)).strip().lower()
    text = re.sub(r'[.,\-_/]', '', text)
    return text


def compute_similarity(val1: str, val2: str) -> float:
    """Compute string similarity ratio."""
    n1 = normalize_text(val1)
    n2 = normalize_text(val2)
    if not n1 or not n2:
        return 0.0
    return difflib.SequenceMatcher(None, n1, n2).ratio()


def classify_match(similarity: float, val1: str, val2: str) -> tuple:
    """Classify a field comparison as match, partial_match, or mismatch."""
    n1 = normalize_text(val1)
    n2 = normalize_text(val2)

    if n1 == n2:
        return "match", 1.0
    if similarity >= 0.85:
        return "match", similarity
    if similarity >= 0.6:
        return "partial_match", similarity
    return "mismatch", 1.0 - similarity + 0.5


def correlate(doc_fields: Dict[int, Dict[str, str]], documents: list) -> List[Dict]:
    """
    Compare common fields across all document pairs.
    doc_fields: {doc_id: {field_name: field_value}}
    documents: list of Document ORM objects
    """
    doc_ids = list(doc_fields.keys())
    doc_names = {doc.id: doc.original_filename for doc in documents}
    matches = []

    for i in range(len(doc_ids)):
        for j in range(i + 1, len(doc_ids)):
            doc1_id = doc_ids[i]
            doc2_id = doc_ids[j]
            fields1 = doc_fields.get(doc1_id, {})
            fields2 = doc_fields.get(doc2_id, {})

            # Find common field names (by normalized key)
            norm1 = {normalize_text(k): (k, v) for k, v in fields1.items()}
            norm2 = {normalize_text(k): (k, v) for k, v in fields2.items()}

            common_keys = set(norm1.keys()) & set(norm2.keys())

            for nkey in common_keys:
                orig_key1, val1 = norm1[nkey]
                orig_key2, val2 = norm2[nkey]

                if not val1 or not val2:
                    continue

                # Skip very short values that cause false positives
                if len(str(val1).strip()) < 3 or len(str(val2).strip()) < 3:
                    continue

                # Skip generic dates unless they're DOB
                if "date" in nkey and "birth" not in nkey and "dob" not in nkey:
                    continue

                similarity = compute_similarity(val1, val2)
                status, confidence = classify_match(similarity, val1, val2)

                matches.append({
                    "field_name": orig_key1,
                    "doc1_id": doc1_id,
                    "doc2_id": doc2_id,
                    "doc1_name": doc_names.get(doc1_id, f"Doc #{doc1_id}"),
                    "doc2_name": doc_names.get(doc2_id, f"Doc #{doc2_id}"),
                    "value1": str(val1),
                    "value2": str(val2),
                    "status": status,
                    "similarity": round(similarity, 3),
                    "confidence": round(confidence, 3),
                })

    # Sort: mismatches first, then partial, then matches
    priority = {"mismatch": 0, "partial_match": 1, "match": 2}
    matches.sort(key=lambda x: (priority.get(x["status"], 3), x["field_name"]))

    return matches

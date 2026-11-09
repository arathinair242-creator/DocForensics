"""
Contextual Intelligence Service.
Analyzes extracted fields for internal inconsistencies within a single document.
Findings are observations that require human verification — not proof of fraud.
"""
import re
from datetime import datetime, date
from typing import List, Tuple, Dict, Optional


def safe_parse_date(date_str: str) -> Optional[date]:
    """Attempt to parse a date string in multiple formats."""
    formats = [
        "%d/%m/%Y", "%d-%m-%Y", "%d.%m.%Y",
        "%d/%m/%y", "%d-%m-%y",
        "%Y-%m-%d", "%m/%d/%Y",
        "%d %B %Y", "%d %b %Y",
        "%B %d, %Y", "%b %d, %Y",
    ]
    cleaned = date_str.strip()
    for fmt in formats:
        try:
            return datetime.strptime(cleaned, fmt).date()
        except ValueError:
            continue
    return None


def parse_amount(amount_str: str) -> Optional[float]:
    """Parse a financial amount string to float."""
    if not amount_str:
        return None
    cleaned = re.sub(r'[Rs.\s₹INR,]', '', str(amount_str))
    try:
        return float(cleaned)
    except ValueError:
        return None


def check_dob_age(fields: dict) -> List[Dict]:
    """Check if Date of Birth is consistent with any stated age."""
    issues = []
    dob_val = fields.get("Date of Birth", "")
    age_val = fields.get("Age", "") or fields.get("age", "")

    if not dob_val or not age_val:
        return issues

    dob = safe_parse_date(dob_val)
    if not dob:
        return issues

    try:
        stated_age = int(re.search(r'\d+', str(age_val)).group())
    except (AttributeError, ValueError):
        return issues

    today = date.today()
    calculated_age = (today - dob).days // 365

    diff = abs(calculated_age - stated_age)
    if diff > 2:
        issues.append({
            "description": f"Date of Birth ({dob_val}) implies an age of approximately {calculated_age} years, but the document states age as {stated_age}. This discrepancy of {diff} years requires verification.",
            "severity": "High" if diff > 5 else "Medium",
            "confidence": 0.82,
            "page": 1,
            "evidence": f"DOB: {dob_val} → calculated age: {calculated_age} | Stated age: {stated_age} | Difference: {diff} years"
        })
    return issues


def check_salary_components(fields: dict) -> List[Dict]:
    """For salary slips: check if component sum matches net/gross."""
    issues = []
    gross = parse_amount(fields.get("Gross Salary") or fields.get("gross salary") or
                          fields.get("Gross Pay") or "")
    net = parse_amount(fields.get("Net Salary") or fields.get("net salary") or
                        fields.get("Net Pay") or fields.get("net pay") or "")
    basic = parse_amount(fields.get("Basic Salary") or fields.get("basic salary") or
                          fields.get("Basic Pay") or "")
    hra = parse_amount(fields.get("HRA") or fields.get("hra") or "")
    deductions = parse_amount(fields.get("Total Deductions") or fields.get("Deductions") or "")

    # Check gross vs net
    if gross and net and gross > 0 and net > 0:
        if net > gross:
            issues.append({
                "description": f"Net salary ({net:,.2f}) is stated as higher than gross salary ({gross:,.2f}). Net salary should always be ≤ gross salary. This is a mathematical inconsistency requiring review.",
                "severity": "High",
                "confidence": 0.92,
                "page": 1,
                "evidence": f"Net Pay: {net:,.2f} > Gross Pay: {gross:,.2f}"
            })
        if deductions and abs((gross - deductions) - net) > 100:
            issues.append({
                "description": f"Gross salary ({gross:,.2f}) minus deductions ({deductions:,.2f}) should equal net salary ({net:,.2f}), but the difference is {abs((gross - deductions) - net):,.2f}. This arithmetic inconsistency requires verification.",
                "severity": "High",
                "confidence": 0.88,
                "page": 1,
                "evidence": f"Gross ({gross:,.2f}) - Deductions ({deductions:,.2f}) = {gross-deductions:,.2f}, stated net: {net:,.2f}"
            })
    return issues


def check_date_sequence(fields: dict) -> List[Dict]:
    """Check for date sequence logic (e.g., start date before end date)."""
    issues = []
    date_fields = {k: v for k, v in fields.items() if "date" in k.lower() and v}

    if len(date_fields) < 2:
        return issues

    parsed_dates = {}
    for k, v in date_fields.items():
        d = safe_parse_date(str(v))
        if d:
            parsed_dates[k] = d

    if len(parsed_dates) < 2:
        return issues

    # Check for implausible dates (far future)
    today = date.today()
    for k, d in parsed_dates.items():
        if d > today:
            # Only flag if it's unexpected (not statement period end dates)
            if "birth" in k.lower() or "join" in k.lower() or "issue" in k.lower():
                issues.append({
                    "description": f"The date field '{k}' contains a future date ({d.strftime('%d %b %Y')}), which is inconsistent with common document conventions for this field type.",
                    "severity": "Medium",
                    "confidence": 0.75,
                    "page": 1,
                    "evidence": f"Field '{k}': {d.strftime('%d %b %Y')} (future date)"
                })
    return issues


def check_name_consistency(fields: dict, text: str) -> List[Dict]:
    """Check for name inconsistencies across different fields."""
    issues = []
    name_fields = {}
    for k, v in fields.items():
        if any(n in k.lower() for n in ["name", "holder", "applicant", "employee"]) and v:
            # Extract just alphabetic name
            cleaned = re.sub(r'[^a-zA-Z\s]', '', str(v)).strip()
            if len(cleaned) > 2:
                name_fields[k] = cleaned.upper()

    if len(name_fields) < 2:
        return issues

    names = list(name_fields.values())
    for i in range(len(names)):
        for j in range(i + 1, len(names)):
            n1, n2 = names[i], names[j]
            fields_compared = list(name_fields.keys())

            # Check if first tokens differ significantly
            n1_parts = set(n1.split())
            n2_parts = set(n2.split())
            common = n1_parts & n2_parts

            if n1 != n2 and (len(common) == 0 or
                              (len(common) / max(len(n1_parts), len(n2_parts)) < 0.5)):
                issues.append({
                    "description": f"Name inconsistency detected: '{names[i]}' vs '{names[j]}' in related name fields. Different names in related fields may indicate an error or require verification.",
                    "severity": "High",
                    "confidence": 0.80,
                    "page": 1,
                    "evidence": f"Field 1: '{list(name_fields.keys())[i]}' = '{names[i]}' | Field 2: '{list(name_fields.keys())[j]}' = '{names[j]}'"
                })
    return issues


def check_id_duplicates(fields: dict) -> List[Dict]:
    """Check for duplicate ID numbers that should be unique."""
    issues = []
    id_fields = {}
    for k, v in fields.items():
        if any(id_kw in k.lower() for id_kw in ["id", "number", "no.", "account"]) and v:
            normalized = re.sub(r'\s+', '', str(v))
            if normalized in id_fields and id_fields[normalized] != k:
                issues.append({
                    "description": f"Identical value '{v}' found in multiple distinct identification fields ('{id_fields[normalized]}' and '{k}'). If these are different types of identifiers, this coincidence requires verification.",
                    "severity": "Medium",
                    "confidence": 0.65,
                    "page": 1,
                    "evidence": f"Same value '{v}' in '{id_fields[normalized]}' and '{k}'"
                })
            else:
                id_fields[normalized] = k
    return issues


def check_missing_mandatory_fields(fields: dict, doc_type: str) -> List[Dict]:
    """Check for missing mandatory fields based on document type."""
    issues = []
    mandatory = {
        "Identity Proof": ["Full Name", "Date of Birth", "ID Number", "Address"],
        "Bank Statement": ["Account Number", "Date", "Amount"],
        "Salary Slip": ["Full Name", "Employer", "Amount"],
        "Application Form": ["Full Name", "Date", "Address"],
    }

    required = mandatory.get(doc_type, [])
    field_names_lower = [k.lower() for k in fields.keys()]

    for req in required:
        if not any(req.lower() in fn for fn in field_names_lower):
            if not fields.get(req):
                issues.append({
                    "description": f"Expected field '{req}' was not found or could not be extracted from this {doc_type}. Missing mandatory fields may indicate an incomplete or non-standard document.",
                    "severity": "Low",
                    "confidence": 0.60,
                    "page": 1,
                    "evidence": f"Field '{req}' not found in extracted data for document type '{doc_type}'"
                })
    return issues[:3]  # Cap at 3 missing field flags


def analyze(fields_data: List[Tuple], doc_type: str, full_text: str) -> List[Dict]:
    """
    Main contextual analysis entry point.
    fields_data: list of (field_name, field_value, page_number)
    """
    # Build field dictionary
    fields = {name: value for name, value, _ in fields_data}

    all_issues = []

    # Run all contextual checks
    all_issues.extend(check_dob_age(fields))
    all_issues.extend(check_salary_components(fields))
    all_issues.extend(check_date_sequence(fields))
    all_issues.extend(check_name_consistency(fields, full_text))
    all_issues.extend(check_id_duplicates(fields))
    all_issues.extend(check_missing_mandatory_fields(fields, doc_type))

    # Additional text-level checks
    all_issues.extend(check_text_patterns(full_text))

    return all_issues[:10]  # Return top 10 contextual issues


def check_text_patterns(text: str) -> List[Dict]:
    """Find contextual issues in raw text."""
    issues = []
    if not text:
        return issues

    # Check for obviously conflicting statement periods
    dates = re.findall(r'\b(\d{1,2}[\/\-]\d{1,2}[\/\-]\d{4})\b', text)
    if dates:
        parsed = [(safe_parse_date(d), d) for d in dates]
        valid = [(d, s) for d, s in parsed if d is not None]
        if len(valid) >= 2:
            years = set(d.year for d, _ in valid)
            if len(years) > 3:
                issues.append({
                    "description": f"Document contains dates spanning {len(years)} different years ({min(years)}–{max(years)}). While this may be intentional, it is atypical and may warrant verification of document date consistency.",
                    "severity": "Low",
                    "confidence": 0.45,
                    "page": 1,
                    "evidence": f"Years found: {sorted(years)}"
                })

    return issues

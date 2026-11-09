"""
OCR Service: Extracts text and structured fields from PDFs and images.
Uses pytesseract + pdfplumber + PyMuPDF.
"""
import os
import re
import json
from typing import Dict, List, Any

try:
    import pytesseract
    from PIL import Image
    TESSERACT_AVAILABLE = True
except ImportError:
    TESSERACT_AVAILABLE = False

try:
    import fitz  # PyMuPDF
    PYMUPDF_AVAILABLE = True
except ImportError:
    PYMUPDF_AVAILABLE = False

try:
    import pdfplumber
    PDFPLUMBER_AVAILABLE = True
except ImportError:
    PDFPLUMBER_AVAILABLE = False

# Configure tesseract path from env
tesseract_cmd = os.getenv("TESSERACT_CMD", "tesseract")
if TESSERACT_AVAILABLE:
    pytesseract.pytesseract.tesseract_cmd = tesseract_cmd


# ── Field extraction patterns ──────────────────────────────────────────────────

FIELD_PATTERNS = {
    "Full Name": [
        r"(?i)(?:full\s*name|name|applicant\s*name)[:\s]+([A-Z][a-z]+(?:\s+[A-Z][a-z]+){1,3})",
        r"(?i)(?:name\s*of\s*(?:the\s*)?(?:applicant|holder|employee))[:\s]+([A-Z][a-z]+(?:\s+[A-Z][a-z]+){1,3})",
    ],
    "Date of Birth": [
        r"(?i)(?:date\s*of\s*birth|dob|d\.o\.b|born)[:\s]+(\d{1,2}[\/\-\.]\d{1,2}[\/\-\.]\d{2,4})",
        r"(?i)(?:date\s*of\s*birth|dob)[:\s]+(\d{1,2}\s+\w+\s+\d{4})",
    ],
    "ID Number": [
        r"(?i)(?:id\s*(?:no|number|num)|identification\s*(?:no|number)|aadhar|pan|passport\s*(?:no|number))[:\s#]*([A-Z0-9]{5,20})",
        r"(?i)(?:aadhaar|aadhar)[:\s]+(\d{4}\s?\d{4}\s?\d{4})",
    ],
    "Address": [
        r"(?i)(?:address|residence|residential\s*address|permanent\s*address)[:\s]+(.{10,120}?)(?:\n|$)",
    ],
    "Account Number": [
        r"(?i)(?:account\s*(?:no|number|num)|acc\.?\s*(?:no|num))[:\s#]+([0-9\-]{8,20})",
    ],
    "IFSC Code": [
        r"\b([A-Z]{4}0[A-Z0-9]{6})\b",
    ],
    "Phone Number": [
        r"(?i)(?:phone|mobile|contact|tel)[:\s]+(\+?[\d\s\-]{10,15})",
        r"\b(\d{10})\b",
    ],
    "Email": [
        r"\b([a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,})\b",
    ],
    "Date": [
        r"\b(\d{1,2}[\/\-]\d{1,2}[\/\-]\d{2,4})\b",
        r"\b(\d{1,2}\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\w*\s+\d{4})\b",
    ],
    "Amount": [
        r"(?i)(?:amount|salary|net\s*pay|gross|total|balance|credit|debit)[:\s]+(?:Rs\.?|INR|₹)?\s*([\d,]+(?:\.\d{2})?)",
        r"(?:Rs\.?|INR|₹)\s*([\d,]+(?:\.\d{2})?)",
    ],
    "Bank Name": [
        r"(?i)(?:bank\s*name|bank)[:\s]+([A-Z][A-Za-z\s]+Bank(?:\s+Ltd)?)",
    ],
    "Employer": [
        r"(?i)(?:employer|company\s*name|organization|organisation)[:\s]+([A-Z][A-Za-z\s&.,]{3,50})",
    ],
    "Designation": [
        r"(?i)(?:designation|position|title)[:\s]+([A-Za-z\s]{3,40})",
    ],
    "PAN Number": [
        r"\b([A-Z]{5}[0-9]{4}[A-Z]{1})\b",
    ],
    "Signature Region": [
        r"(?i)(signature|sign here|authorized\s*signatory)",
    ],
}


def extract_fields_from_text(text: str, page_num: int = 1) -> List[Dict]:
    """Extract structured fields from raw OCR text using regex patterns."""
    fields = []
    seen_keys = set()

    for field_name, patterns in FIELD_PATTERNS.items():
        for pattern in patterns:
            matches = re.finditer(pattern, text)
            for match in matches:
                value = match.group(1).strip() if match.lastindex else match.group(0).strip()
                value = re.sub(r'\s+', ' ', value)
                if len(value) < 2:
                    continue
                key = f"{field_name}:{value[:20]}"
                if key in seen_keys:
                    continue
                seen_keys.add(key)
                confidence = 0.85 if field_name in ["Full Name", "Date of Birth", "ID Number"] else 0.75
                fields.append({
                    "name": field_name,
                    "value": value,
                    "confidence": confidence,
                    "page": page_num,
                    "bbox": [],
                    "section": infer_section(field_name)
                })
                break  # take first match per pattern group
    return fields


def infer_section(field_name: str) -> str:
    personal = {"Full Name", "Date of Birth", "ID Number", "PAN Number", "Phone Number",
                 "Email", "Address"}
    financial = {"Amount", "Account Number", "IFSC Code", "Bank Name"}
    employment = {"Employer", "Designation"}
    if field_name in personal:
        return "Personal Information"
    if field_name in financial:
        return "Financial Information"
    if field_name in employment:
        return "Employment Information"
    return "General"


def pdf_to_text_pymupdf(file_path: str) -> tuple:
    """Extract text from PDF using PyMuPDF, returns (pages_text, page_count)."""
    pages = []
    try:
        doc = fitz.open(file_path)
        for page in doc:
            pages.append(page.get_text("text"))
        doc.close()
        return pages, len(pages)
    except Exception as e:
        return [], 0


def pdf_to_images(file_path: str, dpi: int = 200) -> List:
    """Convert PDF pages to PIL Images for OCR."""
    images = []
    try:
        doc = fitz.open(file_path)
        for page in doc:
            mat = fitz.Matrix(dpi / 72, dpi / 72)
            pix = page.get_pixmap(matrix=mat)
            img_data = pix.tobytes("png")
            from io import BytesIO
            images.append(Image.open(BytesIO(img_data)))
        doc.close()
    except Exception:
        pass
    return images


def image_ocr(image_path: str) -> str:
    """Run Tesseract OCR on an image file."""
    try:
        img = Image.open(image_path)
        # Convert to RGB if needed
        if img.mode not in ("RGB", "L"):
            img = img.convert("RGB")
        config = "--psm 6 --oem 3"
        text = pytesseract.image_to_string(img, config=config)
        return text
    except Exception as e:
        return f"[OCR Error: {str(e)}]"


def extract(file_path: str) -> Dict[str, Any]:
    """
    Main extraction entry point. Returns:
    {
      "full_text": str,
      "page_count": int,
      "fields": [...],
      "raw_pages": [str, ...]
    }
    """
    ext = os.path.splitext(file_path)[1].lower()
    all_text = ""
    raw_pages = []
    page_count = 1
    all_fields = []

    if ext == ".pdf":
        # Try PyMuPDF first
        if PYMUPDF_AVAILABLE:
            pages, page_count = pdf_to_text_pymupdf(file_path)
            if pages:
                raw_pages = pages
                all_text = "\n\n".join(pages)

        # If no text extracted (scanned PDF), use tesseract on images
        if not all_text.strip() and TESSERACT_AVAILABLE and PYMUPDF_AVAILABLE:
            images = pdf_to_images(file_path)
            raw_pages = []
            for img in images:
                txt = pytesseract.image_to_string(img, config="--psm 6")
                raw_pages.append(txt)
            all_text = "\n\n".join(raw_pages)
            page_count = len(raw_pages)

    elif ext in (".jpg", ".jpeg", ".png"):
        page_count = 1
        if TESSERACT_AVAILABLE:
            text = image_ocr(file_path)
        else:
            text = "[Tesseract not available - install pytesseract and tesseract-ocr]"
        raw_pages = [text]
        all_text = text

    # Extract fields from each page
    for i, page_text in enumerate(raw_pages):
        page_fields = extract_fields_from_text(page_text, page_num=i + 1)
        all_fields.extend(page_fields)

    # If raw_pages empty but text present
    if not raw_pages and all_text:
        all_fields = extract_fields_from_text(all_text, 1)

    # Deduplicate fields (same name+value)
    seen = set()
    deduped = []
    for f in all_fields:
        k = f"{f['name']}:{f['value']}"
        if k not in seen:
            seen.add(k)
            deduped.append(f)

    return {
        "full_text": all_text,
        "page_count": page_count,
        "fields": deduped,
        "raw_pages": raw_pages
    }

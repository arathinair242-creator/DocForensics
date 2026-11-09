"""
Demo Data Service.
Generates 5 synthetic demonstration documents clearly marked as SYNTHETIC.
Documents are created using ReportLab + Pillow and then processed through the full pipeline.
"""
import os
import io
import time
from datetime import datetime, date
from typing import Optional

try:
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import cm
    from reportlab.lib import colors
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
    from reportlab.lib.enums import TA_CENTER, TA_LEFT
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False

DEMO_DIR = "uploads"
NAVY = colors.HexColor("#0D2137") if REPORTLAB_AVAILABLE else None
LIGHT_BLUE = colors.HexColor("#D6EAF8") if REPORTLAB_AVAILABLE else None


def watermark_style():
    return ParagraphStyle("wm", fontSize=8, textColor=colors.HexColor("#E74C3C"),
                           fontName="Helvetica-Bold", alignment=TA_CENTER)


def make_header_style():
    return ParagraphStyle("hdr", fontSize=16, textColor=NAVY, fontName="Helvetica-Bold",
                           alignment=TA_CENTER, spaceBefore=6, spaceAfter=4)


def make_body_style():
    return ParagraphStyle("body", fontSize=10, textColor=colors.HexColor("#1C2833"),
                           leading=14, alignment=TA_LEFT)


def create_pdf(path: str, title: str, content_fn):
    """Create a single PDF document at the given path."""
    doc = SimpleDocTemplate(path, pagesize=A4, rightMargin=2*cm, leftMargin=2*cm,
                             topMargin=2*cm, bottomMargin=2*cm)
    story = []
    # Synthetic watermark
    story.append(Paragraph("⚠ SYNTHETIC DEMONSTRATION DOCUMENT — NOT A REAL DOCUMENT ⚠",
                            watermark_style()))
    story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#E74C3C")))
    story.append(Spacer(1, 0.3*cm))
    content_fn(story)
    story.append(Spacer(1, 0.5*cm))
    story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#E74C3C")))
    story.append(Paragraph("⚠ SYNTHETIC DEMONSTRATION DOCUMENT — NOT A REAL DOCUMENT ⚠",
                            watermark_style()))
    doc.build(story)


def doc1_genuine_id(story):
    """Document 1: Genuine identity proof."""
    styles = getSampleStyleSheet()
    hdr = make_header_style()
    body = make_body_style()

    story.append(Paragraph("GOVERNMENT IDENTITY VERIFICATION DOCUMENT", hdr))
    story.append(Paragraph("Synthetic Sample — For Demonstration Purposes Only", watermark_style()))
    story.append(Spacer(1, 0.5*cm))

    data = [
        ["Full Name:", "ARUN KUMAR SHARMA"],
        ["Date of Birth:", "12/03/1985"],
        ["Age:", "39"],
        ["Gender:", "Male"],
        ["ID Number:", "AADHAAR 5678 9012 3456"],
        ["PAN Number:", "ABCPS1234K"],
        ["Address:", "42, MG Road, Bengaluru, Karnataka 560001"],
        ["Phone Number:", "9876543210"],
        ["Email:", "arun.sharma@example.com"],
        ["Nationality:", "Indian"],
        ["Issue Date:", "15/06/2020"],
        ["Valid Until:", "14/06/2030"],
    ]
    t = Table(data, colWidths=[4.5*cm, 12*cm])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (0, -1), LIGHT_BLUE),
        ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 10),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#D5D8DC")),
        ("ROWBACKGROUNDS", (0, 0), (-1, -1), [colors.HexColor("#F5F6FA"), colors.white]),
        ("PADDING", (0, 0), (-1, -1), 6),
    ]))
    story.append(t)
    story.append(Spacer(1, 0.5*cm))
    story.append(Paragraph("Signature: ___________________________", body))
    story.append(Spacer(1, 0.3*cm))
    story.append(Paragraph("Authorized Officer: ___________________________", body))


def doc2_modified_id(story):
    """Document 2: Modified identity proof — different name, DOB inconsistency."""
    hdr = make_header_style()
    body = make_body_style()

    story.append(Paragraph("GOVERNMENT IDENTITY VERIFICATION DOCUMENT", hdr))
    story.append(Paragraph("Synthetic Sample — For Demonstration Purposes Only", watermark_style()))
    story.append(Spacer(1, 0.5*cm))

    # INTENTIONAL ANOMALIES: Name changed to "ARUN KUMAR" (missing "SHARMA"),
    # DOB changed but age left the same (inconsistency)
    data = [
        ["Full Name:", "ARUN KUMAR"],            # ← Name differs from Doc 1
        ["Date of Birth:", "22/07/1990"],         # ← DOB changed (1985 → 1990)
        ["Age:", "39"],                            # ← Age NOT updated (inconsistent with 1990 DOB)
        ["Gender:", "Male"],
        ["ID Number:", "AADHAAR 5678 9012 3456"], # ← Same Aadhaar as Doc 1
        ["PAN Number:", "ABCPS1234K"],
        ["Address:", "42, MG Road, Bengaluru, Karnataka 560001"],
        ["Phone Number:", "9876543210"],
        ["Email:", "arun.sharma@example.com"],
        ["Nationality:", "Indian"],
        ["Issue Date:", "15/06/2020"],
        ["Valid Until:", "14/06/2030"],
    ]
    t = Table(data, colWidths=[4.5*cm, 12*cm])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (0, -1), LIGHT_BLUE),
        ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 10),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#D5D8DC")),
        ("ROWBACKGROUNDS", (0, 0), (-1, -1), [colors.HexColor("#F5F6FA"), colors.white]),
        ("PADDING", (0, 0), (-1, -1), 6),
    ]))
    story.append(t)
    story.append(Spacer(1, 0.5*cm))
    story.append(Paragraph("Signature: ___________________________", body))
    story.append(Paragraph("NOTE: Name on this document differs from associated records.", body))


def doc3_bank_statement(story):
    """Document 3: Bank Statement matching the genuine ID (Doc 1)."""
    hdr = make_header_style()
    body = make_body_style()

    story.append(Paragraph("FIRST NATIONAL BANK OF INDIA", hdr))
    story.append(Paragraph("Account Statement — Synthetic Demonstration Sample", watermark_style()))
    story.append(Spacer(1, 0.4*cm))

    meta = [
        ["Account Holder:", "ARUN KUMAR SHARMA"],  # ← Matches Doc 1 correctly
        ["Account Number:", "FNBI-00987654321"],
        ["IFSC Code:", "FNBI0004567"],
        ["Statement Period:", "01/04/2024 to 31/03/2025"],
        ["Account Type:", "Savings Account"],
        ["Branch:", "MG Road, Bengaluru"],
        ["Email:", "arun.sharma@example.com"],
    ]
    mt = Table(meta, colWidths=[4.5*cm, 12*cm])
    mt.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (0, -1), LIGHT_BLUE),
        ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 10),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#D5D8DC")),
        ("PADDING", (0, 0), (-1, -1), 6),
    ]))
    story.append(mt)
    story.append(Spacer(1, 0.4*cm))

    # Transaction history
    txn_data = [
        ["Date", "Description", "Debit (₹)", "Credit (₹)", "Balance (₹)"],
        ["01/04/2024", "Opening Balance", "", "", "45,000.00"],
        ["05/04/2024", "Salary Credit - TechSolutions Ltd", "", "85,000.00", "1,30,000.00"],
        ["08/04/2024", "Electricity Bill Payment", "3,200.00", "", "1,26,800.00"],
        ["15/04/2024", "ATM Withdrawal", "10,000.00", "", "1,16,800.00"],
        ["30/04/2024", "Rent Payment", "25,000.00", "", "91,800.00"],
        ["05/05/2024", "Salary Credit - TechSolutions Ltd", "", "85,000.00", "1,76,800.00"],
        ["10/05/2024", "Insurance Premium", "12,500.00", "", "1,64,300.00"],
        ["31/05/2024", "Closing Balance", "", "", "1,64,300.00"],
    ]
    txn_table = Table(txn_data, colWidths=[2.8*cm, 6*cm, 2.5*cm, 2.5*cm, 2.8*cm])
    txn_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), NAVY),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F5F6FA")]),
        ("GRID", (0, 0), (-1, -1), 0.3, colors.HexColor("#D5D8DC")),
        ("ALIGN", (2, 0), (-1, -1), "RIGHT"),
        ("PADDING", (0, 0), (-1, -1), 5),
    ]))
    story.append(txn_table)


def doc4_application_form(story):
    """Document 4: Application form with conflicting address vs ID documents."""
    hdr = make_header_style()
    body = make_body_style()

    story.append(Paragraph("LOAN APPLICATION FORM", hdr))
    story.append(Paragraph("XYZ Financial Services — Synthetic Demonstration Sample", watermark_style()))
    story.append(Spacer(1, 0.4*cm))

    # ANOMALY: Address is different from ID documents (Pune vs Bengaluru)
    data = [
        ["Applicant Name:", "ARUN KUMAR SHARMA"],
        ["Date of Birth:", "12/03/1985"],
        ["PAN Number:", "ABCPS1234K"],
        ["Address:", "17, Shivaji Nagar, Pune, Maharashtra 411005"],  # ← CONFLICT with ID
        ["Phone Number:", "9876543210"],
        ["Email:", "arun.sharma@example.com"],
        ["Employment Type:", "Salaried"],
        ["Employer:", "TechSolutions Ltd"],
        ["Monthly Salary:", "Rs. 85,000"],
        ["Account Number:", "FNBI-00987654321"],
        ["Loan Amount Requested:", "Rs. 5,00,000"],
        ["Purpose:", "Home Renovation"],
        ["Date of Application:", "15/10/2024"],
    ]
    t = Table(data, colWidths=[4.5*cm, 12*cm])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (0, -1), LIGHT_BLUE),
        ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 10),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#D5D8DC")),
        ("ROWBACKGROUNDS", (0, 0), (-1, -1), [colors.HexColor("#F5F6FA"), colors.white]),
        ("PADDING", (0, 0), (-1, -1), 6),
    ]))
    story.append(t)
    story.append(Spacer(1, 0.5*cm))
    story.append(Paragraph("Declaration: I hereby declare that the information provided above is true and accurate.", body))
    story.append(Spacer(1, 0.4*cm))
    story.append(Paragraph("Signature: ___________________________         Date: _______________", body))


def doc5_salary_slip(story):
    """Document 5: Salary slip with arithmetic inconsistency in net pay."""
    hdr = make_header_style()
    body = make_body_style()

    story.append(Paragraph("TECHSOLUTIONS LTD", hdr))
    story.append(Paragraph("SALARY SLIP — October 2024 — Synthetic Demonstration Sample", watermark_style()))
    story.append(Spacer(1, 0.4*cm))

    emp_data = [
        ["Employee Name:", "ARUN KUMAR SHARMA"],
        ["Employee ID:", "EMP-2019-0487"],
        ["Designation:", "Senior Software Engineer"],
        ["Department:", "Technology"],
        ["Month:", "October 2024"],
        ["Bank Account:", "FNBI-00987654321"],
        ["PAN:", "ABCPS1234K"],
    ]
    et = Table(emp_data, colWidths=[4.5*cm, 12*cm])
    et.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (0, -1), LIGHT_BLUE),
        ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 10),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#D5D8DC")),
        ("PADDING", (0, 0), (-1, -1), 6),
    ]))
    story.append(et)
    story.append(Spacer(1, 0.4*cm))

    # ANOMALY: Basic + HRA + DA + Other = 85,000 (Gross)
    # Deductions: PF=10,200, ESI=638, TDS=8,500, Prof Tax=200 = 19,538
    # Correct Net = 85,000 - 19,538 = 65,462
    # But stated Net Pay = 72,500 ← ARITHMETIC ERROR (intentional anomaly)
    salary_data = [
        ["EARNINGS", "Amount (₹)", "DEDUCTIONS", "Amount (₹)"],
        ["Basic Salary", "50,000", "Provident Fund (PF)", "10,200"],
        ["House Rent Allowance (HRA)", "20,000", "ESI", "638"],
        ["Dearness Allowance (DA)", "10,000", "TDS", "8,500"],
        ["Other Allowances", "5,000", "Professional Tax", "200"],
        ["Gross Salary", "85,000", "Total Deductions", "19,538"],
        ["", "", "", ""],
        ["", "", "NET PAY", "72,500"],  # ← SHOULD BE 65,462 — intentional anomaly
    ]
    st = Table(salary_data, colWidths=[5.0*cm, 3.5*cm, 5.0*cm, 3.0*cm])
    st.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), NAVY),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTNAME", (0, -1), (-1, -1), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 10),
        ("BACKGROUND", (0, -1), (-1, -1), colors.HexColor("#D6EAF8")),
        ("ROWBACKGROUNDS", (0, 1), (-1, -2), [colors.white, colors.HexColor("#F5F6FA")]),
        ("GRID", (0, 0), (-1, -1), 0.3, colors.HexColor("#D5D8DC")),
        ("ALIGN", (1, 0), (1, -1), "RIGHT"),
        ("ALIGN", (3, 0), (3, -1), "RIGHT"),
        ("PADDING", (0, 0), (-1, -1), 6),
    ]))
    story.append(st)
    story.append(Spacer(1, 0.4*cm))
    story.append(Paragraph("Note: Net Pay after all applicable deductions as per company policy.", body))


def create_demo_documents(db, investigation_id: int, user_id: int):
    """Generate all 5 synthetic demo documents, store them, and run the full analysis pipeline."""
    from database import Document, ExtractedField, Anomaly, AuditLog
    from services.routers_analysis_helper import run_pipeline_for_doc

    if not REPORTLAB_AVAILABLE:
        _log(db, user_id, investigation_id, "Demo Error", "ReportLab not installed. Cannot generate demo documents.")
        return

    os.makedirs(DEMO_DIR, exist_ok=True)

    demos = [
        ("Demo_01_Genuine_Identity_Proof.pdf", doc1_genuine_id),
        ("Demo_02_Modified_Identity_Proof.pdf", doc2_modified_id),
        ("Demo_03_Bank_Statement.pdf", doc3_bank_statement),
        ("Demo_04_Application_Form.pdf", doc4_application_form),
        ("Demo_05_Salary_Slip.pdf", doc5_salary_slip),
    ]

    doc_ids = []
    for filename, content_fn in demos:
        filepath = os.path.join(DEMO_DIR, filename)
        try:
            create_pdf(filepath, filename, content_fn)
            file_size = os.path.getsize(filepath)

            doc_rec = Document(
                investigation_id=investigation_id,
                original_filename=filename,
                stored_filename=filename,
                file_path=filepath,
                file_size=file_size,
                processing_status="pending",
                source_reference="Synthetic Demonstration Document"
            )
            db.add(doc_rec)
            db.commit()
            db.refresh(doc_rec)
            _log(db, user_id, investigation_id, "Demo Document Created",
                 f"Synthetic document '{filename}' created", doc_rec.id)
            doc_ids.append(doc_rec.id)
        except Exception as e:
            _log(db, user_id, investigation_id, "Demo Document Error", f"Failed to create '{filename}': {str(e)}")

    # Run full pipeline on each document
    for doc_id in doc_ids:
        try:
            _run_pipeline(db, doc_id, user_id)
            time.sleep(0.5)  # Be gentle to the system
        except Exception as e:
            _log(db, user_id, investigation_id, "Demo Pipeline Error", f"Pipeline error for doc {doc_id}: {str(e)}")

    # Cross-document correlation
    try:
        if len(doc_ids) >= 2:
            from services import cross_doc_correlation
            from database import ExtractedField, Anomaly, CrossDocMatch
            docs = db.query(Document).filter(Document.id.in_(doc_ids)).all()
            doc_fields = {}
            for doc in docs:
                fields = db.query(ExtractedField).filter(ExtractedField.document_id == doc.id).all()
                doc_fields[doc.id] = {f.field_name: f.field_value for f in fields}
            matches = cross_doc_correlation.correlate(doc_fields, docs)
            counter = db.query(Anomaly).filter(Anomaly.investigation_id == investigation_id).count()
            for m in matches:
                db.add(CrossDocMatch(
                    investigation_id=investigation_id, field_name=m["field_name"],
                    doc1_id=m["doc1_id"], doc2_id=m["doc2_id"],
                    value1=m["value1"], value2=m["value2"],
                    doc1_name=m["doc1_name"], doc2_name=m["doc2_name"],
                    match_status=m["status"], confidence=m.get("confidence", 1.0)))
                if m["status"] == "mismatch":
                    counter += 1
                    db.add(Anomaly(
                        investigation_id=investigation_id, document_id=m["doc1_id"],
                        anomaly_id_str=f"ANO-{counter:04d}", category="cross_document",
                        description=f"Cross-document mismatch: '{m['field_name']}' — '{m['value1']}' in {m['doc1_name']} vs '{m['value2']}' in {m['doc2_name']}",
                        severity="High", confidence=m.get("confidence", 0.85),
                        detection_method="Cross-Document Correlation",
                        evidence_reference=f"{m['doc1_name']} ↔ {m['doc2_name']}"))
            db.commit()
            _log(db, user_id, investigation_id, "Demo Cross-Document Correlation",
                 f"Compared {len(docs)} docs, found {sum(1 for m in matches if m['status']=='mismatch')} mismatches")
    except Exception as e:
        _log(db, user_id, investigation_id, "Demo Correlation Error", str(e)[:200])

    _log(db, user_id, investigation_id, "Demo Investigation Ready",
         f"All {len(doc_ids)} synthetic documents processed. Investigation ready for review.")


def _log(db, user_id, investigation_id, activity, details="", document_id=None):
    from database import AuditLog
    db.add(AuditLog(user_id=user_id, investigation_id=investigation_id,
                    document_id=document_id, activity=activity, details=details))
    db.commit()


def _run_pipeline(db, doc_id: int, user_id: int):
    """Run the full analysis pipeline on a single document."""
    from services import ocr_service, classification_service, visual_forensics, contextual_intelligence
    from database import Document, ExtractedField, Anomaly

    doc = db.query(Document).filter(Document.id == doc_id).first()
    if not doc:
        return

    doc.processing_status = "processing"
    db.commit()

    try:
        # OCR
        result = ocr_service.extract(doc.file_path)
        doc.page_count = result.get("page_count", 1)
        for field in result.get("fields", []):
            db.add(ExtractedField(
                document_id=doc.id, field_name=field["name"], field_value=field["value"],
                confidence=field.get("confidence", 0.75), page_number=field.get("page", 1),
                bbox_json=str(field.get("bbox", [])), section=field.get("section", "")))
        db.commit()

        # Classification
        cls = classification_service.classify(result.get("full_text", ""), doc.file_path)
        doc.doc_type = cls["doc_type"]
        doc.classification_confidence = cls["confidence"]
        db.commit()

        # Visual forensics
        forensics = visual_forensics.analyze(doc.file_path, doc.id)
        if forensics.get("annotated_path"):
            doc.annotated_path = forensics["annotated_path"]
        db.commit()
        counter = db.query(Anomaly).filter(Anomaly.investigation_id == doc.investigation_id).count()
        for f in forensics.get("findings", []):
            counter += 1
            db.add(Anomaly(
                investigation_id=doc.investigation_id, document_id=doc.id,
                anomaly_id_str=f"ANO-{counter:04d}", category="visual",
                description=f["description"], severity=f.get("severity", "Medium"),
                confidence=f.get("confidence", 0.5), page_number=f.get("page", 1),
                bbox_json=str(f.get("bbox", [])), detection_method=f.get("method", "Visual"),
                evidence_reference=f.get("evidence", "")))
        db.commit()

        # Contextual
        fields_data = [(ef.field_name, ef.field_value, ef.page_number)
                       for ef in db.query(ExtractedField).filter(ExtractedField.document_id == doc.id).all()]
        ctx = contextual_intelligence.analyze(fields_data, doc.doc_type, result.get("full_text", ""))
        counter = db.query(Anomaly).filter(Anomaly.investigation_id == doc.investigation_id).count()
        for issue in ctx:
            counter += 1
            db.add(Anomaly(
                investigation_id=doc.investigation_id, document_id=doc.id,
                anomaly_id_str=f"ANO-{counter:04d}", category="contextual",
                description=issue["description"], severity=issue.get("severity", "Medium"),
                confidence=issue.get("confidence", 0.7), page_number=issue.get("page", 1),
                detection_method="Contextual Intelligence",
                evidence_reference=issue.get("evidence", "")))
        db.commit()

        doc.processing_status = "completed"
        db.commit()
        _log(db, None, doc.investigation_id, "Demo Document Processed",
             f"'{doc.original_filename}' → {doc.doc_type} ({doc.classification_confidence:.0%})", doc.id)

    except Exception as e:
        doc.processing_status = "error"
        db.commit()
        _log(db, None, doc.investigation_id, "Processing Error",
             f"Error on '{doc.original_filename}': {str(e)[:150]}", doc.id)

"""
PDF Investigation Dossier Generator.
Uses ReportLab to create professional investigation reports.
"""
import os
from datetime import datetime
from typing import List, Dict, Any

try:
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import cm, mm
    from reportlab.lib import colors
    from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
                                     PageBreak, HRFlowable, Image as RLImage, KeepTogether)
    from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT, TA_JUSTIFY
    from reportlab.pdfgen import canvas
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False

# ── Color palette ─────────────────────────────────────────────────────────────
NAVY = colors.HexColor("#0D2137")
DARK_BLUE = colors.HexColor("#1B4F72")
MID_BLUE = colors.HexColor("#2E86AB")
LIGHT_BLUE = colors.HexColor("#D6EAF8")
LIGHT_GREY = colors.HexColor("#F5F6FA")
BORDER_GREY = colors.HexColor("#D5D8DC")
TEXT_DARK = colors.HexColor("#1C2833")
TEXT_MED = colors.HexColor("#4A4A4A")
RED = colors.HexColor("#C0392B")
ORANGE = colors.HexColor("#E67E22")
YELLOW = colors.HexColor("#F39C12")
GREEN = colors.HexColor("#27AE60")
WHITE = colors.white

SEVERITY_COLORS = {
    "Critical": RED,
    "High": ORANGE,
    "Medium": YELLOW,
    "Low": colors.HexColor("#3498DB"),
}


class NumberedCanvas(canvas.Canvas):
    def __init__(self, *args, **kwargs):
        canvas.Canvas.__init__(self, *args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_number(num_pages)
            canvas.Canvas.showPage(self)
        canvas.Canvas.save(self)

    def draw_page_number(self, page_count):
        self.setFont("Helvetica", 8)
        self.setFillColor(TEXT_MED)
        self.drawRightString(A4[0] - 2*cm, 1.5*cm,
                              f"Page {self._pageNumber} of {page_count}")
        self.drawString(2*cm, 1.5*cm, "CONFIDENTIAL — FOR AUTHORIZED INVESTIGATION USE ONLY")
        # Header line
        self.setStrokeColor(NAVY)
        self.setLineWidth(0.5)
        self.line(2*cm, A4[1] - 2*cm, A4[0] - 2*cm, A4[1] - 2*cm)
        self.drawString(2*cm, A4[1] - 1.7*cm, "DocForensics — AI Document Investigation Platform")
        self.drawRightString(A4[0] - 2*cm, A4[1] - 1.7*cm,
                              f"Generated: {datetime.now().strftime('%d %b %Y, %H:%M')}")


def make_styles():
    styles = getSampleStyleSheet()
    custom = {}

    custom["cover_title"] = ParagraphStyle("cover_title", fontSize=28, textColor=NAVY,
                                            leading=34, alignment=TA_CENTER, fontName="Helvetica-Bold")
    custom["cover_sub"] = ParagraphStyle("cover_sub", fontSize=14, textColor=DARK_BLUE,
                                          leading=18, alignment=TA_CENTER)
    custom["cover_meta"] = ParagraphStyle("cover_meta", fontSize=11, textColor=TEXT_MED,
                                           leading=16, alignment=TA_CENTER)
    custom["section_header"] = ParagraphStyle("section_header", fontSize=14, textColor=WHITE,
                                               leading=18, fontName="Helvetica-Bold",
                                               backColor=NAVY, leftIndent=6, rightIndent=6,
                                               spaceBefore=14, spaceAfter=6)
    custom["subsection"] = ParagraphStyle("subsection", fontSize=12, textColor=DARK_BLUE,
                                           leading=16, fontName="Helvetica-Bold",
                                           spaceBefore=8, spaceAfter=4)
    custom["body"] = ParagraphStyle("body", fontSize=10, textColor=TEXT_DARK,
                                     leading=14, alignment=TA_JUSTIFY)
    custom["body_small"] = ParagraphStyle("body_small", fontSize=9, textColor=TEXT_MED, leading=13)
    custom["warning_box"] = ParagraphStyle("warning_box", fontSize=9, textColor=colors.HexColor("#7D6608"),
                                            leading=13, leftIndent=8, rightIndent=8,
                                            backColor=colors.HexColor("#FEFBD8"))
    custom["label"] = ParagraphStyle("label", fontSize=9, textColor=TEXT_MED, leading=12,
                                      fontName="Helvetica-Oblique")
    return custom


def section_header(text, styles):
    return Paragraph(f"  {text}", styles["section_header"])


def severity_badge(severity):
    color_map = {"Critical": "#C0392B", "High": "#E67E22", "Medium": "#F39C12", "Low": "#3498DB"}
    c = color_map.get(severity, "#888")
    return f'<font color="{c}"><b>[{severity}]</b></font>'


def generate(output_path: str, investigation, documents: list,
             fields_by_doc: dict, anomalies: list, cross_matches: list, investigator_name: str):
    """Generate a complete investigation dossier PDF."""
    if not REPORTLAB_AVAILABLE:
        raise RuntimeError("ReportLab is required to generate PDF dossiers. Install backend requirements.")

    report_doc = SimpleDocTemplate(output_path, pagesize=A4,
                                    rightMargin=2*cm, leftMargin=2*cm,
                                    topMargin=2.5*cm, bottomMargin=2*cm)
    styles = make_styles()
    story = []

    # ── COVER PAGE ─────────────────────────────────────────────────────────────
    story.append(Spacer(1, 3*cm))
    story.append(HRFlowable(width="100%", thickness=3, color=NAVY))
    story.append(Spacer(1, 0.5*cm))
    story.append(Paragraph("INVESTIGATION DOSSIER", styles["cover_title"]))
    story.append(Spacer(1, 0.3*cm))
    story.append(Paragraph("AI-Powered Document Forensics &amp; Contextual Intelligence", styles["cover_sub"]))
    story.append(Spacer(1, 0.5*cm))
    story.append(HRFlowable(width="100%", thickness=1, color=DARK_BLUE))
    story.append(Spacer(1, 1.5*cm))

    meta_data = [
        ["Investigation Name:", investigation.name],
        ["Investigation ID:", f"INV-{investigation.id:04d}"],
        ["Status:", investigation.status.upper()],
        ["Investigator:", investigator_name],
        ["Documents Analyzed:", str(len(documents))],
        ["Anomalies Detected:", str(len(anomalies))],
        ["Report Generated:", datetime.now().strftime("%d %B %Y, %H:%M IST")],
    ]
    meta_table = Table(meta_data, colWidths=[5*cm, 12*cm])
    meta_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (0, -1), LIGHT_BLUE),
        ("TEXTCOLOR", (0, 0), (0, -1), NAVY),
        ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 10),
        ("ROWBACKGROUNDS", (0, 0), (-1, -1), [LIGHT_GREY, WHITE]),
        ("GRID", (0, 0), (-1, -1), 0.5, BORDER_GREY),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ]))
    story.append(meta_table)
    story.append(Spacer(1, 1.5*cm))

    disclaimer = ("IMPORTANT NOTICE: This investigation dossier contains observations generated by an "
                   "AI-assisted document analysis system. Findings represent potential anomalies and "
                   "inconsistencies identified through automated analysis. They do NOT constitute "
                   "confirmation of forgery, fraud, or manipulation. All findings require human "
                   "verification and professional judgment before any consequential decision is made.")
    story.append(Table([[Paragraph(disclaimer, styles["warning_box"])]],
                        colWidths=[17*cm],
                        style=[("BOX", (0, 0), (-1, -1), 1, ORANGE),
                                ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#FEFBD8")),
                                ("PADDING", (0, 0), (-1, -1), 10)]))
    story.append(PageBreak())

    # ── SECTION 1: DOCUMENT OVERVIEW ───────────────────────────────────────────
    story.append(section_header("1. Document Overview", styles))
    story.append(Spacer(1, 0.3*cm))
    story.append(Paragraph(f"This investigation includes {len(documents)} submitted document(s).", styles["body"]))
    story.append(Spacer(1, 0.3*cm))

    if documents:
        doc_table_data = [["#", "Document", "Type", "Classification", "Status", "Size"]]
        for idx, d in enumerate(documents, 1):
            conf_str = f"{d.classification_confidence*100:.0f}%" if d.classification_confidence else "N/A"
            size_str = f"{d.file_size/1024:.1f} KB" if d.file_size else "N/A"
            doc_table_data.append([
                str(idx), Paragraph(d.original_filename, styles["body_small"]),
                d.doc_type, conf_str, d.processing_status.title(), size_str
            ])
        doc_table = Table(doc_table_data, colWidths=[0.8*cm, 5*cm, 3.5*cm, 2*cm, 2*cm, 2*cm])
        doc_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), NAVY),
            ("TEXTCOLOR", (0, 0), (-1, 0), WHITE),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 9),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [WHITE, LIGHT_GREY]),
            ("GRID", (0, 0), (-1, -1), 0.3, BORDER_GREY),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("LEFTPADDING", (0, 0), (-1, -1), 6),
            ("TOPPADDING", (0, 0), (-1, -1), 5),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ]))
        story.append(doc_table)
    story.append(Spacer(1, 0.5*cm))

    # ── SECTION 2: EXTRACTED INFORMATION ───────────────────────────────────────
    story.append(section_header("2. Extracted Information", styles))
    story.append(Spacer(1, 0.3*cm))
    for d in documents:
        fields = fields_by_doc.get(d.id, [])
        if not fields:
            continue
        story.append(Paragraph(f"Document: {d.original_filename} ({d.doc_type})", styles["subsection"]))
        field_data = [["Field Name", "Extracted Value", "Confidence", "Page", "Section"]]
        for f in fields[:20]:
            conf_str = f"{f.confidence*100:.0f}%"
            field_data.append([
                f.field_name, Paragraph(str(f.field_value)[:80], styles["body_small"]),
                conf_str, str(f.page_number), f.section or "General"
            ])
        field_table = Table(field_data, colWidths=[3.5*cm, 6.5*cm, 1.8*cm, 1.2*cm, 3.3*cm])
        field_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), DARK_BLUE),
            ("TEXTCOLOR", (0, 0), (-1, 0), WHITE),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 8),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [WHITE, LIGHT_GREY]),
            ("GRID", (0, 0), (-1, -1), 0.3, BORDER_GREY),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("LEFTPADDING", (0, 0), (-1, -1), 5),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ]))
        story.append(field_table)
        story.append(Spacer(1, 0.3*cm))

    story.append(PageBreak())

    # ── SECTION 3: CONTEXTUAL ANALYSIS ─────────────────────────────────────────
    story.append(section_header("3. Contextual Analysis", styles))
    story.append(Spacer(1, 0.3*cm))
    ctx_anomalies = [a for a in anomalies if a.category == "contextual"]
    if ctx_anomalies:
        for a in ctx_anomalies:
            doc = next((d for d in documents if d.id == a.document_id), None)
            doc_name = doc.original_filename if doc else "Unknown"
            sev_color = SEVERITY_COLORS.get(a.severity, MID_BLUE)
            story.append(KeepTogether([
                Paragraph(f"{a.anomaly_id_str} — {a.description[:100]}...", styles["subsection"]),
                Table([[
                    Paragraph(f"<b>Document:</b> {doc_name}", styles["body_small"]),
                    Paragraph(f"<b>Severity:</b> {a.severity}", styles["body_small"]),
                    Paragraph(f"<b>Confidence:</b> {a.confidence*100:.0f}%", styles["body_small"]),
                ]],
                    colWidths=[6*cm, 3*cm, 3*cm],
                    style=[("GRID", (0, 0), (-1, -1), 0.3, BORDER_GREY),
                            ("BACKGROUND", (0, 0), (-1, -1), LIGHT_GREY),
                            ("PADDING", (0, 0), (-1, -1), 4)]),
                Paragraph(a.description, styles["body"]),
                Paragraph(f"Evidence: {a.evidence_reference}", styles["label"]),
                Spacer(1, 0.3*cm),
            ]))
    else:
        story.append(Paragraph("No contextual inconsistencies were detected in this investigation.", styles["body"]))

    # Cross-document findings in contextual section
    if cross_matches:
        story.append(Paragraph("Cross-Document Field Comparison", styles["subsection"]))
        compare_data = [["Field", "Document 1", "Value 1", "Document 2", "Value 2", "Result"]]
        for m in cross_matches[:20]:
            status_str = "✓ Match" if m.match_status == "match" else ("≈ Partial" if m.match_status == "partial_match" else "✗ Mismatch")
            compare_data.append([
                m.field_name, Paragraph(m.doc1_name[:20], styles["body_small"]),
                Paragraph(str(m.value1)[:30], styles["body_small"]),
                Paragraph(m.doc2_name[:20], styles["body_small"]),
                Paragraph(str(m.value2)[:30], styles["body_small"]),
                status_str
            ])
        compare_table = Table(compare_data, colWidths=[2.5*cm, 3*cm, 3*cm, 3*cm, 3*cm, 1.8*cm])
        compare_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), DARK_BLUE),
            ("TEXTCOLOR", (0, 0), (-1, 0), WHITE),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 8),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [WHITE, LIGHT_GREY]),
            ("GRID", (0, 0), (-1, -1), 0.3, BORDER_GREY),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("PADDING", (0, 0), (-1, -1), 4),
        ]))
        story.append(compare_table)

    story.append(PageBreak())

    # ── SECTION 4: VISUAL FORENSIC FINDINGS ────────────────────────────────────
    story.append(section_header("4. Visual Forensic Findings", styles))
    story.append(Spacer(1, 0.3*cm))
    visual_anomalies = [a for a in anomalies if a.category == "visual"]
    if visual_anomalies:
        for a in visual_anomalies:
            doc = next((d for d in documents if d.id == a.document_id), None)
            doc_name = doc.original_filename if doc else "Unknown"
            story.append(KeepTogether([
                Paragraph(f"{a.anomaly_id_str}: {a.detection_method}", styles["subsection"]),
                Paragraph(f"<b>Document:</b> {doc_name} | <b>Severity:</b> {a.severity} | <b>Confidence:</b> {a.confidence*100:.0f}% | <b>Page:</b> {a.page_number}", styles["body_small"]),
                Spacer(1, 0.2*cm),
                Paragraph(a.description, styles["body"]),
                Paragraph(f"Supporting Evidence: {a.evidence_reference}", styles["label"]),
                Spacer(1, 0.3*cm),
            ]))
    else:
        story.append(Paragraph("No visual anomalies were detected in this investigation.", styles["body"]))

    story.append(PageBreak())

    # ── SECTION 5: EVIDENCE & TRACEABILITY ─────────────────────────────────────
    story.append(section_header("5. Evidence and Traceability", styles))
    story.append(Spacer(1, 0.3*cm))
    story.append(Paragraph("All findings in this dossier are traceable to their original document sources as recorded in the system database.", styles["body"]))
    story.append(Spacer(1, 0.3*cm))

    evidence_data = [["Anomaly ID", "Document", "Category", "Severity", "Detection Method", "Investigation Status"]]
    for a in anomalies:
        doc = next((d for d in documents if d.id == a.document_id), None)
        evidence_data.append([
            a.anomaly_id_str,
            Paragraph((doc.original_filename if doc else "?")[:25], styles["body_small"]),
            a.category.replace("_", " ").title(),
            a.severity,
            Paragraph(a.detection_method[:30], styles["body_small"]),
            a.status.replace("_", " ").title()
        ])

    if len(evidence_data) > 1:
        ev_table = Table(evidence_data, colWidths=[1.8*cm, 3.5*cm, 2.8*cm, 1.8*cm, 3.5*cm, 3*cm])
        ev_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), NAVY),
            ("TEXTCOLOR", (0, 0), (-1, 0), WHITE),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 8),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [WHITE, LIGHT_GREY]),
            ("GRID", (0, 0), (-1, -1), 0.3, BORDER_GREY),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("PADDING", (0, 0), (-1, -1), 4),
        ]))
        story.append(ev_table)

    story.append(PageBreak())

    # ── SECTION 6: INVESTIGATION SUMMARY ───────────────────────────────────────
    story.append(section_header("6. Investigation Summary", styles))
    story.append(Spacer(1, 0.3*cm))

    # Stats
    sev_counts = {"Critical": 0, "High": 0, "Medium": 0, "Low": 0}
    cat_counts = {"visual": 0, "contextual": 0, "cross_document": 0, "structural": 0}
    for a in anomalies:
        sev_counts[a.severity] = sev_counts.get(a.severity, 0) + 1
        cat_counts[a.category] = cat_counts.get(a.category, 0) + 1

    summary_data = [
        ["Total Documents", str(len(documents))],
        ["Total Extracted Fields", str(sum(len(f) for f in fields_by_doc.values()))],
        ["Total Anomalies Detected", str(len(anomalies))],
        ["Critical Anomalies", str(sev_counts["Critical"])],
        ["High Severity", str(sev_counts["High"])],
        ["Medium Severity", str(sev_counts["Medium"])],
        ["Low Severity", str(sev_counts["Low"])],
        ["Visual Anomalies", str(cat_counts["visual"])],
        ["Contextual Issues", str(cat_counts["contextual"])],
        ["Cross-Document Mismatches", str(cat_counts["cross_document"])],
    ]
    sum_table = Table(summary_data, colWidths=[8*cm, 8*cm])
    sum_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (0, -1), LIGHT_BLUE),
        ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
        ("TEXTCOLOR", (0, 0), (0, -1), NAVY),
        ("FONTSIZE", (0, 0), (-1, -1), 10),
        ("ROWBACKGROUNDS", (0, 0), (-1, -1), [LIGHT_GREY, WHITE]),
        ("GRID", (0, 0), (-1, -1), 0.5, BORDER_GREY),
        ("PADDING", (0, 0), (-1, -1), 7),
    ]))
    story.append(sum_table)
    story.append(Spacer(1, 0.5*cm))

    # Limitations
    story.append(Paragraph("Investigation Limitations and Assumptions", styles["subsection"]))
    limitations = [
        "This analysis was conducted using automated AI methods including OCR, computer vision, and rule-based contextual analysis.",
        "OCR accuracy depends on document scan quality. Poor quality scans may result in extraction errors.",
        "Visual forensic methods (ELA, noise analysis, edge detection) indicate areas of interest but cannot conclusively determine document authenticity.",
        "Cross-document comparison uses fuzzy string matching which may produce false positives for names with alternate romanizations.",
        "This system does not access external databases or ground truth sources for verification.",
        "All findings must be reviewed and verified by qualified human investigators before any consequential decision is made.",
        "The system distinguishes between observed characteristics, detected inconsistencies, and potential manipulation as separate observation categories.",
    ]
    for lim in limitations:
        story.append(Paragraph(f"• {lim}", styles["body_small"]))
        story.append(Spacer(1, 0.1*cm))

    story.append(Spacer(1, 1*cm))
    story.append(HRFlowable(width="100%", thickness=1, color=NAVY))
    story.append(Spacer(1, 0.3*cm))
    story.append(Paragraph(f"End of Investigation Dossier — INV-{investigation.id:04d} — {investigation.name}",
                            styles["body_small"]))

    report_doc.build(story, canvasmaker=NumberedCanvas)

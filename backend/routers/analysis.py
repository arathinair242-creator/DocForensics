from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from database import (get_db, Document, Investigation, Anomaly, AuditLog,
                       ExtractedField, CrossDocMatch, User, SessionLocal)
from routers.auth_router import get_current_user

router = APIRouter(prefix="/analysis", tags=["analysis"])


def log_audit(db, user_id, investigation_id, activity, details="", document_id=None):
    db.add(AuditLog(user_id=user_id, investigation_id=investigation_id,
                    document_id=document_id, activity=activity, details=details))
    db.commit()


def run_full_pipeline(doc_id: int, user_id: int, db_session):
    from services import ocr_service, classification_service, visual_forensics, contextual_intelligence
    doc = db_session.query(Document).filter(Document.id == doc_id).first()
    if not doc:
        return
    try:
        doc.processing_status = "processing"
        db_session.commit()

        # --- OCR & Extraction ---
        result = ocr_service.extract(doc.file_path)
        doc.page_count = result.get("page_count", 1)
        for field in result.get("fields", []):
            db_session.add(ExtractedField(
                document_id=doc.id, field_name=field["name"], field_value=field["value"],
                confidence=field.get("confidence", 0.5), page_number=field.get("page", 1),
                bbox_json=str(field.get("bbox", [])), section=field.get("section", "")))
        db_session.commit()
        log_audit(db_session, user_id, doc.investigation_id, "OCR Completed",
                  f"Extracted {len(result.get('fields', []))} fields from '{doc.original_filename}'", doc.id)

        # --- Classification ---
        cls = classification_service.classify(result.get("full_text", ""), doc.file_path)
        doc.doc_type = cls["doc_type"]
        doc.classification_confidence = cls["confidence"]
        db_session.commit()
        log_audit(db_session, user_id, doc.investigation_id, "Document Classified",
                  f"'{doc.original_filename}' → {cls['doc_type']} ({cls['confidence']:.0%})", doc.id)

        # --- Visual Forensics ---
        forensics = visual_forensics.analyze(doc.file_path, doc.id)
        if forensics.get("annotated_path"):
            doc.annotated_path = forensics["annotated_path"]
        db_session.commit()
        counter = db_session.query(Anomaly).filter(Anomaly.investigation_id == doc.investigation_id).count()
        for f in forensics.get("findings", []):
            counter += 1
            db_session.add(Anomaly(
                investigation_id=doc.investigation_id, document_id=doc.id,
                anomaly_id_str=f"ANO-{counter:04d}", category="visual",
                description=f["description"], severity=f.get("severity", "Medium"),
                confidence=f.get("confidence", 0.5), page_number=f.get("page", 1),
                bbox_json=str(f.get("bbox", [])), detection_method=f.get("method", "Visual Analysis"),
                evidence_reference=f.get("evidence", "")))
        db_session.commit()
        log_audit(db_session, user_id, doc.investigation_id, "Visual Forensics Completed",
                  f"Found {len(forensics.get('findings', []))} visual anomalies", doc.id)

        # --- Contextual Intelligence ---
        fields_data = [(ef.field_name, ef.field_value, ef.page_number)
                       for ef in db_session.query(ExtractedField).filter(
                           ExtractedField.document_id == doc.id).all()]
        ctx_issues = contextual_intelligence.analyze(fields_data, doc.doc_type, result.get("full_text", ""))
        counter = db_session.query(Anomaly).filter(Anomaly.investigation_id == doc.investigation_id).count()
        for issue in ctx_issues:
            counter += 1
            db_session.add(Anomaly(
                investigation_id=doc.investigation_id, document_id=doc.id,
                anomaly_id_str=f"ANO-{counter:04d}", category="contextual",
                description=issue["description"], severity=issue.get("severity", "Medium"),
                confidence=issue.get("confidence", 0.7), page_number=issue.get("page", 1),
                detection_method="Contextual Intelligence", evidence_reference=issue.get("evidence", "")))
        db_session.commit()

        doc.processing_status = "completed"
        db_session.commit()
        log_audit(db_session, user_id, doc.investigation_id, "Processing Completed",
                  f"Full pipeline complete for '{doc.original_filename}'", doc.id)
    except Exception as e:
        doc.processing_status = "error"
        db_session.commit()
        log_audit(db_session, user_id, doc.investigation_id, "Processing Error",
                  f"Error: {str(e)[:200]}", doc.id)


@router.post("/process/{doc_id}")
def process_document(doc_id: int, background_tasks: BackgroundTasks,
                     db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    doc = db.query(Document).filter(Document.id == doc_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    def run_bg():
        bg_db = SessionLocal()
        try:
            run_full_pipeline(doc_id, current_user.id, bg_db)
        finally:
            bg_db.close()

    background_tasks.add_task(run_bg)
    return {"message": "Processing started", "doc_id": doc_id}


@router.get("/status/{doc_id}")
def get_status(doc_id: int, db: Session = Depends(get_db),
               current_user: User = Depends(get_current_user)):
    doc = db.query(Document).filter(Document.id == doc_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Not found")
    return {"doc_id": doc_id, "status": doc.processing_status,
            "doc_type": doc.doc_type, "confidence": doc.classification_confidence}


@router.post("/correlate/{investigation_id}")
def correlate_documents(investigation_id: int, db: Session = Depends(get_db),
                        current_user: User = Depends(get_current_user)):
    from services import cross_doc_correlation
    inv = db.query(Investigation).filter(Investigation.id == investigation_id,
                                          Investigation.created_by == current_user.id).first()
    if not inv:
        raise HTTPException(status_code=404, detail="Investigation not found")
    docs = db.query(Document).filter(Document.investigation_id == investigation_id,
                                      Document.processing_status == "completed").all()
    if len(docs) < 2:
        return {"message": "Need at least 2 processed documents", "matches": []}

    db.query(CrossDocMatch).filter(CrossDocMatch.investigation_id == investigation_id).delete()
    db.commit()

    doc_fields = {}
    for doc in docs:
        fields = db.query(ExtractedField).filter(ExtractedField.document_id == doc.id).all()
        doc_fields[doc.id] = {f.field_name: f.field_value for f in fields}

    matches = cross_doc_correlation.correlate(doc_fields, docs)
    counter = db.query(Anomaly).filter(Anomaly.investigation_id == investigation_id).count()
    for m in matches:
        db.add(CrossDocMatch(investigation_id=investigation_id, field_name=m["field_name"],
                              doc1_id=m["doc1_id"], doc2_id=m["doc2_id"],
                              value1=m["value1"], value2=m["value2"],
                              doc1_name=m["doc1_name"], doc2_name=m["doc2_name"],
                              match_status=m["status"], confidence=m.get("confidence", 1.0)))
        if m["status"] == "mismatch":
            counter += 1
            db.add(Anomaly(investigation_id=investigation_id, document_id=m["doc1_id"],
                            anomaly_id_str=f"ANO-{counter:04d}", category="cross_document",
                            description=f"Field '{m['field_name']}': '{m['value1']}' in {m['doc1_name']} vs '{m['value2']}' in {m['doc2_name']}",
                            severity="High", confidence=m.get("confidence", 0.85),
                            detection_method="Cross-Document Correlation",
                            evidence_reference=f"{m['doc1_name']} ↔ {m['doc2_name']}"))
    db.commit()
    log_audit(db, current_user.id, investigation_id, "Cross-Document Correlation Completed",
              f"Correlated {len(docs)} docs, {sum(1 for m in matches if m['status']=='mismatch')} mismatches")
    return {"matches": matches, "total": len(matches),
            "mismatches": sum(1 for m in matches if m["status"] == "mismatch")}


@router.get("/correlate/{investigation_id}/results")
def correlation_results(investigation_id: int, db: Session = Depends(get_db),
                        current_user: User = Depends(get_current_user)):
    matches = db.query(CrossDocMatch).filter(CrossDocMatch.investigation_id == investigation_id).all()
    return [{"id": m.id, "field_name": m.field_name, "doc1_name": m.doc1_name,
              "doc2_name": m.doc2_name, "value1": m.value1, "value2": m.value2,
              "match_status": m.match_status, "confidence": m.confidence,
              "doc1_id": m.doc1_id, "doc2_id": m.doc2_id} for m in matches]

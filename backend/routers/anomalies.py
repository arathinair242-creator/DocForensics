from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Optional
from database import get_db, Anomaly, AuditLog, User, Document
from routers.auth_router import get_current_user
from pydantic import BaseModel

router = APIRouter(prefix="/anomalies", tags=["anomalies"])


class AnomalyUpdate(BaseModel):
    status: Optional[str] = None
    investigator_notes: Optional[str] = None


def log_audit(db, user_id, investigation_id, activity, details="", document_id=None):
    db.add(AuditLog(user_id=user_id, investigation_id=investigation_id,
                    document_id=document_id, activity=activity, details=details))
    db.commit()


@router.get("/{investigation_id}")
def get_anomalies(investigation_id: int, category: Optional[str] = None,
                  severity: Optional[str] = None, doc_id: Optional[int] = None,
                  db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    q = db.query(Anomaly).filter(Anomaly.investigation_id == investigation_id)
    if category:
        q = q.filter(Anomaly.category == category)
    if severity:
        q = q.filter(Anomaly.severity == severity)
    if doc_id:
        q = q.filter(Anomaly.document_id == doc_id)
    anomalies = q.order_by(Anomaly.created_at.desc()).all()
    result = []
    for a in anomalies:
        doc = db.query(Document).filter(Document.id == a.document_id).first()
        result.append({"id": a.id, "anomaly_id_str": a.anomaly_id_str, "document_id": a.document_id,
                        "document_name": doc.original_filename if doc else "Unknown",
                        "category": a.category, "description": a.description, "severity": a.severity,
                        "confidence": a.confidence, "page_number": a.page_number,
                        "bbox_json": a.bbox_json, "detection_method": a.detection_method,
                        "evidence_reference": a.evidence_reference, "status": a.status,
                        "investigator_notes": a.investigator_notes, "created_at": a.created_at})
    return result


@router.patch("/{anomaly_id}")
def update_anomaly(anomaly_id: int, update: AnomalyUpdate, db: Session = Depends(get_db),
                   current_user: User = Depends(get_current_user)):
    a = db.query(Anomaly).filter(Anomaly.id == anomaly_id).first()
    if not a:
        raise HTTPException(status_code=404, detail="Anomaly not found")
    if update.status:
        a.status = update.status
    if update.investigator_notes is not None:
        a.investigator_notes = update.investigator_notes
    db.commit()
    log_audit(db, current_user.id, a.investigation_id, "Anomaly Updated",
              f"{a.anomaly_id_str} → '{update.status}'", a.document_id)
    return {"id": a.id, "status": a.status, "investigator_notes": a.investigator_notes}


@router.get("/stats/{investigation_id}")
def anomaly_stats(investigation_id: int, db: Session = Depends(get_db),
                  current_user: User = Depends(get_current_user)):
    anomalies = db.query(Anomaly).filter(Anomaly.investigation_id == investigation_id).all()
    sev = {"Low": 0, "Medium": 0, "High": 0, "Critical": 0}
    cat = {"visual": 0, "contextual": 0, "cross_document": 0, "structural": 0}
    for a in anomalies:
        sev[a.severity] = sev.get(a.severity, 0) + 1
        cat[a.category] = cat.get(a.category, 0) + 1
    return {"by_severity": sev, "by_category": cat, "total": len(anomalies)}


@router.post("/{anomaly_id}/explain")
def explain_anomaly_endpoint(anomaly_id: int, db: Session = Depends(get_db),
                             current_user: User = Depends(get_current_user)):
    a = db.query(Anomaly).filter(Anomaly.id == anomaly_id).first()
    if not a:
        raise HTTPException(status_code=404, detail="Anomaly not found")
    doc = db.query(Document).filter(Document.id == a.document_id).first()
    doc_name = doc.original_filename if doc else "Document"
    from services import llm_service
    explanation = llm_service.explain_anomaly(a.category, a.description, a.evidence_reference or "", doc_name)
    status_info = llm_service.get_llm_status()
    return {
        "anomaly_id": a.id,
        "anomaly_id_str": a.anomaly_id_str,
        "explanation": explanation,
        "llm_status": status_info
    }

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from typing import Literal
from typing import Optional
from database import get_db, Investigation, Document, Anomaly, AuditLog, User, InvestigationNote
from routers.auth_router import get_current_user

router = APIRouter(prefix="/investigations", tags=["investigations"])


class InvestigationCreate(BaseModel):
    name: str
    description: Optional[str] = ""


class InvestigationNoteCreate(BaseModel):
    note_type: Literal["lead", "follow_up", "finding", "conclusion"] = "lead"
    title: str = Field(min_length=1, max_length=120)
    content: str = Field(min_length=1, max_length=5000)
    anomaly_id: Optional[int] = None


def log_audit(db, user_id, investigation_id, activity, details="", document_id=None):
    log = AuditLog(user_id=user_id, investigation_id=investigation_id,
                   document_id=document_id, activity=activity, details=details)
    db.add(log)
    db.commit()


@router.get("/{investigation_id}/notes")
def list_investigation_notes(investigation_id: int, db: Session = Depends(get_db),
                             current_user: User = Depends(get_current_user)):
    inv = db.query(Investigation).filter(
        Investigation.id == investigation_id,
        Investigation.created_by == current_user.id
    ).first()
    if not inv:
        raise HTTPException(status_code=404, detail="Investigation not found")

    notes = db.query(InvestigationNote).filter(
        InvestigationNote.investigation_id == investigation_id
    ).order_by(InvestigationNote.created_at.desc(), InvestigationNote.id.desc()).all()
    return [{
        "id": note.id,
        "note_type": note.note_type,
        "title": note.title,
        "content": note.content,
        "anomaly_id": note.anomaly_id,
        "created_at": note.created_at,
        "author": db.query(User.full_name).filter(User.id == note.user_id).scalar() or "Unknown",
    } for note in notes]


@router.post("/{investigation_id}/notes", status_code=201)
def create_investigation_note(investigation_id: int, req: InvestigationNoteCreate,
                              db: Session = Depends(get_db),
                              current_user: User = Depends(get_current_user)):
    inv = db.query(Investigation).filter(
        Investigation.id == investigation_id,
        Investigation.created_by == current_user.id
    ).first()
    if not inv:
        raise HTTPException(status_code=404, detail="Investigation not found")

    title = req.title.strip()
    content = req.content.strip()
    if not title or not content:
        raise HTTPException(status_code=422, detail="Title and note content cannot be blank")

    if req.anomaly_id is not None:
        anomaly = db.query(Anomaly).filter(
            Anomaly.id == req.anomaly_id,
            Anomaly.investigation_id == investigation_id
        ).first()
        if not anomaly:
            raise HTTPException(status_code=400, detail="Selected finding does not belong to this investigation")

    note = InvestigationNote(
        investigation_id=investigation_id,
        user_id=current_user.id,
        anomaly_id=req.anomaly_id,
        note_type=req.note_type,
        title=title,
        content=content,
    )
    db.add(note)
    db.commit()
    db.refresh(note)
    log_audit(db, current_user.id, investigation_id, "Investigation Note Added",
              f"{req.note_type.replace('_', ' ').title()}: {title}")
    return {
        "id": note.id,
        "note_type": note.note_type,
        "title": note.title,
        "content": note.content,
        "anomaly_id": note.anomaly_id,
        "created_at": note.created_at,
        "author": current_user.full_name,
    }


@router.post("/")
def create_investigation(req: InvestigationCreate, db: Session = Depends(get_db),
                         current_user: User = Depends(get_current_user)):
    inv = Investigation(name=req.name, description=req.description, created_by=current_user.id)
    db.add(inv)
    db.commit()
    db.refresh(inv)
    log_audit(db, current_user.id, inv.id, "Investigation Created", f"'{req.name}' created")
    return {"id": inv.id, "name": inv.name, "description": inv.description,
            "status": inv.status, "created_at": inv.created_at}


@router.get("/dashboard-stats")
def dashboard_stats(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    user_inv_ids = [i.id for i in db.query(Investigation.id).filter(
        Investigation.created_by == current_user.id).all()]
    total_investigations = len(user_inv_ids)
    total_documents = db.query(Document).filter(
        Document.investigation_id.in_(user_inv_ids)).count() if user_inv_ids else 0
    requiring_review = db.query(Document).filter(
        Document.investigation_id.in_(user_inv_ids),
        Document.processing_status == "completed").count() if user_inv_ids else 0
    total_anomalies = db.query(Anomaly).filter(
        Anomaly.investigation_id.in_(user_inv_ids)).count() if user_inv_ids else 0
    critical_anomalies = db.query(Anomaly).filter(
        Anomaly.investigation_id.in_(user_inv_ids),
        Anomaly.severity == "Critical").count() if user_inv_ids else 0
    pending_docs = db.query(Document).filter(
        Document.investigation_id.in_(user_inv_ids),
        Document.processing_status.in_(["pending", "processing"])).count() if user_inv_ids else 0
    recent_invs = db.query(Investigation).filter(
        Investigation.created_by == current_user.id).order_by(
        Investigation.created_at.desc()).limit(5).all()
    recent_logs = db.query(AuditLog).filter(
        AuditLog.user_id == current_user.id).order_by(
        AuditLog.timestamp.desc()).limit(10).all()
    return {
        "total_investigations": total_investigations,
        "total_documents": total_documents,
        "requiring_review": requiring_review,
        "total_anomalies": total_anomalies,
        "critical_anomalies": critical_anomalies,
        "pending_documents": pending_docs,
        "recent_investigations": [{"id": i.id, "name": i.name, "status": i.status,
                                    "created_at": i.created_at} for i in recent_invs],
        "recent_activities": [{"activity": l.activity, "details": l.details,
                                "timestamp": l.timestamp} for l in recent_logs]
    }


@router.get("/")
def list_investigations(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    invs = db.query(Investigation).filter(Investigation.created_by == current_user.id)\
        .order_by(Investigation.created_at.desc()).all()
    result = []
    for inv in invs:
        doc_count = db.query(Document).filter(Document.investigation_id == inv.id).count()
        anomaly_count = db.query(Anomaly).filter(Anomaly.investigation_id == inv.id).count()
        result.append({"id": inv.id, "name": inv.name, "description": inv.description,
                        "status": inv.status, "created_at": inv.created_at,
                        "document_count": doc_count, "anomaly_count": anomaly_count})
    return result


@router.get("/{investigation_id}")
def get_investigation(investigation_id: int, db: Session = Depends(get_db),
                      current_user: User = Depends(get_current_user)):
    inv = db.query(Investigation).filter(Investigation.id == investigation_id,
                                          Investigation.created_by == current_user.id).first()
    if not inv:
        raise HTTPException(status_code=404, detail="Investigation not found")
    docs = db.query(Document).filter(Document.investigation_id == inv.id).all()
    anomalies = db.query(Anomaly).filter(Anomaly.investigation_id == inv.id).all()
    return {"id": inv.id, "name": inv.name, "description": inv.description,
            "status": inv.status, "created_at": inv.created_at,
            "documents": [{"id": d.id, "original_filename": d.original_filename,
                            "doc_type": d.doc_type, "processing_status": d.processing_status,
                            "file_size": d.file_size, "created_at": d.created_at} for d in docs],
            "anomaly_count": len(anomalies)}


@router.patch("/{investigation_id}/status")
def update_status(investigation_id: int, new_status: str, db: Session = Depends(get_db),
                  current_user: User = Depends(get_current_user)):
    inv = db.query(Investigation).filter(Investigation.id == investigation_id,
                                          Investigation.created_by == current_user.id).first()
    if not inv:
        raise HTTPException(status_code=404, detail="Not found")
    inv.status = new_status
    db.commit()
    return {"status": new_status}

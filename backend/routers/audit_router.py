from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from database import get_db, AuditLog, User, Investigation, Document
from routers.auth_router import get_current_user

router = APIRouter(prefix="/audit", tags=["audit"])


def _format_logs(logs, db):
    result = []
    for log in logs:
        doc_name = None
        if log.document_id:
            doc = db.query(Document).filter(Document.id == log.document_id).first()
            doc_name = doc.original_filename if doc else None
        inv_name = None
        if log.investigation_id:
            inv = db.query(Investigation).filter(Investigation.id == log.investigation_id).first()
            inv_name = inv.name if inv else None
        user = db.query(User).filter(User.id == log.user_id).first()
        result.append({"id": log.id, "activity": log.activity, "details": log.details,
                        "timestamp": log.timestamp, "user_name": user.full_name if user else "System",
                        "investigation_id": log.investigation_id, "investigation_name": inv_name,
                        "document_id": log.document_id, "document_name": doc_name})
    return result


@router.get("/")
def get_all_audit_logs(db: Session = Depends(get_db), current_user: User = Depends(get_current_user),
                       limit: int = 200):
    user_inv_ids = [i.id for i in db.query(Investigation.id).filter(
        Investigation.created_by == current_user.id).all()]
    if not user_inv_ids:
        return []
    logs = db.query(AuditLog).filter(
        AuditLog.investigation_id.in_(user_inv_ids)).order_by(
        AuditLog.timestamp.desc()).limit(limit).all()
    return _format_logs(logs, db)


@router.get("/{investigation_id}")
def get_investigation_audit(investigation_id: int, db: Session = Depends(get_db),
                             current_user: User = Depends(get_current_user)):
    logs = db.query(AuditLog).filter(AuditLog.investigation_id == investigation_id)\
        .order_by(AuditLog.timestamp.desc()).all()
    return _format_logs(logs, db)

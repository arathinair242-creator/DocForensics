from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from database import get_db, Investigation, Document, ExtractedField, Anomaly, AuditLog, CrossDocMatch, User
from routers.auth_router import get_current_user
from services import dossier_generator
import os

router = APIRouter(prefix="/dossier", tags=["dossier"])
DOSSIERS_DIR = "dossiers"


def log_audit(db, user_id, investigation_id, activity, details=""):
    db.add(AuditLog(user_id=user_id, investigation_id=investigation_id, activity=activity, details=details))
    db.commit()


@router.post("/{investigation_id}/generate")
def generate_dossier(investigation_id: int, db: Session = Depends(get_db),
                     current_user: User = Depends(get_current_user)):
    inv = db.query(Investigation).filter(Investigation.id == investigation_id,
                                          Investigation.created_by == current_user.id).first()
    if not inv:
        raise HTTPException(status_code=404, detail="Investigation not found")
    docs = db.query(Document).filter(Document.investigation_id == investigation_id).all()
    all_fields = {doc.id: db.query(ExtractedField).filter(ExtractedField.document_id == doc.id).all()
                  for doc in docs}
    anomalies = db.query(Anomaly).filter(Anomaly.investigation_id == investigation_id).all()
    cross_matches = db.query(CrossDocMatch).filter(CrossDocMatch.investigation_id == investigation_id).all()
    os.makedirs(DOSSIERS_DIR, exist_ok=True)
    output_path = os.path.join(DOSSIERS_DIR, f"dossier_{investigation_id}.pdf")
    dossier_generator.generate(output_path=output_path, investigation=inv, documents=docs,
                                fields_by_doc=all_fields, anomalies=anomalies,
                                cross_matches=cross_matches, investigator_name=current_user.full_name)
    log_audit(db, current_user.id, investigation_id, "Dossier Generated",
              f"Investigation dossier generated for '{inv.name}'")
    return {"message": "Dossier generated successfully", "path": output_path}


@router.get("/{investigation_id}/download")
def download_dossier(investigation_id: int, db: Session = Depends(get_db),
                     current_user: User = Depends(get_current_user)):
    inv = db.query(Investigation).filter(Investigation.id == investigation_id,
                                          Investigation.created_by == current_user.id).first()
    if not inv:
        raise HTTPException(status_code=404, detail="Not found")
    path = os.path.join(DOSSIERS_DIR, f"dossier_{investigation_id}.pdf")
    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail="Dossier not yet generated. Please generate first.")
    fname = f"Dossier_{inv.name.replace(' ', '_')}_{investigation_id}.pdf"
    return FileResponse(path, filename=fname, media_type="application/pdf")

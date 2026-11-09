from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, BackgroundTasks
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from database import get_db, Document, ExtractedField, Investigation, AuditLog, User
from routers.auth_router import get_current_user
import os, uuid

router = APIRouter(prefix="/documents", tags=["documents"])
UPLOAD_DIR = os.getenv("UPLOAD_DIR", "uploads")
ALLOWED_EXTENSIONS = {".pdf", ".jpg", ".jpeg", ".png"}
MAX_FILE_SIZE = 50 * 1024 * 1024


def log_audit(db, user_id, investigation_id, activity, details="", document_id=None):
    log = AuditLog(user_id=user_id, investigation_id=investigation_id,
                   document_id=document_id, activity=activity, details=details)
    db.add(log)
    db.commit()


@router.post("/upload")
async def upload_document(investigation_id: int = Form(...), file: UploadFile = File(...),
                           db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    inv = db.query(Investigation).filter(Investigation.id == investigation_id,
                                          Investigation.created_by == current_user.id).first()
    if not inv:
        raise HTTPException(status_code=404, detail="Investigation not found")
    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail=f"Unsupported file type: {ext}")
    contents = await file.read()
    if len(contents) > MAX_FILE_SIZE:
        raise HTTPException(status_code=400, detail="File too large (max 50MB)")
    os.makedirs(UPLOAD_DIR, exist_ok=True)
    stored_name = f"{uuid.uuid4()}{ext}"
    file_path = os.path.join(UPLOAD_DIR, stored_name)
    with open(file_path, "wb") as f:
        f.write(contents)
    doc = Document(investigation_id=investigation_id, original_filename=file.filename,
                   stored_filename=stored_name, file_path=file_path, file_size=len(contents),
                   processing_status="pending", source_reference=f"Uploaded by {current_user.full_name}")
    db.add(doc)
    db.commit()
    db.refresh(doc)
    log_audit(db, current_user.id, investigation_id, "Document Uploaded",
              f"'{file.filename}' ({len(contents)} bytes)", doc.id)
    return {"id": doc.id, "original_filename": doc.original_filename,
            "file_size": doc.file_size, "processing_status": doc.processing_status,
            "created_at": doc.created_at}


@router.get("/{document_id}")
def get_document(document_id: int, db: Session = Depends(get_db),
                 current_user: User = Depends(get_current_user)):
    doc = db.query(Document).filter(Document.id == document_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    fields = db.query(ExtractedField).filter(ExtractedField.document_id == document_id).all()
    return {"id": doc.id, "original_filename": doc.original_filename, "doc_type": doc.doc_type,
            "classification_confidence": doc.classification_confidence,
            "processing_status": doc.processing_status, "file_size": doc.file_size,
            "page_count": doc.page_count, "source_reference": doc.source_reference,
            "annotated_path": doc.annotated_path, "created_at": doc.created_at,
            "extracted_fields": [{"id": f.id, "field_name": f.field_name, "field_value": f.field_value,
                                   "confidence": f.confidence, "page_number": f.page_number,
                                   "bbox_json": f.bbox_json, "section": f.section,
                                   "is_verified": f.is_verified} for f in fields]}


@router.get("/{document_id}/preview")
def preview_document(document_id: int, db: Session = Depends(get_db),
                     current_user: User = Depends(get_current_user)):
    doc = db.query(Document).filter(Document.id == document_id).first()
    if not doc or not os.path.exists(doc.file_path):
        raise HTTPException(status_code=404, detail="Document file not found")
    return FileResponse(doc.file_path, filename=doc.original_filename)


@router.get("/{document_id}/annotated")
def annotated_document(document_id: int, db: Session = Depends(get_db),
                       current_user: User = Depends(get_current_user)):
    doc = db.query(Document).filter(Document.id == document_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Not found")
    path = doc.annotated_path if doc.annotated_path and os.path.exists(doc.annotated_path) else doc.file_path
    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail="File not found")
    return FileResponse(path)


@router.patch("/{document_id}/classification")
def update_classification(document_id: int, doc_type: str, db: Session = Depends(get_db),
                          current_user: User = Depends(get_current_user)):
    doc = db.query(Document).filter(Document.id == document_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Not found")
    doc.doc_type = doc_type
    db.commit()
    log_audit(db, current_user.id, doc.investigation_id, "Classification Updated",
              f"'{doc.original_filename}' → '{doc_type}'", doc.id)
    return {"doc_type": doc_type}


@router.patch("/fields/{field_id}")
def update_field(field_id: int, value: str, db: Session = Depends(get_db),
                 current_user: User = Depends(get_current_user)):
    field = db.query(ExtractedField).filter(ExtractedField.id == field_id).first()
    if not field:
        raise HTTPException(status_code=404, detail="Field not found")
    field.field_value = value
    field.is_verified = True
    db.commit()
    return {"field_id": field_id, "field_value": value}


@router.get("/by-investigation/{investigation_id}")
def docs_by_investigation(investigation_id: int, db: Session = Depends(get_db),
                           current_user: User = Depends(get_current_user)):
    docs = db.query(Document).filter(Document.investigation_id == investigation_id).all()
    result = []
    for doc in docs:
        fc = db.query(ExtractedField).filter(ExtractedField.document_id == doc.id).count()
        result.append({"id": doc.id, "original_filename": doc.original_filename,
                        "doc_type": doc.doc_type, "classification_confidence": doc.classification_confidence,
                        "processing_status": doc.processing_status, "file_size": doc.file_size,
                        "page_count": doc.page_count, "created_at": doc.created_at, "field_count": fc})
    return result

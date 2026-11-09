from fastapi import APIRouter, Depends, BackgroundTasks
from sqlalchemy.orm import Session
from database import get_db, User, Investigation, AuditLog, SessionLocal
from routers.auth_router import get_current_user

router = APIRouter(prefix="/demo", tags=["demo"])


def log_audit(db, user_id, investigation_id, activity, details=""):
    db.add(AuditLog(user_id=user_id, investigation_id=investigation_id, activity=activity, details=details))
    db.commit()


@router.post("/load")
def load_demo_investigation(background_tasks: BackgroundTasks, db: Session = Depends(get_db),
                             current_user: User = Depends(get_current_user)):
    inv = Investigation(name="[DEMO] Document Investigation Sample",
                        description="Synthetic demonstration investigation using artificially created sample documents to showcase all platform capabilities. All documents are clearly marked SYNTHETIC.",
                        created_by=current_user.id, status="in_progress")
    db.add(inv)
    db.commit()
    db.refresh(inv)
    log_audit(db, current_user.id, inv.id, "Demo Investigation Created",
              "Synthetic demonstration investigation loaded")
    inv_id = inv.id
    user_id = current_user.id

    def run_demo():
        bg_db = SessionLocal()
        try:
            from services import demo_data
            demo_data.create_demo_documents(bg_db, inv_id, user_id)
        finally:
            bg_db.close()

    background_tasks.add_task(run_demo)
    return {"investigation_id": inv.id,
            "message": "Demo investigation is being prepared. Documents will be ready in 30-60 seconds."}

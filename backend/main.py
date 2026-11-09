from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from dotenv import load_dotenv
import os

load_dotenv()

from database import engine, Base
Base.metadata.create_all(bind=engine)

from routers import auth_router, investigations, documents, analysis, anomalies, dossier_router, audit_router, demo_router

app = FastAPI(title="DocForensics API",
              description="AI-Powered Document Forensics and Contextual Intelligence System",
              version="1.0.0")

app.add_middleware(CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000", "http://127.0.0.1:5173"],
    allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

for d in ["uploads", "uploads/annotated", "dossiers", "demo_docs"]:
    os.makedirs(d, exist_ok=True)

app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

app.include_router(auth_router.router)
app.include_router(investigations.router)
app.include_router(documents.router)
app.include_router(analysis.router)
app.include_router(anomalies.router)
app.include_router(dossier_router.router)
app.include_router(audit_router.router)
app.include_router(demo_router.router)


@app.get("/health")
def health():
    return {"status": "ok", "service": "DocForensics API v1.0.0"}


@app.get("/")
def root():
    return {"message": "DocForensics API"}

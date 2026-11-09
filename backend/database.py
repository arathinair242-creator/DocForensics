from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Text, ForeignKey, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
from datetime import datetime
import os

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./docforensics.db")

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    full_name = Column(String, nullable=False)
    hashed_password = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    investigations = relationship("Investigation", back_populates="owner")
    audit_logs = relationship("AuditLog", back_populates="user")


class Investigation(Base):
    __tablename__ = "investigations"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    description = Column(Text, default="")
    status = Column(String, default="open")
    created_by = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    owner = relationship("User", back_populates="investigations")
    documents = relationship("Document", back_populates="investigation", cascade="all, delete-orphan")
    anomalies = relationship("Anomaly", back_populates="investigation", cascade="all, delete-orphan")
    audit_logs = relationship("AuditLog", back_populates="investigation")
    cross_matches = relationship("CrossDocMatch", back_populates="investigation", cascade="all, delete-orphan")


class Document(Base):
    __tablename__ = "documents"
    id = Column(Integer, primary_key=True, index=True)
    investigation_id = Column(Integer, ForeignKey("investigations.id"))
    original_filename = Column(String, nullable=False)
    stored_filename = Column(String, nullable=False)
    file_path = Column(String, nullable=False)
    file_size = Column(Integer, default=0)
    doc_type = Column(String, default="Other")
    classification_confidence = Column(Float, default=0.0)
    processing_status = Column(String, default="pending")
    page_count = Column(Integer, default=1)
    source_reference = Column(String, default="")
    annotated_path = Column(String, default="")
    created_at = Column(DateTime, default=datetime.utcnow)
    investigation = relationship("Investigation", back_populates="documents")
    extracted_fields = relationship("ExtractedField", back_populates="document", cascade="all, delete-orphan")
    anomalies = relationship("Anomaly", back_populates="document", cascade="all, delete-orphan")
    audit_logs = relationship("AuditLog", back_populates="document")


class ExtractedField(Base):
    __tablename__ = "extracted_fields"
    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(Integer, ForeignKey("documents.id"))
    field_name = Column(String, nullable=False)
    field_value = Column(Text, default="")
    confidence = Column(Float, default=0.0)
    page_number = Column(Integer, default=1)
    bbox_json = Column(Text, default="")
    section = Column(String, default="")
    is_verified = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    document = relationship("Document", back_populates="extracted_fields")


class Anomaly(Base):
    __tablename__ = "anomalies"
    id = Column(Integer, primary_key=True, index=True)
    investigation_id = Column(Integer, ForeignKey("investigations.id"))
    document_id = Column(Integer, ForeignKey("documents.id"))
    anomaly_id_str = Column(String, default="")
    category = Column(String, default="")
    description = Column(Text, default="")
    severity = Column(String, default="Low")
    confidence = Column(Float, default=0.0)
    page_number = Column(Integer, default=1)
    bbox_json = Column(Text, default="")
    detection_method = Column(String, default="")
    evidence_reference = Column(Text, default="")
    status = Column(String, default="detected")
    investigator_notes = Column(Text, default="")
    created_at = Column(DateTime, default=datetime.utcnow)
    investigation = relationship("Investigation", back_populates="anomalies")
    document = relationship("Document", back_populates="anomalies")


class AuditLog(Base):
    __tablename__ = "audit_logs"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    investigation_id = Column(Integer, ForeignKey("investigations.id"), nullable=True)
    document_id = Column(Integer, ForeignKey("documents.id"), nullable=True)
    activity = Column(String, nullable=False)
    details = Column(Text, default="")
    timestamp = Column(DateTime, default=datetime.utcnow)
    user = relationship("User", back_populates="audit_logs")
    investigation = relationship("Investigation", back_populates="audit_logs")
    document = relationship("Document", back_populates="audit_logs")


class CrossDocMatch(Base):
    __tablename__ = "cross_doc_matches"
    id = Column(Integer, primary_key=True, index=True)
    investigation_id = Column(Integer, ForeignKey("investigations.id"))
    field_name = Column(String, nullable=False)
    doc1_id = Column(Integer, ForeignKey("documents.id"))
    doc2_id = Column(Integer, ForeignKey("documents.id"))
    value1 = Column(Text, default="")
    value2 = Column(Text, default="")
    doc1_name = Column(String, default="")
    doc2_name = Column(String, default="")
    match_status = Column(String, default="match")
    confidence = Column(Float, default=1.0)
    created_at = Column(DateTime, default=datetime.utcnow)
    investigation = relationship("Investigation", back_populates="cross_matches")


class InvestigationNote(Base):
    __tablename__ = "investigation_notes"
    id = Column(Integer, primary_key=True, index=True)
    investigation_id = Column(Integer, ForeignKey("investigations.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    anomaly_id = Column(Integer, ForeignKey("anomalies.id"), nullable=True)
    note_type = Column(String, nullable=False, default="lead")
    title = Column(String(120), nullable=False)
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

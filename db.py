import os
from datetime import datetime
from typing import Optional

from sqlalchemy import (
    Column,
    DateTime,
    Integer,
    String,
    Text,
    create_engine,
)
from sqlalchemy.orm import declarative_base, sessionmaker, Session


Base = declarative_base()


class AnalysisResult(Base):
    __tablename__ = "analysis_results"

    id = Column(Integer, primary_key=True, index=True)
    job_id = Column(String(64), index=True, nullable=True)
    file_name = Column(String(255), nullable=True)
    file_path = Column(String(512), nullable=True)
    query = Column(Text, nullable=False)
    analysis = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)


def _get_database_url() -> str:
    # Default to a local SQLite database inside the data directory
    default_url = "sqlite:///./data/analysis.db"
    return os.getenv("DATABASE_URL", default_url)


def _create_engine():
    database_url = _get_database_url()

    # Ensure data directory exists for the default SQLite URL
    if database_url.startswith("sqlite:///./data/"):
        os.makedirs("data", exist_ok=True)
        connect_args = {"check_same_thread": False}
    else:
        connect_args = {}

    return create_engine(database_url, connect_args=connect_args)


engine = _create_engine()
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_db() -> None:
    """Create tables if they do not exist."""
    Base.metadata.create_all(bind=engine)


def save_analysis(
    query: str,
    analysis: str,
    file_name: Optional[str] = None,
    file_path: Optional[str] = None,
    job_id: Optional[str] = None,
) -> AnalysisResult:
    """Persist a single analysis result and return the ORM object."""
    init_db()
    db: Session = SessionLocal()
    try:
        record = AnalysisResult(
            job_id=job_id,
            file_name=file_name,
            file_path=file_path,
            query=query,
            analysis=analysis,
        )
        db.add(record)
        db.commit()
        db.refresh(record)
        return record
    finally:
        db.close()


def get_analysis_by_job_id(job_id: str) -> Optional[AnalysisResult]:
    init_db()
    db: Session = SessionLocal()
    try:
        return (
            db.query(AnalysisResult)
            .filter(AnalysisResult.job_id == job_id)
            .order_by(AnalysisResult.id.desc())
            .first()
        )
    finally:
        db.close()


from fastapi import FastAPI, File, UploadFile, Form, HTTPException, BackgroundTasks
import os
import sys
import uuid

from crew_runner import run_crew  # noqa: F401  (imported for completeness)
from jobs import run_analysis_job
from db import get_analysis_by_job_id


# Ensure logs can handle UTF-8 on Windows consoles
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
if hasattr(sys.stderr, "reconfigure"):
    try:
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass


app = FastAPI(title="Financial Document Analyzer")


@app.get("/")
async def root():
    """Health check endpoint"""
    return {"message": "Financial Document Analyzer API is running"}


@app.post("/analyze")
async def analyze_financial_document_endpoint(
    file: UploadFile = File(...),
    query: str = Form(default="Analyze this financial document for investment insights"),
):
    """Synchronously analyze a financial document and return the full analysis."""

    file_id = str(uuid.uuid4())
    file_path = f"data/financial_document_{file_id}.pdf"

    try:
        os.makedirs("data", exist_ok=True)

        with open(file_path, "wb") as f:
            content = await file.read()
            f.write(content)

        if not query:
            query = "Analyze this financial document for investment insights"

        result = run_analysis_job(
            query=query.strip(),
            file_path=file_path,
            file_name=file.filename,
            job_id=None,
        )

        return {
            "status": "success",
            "mode": "sync",
            "query": query.strip(),
            "analysis_id": result["id"],
            "analysis_metadata": result,
            "file_processed": file.filename,
        }

    except Exception:
        raise HTTPException(
            status_code=500,
            detail=(
                "Unexpected error while processing the financial document. "
                "Please check the server logs for details."
            ),
        )

    finally:
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
            except Exception:
                pass


@app.post("/analyze/async")
async def analyze_financial_document_async(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    query: str = Form(default="Analyze this financial document for investment insights"),
):
    """Enqueue an asynchronous analysis job using FastAPI background tasks."""

    file_id = str(uuid.uuid4())
    job_id = str(uuid.uuid4())
    file_path = f"data/financial_document_{file_id}.pdf"

    try:
        os.makedirs("data", exist_ok=True)

        with open(file_path, "wb") as f:
            content = await file.read()
            f.write(content)

        if not query:
            query = "Analyze this financial document for investment insights"

        # Schedule background execution within this process (Windows-friendly)
        background_tasks.add_task(
            run_analysis_job,
            query.strip(),
            file_path,
            file.filename,
            job_id,
        )

        return {
            "status": "queued",
            "mode": "async",
            "job_id": job_id,
            "query": query.strip(),
            "file_saved_as": file_path,
        }

    except Exception:
        raise HTTPException(
            status_code=500,
            detail=(
                "Unexpected error while enqueuing the financial document. "
                "Please check the server logs for details."
            ),
        )


@app.get("/jobs/{job_id}")
async def get_job_status(job_id: str):
    """Check the status of an asynchronous analysis job and return the stored result if available."""
    record = get_analysis_by_job_id(job_id)

    if record is None:
        status = "pending"
    else:
        status = "finished"

    return {
        "job_id": job_id,
        "status": status,
        "analysis": {
            "id": record.id,
            "query": record.query,
            "file_name": record.file_name,
            "file_path": record.file_path,
            "analysis": record.analysis,
            "created_at": record.created_at.isoformat(),
        }
        if record
        else None,
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)

